'''
AVC 2026 example code for Intel RealSense cameras using the pyrealsense2 library.

This script initializes the RealSense camera, configures it to stream both depth and color data, and displays the combined output in a window.
'''



import pyrealsense2 as rs
import numpy as np
import cv2


# 1. Configure the pipeline
pipeline = rs.pipeline()
config = rs.config()


# 2. Enable Streams (Depth + Color)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)


# 3. Start Streaming
try:
    pipeline.start(config)
    print("Camera started successfully. Press 'q' to exit.")
    
    while True:
        frames = pipeline.wait_for_frames()  # This returns both depth and color frames when available
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue
            
        # Convert to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        
        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        # Stack both images horizontally
        images = np.hstack((color_image, depth_colormap))

        cv2.imshow('RealSense', images)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()