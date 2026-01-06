import os
import time
import torch
from ultralytics import YOLO
import jetson_inference
import jetson_utils
import cv2
import pygame
from Arm import CoOrdinateBaseSys as Arm
from Systems.mode_State import modeState

# Headless mode setup
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["LD_PRELOAD"] = "/usr/lib/aarch64-linux-gnu/libgomp.so.1"

# ==============================================================
# ORIGINAL LEGACY AI CLASS (Jetson Inference)
# ==============================================================
class AI:
    def __init__(self):
        self.net = jetson_inference.detectNet(
            model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_jone/ssd-mobilenet.onnx",
            labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_jone/labels.txt",
            input_blob="input_0",
            output_cvg="scores",
            output_bbox="boxes",
            threshold=0.5)

    def detect(self, img):
        if(img):
            detections = self.net.Detect(img)
            if detections:
                for detect in detections:
                    ID = detect.ClassID
                    w = detect.Right - detect.Left
                    print(f'Width of object: {w}')
        else:
            pass

# ==============================================================
# FIXED YOLO CLASS (TensorRT)
# ==============================================================
class AI_YOLO:
    def __init__(self, model_path='/home/uafs/Downloads/best.engine', conf_threshold=0.5):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model = None
        self.class_names = {}

        try:
            print(f"🔍 Loading YOLO TensorRT model from: {model_path}")
            self.model = YOLO(model_path)
            self.class_names = self.model.names
            print(f"✅ Model loaded successfully ({len(self.class_names)} classes).")
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
            self.model = None

    def detect(self, frame, display=False):
        if self.model is None or frame is None:
            return []

        results = self.model(frame, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf < self.conf_threshold:
                    continue

                x1, y1, x2, y2 = map(float, box.xyxy[0])
                cls_id = int(box.cls[0])
                label = self.class_names.get(cls_id, f"class_{cls_id}")

                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                box_width = x2 - x1

                detections.append({
                    "class_id": cls_id,
                    "label": label,
                    "confidence": conf,
                    "bbox": (int(x1), int(y1), int(x2), int(y2)),
                    "center": (int(center_x), int(center_y)),
                    "width": int(box_width)
                })
        return detections

    def release(self):
        cv2.destroyAllWindows()
        print("🧹 YOLO resources released.")

# ==============================================================
# FIXED CVWEBCAM CLASS
# ==============================================================
class cvWebcam:
    def __init__(self, cam_id=0, width=640, height=480):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.camera = None
        self.initialized = False

        try:
            path = f"/dev/video{cam_id}"
            if not os.path.exists(path):
                raise FileNotFoundError(f"No device found at {path}")

            self.camera = cv2.VideoCapture(cam_id)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera.set(cv2.CAP_PROP_FPS, 60)

            if not self.camera.isOpened():
                raise RuntimeError(f"Failed to open camera {cam_id}")

            print(f"✅ cvWebcam initialized on {path} [{width}x{height}]")
            self.initialized = True
        except Exception as e:
            print(f"⚠️ cvWebcam init failed: {e}")
            self.camera = None

    def get_frame(self):
        if not self.initialized or self.camera is None:
            return None
        ret, frame = self.camera.read()
        if not ret:
            return None
        return frame

    def release(self):
        if self.camera:
            self.camera.release()
            self.initialized = False

# ==============================================================
# ORIGINAL LEGACY WEBCAM CLASS (Jetson Utils)
# ==============================================================
class Webcam:
    def __init__(self, cam_id=0, width=640, height=480):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.camera = None
        self.display = None

        try:
            self.display = jetson_utils.videoOutput(
                "display://0",
                argv=[f"--output-width={width}", f"--output-height={height}"]
            )
        except Exception as e:
            print(f"⚠️ Display init failed: {e}")
            self.display = None

        try:
            path = f"/dev/video{cam_id}"
            if not os.path.exists(path):
                raise FileNotFoundError(f"No device at {path}")

            self.camera = jetson_utils.videoSource(
                path,
                argv=[f"--input-width={width}", f"--input-height={height}"]
            )
            print(f"✅ Camera initialized on {path}")
        except Exception as e:
            print(f"⚠️ Camera init failed: {e}")
            self.camera = None

    def get_frame(self):
        if self.camera is None:
            return None
        try:
            return self.camera.Capture()
        except Exception as e:
            return None

    def show_frame(self, img):
        if self.display is not None and img is not None:
            self.display.Render(img)
            self.display.SetStatus("Webcam Stream")

    def release(self):
        if self.camera: self.camera.Close()
        if self.display: self.display.Close()

# ==============================================================
# FIXED CONTROLLER CLASS
# ==============================================================
class XboxController:
    def __init__(self, state: modeState , deadzone=0.05):
        self.deadzone = deadzone
        self.data = {"L": 0, "R": 0, "buttons": []}
        self.mode = 0
        self.state = state

        # Arm vars
        self.x, self.y, self.z = 10, 0, 10
        self.jawA, self.wristA = 5.0, -90.0
        self.last_xyz = (self.x, self.y, self.z)
        self.last_jawA = self.jawA
        self.last_wristA = self.wristA

        if pygame.joystick.get_count() == 0:
            self.connected = False
        else:
            self.connected = True
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"✅ Controller: {self.joystick.get_name()}")

    def scale_axis(self, val):
        return int(val * 100)

    def poll(self):
        if self.connected:
            # FIX: Initialize variables so they exist in all modes
            left_speed = 0
            right_speed = 0
            buttons = []

            # DRIVE MODE (Manual)
            if self.mode == 0 and self.state.mode == False:
                left_speed = self.scale_axis(self.joystick.get_axis(1))
                right_speed = self.scale_axis(self.joystick.get_axis(3))
                if abs(left_speed) < self.deadzone * 100: left_speed = 0
                if abs(right_speed) < self.deadzone * 100: right_speed = 0
            
            # ARM MODE (Manual)
            elif self.mode == 1 and self.state.mode == False:
                left_x = self.joystick.get_axis(0)
                left_y = self.joystick.get_axis(1)
                right_y = self.joystick.get_axis(3)
                
                if abs(left_x) > 0.2: self.x += left_x * 0.5
                if abs(left_y) > 0.2: self.z -= left_y * 0.5
                if abs(right_y) > 0.2: self.y -= right_y * 0.5

                if (self.x, self.y, self.z) != self.last_xyz:
                    Arm.move_arm_to(self.x, self.y, self.z, speed=200, acc=100)
                    self.last_xyz = (self.x, self.y, self.z)

            buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
            
            if buttons[0] == 1:
                self.mode = 1 if self.mode == 0 else 0
                print(f"🔀 Mode: {'ARM' if self.mode == 1 else 'DRIVE'}")
                time.sleep(0.5)

            if buttons[1] == 1:
                self.state.toggle()
                print(f"🔀 Mode: {'AI' if self.state.mode else 'MANUAL'}")
                time.sleep(0.5)

            if buttons[4]: self.jawA += 2
            if buttons[3]: self.jawA -= 2
            if buttons[6]: self.wristA -= 5
            if buttons[7]: self.wristA += 5

            self.data = {"L": left_speed, "R": right_speed, "buttons": buttons}
            return self.data
        else:
            return {"L": 0, "R": 0, "buttons": []}

    def get_axes(self):
        return [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())] if self.connected else [0]

