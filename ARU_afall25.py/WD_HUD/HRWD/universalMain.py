# --- IMPORTS ---
from Systems.InputSystem import XboxController, cvWebcam, AI_YOLO, AI_Inputs
from Systems.motorSystem import CytronMotor
from Systems.sensorSystem import sensorSystem
from Systems.displaySystem import DisplaySystem
from Systems.mode_State import modeState
from Arm import CoOrdinateBaseSys as Arm

import pygame
import time
import serial
from itertools import permutations

# --- GLOBAL STATE INIT ---
inputState = modeState()

# =========================================================================
# 1. DEFINE MOCK SERIAL CLASS
# =========================================================================
class MockSerial:
    """
    A fake serial class that mimics the behavior of the real PySerial object
    so the rest of the system doesn't crash when Arduino is unplugged.
    """
    def __init__(self):
        self.in_waiting = 0  # Always say there is 0 data waiting to be read
        
    def write(self, data):
        # Optional: Print commands to console to see what WOULD be sent
        # print(f"[MOCK SERIAL] Sending: {data}")
        pass

    def readline(self):
        return b"" # Return empty bytes
        
    def close(self):
        pass

# =========================================================================
# 2. PROMPT USER & HARDWARE SETUP
# =========================================================================
PORT = "/dev/ttyACM0"
BAUD = 115200

# Ask the user before attempting connection


try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    print("✅ Serial Connected Successfully.")
except serial.SerialException as e:
    print(f"❌ Connection Failed: {e}")
    print("⚠️  Falling back to MOCK SERIAL mode.")
    ser = MockSerial()


# =========================================================================
# 3. OBJECT INSTANTIATION (Standard logic continues below)
# =========================================================================




pygame.init()
pygame.joystick.init()

controller = XboxController(state=inputState)
cam = cvWebcam(cam_id=0, width=640, height=480)
infer = AI_YOLO(conf_threshold=0.3)

# Pass the 'ser' object (real or mock) to the systems
motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
sensors = sensorSystem(ser)

display = DisplaySystem(cam.camera, mode="YOLO")
ai_Inputs = AI_Inputs(frame_width=cam.width, frame_height=cam.height, state=inputState)

# --- TIMING VARIABLES ---
max_fps = 60                   # Target speed of the loop
last_time = 0                  # Tracks when the previous loop finished
frame_delay = 1.0 / max_fps    # Minimum time per frame (approx 0.016 seconds)


# --- LOGIC CONFIGURATION ---
# Define the possible colors the robot might look for.
BASE_COLORS = ["Green", "Red", "Yellow", "Blue"]

# Generate all possible orders of these colors (e.g., Green-Red-Yellow-Blue, Red-Green...)
# This is likely for a challenge where the robot must visit colors in a specific order.
ALL_CASES = [list(p) for p in permutations(BASE_COLORS)]

# Map specific command IDs (received from sensors/RFID?) to a specific case index.
# Example: If sensors read ID "22", the robot targets the 0th permutation.
CMD_TO_CASE_MAP = {
    "22": 0,  # Case 1
    "23": 1,  # Case 2
    "24": 2,  # Case 3
    #ect
}

# --- MAIN ENTRY POINT ---
def main():
    global last_time  # Allow modification of the global timer variable
    try:
        # Start an infinite loop
        while True:
            now = time.time()  # Get current time
            
            # Rate Limiter: Only run the logic if enough time has passed (60 FPS cap)
            if now - last_time >= frame_delay:
                inputDisplay() # Call the main logic function
                last_time = now # Reset the timer
                
    except KeyboardInterrupt:
        # If user presses Ctrl+C, run this safety code:
        print("Stopping...")
        motors.set_power(0, 0) # Emergency stop the wheels
        cam.release()          # Free the camera
        infer.release()        # Free the AI memory

# --- CORE LOGIC LOOP ---
def inputDisplay():
    # Dictionary to hold the final Left/Right motor power values (Default 0)
    active_Cmd = {"L": 0, "R": 0}
    
    # 1. READ SENSORS
    # Ask the microcontroller for sensor data (Distance, Battery, Command IDs)
    data = sensors.readSensors()
    
    # Update the AI Driver with this data (so it knows when to stop if close to a wall)
    ai_Inputs.sensorData = data 

    # Check if "CMDID" exists in data AND if it is a valid map key
    # .get() returns None if the key is missing, preventing the crash
    cmd_id = data.get("CMDID")
    
    if cmd_id in CMD_TO_CASE_MAP:
        # Find which color order corresponds to this ID
        case_index = CMD_TO_CASE_MAP[cmd_id]
        # Tell the AI: "These are your new targets, in this order."
        ai_Inputs.targets = ALL_CASES[case_index]


    # 2. READ CONTROLLER
    pygame.event.pump()         # Refresh Pygame internal event queue
    ctrl_data = controller.poll() # Get current joystick positions and button presses

    # 3. VISION INFERENCE
    img = cam.get_frame()       # Grab a photo
    detections = infer.detect(img) # Ask YOLO: "Where are the objects in this photo?"

    # 4. CONTROL LOGIC (The Brain)
    
    # CHECK: Is the Controller plugged in? AND Is AI Mode turned OFF?
    if controller.connected and not inputState.mode:
        # --- MANUAL MODE ---
        ai_Inputs.driving = False # Tell AI to relax
        # Map the Joystick L/R values directly to the motor command
        active_Cmd = {"L": ctrl_data["L"], "R": ctrl_data["R"]}
    
    else:
        # --- AI MODE ---
        # Update the AI with the objects we saw (Vision Tracking)
        if detections:
            ai_Inputs.update_target(detections[0]) # Lock onto the first object found
        else:
            # If blind, stop driving (Safety)
            ai_Inputs.driving = False

        # Run the AI movement logic. 
        # Note: We run this even if 'driving' is False, so it can handle state transitions 
        # or sensor checks.
        ai_data = ai_Inputs.move_command()
        
        # Override the motor command with the AI's calculation
        active_Cmd = {"L": ai_data["L"], "R": ai_data["R"]}

    # 5. SEND TO MOTORS
    # Physically send the calculated power to the wheel controllers
    motors.set_power(active_Cmd["L"], active_Cmd["R"])

    # 6. DISPLAY
    # Draw the camera feed, bounding boxes, joystick status, and motor values to the screen.
    display.update_display(
        img,
        detections,
        controller.get_axes(),
        ctrl_data["buttons"],
        (active_Cmd["L"], active_Cmd["R"]),
        data,
        inputState
    )

# Standard Python check: Only run main() if this file is run directly (not imported)
if __name__ == "__main__":
    main()