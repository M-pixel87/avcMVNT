
from Systems.InputSystem import AI_YOLO
from Systems.displaySystem import DisplaySystem
import time
import numpy as np             # REQUIRED for RealSense to OpenCV conversion
import pyrealsense2 as rs

infer = AI_YOLO(conf_threshold=0.3)

display = DisplaySystem(cam = None, mode="YOLO") 

targetId = "red_ball" 


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

def testCam():
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
            detections = infer.detect(color_image)

            for det in detections:
                if det["label"] == targetId:
                    x_center = int((det["bbox"][0] + det["bbox"][2]) / 2)
                    y_center = int((det["bbox"][1] + det["bbox"][3]) / 2)

                        
                    
                    # --- DISTANCE MEASUREMENT ---
                    dist = depth_frame.get_distance(x_center, y_center)

                    if(target_found):
                        targetX = dist #places arm above target (hopefully)

                    print(f"Ball is {dist:.3f} meters away")
            


            # Pass the numpy image to your display system
            display.update_display(img=color_image, detections=detections)
            time.sleep(0.01)
    finally:
        pipeline.stop()

def main():
    testCam()
    
if __name__ == "__main__":
    main()