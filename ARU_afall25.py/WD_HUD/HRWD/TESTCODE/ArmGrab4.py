from Arm import CoOrdinateBaseSys as Arm
from Systems.InputSystem import AI_YOLO
from Systems.displaySystem import DisplaySystem
import time
import numpy as np             # REQUIRED for RealSense to OpenCV conversion
import pyrealsense2 as rs

infer = AI_YOLO(conf_threshold=0.3)
# cam = cvWebcam(...)          # REMOVE THIS: You are using RealSense now, not the standard webcam class
display = DisplaySystem(mode="YOLO") # Removed 'cam' arg since we manually feed frames now

targetId = "blue_ball" 
targetX = 200 # Safe forward distance
targetY = 0
targetZ = 10.0 

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
    global targetX, targetY, targetZ 
    target_found = False

    try:
        while True:
            # 1. Get frames
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
            detections = infer.run_inference(color_image)

            for det in detections:
                if det["label"] == targetId:
                    x_center = int((det["bbox"][0] + det["bbox"][2]) / 2)
                    y_center = int((det["bbox"][1] + det["bbox"][3]) / 2)

                    # --- VISUAL CENTERING ---
                    if x_center <= 300:
                        targetY += 1 
                        print("Moving LEFT")
                    elif x_center >= 340:
                        targetY -= 1
                        print("Moving RIGHT")
                    else:
                        print("CENTERED Y")
                        target_found = True
                        
                    
                    # --- DISTANCE MEASUREMENT ---
                    dist = depth_frame.get_distance(x_center, y_center)

                    if(target_found):
                        targetX = dist #places arm above target (hopefully)

                    Arm.ik(targetX, targetY, targetZ, [0,0,90,0,0,0], error=0.3)
                    print(f"Ball is {dist:.3f} meters away")
            


            # Pass the numpy image to your display system
            display.update_display(frame=color_image, detections=detections)
            time.sleep(0.05)
    finally:
        pipeline.stop()

def main():
    test_arm_grab()
    
if __name__ == "__main__":
    main()