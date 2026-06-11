import os 
import time 
import torch 
import math 
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

os.environ["SDL_VIDEODRIVER"] = "dummy" 
os.environ["LD_PRELOAD"] = "/usr/lib/aarch64-linux-gnu/libgomp.so.1" 

class AI: 
    def __init__(self): 
        self.net = jetson_inference.detectNet( 
            model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_jone/ssd-mobilenet.onnx", 
            labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_jone/labels.txt", 
            input_blob="input_0", output_cvg="scores", output_bbox="boxes", threshold=0.5) 

    def detect(self, img): 
        if img: 
            detections = self.net.Detect(img) 
            if detections: 
                for detect in detections: 
                    print(f'Width of object: {detect.Right - detect.Left}') 

class AI_YOLO: 
    def __init__(self, model_path='/home/uafs/Downloads/weights(4).engine', conf_threshold=0.5): 
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
        if self.model is None or frame is None: return [] 
        results = self.model(frame, verbose=False) 
        detections = [] 
        for result in results: 
            for box in result.boxes: 
                conf = float(box.conf[0]) 
                if conf < self.conf_threshold: continue 
                x1, y1, x2, y2 = map(float, box.xyxy[0]) 
                cls_id = int(box.cls[0]) 
                label = self.class_names.get(cls_id, f"class_{cls_id}") 
                detections.append({ 
                    "class_id": cls_id, "label": label, "confidence": conf, 
                    "bbox": (int(x1), int(y1), int(x2), int(y2)), 
                    "center": (int((x1+x2)/2), int((y1+y2)/2)), 
                    "width": int(x2 - x1) 
                }) 
        return detections 

    def release(self): 
        cv2.destroyAllWindows() 

class intelCamera: 
    def __init__(self, width=640, height=480, fps=15): 
        self.width, self.height, self.fps = width, height, fps 
        self.stopped = False 
        self.frame_data = (None, None)  
        self.pipeline = rs.pipeline() 
        self.config = rs.config() 
        self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps) 
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps) 
        try: 
            self.profile = self.pipeline.start(self.config) 
            print(f"✅ Intel RealSense initialized [{width}x{height} @ {fps} FPS]") 
        except Exception as e: 
            print(f"❌ Initial Intel Cam startup failed: {e}") 

        self.thread = threading.Thread(target=self.update, daemon=True) 
        self.thread.start() 

    def update(self): 
        while not self.stopped: 
            try: 
                frames = self.pipeline.wait_for_frames(timeout_ms=1000) 
                depth_frame = frames.get_depth_frame() 
                color_frame = frames.get_color_frame() 
                if depth_frame and color_frame: 
                    d_img = np.asanyarray(depth_frame.get_data()) 
                    c_img = np.asanyarray(color_frame.get_data()) 
                    self.frame_data = (d_img, c_img) 
            except Exception as e: 
                print(f"⚠️ Intel Cam Error: {e} | Attempting hardware recovery...") 
                cv2.waitKey(2000)  
                try: self.pipeline.stop() 
                except: pass  
                try: 
                    self.pipeline.start(self.config) 
                    print("✅ Intel Cam successfully recovered!") 
                except Exception as reset_e: 
                    print(f"❌ Recovery failed: {reset_e}") 

    def get_frames(self): return self.frame_data 
    def release(self): 
        self.stopped = True 
        try: self.pipeline.stop() 
        except: pass 

class cvWebcam: 
    def __init__(self, cam_id=0, width=640, height=480, fps=30): 
        self.cam_id, self.width, self.height = cam_id, width, height 
        self.stopped = False 
        self.grabbed = False 
        self.frame = None 
        self.camera = cv2.VideoCapture(cam_id, cv2.CAP_V4L2) 
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width) 
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height) 
        self.camera.set(cv2.CAP_PROP_FPS, fps) 
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1) 

        if self.camera.isOpened(): 
            print(f"✅ cvWebcam threaded on /dev/video{cam_id}") 
            self.grabbed, self.frame = self.camera.read() 
            self.thread = threading.Thread(target=self.update, daemon=True) 
            self.thread.start() 
        else: 
            print(f"❌ Failed to open cvWebcam {cam_id}") 

    def update(self): 
        while not self.stopped: 
            if not self.camera.isOpened(): break 
            grabbed, frame = self.camera.read() 
            if grabbed: 
                self.grabbed = grabbed 
                self.frame = frame 

    def get_frame(self): return self.frame 
    def release(self): 
        self.stopped = True 
        self.camera.release() 

