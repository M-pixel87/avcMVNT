import os

# Headless mode (no display)
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Fix for TLS conflict: preload OpenMP first
os.environ["LD_PRELOAD"] = "/usr/lib/aarch64-linux-gnu/libgomp.so.1"

# === FIXED IMPORT ORDER ===
import torch
from ultralytics import YOLO  # Uses torch internally
import jetson_inference       # Uses TensorRT, not PyTorch
import jetson_utils
import cv2
import pygame
from Arm import CoOrdinateBaseSys as Arm



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

            width = img.width
            height = img.height

            if detections:
                for detect in detections:
                    ID = detect.ClassID
                    top = int(detect.Top)
                    left = int(detect.Left)
                    bottom = int(detect.Bottom)
                    right = int(detect.Right)
                    item = self.net.GetClassDesc(ID)
                    w = right - left
                    print(f'Width of object: {w}')
        else:
            pass




# ==============================================================
# Optimized YOLO (TensorRT) Inference Class                    
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





class XboxController:
    def __init__(self, deadzone=0.05):
        self.deadzone = deadzone
        self.data = {"L": 0, "R": 0, "buttons": []}
        self.mode = 0  # start in drive mode (0=drive, 1=arm)
        self.x = 10
        self.y = 0
        self.z = 10
        self.jawA = 5.0
        self.wristA = -90.0

        # Track last commanded positions
        self.last_xyz = (self.x, self.y, self.z)
        self.last_jawA = self.jawA
        self.last_wristA = self.wristA

        if pygame.joystick.get_count() == 0:
            self.controller = False
        else:
            self.controller = True
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"✅ Controller: {self.joystick.get_name()}")

    def scale_axis(self, val):
        return int(val * 100)

    def poll(self):
        if(self.controller is not False):
            if(self.mode == 0):
                left_y = self.joystick.get_axis(1)
                right_y = self.joystick.get_axis(3)

                left_speed = self.scale_axis(left_y)
                right_speed = self.scale_axis(right_y)

                if abs(left_speed) < self.deadzone * 100:
                    left_speed = 0
                if abs(right_speed) < self.deadzone * 100:
                    right_speed = 0
            else:
                left_speed = 0
                right_speed = 0
                left_x = self.joystick.get_axis(0)
                left_y = self.joystick.get_axis(1)
                right_y = self.joystick.get_axis(3)

                deadzone = 0.2
                step_size = 0.5

                # Save old values for comparison
                old_xyz = (self.x, self.y, self.z)
                old_jawA = self.jawA
                old_wristA = self.wristA

                # Move X with left stick horizontal
                if abs(left_x) > deadzone:
                    self.x += left_x * step_size

                # Move Z with left stick vertical (inverted so up = increase z)
                if abs(left_y) > deadzone:
                    self.z -= left_y * step_size

                # Move Y with right stick vertical
                if abs(right_y) > deadzone:
                    self.y -= right_y * step_size

                # ARM CONTROL: Only send if changed
                if (self.x, self.y, self.z) != self.last_xyz:
                    Arm.move_arm_to(self.x, self.y, self.z, speed=200, acc=100)
                    self.last_xyz = (self.x, self.y, self.z)

                if self.jawA != self.last_jawA:
                    Arm.move_joint(5, self.jawA)
                    self.last_jawA = self.jawA

                if self.wristA != self.last_wristA:
                    Arm.move_joint(4, self.wristA)
                    self.last_wristA = self.wristA

            buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
            if buttons[0] == 1:
                print("A pressed")
                self.mode = 1 if self.mode == 0 else 0
                print(f"🔀 Mode: {'ARM' if self.mode == 1 else 'DRIVE'}")

            if buttons[4] == 1:
                self.jawA += 2

            if buttons[3] == 1:
                self.jawA -= 2

            if buttons[6] == 1:
                self.wristA -= 5

            if buttons[7] == 1:
                self.wristA += 5

            self.data = {"L": left_speed, "R": right_speed,  "buttons": buttons}
            return self.data
        else:
            self.data = {"L": 0, "R": 0, "buttons": []}
            return self.data

    def get_data(self):
        return self.data

    def get_axes(self):
        if(self.controller):
            return [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
        else:
            return [0]
