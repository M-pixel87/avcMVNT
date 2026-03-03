# --- MAJOR PIVOT UPDATE: TOP CAMERA INTEGRATION & ARM SCANNING ---
# 1. Dual-Camera Tracking: The AI now checks both the bottom (depth) camera and the top (arm) camera for targets.
# 2. Handoff Logic: If the top camera sees a target but the bottom doesn't, it takes over chassis steering. 
#    Since it lacks depth, it feeds a dummy distance (3000mm) to keep the vehicle driving forward until the bottom camera catches sight.
# 3. Active Scanning (Mode 4): When no target is found, the robot spins the chassis AND sweeps the arm left/right (modifying targetY) 
#    to massively increase the field of view. Once a target is spotted, the arm snaps back to center.
# 4. Universal Arm Updates: The arm logic now runs continuously in the main loop, not just in Mode 2, allowing active scanning.

from Systems.InputSystem import XboxController, cvWebcam, AI_YOLO, AI_Inputs, intelCamera
from Systems.motorSystem import CytronMotor
from Systems.sensorSystem import sensorSystem
from Systems.displaySystem import DisplaySystem
from Systems.mode_State import modeState
from Arm import CoOrdinateBaseSys as Arm

import pygame
import time
import serial
import math
import numpy as np
from itertools import permutations

# --- GLOBAL Variables ---
inputState = modeState()

class MockSerial:
    """
    A fake serial class that mimics the behavior of the real PySerial object
    so the rest of the system doesn't crash when Arduino is unplugged.
    """
    def __init__(self):
        self.in_waiting = 0  
        
    def write(self, data):
        pass

    def readline(self):
        return b"" 
        
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

motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
sensors = sensorSystem(ser)

# >>> NEW: Start the background serial reading thread immediately <<<
sensors.start()

display = DisplaySystem(cam.camera, mode="YOLO")
display2 = DisplaySystem(cam = cam2 ,name = "CAM2", mode="YOLO")
ai_Inputs = AI_Inputs(motorSystem = motors, frame_width=cam.width, frame_height=cam.height, state=inputState)

# --- TIMING VARIABLES ---
max_fps = 60                   
last_time = 0                  
frame_delay = 1.0 / max_fps    

# --- LOGIC CONFIGURATION ---
BASE_COLORS = ["green_ball", "red_ball", "yellow_ball", "blue_ball"]
ALL_CASES = [list(p) for p in permutations(BASE_COLORS)]

CMD_TO_CASE_MAP = {
    "22": 0,  
    "23": 1,  
    "24": 2,  
}
time.sleep(2)
motors.set_power(80, -80)
time.sleep(1.75)

# --- MAIN POINT ---
def main():
    global last_time  
    try:
        while True:
            now = time.time()  
            if now - last_time >= frame_delay:
                inputDisplay() 
                last_time = now 
                
    except KeyboardInterrupt:
        print("Stopping...")
        motors.set_power(0, 0) 
        cam.release()          
        infer.release()
        # >>> NEW: Cleanly shut down the background serial thread on exit <<<
        sensors.stop()        

# --- CORE LOGIC LOOP ---
def inputDisplay():
    active_Cmd = {"L": 0, "R": 0}
    
    # >>> NEW: Instantly grab the latest dictionary without waiting for the serial buffer <<<
    data = sensors.get_data()
    
    ai_Inputs.sensorData = data 
    cmd_id = data.get("CMDID")
    
    if cmd_id in CMD_TO_CASE_MAP:
        case_index = CMD_TO_CASE_MAP[cmd_id]
        ai_Inputs.targets = ALL_CASES[case_index]
        print(ALL_CASES[case_index])

    pygame.event.pump()         
    ctrl_data = controller.poll() 

    # 3. VISION INFERENCE
    img = cam.get_frame()       
    detections = infer.detect(img) # Top Camera Detections
    depthImg2, img2 = cam2.get_frames()
    detections2 = infer.detect(img2) # Bottom Camera Detections

    if controller.connected and not inputState.mode:
        # --- MANUAL MODE ---
        ai_Inputs.driving = False 
        active_Cmd = {"L": ctrl_data["L"], "R": ctrl_data["R"]}
    
    else:
        # --- AI MODE ---
        # Pass both sets of detections for handoff
        ai_Inputs.update_target(bottom_detections=detections2, top_detections=detections, depth_frame=depthImg2)
        
        # Always run arm logic so it can sweep and recenter during search/drive modes
        ai_Inputs.update_arm_logic(detections)
        
        ai_data = ai_Inputs.move_command()
        active_Cmd = {"L": ai_data["L"], "R": ai_data["R"]}

    motors.set_power(active_Cmd["L"], active_Cmd["R"])

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