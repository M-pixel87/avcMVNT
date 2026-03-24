# --- MAJOR PIVOT UPDATE: TOP CAMERA INTEGRATION & ARM SCANNING ---

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
sensors.start()

display = DisplaySystem(cam.camera, mode="YOLO")
display2 = DisplaySystem(cam = cam2 ,name = "CAM2", mode="YOLO")
ai_Inputs = AI_Inputs(motorSystem = motors, frame_width=cam.width, frame_height=cam.height, state=inputState)

# --- TIMING VARIABLES ---
max_fps = 60                   
last_time = 0                  
frame_delay = 1.0 / max_fps    

# --- LOGIC CONFIGURATION ---
BASE_COLORS = ["green_ball", "red_ball", "blue_ball", "yellow_ball"]
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
        sensors.stop()        

# --- CORE LOGIC LOOP ---
def inputDisplay():
    active_Cmd = {"L": 0, "R": 0}
    
    data = sensors.get_data()
    ai_Inputs.sensorData = data 
    cmd_id = data.get("CMDID")
    
    if cmd_id in CMD_TO_CASE_MAP:
        case_index = CMD_TO_CASE_MAP[cmd_id]
        ai_Inputs.targets = ALL_CASES[case_index]
        print(ALL_CASES[case_index])

    pygame.event.pump()         
    ctrl_data = controller.poll() 

    # ==============================================================
    # 3. OPTIMIZED VISION INFERENCE (With Buffer Corruption Fix)
    # ==============================================================
    # Always check the bottom (primary) camera first. COPY the frame!
    depthImg2, raw_img2 = cam2.get_frames()
    img2 = raw_img2.copy() if raw_img2 is not None else None
    
    detections2 = infer.detect(img2) if img2 is not None else []

    # Figure out exactly what target we are looking for right now
    current_target = ""
    if ai_Inputs.count < len(ai_Inputs.targets):
        if ai_Inputs.ball_grabbed:
            current_target = (ai_Inputs.targets[ai_Inputs.count].split("_"))[0] + "_bucket"
        else:
            current_target = ai_Inputs.targets[ai_Inputs.count]

    # Check if the bottom camera successfully found our target
    bottom_found_target = any(d["label"].lower() == current_target.lower() for d in detections2)
    detections = []

    # Grab the top frame and COPY it to prevent the "Black Screen" memory crash
    raw_img = cam.get_frame()
    img = raw_img.copy() if raw_img is not None else None
    
    # Run top camera ONLY if the bottom missed it (fallback), OR if we are grabbing (Mode 2)
    if img is not None:
        if (not bottom_found_target) or (ai_Inputs.mode == 2):
            detections = infer.detect(img)

    # ==============================================================
    # CHASSIS & ARM CONTROL
    # ==============================================================
    if controller.connected and not inputState.mode:
        # --- MANUAL MODE ---
        ai_Inputs.driving = False 
        active_Cmd = {"L": ctrl_data["L"], "R": ctrl_data["R"]}
    
    else:
        # --- AI MODE ---
        ai_Inputs.update_target(bottom_detections=detections2, top_detections=detections, depth_frame=depthImg2)
        ai_Inputs.update_arm_logic(detections)
        
        ai_data = ai_Inputs.move_command()
        active_Cmd = {"L": ai_data["L"], "R": ai_data["R"]}

    motors.set_power(active_Cmd["L"], active_Cmd["R"])

    display.update_display(
        img2, detections2, controller.get_axes(),
        ctrl_data["buttons"], (active_Cmd["L"], active_Cmd["R"]),
        data, inputState
    )
    display2.update_display(img=img, detections=detections)
    
if __name__ == "__main__":
    main()