class XboxController: 
    def __init__(self, state: modeState , deadzone=0.05): 
        self.deadzone = deadzone 
        self.data = {"L": 0, "R": 0, "buttons": []} 
        self.mode = 0 
        self.state = state 
        self.x, self.y, self.z = 10, 0, 10 
        self.jawA, self.wristA = 5.0, -90.0 
        self.last_xyz = (self.x, self.y, self.z) 

        if pygame.joystick.get_count() == 0: 
            self.connected = False 
        else: 
            self.connected = True 
            self.joystick = pygame.joystick.Joystick(0) 
            self.joystick.init() 
            print(f"✅ Controller: {self.joystick.get_name()}") 

    def scale_axis(self, val): return int(val * 100) 

    def poll(self): 
        if self.connected: 
            left_speed, right_speed = 0, 0 
            buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())] 

            if self.mode == 0 and self.state.mode == False: 
                left_speed = self.scale_axis(self.joystick.get_axis(1)) 
                right_speed = self.scale_axis(self.joystick.get_axis(3)) 
                if abs(left_speed) < self.deadzone * 100: left_speed = 0 
                if abs(right_speed) < self.deadzone * 100: right_speed = 0 
            elif self.mode == 1 and self.state.mode == False: 
                left_x, left_y, right_y = self.joystick.get_axis(0), self.joystick.get_axis(1), self.joystick.get_axis(3) 
                if abs(left_x) > 0.2: self.x += left_x * 0.5 
                if abs(left_y) > 0.2: self.z -= left_y * 0.5 
                if abs(right_y) > 0.2: self.y -= right_y * 0.5 
                if (self.x, self.y, self.z) != self.last_xyz: 
                    Arm.move_arm_to(self.x, self.y, self.z, speed=200, acc=100) 
                    self.last_xyz = (self.x, self.y, self.z) 

            if buttons[0] == 1: 
                self.mode = 1 if self.mode == 0 else 0 
                time.sleep(0.3) 
            if buttons[1] == 1: 
                self.state.toggle() 
                time.sleep(0.3) 
            if buttons[4]: self.jawA += 2 
            if buttons[3]: self.jawA -= 2 
            if buttons[6]: self.wristA -= 5 
            if buttons[7]: self.wristA += 5 

            self.data = {"L": left_speed, "R": right_speed, "buttons": buttons} 
            return self.data 
        return {"L": 0, "R": 0, "buttons": []} 


    def get_axes(self): return [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())] if self.connected else [0] 

