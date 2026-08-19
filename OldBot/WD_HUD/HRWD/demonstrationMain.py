# --- HIGH-PERFORMANCE ASYNC ARCHITECTURE ---

import os
from Systems.inputSystemDemo import XboxController, cvWebcam, AI_YOLO, AI_Inputs, intelCamera
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

last_save_time = time.time()
image_counter = 0

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

# Initialize AI_Inputs with the base demonstration colors
BASE_COLORS = ["green_ball", "red_ball", "blue_ball", "yellow_ball"]
ai_Inputs = AI_Inputs(
    motorSystem=motors, 
    frame_width=cam.width, 
    frame_height=cam.height, 
    state=inputState,
    targets=BASE_COLORS
)

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

            # 2. Primary Inference (Intel RealSense)
            detections2 = infer.detect(img2) if img2 is not None else []

            # 3. Safe State Check (Read only)
            with ai_Inputs.lock:
                targets = ai_Inputs.targets
                current_count = ai_Inputs.count % len(targets) if targets else 0
                current_mode = ai_Inputs.mode

            # Determine Target directly from targets list (No bucket logic)
            current_target = targets[current_count] if targets else ""

            bottom_found_target = any(d["label"].lower() == current_target.lower() for d in detections2)
            detections = []

            # 4. Secondary Inference (Webcam / Arm Camera)
            if img is not None and (not bottom_found_target or current_mode == 2):
                detections = infer.detect(img)

            # 5. Push to Memory Buffer
            with self.lock:
                self.data = {
                    "img": img, "img2": img2, "depthImg2": depthImg2,
                    "detections": detections, "detections2": detections2
                }
            
            time.sleep(0.005)  # Yield CPU to prevent core starvation

vision_thread = VisionWorker()
vision_thread.start()

time.sleep(1.75)

# --- CONTROL FREQUENCY TIMING ---
target_hz = 30
loop_delay = 1.0 / target_hz

# --- LOGIC CONFIGURATION ---
ALL_CASES = [list(p) for p in permutations(BASE_COLORS)]

CMD_TO_CASE_MAP = {
    "22": 0, "23": 1, "24": 2, "36": 3, "34": 4, "45": 5,
    "47": 6, "46": 7, "48": 8, "82": 9, "96": 10, "106": 11,
    "116": 12, "130": 13, "141": 14, "124": 15, "102": 16, "113": 17,
    "123": 18, "120": 19, "128": 20, "137": 21, "138": 22, "139": 23
}

time.sleep(2)

def main():
    try:
        while True:
            start_time = time.time()
            control_loop()
            
            # Universal Display Render Hook
            cv2.waitKey(1) 
            
            # Lock execution to strict frequency for smooth motor PWM
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
    global last_save_time, image_counter
    active_Cmd = {"L": 0, "R": 0}
    
    # 1. Grab Sensors & Voice Commands
    data = sensors.get_data()
    with ai_Inputs.lock:
        ai_Inputs.sensorData = data 
        cmd_id = data.get("CMDID")
        
        if cmd_id in CMD_TO_CASE_MAP:
            case_index = CMD_TO_CASE_MAP[cmd_id]
            print(f"\n🎤 Voice Command {cmd_id} received -> Switching targets: {ALL_CASES[case_index]}")
            ai_Inputs.targets = ALL_CASES[case_index]
            ai_Inputs.count = 0
            ai_Inputs.grab_state = 0
            ai_Inputs.center_counter = 0
            ai_Inputs.y_aligned = False

    pygame.event.pump()
    ctrl_data = controller.poll()

    # 2. Grab Latest Processed Vision
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
        # Pass detection feeds to AI
        ai_Inputs.update_target(bottom_detections=detections2, top_detections=detections, depth_frame=depthImg2)
        ai_Inputs.update_arm_logic(detections)
        
        ai_data = ai_Inputs.move_command()
        active_Cmd = {"L": ai_data["L"], "R": ai_data["R"]}

    # 4. Motor Drive Command
    motors.set_power(active_Cmd["L"], active_Cmd["R"])

    # 5. UI Updates
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