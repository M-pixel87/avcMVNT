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
import threading

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
    def __init__(self, model_path='/home/uafs/Downloads/YOLO-inferenceHR/runs/detect/brokeback_mountain/weights/best.engine', conf_threshold=0.5):
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
        self.stopped = False
        self.frame_data = (None, None) # (depth, color)

        # Configure stream
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        
        # Start streaming
        self.profile = self.pipeline.start(self.config)
        print(f"✅ Intel RealSense initialized [{width}x{height} @ {fps} FPS]")

        # Start the capture thread
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        """Background thread to constantly fetch the newest frame"""
        while not self.stopped:
            try:
                frames = self.pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                
                if depth_frame and color_frame:
                    d_img = np.asanyarray(depth_frame.get_data())
                    c_img = np.asanyarray(color_frame.get_data())
                    self.frame_data = (d_img, c_img)
            except Exception as e:
                print(f"Intel Cam Error: {e}")

    def get_frames(self):
        """Returns the most recent frame instantly"""
        return self.frame_data

    def release(self):
        self.stopped = True
        self.thread.join()
        self.pipeline.stop()
        print("Intel RealSense released.")




class cvWebcam:
    def __init__(self, cam_id=0, width=640, height=480, fps=30):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.stopped = False
        self.grabbed = False
        self.frame = None

        path = f"/dev/video{cam_id}"
        # Force V4L2 for Jetson
        self.camera = cv2.VideoCapture(cam_id, cv2.CAP_V4L2)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.camera.set(cv2.CAP_PROP_FPS, fps)
        
        # Buffer size 1 ensures we always get the *newest* frame, not an old buffered one
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if self.camera.isOpened():
            print(f"✅ cvWebcam threaded on {path}")
            # Read one frame to ensure it works
            self.grabbed, self.frame = self.camera.read()
            
            # Start thread
            self.thread = threading.Thread(target=self.update, args=())
            self.thread.daemon = True
            self.thread.start()
        else:
            print(f"❌ Failed to open cvWebcam {cam_id}")

    def update(self):
        while not self.stopped:
            if not self.camera.isOpened():
                break
            # Grab frame (blocking only in this thread, not main)
            grabbed, frame = self.camera.read()
            if grabbed:
                self.grabbed = grabbed
                self.frame = frame

    def get_frame(self):
        return self.frame

    def release(self):
        self.stopped = True
        self.thread.join()
        self.camera.release()
        print("cvWebcam released.")



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
# FIXED AI INPUTS CLASS (With Fixed Bucket Drop & Protected States)
# ==============================================================
from Arm import CoOrdinateBaseSys as Arm
import time

# ==============================================================
# FIXED AI INPUTS CLASS (With High-Carry & Close-Range Steering)
# ==============================================================
from Arm import CoOrdinateBaseSys as Arm
import time

# ==============================================================
# FIXED AI INPUTS CLASS (With Ghost-Steering Fix)
# ==============================================================
from Arm import CoOrdinateBaseSys as Arm
import time