class AI_Inputs: 

    def __init__(self, motorSystem, state, frame_width=640, frame_height=480, sensorData=None, targets=["Empty","Empty","Empty","Empty"]): 
        self.lock = threading.Lock() 
        self.max_speed = 99           
        self.min_speed = 30           
        self.reverse_speed = 70       
        self.spin_speed = 28          
        self.ramming_speed = -70      
         
        self.turn_scale = 0.90       
        self.center_threshold = 50    
         
        self.slow_start_dist = 800    
        self.stop_dist = 300          
        self.avoidance_zone = 800.0   
        self.sensor_stop_max = 10     # Reverted to 10
        self.sensor_stop_min = 9      
        self.cam_stop_ball = 300      # Reverted to 300
        self.cam_stop_bucket = 275    
         
        self.top_cam_speed = 70             
        self.search_timeout = 8.0     
        self.wander_base_duration = 3.0     
        self.wander_dist_scalar = 0.030    
        self.dynamic_wander_duration = 3.0  
         
        self.stuck_timer = time.time() 
        self.last_stuck_dist = 5000 
        self.stuck_threshold_mm = 50  
        self.stuck_timeout = 3.0      

        self.SAFE_HEIGHT = 7          
        self.GRAB_HEIGHT = -2.0       
        self.DROP_HEIGHT = 16         
        self.DROP_REACH_X = 16        
        self.JAW_OPEN = 70            
        self.JAW_CLOSED = 10          
        self.GRAB_OFFSET_Y = 4        
        self.GRAB_OFFSET_X = 0.0      
         
        self.DROP_OFFSET_X = 0.0      
        self.DROP_OFFSET_Y = 2.0      
        self.DROP_OFFSET_Z = 0.0      
         
        self.sweep_rate = 0.2         
        self.centering_rate = 0.1     
        self.command_delay = 0.1      

        self.motorSystem = motorSystem 
        self.state = state 
        self.sensorData = sensorData 
        self.targets = targets 
        self.count = 0 
        self.obstacles = [] 

        self.frame_width = frame_width 
        self.frame_height = frame_height 
        self.active_camera = "bottom" 
        self.camera_fov_deg = 70.0 
         
        self.data = {"L": 0, "R": 0} 
        self.target_pos = {"x": 0, "y": 0} 
        self.last_target_x = self.frame_width / 2  
        self.distance_mm = 5000 
        self.dist = 5  
         
        self.mode = 0   
        self.driving = False 
        self.rightActive = True 
        self.leftActive = True 
        self.has_locked_target = False  
        self.target_visible = False  
         
        self.bypass_timer = 0 
        self.bypass_state = 0  
        self.waypoint_turn_duration = 0.0 
        self.waypoint_drive_duration = 0.0 
        self.waypoint_turn_dir = 1  
        self.verification_timer = 0 
        self.verifying_grab = False 
        self.ramming_timer = 0  
        self.reverse_timer = 0   
         
        self.search_timer = 0 
        self.wander_timer = 0 
        self.wander_target_x = self.frame_width / 2 
         
        self.targetX = 9.0  
        self.targetY = 0.0 
        self.targetZ = self.SAFE_HEIGHT 
        self.targetJawAngle = self.JAW_OPEN 
        self.sweep_dir = 1  
        self.grab_state = 0 
        self.state_timer = 0 
        self.last_command_time = 0 
        self.center_counter = 0  
        self.y_aligned = False  
        self.ball_grabbed = False 
        self.lost_target_timer = 0 

    def get_fast_median_depth(self, depth_frame, cx, cy, patch_w, patch_h): 
        y_min = max(0, int(cy - patch_h//2)) 
        y_max = min(self.frame_height, int(cy + patch_h//2)) 
        x_min = max(0, int(cx - patch_w//2)) 
        x_max = min(self.frame_width, int(cx + patch_w//2)) 
         
        patch = depth_frame[y_min:y_max, x_min:x_max].astype(np.float32) 
        patch[patch == 0] = np.nan  
         
        with np.errstate(all='ignore'): 
            median = np.nanmedian(patch) 
        return median if not np.isnan(median) else 0.0 

    def update_target(self, bottom_detections, top_detections, depth_frame=None): 
        with self.lock: 
            if self.count >= len(self.targets): 
                self.driving, self.has_locked_target, self.target_visible = False, False, False 
                return 
                 
            if self.ball_grabbed or self.mode in [2, 3] or self.verifying_grab: 
                top_detections = []  
                 
            wanted_label = (self.targets[self.count].split("_"))[0] + "_bucket" if self.ball_grabbed else self.targets[self.count] 

            if wanted_label.lower() == "empty": 
                self.driving, self.has_locked_target, self.target_visible, self.mode = False, False, False, 0 
                return 

            found = False 
            target_det = None 
            self.obstacles = []  
            new_active_camera = None 

            best_score = float('-inf') 

            if bottom_detections: 
                for det in bottom_detections: 
                    label_lower = det["label"].lower() 
                    if label_lower == wanted_label.lower(): 
                        width = det["bbox"][2] - det["bbox"][0] 
                        dist_from_center = abs(det["center"][0] - (self.frame_width / 2)) 
                        score = width - (dist_from_center * 0.5)  
                        if score > best_score: 
                            best_score = score 
                            target_det = det 
                            new_active_camera = "bottom" 
                    elif ("ball" in label_lower or "bucket" in label_lower) and label_lower != wanted_label.lower(): 
                        self.obstacles.append(det) 

            if target_det is None and top_detections and (self.distance_mm > 600 or self.active_camera != "bottom"): 
                best_score = float('-inf') 
                for det in top_detections: 
                    if det["label"].lower() == wanted_label.lower(): 
                        width = det["bbox"][2] - det["bbox"][0] 
                        dist_from_center = abs(det["center"][0] - (self.frame_width / 2)) 
                        score = width - (dist_from_center * 0.5) 
                        if score > best_score: 
                            best_score = score 
                            target_det = det 
                            new_active_camera = "top" 

            if target_det: 
                self.active_camera = new_active_camera 
                cx, cy = target_det["center"] 
                self.target_height = target_det["bbox"][3] - target_det["bbox"][1] 
                self.target_pos["x"], self.target_pos["y"] = cx, cy 
                self.last_target_x = cx  
                     
                self.driving, found, self.has_locked_target = True, True, True 
                 
                if self.mode in [1, 4, 8]: 
                    print(f"👀 Target spotted via {self.active_camera} camera! Tracking {wanted_label}...") 
                    self.mode = 0 
                    self.search_timer = 0  
                     
            self.target_visible = found 
             
            if self.driving and depth_frame is not None: 
                if self.target_visible and self.active_camera == "bottom": 
                    median_val = self.get_fast_median_depth(depth_frame, self.target_pos["x"], self.target_pos["y"], 20, 20) 
                    if median_val > 100.0:  
                        self.distance_mm = median_val 
                        self.dist = self.distance_mm * 0.001 

                elif self.ball_grabbed and self.mode == 1: 
                    median_val = self.get_fast_median_depth(depth_frame, self.target_pos["x"], self.target_pos["y"], 100, 60) 
                    if 50.0 < median_val < 1500.0:  
                        self.distance_mm = median_val 
                        self.dist = self.distance_mm * 0.001 

                elif self.active_camera == "top": 
                    self.dist, self.distance_mm = 1.5, 1500 

            if depth_frame is not None: 
                for obs in self.obstacles: 
                    cx, cy = obs["center"] 
                    median_val = self.get_fast_median_depth(depth_frame, cx, cy, 10, 10) 
                    obs["distance_mm"] = median_val if median_val > 0 else 9999 
            else: 
                for obs in self.obstacles: obs["distance_mm"] = 9999 

            if self.mode == 0 and self.distance_mm < 2500 and self.distance_mm > 0: 
                closest_obstacle_dist = 9999 
                closest_obstacle_x = 0 
                 
                for obs in self.obstacles: 
                    if abs(obs["center"][0] - self.target_pos["x"]) < 200:  
                        if obs["distance_mm"] < closest_obstacle_dist: 
                            closest_obstacle_dist = obs["distance_mm"] 
                            closest_obstacle_x = obs["center"][0] 
                 
                if (closest_obstacle_dist < (self.distance_mm - 200) and closest_obstacle_dist <= 2500): 
                    print(f"🛑 Corridor Blocked! Target: {self.distance_mm}mm, Obstacle: {closest_obstacle_dist}mm") 
                    pixels_from_center = closest_obstacle_x - (self.frame_width / 2) 
                    degrees_per_pixel = self.camera_fov_deg / self.frame_width 
                    angle_to_obs = pixels_from_center * degrees_per_pixel 
                     
                    angle_rad = math.radians(angle_to_obs) 
                    obs_cartesian_x = closest_obstacle_dist * math.cos(angle_rad) 
                    obs_cartesian_y = closest_obstacle_dist * math.sin(angle_rad) 
                     
                    flank_offset_mm = 450.0  
                     
                    if closest_obstacle_x < self.target_pos["x"] or abs(closest_obstacle_x - self.target_pos["x"]) < 30: 
                        waypoint_y = obs_cartesian_y + flank_offset_mm 
                        self.waypoint_turn_dir = 1 
                    else: 
                        waypoint_y = obs_cartesian_y - flank_offset_mm 
                        self.waypoint_turn_dir = -1 
                         
                    waypoint_x = obs_cartesian_x  
                    dist_to_waypoint = math.hypot(waypoint_x, waypoint_y) 
                    heading_to_waypoint = math.degrees(math.atan2(waypoint_y, waypoint_x)) 
                     
                    max_speed_mm_s = 914.4 / 1.6  
                    bypass_drive_speed_mm_s = max_speed_mm_s * 0.65  
                    turn_speed_deg_s = 60.0  
                     
                    self.waypoint_turn_duration = max(0.3, abs(heading_to_waypoint) / turn_speed_deg_s) 
                    self.waypoint_drive_duration = max(0.8, dist_to_waypoint / bypass_drive_speed_mm_s) 
                     
                    self.mode = 6  
                    self.bypass_state = 0  
                    self.bypass_timer = time.time() 

            if not found: 
                if self.mode in [1, 2, 3, 6, 7, 8]: pass  
                elif self.driving and self.distance_mm < 1200 and self.has_locked_target and self.mode == 0: 
                    self.mode, self.driving = 1, True 
                else: 
                    self.mode, self.driving, self.has_locked_target = 4, True, False 

    def update_arm_logic(self, webcam_detections): 
        with self.lock: 
            if self.count >= len(self.targets): return  
                 
            current_time = time.time() 
            wanted_label = self.targets[self.count] 

            if self.mode == 4: 
                if not self.ball_grabbed: 
                    self.targetY += self.sweep_rate * self.sweep_dir 
                    if self.targetY > 12.0: self.sweep_dir = -1 
                    elif self.targetY < -12.0: self.sweep_dir = 1 
                else: 
                    self.targetY = 0.0  
                     
                self.targetX = 8.0 
                self.targetZ = self.DROP_HEIGHT if self.ball_grabbed else self.SAFE_HEIGHT 
                 
            elif self.mode in [0, 1]: 
                self.targetY = 0.0 
                self.targetX = 9.0 
                self.targetZ = self.DROP_HEIGHT if self.ball_grabbed else self.SAFE_HEIGHT 

            if self.mode == 2 and self.grab_state == 0: 
                webcam_sees_target = False 
                centered_this_frame = False 
                 
                for det in webcam_detections: 
                    if det["label"].lower() == wanted_label.lower(): 
                        webcam_sees_target = True 
                        x_c = det["center"][0] 
                         
                        error_x = 320 - x_c  
                        if abs(error_x) > 40: 
                            dynamic_step = (error_x / 320.0) * 0.15  
                            clamped_step = max(-0.2, min(0.2, dynamic_step)) 
                             
                            self.targetY += clamped_step 
                            self.center_counter, self.y_aligned = 0, False  
                        else: 
                            centered_this_frame = True 

                if not webcam_sees_target and not self.ball_grabbed: 
                    # FIX: Prevent blindspot ramming. If we are close, it's just out of the camera's FOV.
                    if 0 < self.distance_mm < 400:
                        self.lost_target_timer = 0
                    else:
                        if self.lost_target_timer == 0: 
                            self.lost_target_timer = current_time  
                        elif current_time - self.lost_target_timer > 3.0:  
                            print("⚠️ Ball lost! Ramming to reset...") 
                            self.mode, self.ramming_timer = 7, current_time 
                            self.targetX, self.targetY, self.targetZ = 9.0, 0.0, self.SAFE_HEIGHT 
                            self.grab_state, self.lost_target_timer = 0, 0 
                            self.driving, self.leftActive, self.rightActive = True, True, True 
                            return  
                else: 
                    self.lost_target_timer = 0  
                 
                if webcam_sees_target: 
                    self.center_counter = self.center_counter + 1 if centered_this_frame else 0 

                if self.center_counter >= 20: self.y_aligned = True 

            if self.mode == 2: 
                if self.grab_state == 0: 
                    if self.ball_grabbed: 
                        self.targetZ, self.targetJawAngle, self.y_aligned = self.DROP_HEIGHT, self.JAW_CLOSED, True  
                        old_x = self.targetX  
                        self.targetX = self.DROP_REACH_X  
                        self.targetY = self.targetY * (self.targetX / old_x) 
                        self.grab_state, self.state_timer = 1, current_time 
                    else: 
                        self.targetZ, self.targetJawAngle = self.SAFE_HEIGHT, self.JAW_OPEN 
                        if self.y_aligned and self.dist > 0: 
                            old_x = self.targetX  
                            self.targetX = ((self.dist * 3.3) * 12) + 9  
                            self.targetY = self.targetY * (self.targetX / old_x) 
                             
                            max_reach = 10 + 14 
                            target_dist = math.sqrt(self.targetX**2 + self.targetY**2) 
                             
                            if abs(self.targetZ) > max_reach or target_dist > math.sqrt(max_reach**2 - self.targetZ**2): 
                                # FIX: Don't ram if we are already safely in the pickup zone
                                if self.distance_mm > 400 or self.distance_mm == 0:
                                    print("⚠️ Target is OUT OF REACH! Initiating Ramming Speed...") 
                                    self.mode, self.ramming_timer = 7, time.time() 
                                    self.targetX, self.targetY, self.targetZ, self.grab_state = 9.0, 0.0, self.SAFE_HEIGHT, 0 
                                    return  
                                else:
                                    print("⚠️ Target mathematically out of reach but physically close. Clamping reach.")
                                    scale = math.sqrt(max_reach**2 - self.targetZ**2) / target_dist
                                    self.targetX *= (scale * 0.95)
                                    self.targetY *= (scale * 0.95)
                                    self.grab_state, self.state_timer = 1, current_time
                            else:
                                self.grab_state, self.state_timer = 1, current_time 

                elif self.grab_state == 1: 
                    if current_time - self.state_timer > 2.0: 
                        self.grab_state, self.state_timer = 2, current_time 
                 
                elif self.grab_state == 2: 
                    self.targetZ = self.DROP_HEIGHT if self.ball_grabbed else self.GRAB_HEIGHT 
                    if current_time - self.state_timer > 2.0: 
                        self.grab_state, self.state_timer = 3, current_time 

                elif self.grab_state == 3: 
                    self.targetJawAngle = self.JAW_OPEN if self.ball_grabbed else self.JAW_CLOSED  
                    if current_time - self.state_timer > 1.0: 
                        self.grab_state, self.state_timer = 4, current_time 

                elif self.grab_state == 4: 
                    if self.ball_grabbed: 
                        self.targetZ, self.targetY = self.SAFE_HEIGHT + 1.5, 0 
                    else: 
                        self.targetZ = self.DROP_HEIGHT  
                    self.targetX, self.targetY  = 8, 0 
                     
                    if current_time - self.state_timer > 2.0: 
                        self.grab_state, self.center_counter, self.y_aligned, self.dist, self.distance_mm = 0, 0, False, 0, 5000 
                        self.mode, self.reverse_timer = 3, current_time 
                         
                        if self.ball_grabbed: 
                            print("BALL DROPPED -> BACKING UP & SEEKING NEXT TARGET") 
                            self.ball_grabbed = False 
                            self.count += 1   
                        else: 
                            print("GRAB COMPLETE -> BACKING UP FOR VERIFICATION") 
                            self.verifying_grab = True  

            if current_time - self.last_command_time > self.command_delay: 
                Arm.move_joint(5, self.targetJawAngle) 
                 
                final_x = self.targetX 
                final_y = self.targetY 
                final_z = self.targetZ 
                 
                if self.grab_state > 0: 
                    if not self.ball_grabbed: 
                        final_x += self.GRAB_OFFSET_X 
                        final_y += self.GRAB_OFFSET_Y 
                    else: 
                        final_x += self.DROP_OFFSET_X 
                        final_y += self.DROP_OFFSET_Y 
                        final_z += self.DROP_OFFSET_Z 

                Arm.move_arm_to(final_x, final_y, final_z) 
                self.last_command_time = current_time 

    def move_command(self): 
        with self.lock: 
            left_speed, right_speed = 0, 0 
             
            if not self.driving or self.mode not in [0, 1]: 
                self.stuck_timer = time.time() 
                self.last_stuck_dist = self.distance_mm 
             
            if self.mode == 7: 
                if time.time() - self.ramming_timer < 1.0: 
                    return {"L": self.ramming_speed, "R": self.ramming_speed}  
                else: 
                    self.mode, self.reverse_timer = 3, time.time() 
                    return {"L": 0, "R": 0} 

            if self.mode == 6: 
                elapsed = time.time() - self.bypass_timer 
                if self.bypass_state == 0: 
                    if elapsed < self.waypoint_turn_duration: 
                        return {"L": -50, "R": 50} if self.waypoint_turn_dir == 1 else {"L": 50, "R": -50}  
                    else: 
                        self.bypass_state, self.bypass_timer, elapsed = 1, time.time(), 0 
                 
                if self.bypass_state == 1: 
                    if elapsed < self.waypoint_drive_duration: 
                        return {"L": -50, "R": -50}  
                    else: 
                        self.mode, self.driving, self.leftActive, self.rightActive = 4, True, True, True 
                        return {"L": 0, "R": 0} 

            if self.mode == 3: 
                if time.time() - self.reverse_timer < 2.0: 
                    self.data = {"L": self.reverse_speed, "R": self.reverse_speed} 
                    return self.data 
                else: 
                    if self.verifying_grab: 
                        if self.verification_timer == 0: 
                            self.verification_timer = time.time() 
                            return {"L": 0, "R": 0}  
                        if time.time() - self.verification_timer < 0.5: 
                            return {"L": 0, "R": 0} 
                         
                        if self.target_visible: 
                            print("❌ VERIFICATION FAILED: Retrying grab...") 
                            self.ball_grabbed = False 
                        else: 
                            print("✅ VERIFICATION SUCCESS: Switching to bucket.") 
                            self.ball_grabbed = True 
                             
                        self.verifying_grab, self.verification_timer = False, 0 
                     
                    self.mode, self.driving, self.leftActive, self.rightActive = 4, True, True, True 
             
            if self.mode == 4: 
                if self.search_timer == 0: 
                    self.search_timer = time.time() 
                elif time.time() - self.search_timer > self.search_timeout: 
                    print("🔄 Search timeout! Initiating wander protocol...") 
                    self.mode, self.search_timer, self.wander_timer = 8, 0, time.time() 

                    max_dist = 0 
                    for obs in self.obstacles: 
                        obs_label = obs.get("label", "").lower() 
                        if "bucket" in obs_label or "ball" in obs_label: 
                            dist = obs.get("distance_mm", 9999) 
                            if dist > max_dist and dist < 9000: 
                                max_dist = dist 
                     
                    self.dynamic_wander_duration = self.wander_base_duration 
                    if max_dist > 0: 
                        self.dynamic_wander_duration += max_dist * self.wander_dist_scalar 
                        print(f"📈 Scaled wander duration to {self.dynamic_wander_duration:.2f}s (Max dist: {max_dist}mm)") 

                self.data = {"L": -self.spin_speed, "R": self.spin_speed} if self.last_target_x > (self.frame_width / 2) else {"L": self.spin_speed, "R": -self.spin_speed}  
                return self.data 
                 
            if self.mode == 8: 
                if time.time() - self.wander_timer < self.dynamic_wander_duration: 
                     
                    self.wander_target_x = self.frame_width / 2  
                    for obs in self.obstacles: 
                        obs_label = obs["label"].lower() 
                        if("bucket" in obs_label or "ball" in obs_label): 
                            self.wander_target_x = obs["center"][0] 
                            break 

                    error = self.wander_target_x - (self.frame_width / 2) 
                    turn_amount = (error / (self.frame_width / 2)) * self.turn_scale 
                    base_spd = self.max_speed * 0.75  
                    left_s = base_spd if error > 0 else base_spd * (1 + turn_amount) 
                    right_s = base_spd * (1 - turn_amount) if error > 0 else base_spd 
                    return {"L": int(-max(0, left_s)), "R": int(-max(0, right_s))} 
                else: 
                    self.mode, self.search_timer = 4, time.time() 
                    return {"L": 0, "R": 0} 

            if self.driving and self.mode in [0, 1]: 
                 
                if time.time() - self.stuck_timer > self.stuck_timeout: 
                    if abs(self.distance_mm - self.last_stuck_dist) < self.stuck_threshold_mm and self.distance_mm < 2500: 
                        print(f"⚠️ STUCK DETECTED! (Dist moved: {abs(self.distance_mm - self.last_stuck_dist)}mm). Backing up...") 
                        self.mode, self.reverse_timer = 3, time.time() 
                        self.stuck_timer = time.time() 
                        return {"L": self.reverse_speed, "R": self.reverse_speed} 
                     
                    self.stuck_timer = time.time() 
                    self.last_stuck_dist = self.distance_mm 
                 
                if self.active_camera == "top": 
                    forward_speed = self.top_cam_speed 
                elif self.distance_mm >= self.slow_start_dist: 
                    forward_speed = self.max_speed 
                elif self.distance_mm <= self.stop_dist: 
                    forward_speed = self.min_speed 
                    if self.mode == 0: self.mode = 1  
                else: 
                    ratio = (self.distance_mm - self.stop_dist) / (self.slow_start_dist - self.stop_dist) 
                    forward_speed = self.min_speed + (ratio * (self.max_speed - self.min_speed)) 

                if self.target_visible: 
                    shift_amount = sum([250 * (1.0 - (obs.get("distance_mm", 9999) / self.avoidance_zone))  
                                        for obs in self.obstacles  
                                        if obs.get("distance_mm", 9999) < self.avoidance_zone and abs(obs.get("center", [0,0])[0] - self.target_pos["x"]) < 150]) 

                    virtual_target_x = max(50, min(self.frame_width - 50, self.target_pos["x"] + shift_amount)) 
                    error = virtual_target_x - (self.frame_width / 2) 

                    if abs(error) < self.center_threshold: 
                        left_speed, right_speed = forward_speed, forward_speed 
                    else: 
                        turn_amount = (error / (self.frame_width / 2)) * self.turn_scale 
                        left_speed = forward_speed if error > 0 else forward_speed * (1 + turn_amount) 
                        right_speed = forward_speed * (1 - turn_amount) if error > 0 else forward_speed 
                else: 
                    left_speed, right_speed = forward_speed+5, forward_speed 

            if self.mode == 1: 
                r_dist = float(self.sensorData.get("RightUNO", 999)) if self.sensorData else 999.0 
                l_dist = float(self.sensorData.get("LeftUNO", 999)) if self.sensorData else 999.0 

                if self.sensor_stop_min <= r_dist <= self.sensor_stop_max: self.rightActive = False   
                if self.sensor_stop_min <= l_dist <= self.sensor_stop_max: self.leftActive = False    
                 
                stop_thresh = self.cam_stop_bucket if self.ball_grabbed else self.cam_stop_ball 
                 
                if (self.distance_mm <= stop_thresh and self.distance_mm != 0) or (self.ball_grabbed and getattr(self, "target_height", 0) > (self.frame_height * 0.99)): 
                    self.leftActive, self.rightActive = False, False 
                 
                if not self.rightActive and not self.leftActive: 
                    self.mode, self.driving = 2, False 
                     
            if self.mode == 2: 
               self.driving = False 

            left_speed = 0 if (not self.leftActive or not self.driving or self.mode == 2) else max(0, min(left_speed, self.max_speed)) * -1 
            right_speed = 0 if (not self.rightActive or not self.driving or self.mode == 2) else max(0, min(right_speed, self.max_speed)) * -1 

            self.data = {"L": int(left_speed), "R": int(right_speed)} 
            return self.data