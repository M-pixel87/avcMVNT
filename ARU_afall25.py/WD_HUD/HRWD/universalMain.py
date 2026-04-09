# --- HIGH-PERFORMANCE ASYNC ARCHITECTURE ---

from Systems.InputSystem import XboxController, cvWebcam, AI_YOLO, AI_Inputs, intelCamera
from Systems.motorSystem import CytronMotor
from Systems.sensorSystem import sensorSystem
from Systems.displaySystem import DisplaySystem
from Systems.mode_State import modeState
from Arm import CoOrdinateBaseSys as Arm

import pygame
import time
import serial
import threading
from itertools import permutations
import cv2

# --- GLOBAL Variables ---
inputState = modeState()

class MockSerial:
    def __init__(self):
        self.in_waiting = 0  
    def write(self, data): pass
    def readline(self): return b"" 
    def close(self): pass

PORT = "/dev/ttyACM0"
BAUD = 115200

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    print("✅ Serial Connected Successfully.")
except serial.SerialException as e:
    print(f"❌ Connection Failed: {e}")
    ser = MockSerial()

pygame.init()
pygame.joystick.init()

# --- INITIALIZE HARDWARE ---
controller = XboxController(state=inputState)
cam = cvWebcam(cam_id=6, width=640, height=480)
cam2 = intelCamera(width=640, height=480)
infer = AI_YOLO(conf_threshold=0.3)

motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
sensors = sensorSystem(ser)
sensors.start()

display = DisplaySystem(cam.camera, mode="YOLO")
display2 = DisplaySystem(cam=cam2, name="CAM2", mode="YOLO")
ai_Inputs = AI_Inputs(motorSystem=motors, frame_width=cam.width, frame_height=cam.height, state=inputState)

# ==============================================================
# ASYNC VISION ENGINE (Producer-Consumer Thread)
# ==============================================================
class VisionWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.running = True
        self.data = {
            "img": None, "img2": None, "depthImg2": None,
            "detections": [], "detections2": []
        }

    def run(self):
        while self.running:
            # 1. Pipeline Capture
            depthImg2, raw_img2 = cam2.get_frames()
            img2 = raw_img2.copy() if raw_img2 is not None else None
            
            raw_img = cam.get_frame()
            img = raw_img.copy() if raw_img is not None else None

            # 2. Primary Inference
            detections2 = infer.detect(img2) if img2 is not None else []

            # 3. Safe State Check (Read only)
            with ai_Inputs.lock:
                current_count = ai_Inputs.count
                ball_grabbed = ai_Inputs.ball_grabbed
                current_mode = ai_Inputs.mode
                targets = ai_Inputs.targets

            # Determine Target
            current_target = ""
            if current_count < len(targets):
                if ball_grabbed:
                    current_target = (targets[current_count].split("_"))[0] + "_bucket"
                else:
                    current_target = targets[current_count]

            bottom_found_target = any(d["label"].lower() == current_target.lower() for d in detections2)
            detections = []

            # 4. Secondary Inference (Handoff)
            if img is not None and (not bottom_found_target or current_mode == 2):
                detections = infer.detect(img)

            # 5. Push to Memory Buffer
            with self.lock:
                self.data = {
                    "img": img, "img2": img2, "depthImg2": depthImg2,
                    "detections": detections, "detections2": detections2
                }
            
            time.sleep(0.005) # Yield CPU to prevent core starvation

vision_thread = VisionWorker()
vision_thread.start()

time.sleep(2)
motors.set_power(80, -80)
time.sleep(1.75)

# --- CONTROL FREQUENCY TIMING ---
target_hz = 30
loop_delay = 1.0 / target_hz


# --- LOGIC CONFIGURATION ---
BASE_COLORS = ["green_ball", "red_ball", "blue_ball", "yellow_ball"]
# ALL_CASES generates exactly 24 permutations matching your table's order
ALL_CASES = [list(p) for p in permutations(BASE_COLORS)]

