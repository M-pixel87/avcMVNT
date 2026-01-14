import os
import time
import torch
import numpy as np
from ultralytics import YOLO
import jetson_inference
import jetson_utils
import cv2
import pygame
from Arm import CoOrdinateBaseSys as Arm
from Systems.mode_State import modeState
import pyrealsense2 as rs

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
# Optimized YOLO (TensorRT) Inference Class                    
# ==============================================================
class AI_YOLO:
    def __init__(self, model_path='/home/uafs/Downloads/YOLO-inferenceHR/runs/detect/testMM/weights/best.engine', conf_threshold=0.5):
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
            print("ensure the .engine file exists")
            self.model = None

    def detect(self, frame, display=False):
        """
        Run YOLO inference on a frame.
        Returns a list of detections (dicts) and optionally displays annotated frame.
        """
        if self.model is None or frame is None:
            return []

        # Run inference (TensorRT engine runs directly on GPU)
        results = self.model(frame, verbose=False)

        detections = []
        frame_width = frame.shape[1]

        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf < self.conf_threshold:
                    continue

                x1, y1, x2, y2 = map(float, box.xyxy[0])
                cls_id = int(box.cls[0])
                label = self.class_names.get(cls_id, f"class_{cls_id}")

                # Calculate center and width
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                box_width = x2 - x1

                # Append detection info
                detections.append({
                    "class_id": cls_id,
                    "label": label,
                    "confidence": conf,
                    "bbox": (int(x1), int(y1), int(x2), int(y2)),
                    "center": (int(center_x), int(center_y)),
                    "width": int(box_width)
                })

        # By default, does not display, but can show annotated frame if desired, this bypasses display system
        if display:
            annotated_frame = results[0].plot()
            cv2.imshow("YOLO TensorRT Inference", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                return "quit"

        return detections

    def release(self):
        """Graceful shutdown of any resources."""
        cv2.destroyAllWindows()
        print("🧹 YOLO resources released.")



#Use for intel D435i Realsense camera module
class intelCamera:
    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps

        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)

        # Start streaming
        self.pipeline.start(self.config)
        print(f"✅ Intel RealSense camera initialized [{width}x{height} @ {fps} FPS]")

    def get_frames(self):
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            return None, None

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        return depth_image, color_image

    def release(self):
        self.pipeline.stop()
        print("Intel RealSense camera released.")




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

            # 1. Force V4L2 (Correct for Jetson)
            self.camera = cv2.VideoCapture(cam_id, cv2.CAP_V4L2)

            # 2. DO NOT set FOURCC to MJPG. 
            # Your camera only has YUYV, so we let it use the default.
            
            # 3. Set Resolution (640x480 is safe for YUYV)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # 4. Set FPS to 30 (Safest for YUYV format)
            # Your list says 60 is possible, but YUYV is heavy and often times out at 60.
            self.camera.set(cv2.CAP_PROP_FPS, 30)

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
            print("⚠️ Frame capture failed.")
            return None
        return frame

    def release(self):
        if self.camera:
            self.camera.release()
            self.initialized = False
            print("🧹 cvWebcam released.")




class Webcam:
    def __init__(self, cam_id=0, width=640, height=480):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.camera = None  # will stay None if no cam
        self.display = None

        # try to open a display
        try:
            self.display = jetson_utils.videoOutput(
                "display://0",
                argv=[f"--output-width={width}", f"--output-height={height}"]
            )
        except Exception as e:
            print(f"⚠️ Display init failed: {e}")
            self.display = None

        # Now try to open camera
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
            print(f"⚠️ Capture failed: {e}")
            return None

    def show_frame(self, img):
        if self.display is not None and img is not None:
            self.display.Render(img)
            self.display.SetStatus("Webcam Stream")
        elif self.display is not None:
            # just keep window alive even if no image
            self.display.SetStatus("No Camera Feed")

    def release(self):
        if self.camera is not None:
            self.camera.Close()
        if self.display is not None:
            self.display.Close()

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
    def __init__(self, state: modeState, frame_width=640, frame_height=480, sensorData=None, targets = ["Empty","Empty","Empty","Empty"]):
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
                
        #ARM CONTROL MODE
        if self.mode == 2:
            left_speed = 0
            right_speed = 0


        # 3. APPLY OUTPUT
        if not self.leftActive: left_speed = 0
        else: left_speed = max(self.min_speed, min(left_speed, self.max_speed)) * -1

        if not self.rightActive: right_speed = 0
        else: right_speed = max(self.min_speed, min(right_speed, self.max_speed)) * -1

        self.data = {"L": int(left_speed), "R": int(right_speed)}
        return self.data