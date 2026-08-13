from RoArmM3 import Arm  # This imports the custom inverse kinematics code
import time
import cv2
import numpy as np
from ultralytics import YOLO

def main():
    # 1. Initialize the Arm (Base position at 0)
    # The angles array represents: [Base, Shoulder, Elbow, Wrist, Wrist Roll, Gripper]
    current_angles = [0, 0, 170, -90, 0, 0]
    arm = Arm(port="/dev/ttyUSB0", baudrate=115200)
    arm.joints_angle_ctrl(current_angles, 200, 100)

    # 2. Initialize YOLO11 Object Detector
    # 'yolo11n.pt' automatically downloads if you don't have it locally.
    model = YOLO('/home/uafs/Downloads/best.engine')
    BALL_CLASS_ID = 32  # COCO dataset class 32 is 'sports ball'

    # 3. Setup Camera
    width = 640
    height = 480
    camera = cv2.VideoCapture("/dev/video0")
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    cv2.namedWindow("camFeed", cv2.WINDOW_NORMAL)
    
    # Tracking parameters
    frame_center_x = width // 2
    kp = 0.05  # Proportional gain: adjustments how fast/aggressively the arm turns
    deadzone = 20  # Minimum pixel offset required before moving the arm

    print("Starting YOLO11 tracking. Press 'q' to quit.")

    while True:
        ret, frame = camera.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Run YOLO11 inference on the current frame
        results = model(frame, stream=True, verbose=False)
        
        ball_detected = False
        ball_x = frame_center_x

        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Check if the detected object is a sports ball
                if int(box.cls[0]) == BALL_CLASS_ID:
                    # Get bounding box coordinates [x1, y1, x2, y2]
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Calculate the center x-coordinate of the ball
                    ball_x = int((x1 + x2) / 2)
                    ball_detected = True
                    
                    # Draw a bounding box and center point on the frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(frame, (ball_x, int((y1 + y2) / 2)), 5, (0, 0, 255), -1)
                    break 
            if ball_detected:
                break

        # 4. Tracking Logic (Adjust Base Servo)
        if ball_detected:
            # Calculate pixel error from the center of the image
            error_x = ball_x - frame_center_x

            # Only move if the ball is outside our stable center deadzone
            if abs(error_x) > deadzone:
                # Calculate new base angle. 
                # Note: Flip '-' to '+' if the arm tracks in the opposite direction of the ball.
                angle_adjustment = error_x * kp
                new_base_angle = current_angles[0] - angle_adjustment
                
                # Constrain the base servo limits (between -180 and 180 degrees)
                new_base_angle = max(-180, min(180, new_base_angle))
                
                # Update the target angles and command the arm
                current_angles[0] = int(new_base_angle)
                arm.joints_angle_ctrl(current_angles, 250, 150)

        # Draw target center line for visual feedback
        cv2.line(frame, (frame_center_x, 0), (frame_center_x, height), (255, 0, 0), 1)
        
        # Render frame
        cv2.imshow("camFeed", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup hardware resources properly
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()