# ==============================================================
# FIXED AI INPUTS CLASS (With Sensor Logic)
# ==============================================================
# ==============================================================
# FIXED AI INPUTS CLASS (With String-to-Float Safety)
# ==============================================================
class AI_Inputs:
    def __init__(self, state: modeState, frame_width=640, frame_height=480, sensorData=None, targets = {"Empty","Empty","Empty"}):
        self.data = {"L": 0, "R": 0}
        self.target_pos = {"x": 0, "y": 0}
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.driving = False
        
        self.rightActive = True
        self.leftActive = True
        self.state = state
        self.sensorData = sensorData
        self.mode = 1  # 0=Approach, 1 = stuck, 2=Grab

        self.targets = targets
        self.count = 0
        
        # Params
        self.center_threshold = 50
        self.max_speed = 90
        self.min_speed = 0
        self.turn_scale = 0.5

    def update_target(self, detection):
        if detection:
            if(detection["class_id"] == self.targets[self.count]):
                self.target_pos["x"] = detection["center"][0]
                self.target_pos["y"] = detection["center"][1]
                if detection["width"] < 150:
                    self.driving = True
                else:
                    self.driving = False
        else:
            self.driving = False

    def move_command(self):
        left_speed = 0
        right_speed = 0
        
        # 1. VISUAL DRIVING
        if self.driving and (self.mode == 0 ):
            error = self.target_pos["x"] - (self.frame_width / 2)
            
            if abs(error) < self.center_threshold:
                left_speed = self.max_speed
                right_speed = self.max_speed
            else:
                turn_amount = (error / (self.frame_width / 2)) * self.turn_scale
                if error > 0: # Target Right
                    left_speed = self.max_speed
                    right_speed = self.max_speed * (1 - turn_amount)
                else: # Target Left
                    left_speed = self.max_speed * (1 + turn_amount)
                    right_speed = self.max_speed

        # 2. SENSOR STOP LOGIC (Overrides driving)
        if self.mode == 0 :
            # FIX: Get raw value, then FORCE convert to float
            r_raw = self.sensorData.get("RightUNO", 999) if self.sensorData else 999
            l_raw = self.sensorData.get("LeftUNO", 999) if self.sensorData else 999

            try:
                r_dist = float(r_raw)
            except (ValueError, TypeError):
                r_dist = 999.0

            try:
                l_dist = float(l_raw)
            except (ValueError, TypeError):
                l_dist = 999.0

            # Debug print to confirm it is working now
            # print(f"Dist: L={l_dist} R={r_dist}")

            if r_dist <= 50:
                self.rightActive = False  
            
            if l_dist <= 50:
                self.leftActive = False   
            
            # If both stopped, switch mode
            if not self.rightActive and not self.leftActive:
                print("🛑 TARGET REACHED -> Switching to Mode 2")
                self.mode = 2
                self.driving = False

        # 3. APPLY OUTPUT
        if not self.leftActive: left_speed = 0
        else: left_speed = max(self.min_speed, min(left_speed, self.max_speed)) * -1

        if not self.rightActive: right_speed = 0
        else: right_speed = max(self.min_speed, min(right_speed, self.max_speed)) * -1

        self.data = {"L": int(left_speed), "R": int(right_speed)}
        return self.data