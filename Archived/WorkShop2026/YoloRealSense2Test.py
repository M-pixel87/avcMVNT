import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO



# --- CONFIGURATION ---
# Replace this with your .engine path or just 'yolov8n.pt' for a test
MODEL_PATH = '/home/uafs/Downloads/YOLO-inferenceHR/runs/detect/brokeback_mountain/weights/best.engine'
CONFIDENCE_THRESHOLD = 0.5

def main():
    
    # 1. SETUP YOLO
    print(f"🔍 Loading YOLO model from: {MODEL_PATH}")
    try:
        model = YOLO(MODEL_PATH)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. SETUP REALSENSE CAMERA
    print("Starting RealSense D435i...")
    pipeline = rs.pipeline()
    config = rs.config()

    # Enable Color (RGB) and Depth streams
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    # Start the camera pipeline
    profile = pipeline.start(config)

    # Create an 'align' object. 
    # This aligns the depth image to the color image (crucial for matching pixels!)
    align_to = rs.stream.color
    align = rs.align(align_to)

    try:
        while True:
            # 3. GET FRAMES
            frames = pipeline.wait_for_frames()
            
            # Align the depth frame to color frame
            aligned_frames = align.process(frames)
            
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            # Convert images to numpy arrays for OpenCV/YOLO
            img_color = np.asanyarray(color_frame.get_data())

            # 4. RUN YOLO INFERENCE
            results = model(img_color, verbose=False)

            # 5. PROCESS & DRAW RESULTS
            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    if conf < CONFIDENCE_THRESHOLD:
                        continue
                    
                    # Get Box Coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_id = int(box.cls[0])
                    label = model.names[cls_id]

                    # Calculate Center Point
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)

                    # 6. GET DISTANCE 
                    dist = depth_frame.get_distance(center_x, center_y)

                    # Draw Box
                    cv2.rectangle(img_color, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw Label + Distance
                    # If distance is 0, the camera is too close or too far (invalid depth)
                    dist_text = f"{dist:.2f}m" if dist > 0 else "N/A"
                    text = f"{label}: {dist_text}"
                    
                    cv2.putText(img_color, text, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Draw center point
                    cv2.circle(img_color, (center_x, center_y), 5, (0, 0, 255), -1)

            # 7. DISPLAY
            cv2.imshow('RealSense + YOLO ', img_color)

            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Stop streaming
        pipeline.stop()
        cv2.destroyAllWindows()
        print("🧹 Resources released.")

if __name__ == "__main__":
    main()