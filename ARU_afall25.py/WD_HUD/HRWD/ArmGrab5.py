from Arm import CoOrdinateBaseSys as Arm
from Systems.InputSystem import AI_YOLO
from Systems.InputSystem import cvWebcam
from Systems.displaySystem import DisplaySystem
import time
import numpy as np             # REQUIRED for RealSense to OpenCV conversion
import pyrealsense2 as rs

infer = AI_YOLO(conf_threshold=0.3)
cam = cvWebcam(cam_id=6, width=640, height=480)
display = DisplaySystem(cam = None , mode="YOLO") 
display2 = DisplaySystem(cam = cam ,name = "CAM2", mode="YOLO")

targetId = "red_ball" 
targetX = 9.0 # Safe forward distance
targetY = 0.0
targetZ = 8.0
dist = 0

Arm.move_arm_to(targetX,targetY,targetZ)

# --- REAL SENSE SETUP ---
pipeline = rs.pipeline()
config = rs.config()

# Enable both streams at 640x480 to match
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Create an align object to map depth pixels to color pixels
align_to = rs.stream.color
align = rs.align(align_to)

pipeline.start(config)

def test_arm_grab():
    # We need to access global variables to change position
    global targetX, targetY, targetZ , dist
    target_found = False

    # --- Timer Setup ---
    last_command_time = 0
    command_delay = 0.1  # 0.5s = 2 times per second

    try:
        while True:

            current_time = time.time()

            # 1. Get frames
            frame = cam.get_frame()
            frames = pipeline.wait_for_frames()
            
            # 2. Align depth frame to color frame
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            # 3. Convert RealSense image to Numpy Array (Crucial for YOLO)
            color_image = np.asanyarray(color_frame.get_data())

            # 4. Run YOLO on the numpy image
            detections = infer.detect(color_image)
            detections2 = infer.detect(frame)

            for det in detections:
                if det["label"] == targetId:
                    x_center = int((det["bbox"][0] + det["bbox"][2]) / 2)
                    y_center = int((det["bbox"][1] + det["bbox"][3]) / 2)
                        
                    
                    # --- DISTANCE MEASUREMENT ---
                    dist = depth_frame.get_distance(x_center, y_center)

                    print(f"Ball is {dist:.3f} meters away")
            count2 = 0
            for det in detections2:
                if det["label"] == targetId:
                    x_center = int((det["bbox"][0] + det["bbox"][2]) / 2)
                    y_center = int((det["bbox"][1] + det["bbox"][3]) / 2)

                    # --- VISUAL CENTERING ---
                    if x_center <= 280:
                        targetY += 0.25
                        print("Moving LEFT")
                        target_found = False 
                    elif x_center >= 360:
                        targetY -= 0.25
                        print("Moving RIGHT")
                        target_found = False 
                    else:
                        print("CENTERED Y")
                        count2 += 1
                        if(count2 >= 50):
                            target_found = True 
                        

                    if(target_found and dist != 0.000 ):
                        targetX = ((dist*3.3)*12) + 9 #places arm above target (hopefully)

                    if current_time - last_command_time > command_delay:
                        Arm.move_arm_to(targetX,targetY,targetZ)
                        last_command_time = current_time
                        



            # Pass the numpy image to your display system
            display.update_display(img=color_image, detections=detections)
            display2.update_display(img=frame, detections=detections2)
            time.sleep(0.0001)
    finally:
        pipeline.stop()

def main():
    test_arm_grab()
    
if __name__ == "__main__":
    main()