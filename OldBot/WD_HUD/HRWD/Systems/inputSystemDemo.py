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
    def __init__(self, state: modeState, deadzone=0.05): 
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
    def __init__(self, motorSystem, state, frame_width=640, frame_height=480, sensorData=None, targets=["green_ball", "red_ball", "blue_ball", "yellow_ball"]): 
        self.lock = threading.Lock() 

        # Arm & Tabletop Geometry
        self.SAFE_HEIGHT = 7.0          
        self.GRAB_HEIGHT = -2.0       
        self.SHOWCASE_HEIGHT = 14.0     
        self.JAW_OPEN = 70            
        self.JAW_CLOSED = 10          
        self.GRAB_OFFSET_Y = 4.0        
        self.GRAB_OFFSET_X = 0.0      
         
        self.sweep_rate = 0.2         
        self.command_delay = 0.1      

        self.motorSystem = motorSystem 
        self.state = state 
        self.sensorData = sensorData 
        self.targets = targets 
        self.count = 0 

        self.frame_width = frame_width 
        self.frame_height = frame_height 
        self.active_camera = "bottom" 
         
        self.data = {"L": 0, "R": 0} 
        self.target_pos = {"x": 0, "y": 0} 
        self.distance_mm = 300 
        self.dist = 0.3  
         
        self.mode = 2   
        self.driving = False 
        self.target_visible = False  
         
        self.targetX = 9.0  
        self.targetY = 0.0 
        self.targetZ = self.SAFE_HEIGHT 
        self.saved_ball_x = 9.0
        self.saved_ball_y = 0.0
        
        self.targetJawAngle = self.JAW_OPEN 
        self.sweep_dir = 1  
        self.grab_state = 0 
        self.state_timer = 0 
        self.last_command_time = 0 
        self.center_counter = 0  
        self.y_aligned = False  

    def get_fast_median_depth(self, depth_frame, cx, cy, patch_w=20, patch_h=20): 
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
            if not self.targets: return 
            
            wanted_label = self.targets[self.count % len(self.targets)] 
            found = False 
            target_det = None 
            best_score = float('-inf') 

            # Detect via Intel RealSense (bottom_detections)
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

            if target_det: 
                cx, cy = target_det["center"] 
                self.target_pos["x"], self.target_pos["y"] = cx, cy 
                found = True 
                
                # Sample depth from RealSense frame
                if depth_frame is not None:
                    median_val = self.get_fast_median_depth(depth_frame, cx, cy, 20, 20)
                    if median_val > 100.0:
                        self.distance_mm = median_val
                        self.dist = self.distance_mm * 0.001

            self.target_visible = found 

    def update_arm_logic(self, webcam_detections): 
        with self.lock: 
            if not self.targets: return 
            current_time = time.time() 
            wanted_label = self.targets[self.count % len(self.targets)] 

            # STATE 0: Target Alignment via Webcam & Reach Calculation
            if self.grab_state == 0: 
                self.targetJawAngle = self.JAW_OPEN
                self.targetZ = self.SAFE_HEIGHT
                webcam_sees_target = False 
                centered_this_frame = False 
                 
                if webcam_detections:
                    for det in webcam_detections: 
                        if det["label"].lower() == wanted_label.lower(): 
                            webcam_sees_target = True 
                            x_c = det["center"][0] 
                            error_x = 320 - x_c  
                            
                            if abs(error_x) > 35: 
                                dynamic_step = (error_x / 320.0) * 0.15  
                                clamped_step = max(-0.2, min(0.2, dynamic_step)) 
                                self.targetY += clamped_step 
                                self.center_counter, self.y_aligned = 0, False  
                            else: 
                                centered_this_frame = True 

                if webcam_sees_target: 
                    self.center_counter = self.center_counter + 1 if centered_this_frame else 0 
                    if self.center_counter >= 15: 
                        self.y_aligned = True 
                else:
                    # Gentle sweep search across the table if target not seen
                    self.targetY += self.sweep_rate * self.sweep_dir 
                    if self.targetY > 10.0: self.sweep_dir = -1 
                    elif self.targetY < -10.0: self.sweep_dir = 1 

                # Once Y is aligned, compute reach from RealSense distance
                if self.y_aligned and self.dist > 0: 
                    old_x = self.targetX  
                    
                    self.targetX = ((self.dist * 3.3) * 12) + 9  
                    if old_x != 0:
                        self.targetY = self.targetY * (self.targetX / old_x) 
                     
                    max_reach = 10 + 14  # 24.0 inches full physical reach
                    target_dist = math.sqrt(self.targetX**2 + self.targetY**2) 
                    safe_reach_sq = max_reach**2 - self.targetZ**2
                     
                    if safe_reach_sq > 0 and target_dist > math.sqrt(safe_reach_sq): 
                        print("⚠️ Target near max envelope. Scaling to outer limit.") 
                        scale = math.sqrt(safe_reach_sq) / target_dist 
                        self.targetX *= (scale * 0.95) 
                        self.targetY *= (scale * 0.95) 

                    # Cache target coordinates for returning the ball later
                    self.saved_ball_x = self.targetX
                    self.saved_ball_y = self.targetY

                    print(f"🎯 Locked [{wanted_label}] at X:{self.targetX:.2f}, Y:{self.targetY:.2f} (Dist: {self.distance_mm:.0f}mm)")
                    self.grab_state, self.state_timer = 1, current_time 

            # STATE 1: Hover above Ball Position
            elif self.grab_state == 1: 
                self.targetX = self.saved_ball_x
                self.targetY = self.saved_ball_y
                self.targetZ = self.SAFE_HEIGHT 
                self.targetJawAngle = self.JAW_OPEN 
                if current_time - self.state_timer > 1.5: 
                    self.grab_state, self.state_timer = 2, current_time 
             
            # STATE 2: Lower Gripper to Table
            elif self.grab_state == 2: 
                self.targetZ = self.GRAB_HEIGHT 
                if current_time - self.state_timer > 1.5: 
                    self.grab_state, self.state_timer = 3, current_time 

            # STATE 3: Close Gripper around Ball
            elif self.grab_state == 3: 
                self.targetJawAngle = self.JAW_CLOSED  
                if current_time - self.state_timer > 1.2: 
                    self.grab_state, self.state_timer = 4, current_time 

            # STATE 4: Retract Arm Back to Initialize / Home Showcase Position
            elif self.grab_state == 4: 
                self.targetX = 9.0 
                self.targetY = 0.0 
                self.targetZ = self.SHOWCASE_HEIGHT 
                if current_time - self.state_timer > 1.8: 
                    print(f"✨ Showcasing [{wanted_label}] at home position for 3 seconds...")
                    self.grab_state, self.state_timer = 5, current_time 

            # STATE 5: Hold at Home Position
            elif self.grab_state == 5: 
                self.targetX = 9.0 
                self.targetY = 0.0 
                self.targetZ = self.SHOWCASE_HEIGHT 
                if current_time - self.state_timer > 3.0: 
                    print(f"⬇️ Returning [{wanted_label}] back to pickup spot...")
                    self.grab_state, self.state_timer = 6, current_time 

            # STATE 6: Extend Back Out over the Original Spot (at Safe Height)
            elif self.grab_state == 6: 
                self.targetX = self.saved_ball_x
                self.targetY = self.saved_ball_y
                self.targetZ = self.SAFE_HEIGHT 
                if current_time - self.state_timer > 1.8: 
                    self.grab_state, self.state_timer = 7, current_time 

            # STATE 7: Lower Ball Back to Table Surface
            elif self.grab_state == 7: 
                self.targetZ = self.GRAB_HEIGHT 
                if current_time - self.state_timer > 1.5: 
                    self.grab_state, self.state_timer = 8, current_time 

            # STATE 8: Open Gripper to Release
            elif self.grab_state == 8: 
                self.targetJawAngle = self.JAW_OPEN 
                if current_time - self.state_timer > 1.2: 
                    self.grab_state, self.state_timer = 9, current_time 

            # STATE 9: Retract Arm Home and Advance to Next Target Color
            elif self.grab_state == 9: 
                self.targetX = 9.0 
                self.targetY = 0.0 
                self.targetZ = self.SAFE_HEIGHT 
                if current_time - self.state_timer > 1.5: 
                    self.count = (self.count + 1) % len(self.targets) 
                    print(f"🔄 Demo cycle complete. Next target: [{self.targets[self.count]}]") 
                    self.grab_state, self.center_counter, self.y_aligned = 0, 0, False 

            # Dispatch Kinematics
            if current_time - self.last_command_time > self.command_delay: 
                Arm.move_joint(5, self.targetJawAngle) 
                 
                final_x = self.targetX 
                final_y = self.targetY 
                final_z = self.targetZ 
                 
                # Apply grab offsets ONLY when reaching/lowering at the ball location
                if 1 <= self.grab_state <= 3 or 6 <= self.grab_state <= 8: 
                    final_x += self.GRAB_OFFSET_X 
                    final_y += self.GRAB_OFFSET_Y 

                Arm.move_arm_to(final_x, final_y, final_z) 
                self.last_command_time = current_time 

    def move_command(self): 
        # Base stays stationary on tabletop
        return {"L": 0, "R": 0}