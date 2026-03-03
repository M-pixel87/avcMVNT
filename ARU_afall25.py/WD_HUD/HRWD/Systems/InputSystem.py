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
    def __init__(self, model_path='/home/uafs/Downloads/YOLO-inferenceHR/runs/detect/brokeback_mountain/weights/best.engine', conf_threshold=0.1):
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
        if self.model is None or frame is None:
            return []

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

        if display:
            annotated_frame = results[0].plot()
            cv2.imshow("YOLO TensorRT Inference", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                return "quit"

        return detections

    def release(self):
        cv2.destroyAllWindows()
        print("🧹 YOLO resources released.")

#Use for intel D435i Realsense camera module
class intelCamera:
    def __init__(self, width=640, height=480, fps=30):
        self.width = width
        self.height = height
        self.fps = fps
        self.stopped = False
        self.frame_data = (None, None) 

        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        
        self.profile = self.pipeline.start(self.config)
        print(f"✅ Intel RealSense initialized [{width}x{height} @ {fps} FPS]")

        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
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
        self.camera = cv2.VideoCapture(cam_id, cv2.CAP_V4L2)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.camera.set(cv2.CAP_PROP_FPS, fps)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if self.camera.isOpened():
            print(f"✅ cvWebcam threaded on {path}")
            self.grabbed, self.frame = self.camera.read()
            self.thread = threading.Thread(target=self.update, args=())
            self.thread.daemon = True
            self.thread.start()
        else:
            print(f"❌ Failed to open cvWebcam {cam_id}")

    def update(self):
        while not self.stopped:
            if not self.camera.isOpened():
                break
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
        self.camera = None  
        self.display = None

        try:
            self.display = jetson_utils.videoOutput(
                "display://0",
                argv=[f"--output-width={width}", f"--output-height={height}"]
            )
        except Exception as e:
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
        elif self.display is not None:
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
            left_speed = 0
            right_speed = 0
            buttons = []

            if self.mode == 0 and self.state.mode == False:
                left_speed = self.scale_axis(self.joystick.get_axis(1))
                right_speed = self.scale_axis(self.joystick.get_axis(3))
                if abs(left_speed) < self.deadzone * 100: left_speed = 0
                if abs(right_speed) < self.deadzone * 100: right_speed = 0
            
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
                time.sleep(0.5)

            if buttons[1] == 1:
                self.state.toggle()
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
# FIXED AI INPUTS CLASS (Final: Grab Verification & Ramming Speed)
# ==============================================================
from Arm import CoOrdinateBaseSys as Arm
import time
import math
import numpy as np

# ==============================================================
# REWORKED AI INPUTS CLASS (Smoother logic & Slower speeds)
# ==============================================================
class AI_Inputs:
    def __init__(self, motorSystem, state, frame_width=640, frame_height=480, sensorData=None, targets=["Empty","Empty","Empty","Empty"]):
        self.data = {"L": 0, "R": 0}
        self.target_pos = {"x": 0, "y": 0}
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.driving = False
        self.active_camera = "bottom" 

        self.motorSystem = motorSystem
        self.rightActive = True
        self.leftActive = True
        self.state = state
        self.sensorData = sensorData
        self.distance_mm = 5000
        self.dist = 5 
        self.mode = 0  

        self.bypass_timer = 0
        self.bypass_state = 0 
        self.last_target_x = self.frame_width / 2 
        self.waypoint_turn_duration = 0.0
        self.waypoint_drive_duration = 0.0
        self.waypoint_turn_dir = 1 
        
        self.verification_timer = 0
        self.verifying_grab = False
        self.ramming_timer = 0 

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
        self.sweep_dir = 1 
        
        self.grab_state = 0
        self.state_timer = 0
        self.last_command_time = 0
        self.command_delay = 0.1 
        self.center_counter = 0 
        self.y_aligned = False 
        self.ball_grabbed = False
        self.has_locked_target = False 
        self.target_visible = False 

        self.targets = targets
        self.count = 0
        self.obstacles = [] 
        
        # --- REWORKED DRIVE PARAMS ---
        self.center_threshold = 50
        self.max_speed = 30  # Dropped from 45
        self.min_speed = 15
        self.turn_scale = 0.5 # Dropped from 0.7 to soften proportional turning
        self.camera_fov_deg = 70.0 


    def update_target(self, bottom_detections, top_detections, depth_frame=None):
        if self.count >= len(self.targets):
            self.driving = False
            self.has_locked_target = False 
            self.target_visible = False
            return
            
        if(self.ball_grabbed == False):
            wanted_label = self.targets[self.count]
        else:
            wanted_label = (self.targets[self.count].split("_"))[0] + "_bucket"

        if wanted_label.lower() == "empty":
            self.driving = False
            self.has_locked_target = False
            self.target_visible = False
            self.mode = 0
            return

        found = False
        target_det = None
        self.obstacles = [] 
        self.active_camera = None

        if bottom_detections:
            for det in bottom_detections:
                if det["label"].lower() == wanted_label.lower():
                    target_det = det
                    self.active_camera = "bottom"
                elif "ball" in det["label"].lower() and det["label"].lower() != wanted_label.lower():
                    self.obstacles.append(det)

        if target_det is None and top_detections:
            for det in top_detections:
                if det["label"].lower() == wanted_label.lower():
                    target_det = det
                    self.active_camera = "top"
                    break 

        if target_det:
            cx = int((target_det["bbox"][0] + target_det["bbox"][2]) / 2)
            cy = int((target_det["bbox"][1] + target_det["bbox"][3]) / 2)
            
            self.target_pos["x"] = cx
            self.target_pos["y"] = cy
            self.last_target_x = cx 
                
            self.driving = True
            found = True
            self.has_locked_target = True 
            
            if self.mode == 4 or self.mode == 1:
                print(f"👀 Target spotted via {self.active_camera} camera! Tracking {wanted_label}...")
                self.mode = 0
                
        self.target_visible = found
        
        if self.driving and self.has_locked_target:
            if self.active_camera == "bottom" and depth_frame is not None:
                cx = self.target_pos["x"]
                cy = self.target_pos["y"]
                patch_size = 10
                half_p = patch_size // 2
                
                y_min = max(0, cy - half_p)
                y_max = min(self.frame_height, cy + half_p)
                x_min = max(0, cx - half_p)
                x_max = min(self.frame_width, cx + half_p)
                
                depth_patch = depth_frame[y_min:y_max, x_min:x_max]
                valid_depths = depth_patch[depth_patch > 0]
                
                if valid_depths.size > 0:
                    median_d_val = np.median(valid_depths) * 0.001
                    if median_d_val > 0.1: 
                        self.dist = median_d_val
                        self.distance_mm = median_d_val * 1000
            elif self.active_camera == "top":
                self.dist = 3.0
                self.distance_mm = 3000

            for obs in self.obstacles:
                obs_cx = int((obs["bbox"][0] + obs["bbox"][2]) / 2)
                obs_cy = int((obs["bbox"][1] + obs["bbox"][3]) / 2)
                obs["center"] = (obs_cx, obs_cy)
                
                o_y_min = max(0, obs_cy - 5)
                o_y_max = min(self.frame_height, obs_cy + 5)
                o_x_min = max(0, obs_cx - 5)
                o_x_max = min(self.frame_width, obs_cx + 5)
                
                obs_patch = depth_frame[o_y_min:o_y_max, o_x_min:o_x_max]
                valid_obs = obs_patch[obs_patch > 0]
                if valid_obs.size > 0:
                    obs["distance_mm"] = (np.median(valid_obs) * 0.001) * 1000
                else:
                    obs["distance_mm"] = 9999

            if self.mode == 0 and self.distance_mm < 2500 and self.distance_mm > 0:
                closest_obstacle_dist = 9999
                closest_obstacle_x = 0
                
                for obs in self.obstacles:
                    obs_x = obs["center"][0]
                    obs_dist = obs["distance_mm"]
                    if abs(obs_x - cx) < 200: 
                        if obs_dist < closest_obstacle_dist:
                            closest_obstacle_dist = obs_dist
                            closest_obstacle_x = obs_x
                
                if (closest_obstacle_dist < (self.distance_mm - 200) and closest_obstacle_dist <= 2500):
                    print(f"🛑 Corridor Blocked! Target: {self.distance_mm}mm, Obstacle: {closest_obstacle_dist}mm")
                    pixels_from_center = closest_obstacle_x - (self.frame_width / 2)
                    degrees_per_pixel = self.camera_fov_deg / self.frame_width
                    angle_to_obs = pixels_from_center * degrees_per_pixel
                    
                    angle_rad = math.radians(angle_to_obs)
                    obs_cartesian_x = closest_obstacle_dist * math.cos(angle_rad)
                    obs_cartesian_y = closest_obstacle_dist * math.sin(angle_rad)
                    
                    flank_offset_mm = 450.0 
                    
                    if closest_obstacle_x < cx or abs(closest_obstacle_x - cx) < 30:
                        waypoint_y = obs_cartesian_y + flank_offset_mm
                        self.waypoint_turn_dir = 1
                    else:
                        waypoint_y = obs_cartesian_y - flank_offset_mm
                        self.waypoint_turn_dir = -1
                        
                    waypoint_x = obs_cartesian_x 
                    dist_to_waypoint = math.hypot(waypoint_x, waypoint_y)
                    heading_to_waypoint = math.degrees(math.atan2(waypoint_y, waypoint_x))
                    
                    max_speed_mm_s = 914.4 / 1.6 
                    bypass_drive_speed_mm_s = max_speed_mm_s * 0.325 
                    turn_speed_deg_s = 60.0 # Slowed calculation down to match new drive speeds
                    
                    self.waypoint_turn_duration = abs(heading_to_waypoint) / turn_speed_deg_s
                    self.waypoint_drive_duration = dist_to_waypoint / bypass_drive_speed_mm_s
                    
                    self.waypoint_turn_duration = max(0.3, self.waypoint_turn_duration)
                    self.waypoint_drive_duration = max(0.8, self.waypoint_drive_duration)
                    
                    print(f"📍 Waypoint: Turn {self.waypoint_turn_duration:.2f}s, Drive {self.waypoint_drive_duration:.2f}s")
                    
                    self.mode = 6 
                    self.bypass_state = 0 
                    self.bypass_timer = time.time()

        if not found:
            if self.mode in [1, 2, 3, 6, 7]: 
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
            return 
            
        current_time = time.time()
        wanted_label = self.targets[self.count]

        if self.mode == 4:
            # Slower sweep rate (0.2 instead of 0.5)
            self.targetY += 0.2 * self.sweep_dir
            if self.targetY > 12.0: self.sweep_dir = -1
            elif self.targetY < -12.0: self.sweep_dir = 1
            self.targetX = 8.0
            self.targetZ = self.SAFE_HEIGHT
        elif self.mode in [0, 1]:
            self.targetY = 0.0
            self.targetX = 9.0
            self.targetZ = self.SAFE_HEIGHT

        if self.mode == 2 and self.grab_state == 0:
            webcam_sees_target = False
            centered_this_frame = False
            
            for det in webcam_detections:
                if det["label"].lower() == wanted_label.lower():
                    webcam_sees_target = True
                    x_c = int((det["bbox"][0] + det["bbox"][2]) / 2)
                    
                    if x_c <= 280:
                        # Slower centering (0.1 instead of 0.25)
                        self.targetY += 0.1
                        self.center_counter = 0
                        self.y_aligned = False 
                    elif x_c >= 360:
                        self.targetY -= 0.1
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

        if self.mode == 2:
            if self.grab_state == 0:
                if self.ball_grabbed:
                    self.targetZ = self.DROP_HEIGHT 
                    self.targetJawAngle = self.JAW_CLOSED
                    self.y_aligned = True 
                    print(f"LOCKED ON BUCKET -> PUNCHING FORWARD")
                    
                    old_x = self.targetX 
                    self.targetX = self.DROP_REACH_X 
                    reach_ratio = self.targetX / old_x
                    self.targetY = self.targetY * reach_ratio
                    
                    self.grab_state = 1
                    self.state_timer = current_time
                else:
                    self.targetZ = self.SAFE_HEIGHT 
                    self.targetJawAngle = self.JAW_OPEN
                    if self.y_aligned and self.dist > 0:
                        print(f"LOCKED ON BALL -> REACHING (Dist: {self.dist:.3f}m)")
                        old_x = self.targetX 
                        self.targetX = ((self.dist * 3.3) * 12) + 9 
                        reach_ratio = self.targetX / old_x
                        self.targetY = self.targetY * reach_ratio
                        
                        arm1 = 10
                        arm2 = 14
                        max_reach = arm1 + arm2
                        target_dist = math.sqrt(self.targetX**2 + self.targetY**2)
                        
                        if abs(self.targetZ) > max_reach or target_dist > math.sqrt(max_reach**2 - self.targetZ**2):
                            print("⚠️ Target is OUT OF REACH! Initiating Ramming Speed...")
                            self.mode = 7
                            self.ramming_timer = time.time()
                            self.targetX = 9.0
                            self.targetY = 0.0
                            self.targetZ = self.SAFE_HEIGHT
                            self.grab_state = 0
                            return 
                        
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
                    self.targetZ = self.SAFE_HEIGHT + 1.5
                    self.targetY = 0
                else:
                    self.targetZ = self.DROP_HEIGHT 
                self.targetX = 8
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
                        print("GRAB COMPLETE -> BACKING UP FOR VERIFICATION")
                        self.verifying_grab = True 

        if current_time - self.last_command_time > self.command_delay:
            Arm.move_joint(5, self.targetJawAngle)
            
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
        
        if self.mode == 7:
            if time.time() - self.ramming_timer < 1.0:
                return {"L": -50, "R": -50} # Reduced ramming speed
            else:
                print("Ramming complete. Attempting to re-acquire target...")
                self.mode = 3
                self.reverse_timer = time.time()
                return {"L": 0, "R": 0}

        if self.mode == 6:
            elapsed = time.time() - self.bypass_timer
            if self.bypass_state == 0:
                if elapsed < self.waypoint_turn_duration:
                    if self.waypoint_turn_dir == 1:
                        return {"L": -35, "R": 35} # Reduced bypass turn speed
                    else:
                        return {"L": 35, "R": -35} 
                else:
                    self.bypass_state = 1
                    self.bypass_timer = time.time()
                    elapsed = 0
            
            if self.bypass_state == 1:
                if elapsed < self.waypoint_drive_duration:
                    return {"L": -35, "R": -35} # Reduced bypass drive speed
                else:
                    self.mode = 4 
                    self.driving = True
                    self.leftActive = True 
                    self.rightActive = True
                    return {"L": 0, "R": 0}

        if self.mode == 3:
            if time.time() - self.reverse_timer < 3.0:
                reverse_speed = 30  # Reduced reverse speed
                self.data = {"L": reverse_speed, "R": reverse_speed}
                return self.data
            else:
                if self.verifying_grab:
                    if self.verification_timer == 0:
                        self.verification_timer = time.time()
                        return {"L": 0, "R": 0} 
                    
                    if time.time() - self.verification_timer < 0.5:
                        return {"L": 0, "R": 0}
                    
                    if self.target_visible:
                        print("❌ VERIFICATION FAILED: Ball still detected. Retrying grab...")
                        self.ball_grabbed = False
                    else:
                        print("✅ VERIFICATION SUCCESS: Ball secured. Switching to bucket.")
                        self.ball_grabbed = True
                        
                    self.verifying_grab = False
                    self.verification_timer = 0
                
                print("Spinning to search...")
                self.mode = 4 
                self.driving = True
                self.leftActive = True 
                self.rightActive = True
        
        if self.mode == 4:
            spin_speed = 35 # Halved spin speed
            if self.last_target_x > (self.frame_width / 2):
                self.data = {"L": -spin_speed, "R": spin_speed} 
            else:
                self.data = {"L": spin_speed, "R": -spin_speed} 
            return self.data

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

            if self.target_visible:
                target_x = self.target_pos["x"]
                shift_amount = 0
                avoidance_zone_mm = 800.0 
                
                for obs in self.obstacles:
                    obs_x = obs.get("center", [0, 0])[0]
                    obs_dist = obs.get("distance_mm", 9999)
                    
                    if obs_dist < avoidance_zone_mm and abs(obs_x - target_x) < 150:
                        urgency = 1.0 - (obs_dist / avoidance_zone_mm)
                        if obs_x < target_x:
                            shift_amount += 250 * urgency 
                        else:
                            shift_amount -= 250 * urgency 
                
                virtual_target_x = target_x + shift_amount
                virtual_target_x = max(50, min(self.frame_width - 50, virtual_target_x))
                
                error = virtual_target_x - (self.frame_width / 2)

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
                left_speed = forward_speed+5
                right_speed = forward_speed

        if self.mode == 1:
            r_raw = self.sensorData.get("RightUNO", 999) if self.sensorData else 999
            l_raw = self.sensorData.get("LeftUNO", 999) if self.sensorData else 999
            try:
                r_dist = float(r_raw)
                l_dist = float(l_raw)
            except:
                r_dist, l_dist = 999.0, 999.0

            if not self.ball_grabbed:
                if (r_dist <= 52 and r_dist >= 20) : self.rightActive = False  
                if (l_dist <= 52 and l_dist >= 20) : self.leftActive = False   
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