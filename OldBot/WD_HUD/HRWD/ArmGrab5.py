from Arm import CoOrdinateBaseSys as Arm
from Systems.InputSystem import AI_YOLO
from Systems.InputSystem import cvWebcam
from Systems.displaySystem import DisplaySystem
import time
import numpy as np
import pyrealsense2 as rs

# --- CONFIGURATION ---
SAFE_HEIGHT = 8.0   
GRAB_HEIGHT = -2.0  
JAW_OPEN = 70
JAW_CLOSED = 10     
 
infer = AI_YOLO(conf_threshold=0.3)
cam = cvWebcam(cam_id=6, width=640, height=480)
display = DisplaySystem(cam = None , mode="YOLO") 
display2 = DisplaySystem(cam = cam ,name = "CAM2", mode="YOLO")

# --- GLOBAL STATE VARIABLES ---
targetId = "green_ball" 
targetX = 9.0 
targetY = 0.0
targetZ = SAFE_HEIGHT
targetJawAngle = JAW_OPEN
dist = 0

# Initial Move to Home
time.sleep(3)
Arm.move_arm_to(targetX, targetY, targetZ)
time.sleep(3)

# --- REAL SENSE SETUP ---
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
align_to = rs.stream.color
align = rs.align(align_to)
pipeline.start(config)

def test_arm_grab():
    global targetX, targetY, targetZ, dist, targetJawAngle
    
    grab_state = 0 
    state_timer = 0  
    
    last_command_time = 0
    command_delay = 0.1 
    center_counter = 0 
    
    # NEW: A persistent flag to remember if we are lined up
    y_aligned = False 

    try:
        while True:
            current_time = time.time()
            
            # 1. Capture & Process Frames
            frame = cam.get_frame()
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame: continue

            color_image = np.asanyarray(color_frame.get_data())
            detections = infer.detect(color_image) # RealSense
            detections2 = infer.detect(frame)      # Webcam

            # --- UPDATE DISTANCE (RealSense) ---
            realsense_sees_target = False
            for det in detections:
                if det["label"] == targetId:
                    x_c = int((det["bbox"][0] + det["bbox"][2]) / 2)
                    y_c = int((det["bbox"][1] + det["bbox"][3]) / 2)
                    d_val = depth_frame.get_distance(x_c, y_c)
                    if d_val > 0: 
                        dist = d_val 
                        realsense_sees_target = True
            
            # --- UPDATE Y-CENTERING (Webcam) ---
            if grab_state == 0:
                webcam_sees_target = False
                centered_this_frame = False
                
                for det in detections2:
                    if det["label"] == targetId:
                        webcam_sees_target = True
                        x_c = int((det["bbox"][0] + det["bbox"][2]) / 2)
                        
                        # Centering Logic
                        if x_c <= 280:
                            targetY += 0.25
                            print("Moving LEFT")
                            center_counter = 0
                            y_aligned = False # We moved, so we lost alignment
                        elif x_c >= 360:
                            targetY -= 0.25
                            print("Moving RIGHT")
                            center_counter = 0
                            y_aligned = False # We moved, so we lost alignment
                        else:
                            print("CENTERED Y")
                            centered_this_frame = True
                
                # Logic Update:
                # If the webcam sees it, update the counter based on centering.
                if webcam_sees_target and dist <= 4500:
                    if centered_this_frame:
                        center_counter += 1
                    else:
                        center_counter = 0
                else:
                    # Webcam is BLIND. 
                    # Do NOT reset center_counter or y_aligned.
                    # We assume if we can't see it, we haven't lost alignment yet.
                    pass

                # If counter is high enough, mark as officially aligned
                if center_counter >= 20:
                    y_aligned = True

            
            # --- STATE MACHINE ---

            # STATE 0: SEARCH & CENTER
            if grab_state == 0:
                targetZ = SAFE_HEIGHT
                targetJawAngle = JAW_OPEN
                
                # MODIFIED TRANSITION LOGIC:
                # 1. We are currently centered (center_counter >= 20)
                #    OR
                # 2. We WERE aligned (y_aligned) and RealSense still sees it (dist > 0)
                if (y_aligned and dist > 0):
                    print(f"LOCKED ON (Aligned: {y_aligned}, Dist: {dist:.3f}m) -> REACHING")
                    
                    targetX = ((dist * 3.3) * 12) + 9 
                    grab_state = 1
                    state_timer = time.time()

            # STATE 1: REACH
            elif grab_state == 1:
                if time.time() - state_timer > 2.0:
                    print("⬇️ GOING DOWN")
                    grab_state = 2
                    state_timer = time.time()
            
            # STATE 2: LOWER
            elif grab_state == 2:
                targetZ = GRAB_HEIGHT
                if time.time() - state_timer > 1.5:
                    print("CLOSING JAW")
                    grab_state = 3
                    state_timer = time.time()

            # STATE 3: GRAB
            elif grab_state == 3:
                targetJawAngle = JAW_CLOSED
                if time.time() - state_timer > 2.0:
                    print("⬆️ LIFTING")
                    grab_state = 4
                    state_timer = time.time()

            # STATE 4: LIFT
            elif grab_state == 4:
                targetZ = SAFE_HEIGHT
                targetX = 9.0 
                if time.time() - state_timer > 2.0:
                    print("RESETTING LOOP")
                    # Reset all flags for next run
                    grab_state = 0
                    center_counter = 0
                    y_aligned = False 
                    dist = 0
                    time.sleep(10)

            # --- SEND COMMANDS ---
            if current_time - last_command_time > command_delay:
                Arm.move_joint(5, targetJawAngle)
                Arm.move_arm_to(targetX, targetY, targetZ)
                last_command_time = current_time
                print(f"State: {grab_state} | X:{targetX:.1f} Y:{targetY:.1f} Z:{targetZ:.1f}")

            display.update_display(img=color_image, detections=detections)
            display2.update_display(img=frame, detections=detections2)
            time.sleep(0.0001)

    finally:
        pipeline.stop()

def main():
    test_arm_grab()
    
if __name__ == "__main__":
    main()