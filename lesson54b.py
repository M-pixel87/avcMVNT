# This code is meant to be a first run at executing the AI object detection model that we trained, running in the terminal.

import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np 

# Initialize variables for calculating frames per second (FPS)
timeStamp = time.time()
fpsFilt = 0

# Load your trained model with the correct paths
net = jetson.inference.detectNet(
    model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/ssd-mobilenet.onnx",
    labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt",
    input_blob="input_0",
    output_cvg="scores",
    output_bbox="boxes",
    threshold=0.5
)

# Set display width and height
dispW = 1280
dispH = 720
flip = 2
font = cv2.FONT_HERSHEY_SIMPLEX

# Open a video capture stream from the camera at /dev/video0
cam = cv2.VideoCapture('/dev/video0')
cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

while True:
    # Capture a frame from the camera
    _, img = cam.read()
    height = img.shape[0]
    width = img.shape[1]

    # Convert the frame to RGBA format and then to CUDA format for processing
    frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA).astype(np.float32)
    frame = jetson.utils.cudaFromNumpy(frame)

    # Perform object detection on the frame
    detections = net.Detect(frame, width, height)
    for detect in detections:
        ID = detect.ClassID
        top = int(detect.Top)
        left = int(detect.Left)
        bottom = int(detect.Bottom)
        right = int(detect.Right)
        item = net.GetClassDesc(ID)
        
        # Draw a rectangle around the detected object and display its name at the top
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 1)
        cv2.putText(img, item, (left, top + 20), font, 0.75, (0, 0, 255), 2)

        # Example: handle object position
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        
        # Add your logic here based on object position
        # Example: Print the position
        print(f"Object: {item}, Center position: ({center_x}, {center_y})")

    # Calculate and display the frames per second (FPS)
    dt = time.time() - timeStamp
    timeStamp = time.time()
    fps = 1 / dt
    fpsFilt = 0.9 * fpsFilt + 0.1 * fps
    cv2.putText(img, str(round(fpsFilt, 1)) + ' fps', (0, 30), font, 1, (0, 0, 255), 2)

    # Display the processed frame
    cv2.imshow('detCam', img)
    cv2.moveWindow('detCam', 0, 0)

    # Exit the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break

# Release the camera and close all OpenCV windows
cam.release()
cv2.destroyAllWindows()