# Maps Command Number to the index in ALL_CASES
CMD_TO_CASE_MAP = {
    "22": 0,   # Go forward (G R B Y)
    "23": 1,   # Retreat (G R Y B)
    "24": 2,   # Park a Car (G B R Y)
    "36": 3,   # Face Recognition (G B Y R)
    "34": 4,   # Bluetooth Mode (G Y R B)
    "45": 5,   # Clear Screen (G Y B R)
    
    "47": 6,   # Forget (R G B Y)
    "46": 7,   # Learn Once (R G Y B)
    "48": 8,   # Load Model (R B G Y)
    "82": 9,   # Reset (R B Y G)
    "96": 10,  # Repeat this track (R Y G B)
    "106": 11, # Dim the Light (R Y B G)
    
    "116": 12, # Set to Red (B G R Y)
    "130": 13, # Auto Mode (B G Y R)
    "141": 14, # Open the Door (B R G Y)
    "124": 15, # Turn on AC (B R Y G)
    "102": 16, # Play poem (B Y G R)
    "113": 17, # Daylight mode (B Y R G)
    
    "123": 18, # Set to white (Y G R B)
    "120": 19, # Set to cyan (Y G B R)
    "128": 20, # Cool mode (Y R G B)
    "137": 21, # Close the window (Y R B G)
    "138": 22, # Open the window (Y B G R)
    "139": 23  # Open curtain (Y B R G)
}

time.sleep(2)
motors.set_power(80, -80)
time.sleep(1.75)


def main():
    try:
        while True:
            start_time = time.time()
            control_loop()
            
            # Universal Display Render Hook
            cv2.waitKey(1) 
            
            # Lock execution to strict frequency for perfectly smooth motor PWM
            elapsed = time.time() - start_time
            if elapsed < loop_delay:
                time.sleep(loop_delay - elapsed)

    except KeyboardInterrupt:
        print("Stopping...")
        motors.set_power(0, 0)
        vision_thread.running = False
        cam.release()
        infer.release()
        sensors.stop()

def control_loop():
    active_Cmd = {"L": 0, "R": 0}
    
    # 1. Grab Sensors
    data = sensors.get_data()
    with ai_Inputs.lock:
        ai_Inputs.sensorData = data 
        cmd_id = data.get("CMDID")
        
        if cmd_id in CMD_TO_CASE_MAP:
            print("\n")
            case_index = CMD_TO_CASE_MAP[cmd_id]
            print(ALL_CASES[case_index])
            ai_Inputs.targets = ALL_CASES[case_index]

    pygame.event.pump()
    ctrl_data = controller.poll()

    # 2. Grab Latest Processed Vision (Instantaneous)
    with vision_thread.lock:
        v_data = vision_thread.data
        img, img2, depthImg2 = v_data["img"], v_data["img2"], v_data["depthImg2"]
        detections, detections2 = v_data["detections"], v_data["detections2"]

    # 3. Execute AI & Chassis
    if controller.connected and not inputState.mode:
        with ai_Inputs.lock:
            ai_Inputs.driving = False 
        active_Cmd = {"L": ctrl_data["L"], "R": ctrl_data["R"]}
    else:
        # Pass data into AI
        ai_Inputs.update_target(bottom_detections=detections2, top_detections=detections, depth_frame=depthImg2)
        ai_Inputs.update_arm_logic(detections)
        
        ai_data = ai_Inputs.move_command()
        active_Cmd = {"L": ai_data["L"], "R": ai_data["R"]}

    # 4. Fire Motors immediately
    motors.set_power(active_Cmd["L"], active_Cmd["R"])

    # 5. Queue UI Updates
    if img2 is not None:
        display.update_display(
            img2, detections2, controller.get_axes(),
            ctrl_data["buttons"], (active_Cmd["L"], active_Cmd["R"]),
            data, inputState
        )
    if img is not None:
        display2.update_display(img=img, detections=detections)

if __name__ == "__main__":
    main()