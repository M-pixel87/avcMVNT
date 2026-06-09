def update_arm_logic(self, webcam_detections):
        if self.count >= len(self.targets):
            return 
            
        current_time = time.time()
        
        if not self.ball_grabbed:
            acceptable_labels = [self.targets[self.count].lower()]
        else:
            base_color = self.targets[self.count].split("_")[0].lower()
            acceptable_labels = [f"{base_color}_bucket", f"{base_color} bucket"]

        # --- NON-GRABBING ARM STATES ---
        if self.mode == 4:
            if self.target_visible and self.active_camera == "top":
                # Top camera radar lock! Slowly center the arm so the chassis can turn towards it
                if self.targetY > 0.5: self.targetY -= 0.5
                elif self.targetY < -0.5: self.targetY += 0.5
                else: self.targetY = 0.0
            else:
                # Normal sweeping
                self.targetY += 0.5 * self.sweep_dir
                if self.targetY > 12.0: self.sweep_dir = -1
                elif self.targetY < -12.0: self.sweep_dir = 1
                
            self.targetX = 8.0
            self.targetZ = self.SAFE_HEIGHT + 4 if self.ball_grabbed else self.SAFE_HEIGHT
            
        elif self.mode in [0, 1]:
            self.targetY = 0.0
            self.targetX = 9.0
            self.targetZ = self.SAFE_HEIGHT + 4 if self.ball_grabbed else self.SAFE_HEIGHT

        # --- GRABBING ARM STATES ---
        if self.mode == 2 and self.grab_state == 0:
            webcam_sees_target = False
            centered_this_frame = False
            
            for det in webcam_detections:
                if det["label"].lower() in acceptable_labels:
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
                    
                    # FIX 1: Wipe the phantom distance memory so it actually drives to the next target!
                    self.distance_mm = 5000 
                    
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
