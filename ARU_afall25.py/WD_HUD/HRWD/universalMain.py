# --- IMPORTS ---
from Systems.InputSystem import XboxController, cvWebcam, AI_YOLO, AI_Inputs, intelCamera
from Systems.motorSystem import CytronMotor
from Systems.sensorSystem import sensorSystem
from Systems.displaySystem import DisplaySystem
from Systems.mode_State import modeState
from Arm import CoOrdinateBaseSys as Arm

import pygame
import time
import serial
from itertools import permutations

# --- GLOBAL Variables ---
inputState = modeState()



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


PORT = "/dev/ttyACM0"
BAUD = 115200


try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    print("✅ Serial Connected Successfully.")
except serial.SerialException as e:
    print(f"❌ Connection Failed: {e}")
    print("⚠️  Falling back to MOCK SERIAL mode.")
    ser = MockSerial()



pygame.init()
pygame.joystick.init()

controller = XboxController(state=inputState)
cam = cvWebcam(cam_id=6, width=640, height=480)
cam2 = intelCamera(width = 640, height = 480)
infer = AI_YOLO(conf_threshold=0.3)

# Pass the 'ser' object (real or mock) to the systems
motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
sensors = sensorSystem(ser)

display = DisplaySystem(cam.camera, mode="YOLO")
display2 = DisplaySystem(cam = cam2 ,name = "CAM2", mode="YOLO")
ai_Inputs = AI_Inputs(frame_width=cam.width, frame_height=cam.height, state=inputState)

# --- TIMING VARIABLES ---
max_fps = 60                   
last_time = 0                  
frame_delay = 1.0 / max_fps    


# --- LOGIC CONFIGURATION ---
# Define the possible colors the robot might look for.
BASE_COLORS = ["green_ball", "red_ball", "yellow_ball", "blue_ball"]
ALL_CASES = [list(p) for p in permutations(BASE_COLORS)]

CMD_TO_CASE_MAP = {
    "22": 0,  # Case 1
    "23": 1,  # Case 2
    "24": 2,  # Case 3
    #ect
}

# --- MAIN ENTRY POINT ---
def main():
    global last_time  
    try:
        while True:
            now = time.time()  
            # Rate Limiter: Only run the logic if enough time has passed (60 FPS cap)
            if now - last_time >= frame_delay:
                inputDisplay() 
                last_time = now 
                
    except KeyboardInterrupt:
        print("Stopping...")
        motors.set_power(0, 0) 
        cam.release()          
        infer.release()        

# --- CORE LOGIC LOOP ---
def inputDisplay():
    active_Cmd = {"L": 0, "R": 0}
    
    data = sensors.readSensors()
    ai_Inputs.sensorData = data 
    cmd_id = data.get("CMDID")
    
    if cmd_id in CMD_TO_CASE_MAP:
        case_index = CMD_TO_CASE_MAP[cmd_id]
        ai_Inputs.targets = ALL_CASES[case_index]
        print(ALL_CASES[case_index])


    # 2. READ CONTROLLER
    pygame.event.pump()         
    ctrl_data = controller.poll() 

    # 3. VISION INFERENCE
    img = cam.get_frame()       
    detections = infer.detect(img)
    depthImg2, img2 = cam2.get_frames()
    detections2 = infer.detect(img2)

    if controller.connected and not inputState.mode:
        # --- MANUAL MODE ---
        ai_Inputs.driving = False # Tell AI to relax
        active_Cmd = {"L": ctrl_data["L"], "R": ctrl_data["R"]}
    
    else:
        # --- AI MODE ---
        ai_Inputs.update_target(detections2, depthImg2)
        ai_Inputs.update_target(detections2)
        #ai_Inputs.driving = False
        ai_data = ai_Inputs.move_command()
        
        active_Cmd = {"L": ai_data["L"], "R": ai_data["R"]}

    motors.set_power(active_Cmd["L"], active_Cmd["R"])

    # Draw the camera feed, bounding boxes, joystick status, and motor values to the screen.
    display.update_display(
        img2,
        detections2,
        controller.get_axes(),
        ctrl_data["buttons"],
        (active_Cmd["L"], active_Cmd["R"]),
        data,
        inputState
    )
    display2.update_display(img=img, detections=detections)

if __name__ == "__main__":
    main()