class AI_Inputs:
    def __init__(self, motorSystem, state, frame_width=640, frame_height=480, sensorData=None, targets=["Empty","Empty","Empty","Empty"]):
        self.data = {"L": 0, "R": 0}
        self.target_pos = {"x": 0, "y": 0}
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.driving = False

        self.motorSystem = motorSystem
        
        self.rightActive = True
        self.leftActive = True
        self.state = state
        self.sensorData = sensorData
        self.distance_mm = 5000
        self.dist = 5 # This will be the RealSense meters value
        self.mode = 0  # 0=Approach, 1=Stuck/Sensors, 2=Grab, 3=Reverse, 4=Search

        # --- ARM CONFIGURATION ---
        self.SAFE_HEIGHT = 8  
        self.GRAB_HEIGHT = -2.0
        self.DROP_HEIGHT = 15
        self.DROP_REACH_X = 12  
        self.JAW_OPEN = 70
        self.JAW_CLOSED = 10
        self.GRAB_OFFSET_Y = 4
        self.GRAB_OFFSET_X = 0.0      

        # --- ARM STATE VARIABLES ---
        self.targetX = 9.0 
        self.targetY = 0.0
        self.targetZ = self.SAFE_HEIGHT
        self.targetJawAngle = self.JAW_OPEN
        self.reverse_timer = 0  
        
        self.grab_state = 0
        self.state_timer = 0
        self.last_command_time = 0
        self.command_delay = 0.1 
        self.center_counter = 0 
        self.y_aligned = False 
        self.ball_grabbed = False
        self.has_locked_target = False 
        self.target_visible = False # <--- NEW: Tracks frame-by-frame visibility

        self.targets = targets
        self.count = 0
        
        # Drive Params
        self.center_threshold = 50
        self.max_speed = 95
        self.min_speed = 30
        self.turn_scale = 0.5


    def update_target(self, detections, depth_frame=None):
        if self.count >= len(self.targets):
            self.driving = False
            self.has_locked_target = False 
            self.target_visible = False
            return
            
        if(self.ball_grabbed == False):
            wanted_label = self.targets[self.count]
        else:
            wanted_label = (self.targets[self.count].split("_"))[0] + "_bucket"

        # Do nothing if we haven't received a real voice command yet.
        if wanted_label.lower() == "empty":
            self.driving = False
            self.has_locked_target = False
            self.target_visible = False
            self.mode = 0
            return

        found = False

        if detections:
            for det in detections:
                if det["label"].lower() == wanted_label.lower():
                    cx = int((det["bbox"][0] + det["bbox"][2]) / 2)
                    cy = int((det["bbox"][1] + det["bbox"][3]) / 2)
                    
                    self.target_pos["x"] = cx
                    self.target_pos["y"] = cy
                        
                    self.driving = True
                    found = True
                    self.has_locked_target = True 
                    
                    if self.mode == 4 or self.mode == 1:
                        print(f"👀 Target spotted! Tracking {wanted_label}...")
                        self.mode = 0
                    break
        
        # --- NEW: Update instantaneous visibility ---
        self.target_visible = found
                    
        # --- THE "LIDAR LOCK" (Patch Sampling) ---
        if self.driving and self.has_locked_target and depth_frame is not None:
            cx = self.target_pos["x"]
            cy = self.target_pos["y"]
            
            # Define a 10x10 pixel patch around the center point
            patch_size = 10
            half_p = patch_size // 2
            
            # Clamp boundaries so we don't try to read outside the frame array
            y_min = max(0, cy - half_p)
            y_max = min(self.frame_height, cy + half_p)
            x_min = max(0, cx - half_p)
            x_max = min(self.frame_width, cx + half_p)
            
            # Slice the 2D array to get our patch of depth values
            depth_patch = depth_frame[y_min:y_max, x_min:x_max]
            
            # Filter out the 0s (Intel RealSense returns 0 for failed/reflective pixels)
            valid_depths = depth_patch[depth_patch > 0]
            
            if valid_depths.size > 0:
                # Find the median depth of the valid pixels and convert to meters
                median_d_val = np.median(valid_depths) * 0.001
                
                if median_d_val > 0.1: 
                    self.dist = median_d_val
                    self.distance_mm = median_d_val * 1000
        
        # State-Machine Protection Layer
        if not found:
            if self.mode in [1, 2, 3]:
                pass 
            elif self.driving and self.distance_mm < 1200 and self.has_locked_target and self.mode == 0:
                self.mode = 1
                self.driving = True
            else:
                self.mode = 4
                self.driving = True
                self.has_locked_target = False


    def update_arm_logic(self, webcam_detections):
        if self.count >= len(self.targets):
            return # Stop arm logic if we are done with all targets
            
        current_time = time.time()
        wanted_label = self.targets[self.count]

        # --- 1. Y-CENTERING (Webcam Logic) ---
        if self.mode == 2 and self.grab_state == 0:
            webcam_sees_target = False
            centered_this_frame = False
            
            for det in webcam_detections:
                if det["label"].lower() == wanted_label.lower():
                    webcam_sees_target = True
                    x_c = int((det["bbox"][0] + det["bbox"][2]) / 2)
                    
                    if x_c <= 280:
                        self.targetY += 0.25
                        self.center_counter = 0
                        self.y_aligned = False 
                    elif x_c >= 360:
                        self.targetY -= 0.25
                        self.center_counter = 0
                        self.y_aligned = False
                    else:
                        centered_this_frame = True
            
            if webcam_sees_target:
                if centered_this_frame:
                    self.center_counter += 1
                else:
                    self.center_counter = 0

            if self.center_counter >= 20:
                self.y_aligned = True

        # --- 2. ARM STATE MACHINE ---
        if self.mode == 2:
            if self.grab_state == 0:
                if self.ball_grabbed:
                    self.targetZ = self.DROP_HEIGHT 
                    self.targetJawAngle = self.JAW_CLOSED
                    self.y_aligned = True 
                    print(f"LOCKED ON BUCKET -> PUNCHING FORWARD")
                    
                    old_x = self.targetX # Store the starting X
                    self.targetX = self.DROP_REACH_X 
                    
                    # FIX: Scale Y to lock the base angle
                    reach_ratio = self.targetX / old_x
                    self.targetY = self.targetY * reach_ratio
                    
                    self.grab_state = 1
                    self.state_timer = current_time
                else:
                    self.targetZ = self.SAFE_HEIGHT 
                    self.targetJawAngle = self.JAW_OPEN
                    if self.y_aligned and self.dist > 0:
                        print(f"LOCKED ON BALL -> REACHING (Dist: {self.dist:.3f}m)")
                        
                        old_x = self.targetX # Store the starting X
                        self.targetX = ((self.dist * 3.3) * 12) + 9 
                        
                        # FIX: Scale Y to lock the base angle
                        reach_ratio = self.targetX / old_x
                        self.targetY = self.targetY * reach_ratio
                        
                        self.grab_state = 1
                        self.state_timer = current_time

            elif self.grab_state == 1:
                if current_time - self.state_timer > 2.0:
                    self.grab_state = 2
                    self.state_timer = current_time
            
            elif self.grab_state == 2:
                if self.ball_grabbed:
                    self.targetZ = self.DROP_HEIGHT
                else:
                    self.targetZ = self.GRAB_HEIGHT
                    
                if current_time - self.state_timer > 2.0:
                    self.grab_state = 3
                    self.state_timer = current_time

            elif self.grab_state == 3:
                if self.ball_grabbed:
                    self.targetJawAngle = self.JAW_OPEN 
                else:
                    self.targetJawAngle = self.JAW_CLOSED 
                    
                if current_time - self.state_timer > 3.0:
                    self.grab_state = 4
                    self.state_timer = current_time

            elif self.grab_state == 4:
                if self.ball_grabbed:
                    self.targetZ = self.SAFE_HEIGHT 
                    self.targetY = 0
                else:
                    self.targetZ = self.DROP_HEIGHT 
                self.targetX = 9.0
                self.targetY  = 0
                
                if current_time - self.state_timer > 2.0:
                    self.grab_state = 0
                    self.center_counter = 0
                    self.y_aligned = False 
                    self.dist = 0
                    
                    self.mode = 3  
                    self.reverse_timer = current_time
                    
                    if self.ball_grabbed:
                        print("BALL DROPPED -> BACKING UP & SEEKING NEXT TARGET")
                        self.ball_grabbed = False
                        self.count += 1  
                    else:
                        print("BALL GRABBED -> BACKING UP & SEEKING BUCKET")
                        self.ball_grabbed = True

            # --- 3. SEND COMMANDS ---
            if current_time - self.last_command_time > self.command_delay:
                Arm.move_joint(5, self.targetJawAngle)
                
                # FIX: Only apply the grab offsets if we don't have the ball yet
                if self.grab_state > 0 and not self.ball_grabbed:
                    final_x = self.targetX + self.GRAB_OFFSET_X
                    final_y = self.targetY + self.GRAB_OFFSET_Y
                else:
                    final_x = self.targetX
                    final_y = self.targetY
                
                Arm.move_arm_to(final_x, final_y, self.targetZ)
                self.last_command_time = current_time

    def move_command(self):
        left_speed = 0
        right_speed = 0

        # --- REVERSE MODE (MODE 3) ---
        if self.mode == 3:
            if time.time() - self.reverse_timer < 3.0:
                reverse_speed = 50  
                self.data = {"L": reverse_speed, "R": reverse_speed}
                return self.data
            else:
                print("Finished backing up. Spinning to search for target...")
                self.mode = 4 
                self.driving = True
                self.leftActive = True 
                self.rightActive = True
        
        # --- SEARCH MODE (MODE 4) ---
        if self.mode == 4:
            spin_speed = 60 
            self.data = {"L": spin_speed, "R": -spin_speed} 
            return self.data

        # --- VISUAL DRIVING & APPROACH (MODES 0 & 1) ---
        if self.driving and self.mode in [0, 1]:
            slow_start_dist = 1500 
            stop_dist = 500        
            
            if self.distance_mm >= slow_start_dist:
                forward_speed = self.max_speed
            elif self.distance_mm <= stop_dist:
                forward_speed = self.min_speed
                if self.mode == 0:
                    self.mode = 1 
            else:
                ratio = (self.distance_mm - stop_dist) / (slow_start_dist - stop_dist)
                forward_speed = self.min_speed + (ratio * (self.max_speed - self.min_speed))

            # FIX: Only steer if the camera actively sees the target right now
            if self.target_visible:
                error = self.target_pos["x"] - (self.frame_width / 2)
                if abs(error) < self.center_threshold:
                    left_speed = forward_speed
                    right_speed = forward_speed
                else:
                    turn_amount = (error / (self.frame_width / 2)) * self.turn_scale
                    if error > 0: 
                        left_speed = forward_speed
                        right_speed = forward_speed * (1 - turn_amount)
                    else:
                        left_speed = forward_speed * (1 + turn_amount)
                        right_speed = forward_speed
            else:
                # Target is out of sight (coasting), drive straight
                left_speed = forward_speed+7
                right_speed = forward_speed

        # --- SENSOR STOP LOGIC (MODE 1) ---
        if self.mode == 1:
            r_raw = self.sensorData.get("RightUNO", 999) if self.sensorData else 999
            l_raw = self.sensorData.get("LeftUNO", 999) if self.sensorData else 999
            try:
                r_dist = float(r_raw)
                l_dist = float(l_raw)
            except:
                r_dist, l_dist = 999.0, 999.0

            if not self.ball_grabbed:
                if (r_dist <= 45 and r_dist >= 30) : self.rightActive = False  
                if (l_dist <= 45 and l_dist >= 30) : self.leftActive = False   
                if((self.distance_mm <= 250 and self.distance_mm != 0)):
                     self.leftActive = False 
                     self.rightActive = False
            
            else:
                if self.distance_mm <= 200 and self.distance_mm != 0:
                     self.leftActive = False 
                     self.rightActive = False
            
            if not self.rightActive and not self.leftActive:
                self.mode = 2
                self.driving = False
                
        if self.mode == 2:
           self.driving = False

        # --- APPLY OUTPUT ---
        if not self.leftActive or not self.driving or self.mode == 2: 
            left_speed = 0
        else: 
            left_speed = max(self.min_speed, min(left_speed, self.max_speed)) * -1

        if not self.rightActive or not self.driving or self.mode == 2: 
            right_speed = 0
        else: 
            right_speed = max(self.min_speed, min(right_speed, self.max_speed)) * -1

        self.data = {"L": int(left_speed), "R": int(right_speed)}
        return self.data