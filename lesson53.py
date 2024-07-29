# This program detects objects using a pre-trained model and displays the name of the detected objects on the video feed.

import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np 

# Initialize variables for calculating frames per second (FPS)
timeStamp = time.time()
fpsFilt = 0

# Load the pre-trained object detection model 'ssd-mobilenet-v2' with a detection threshold of 0.5
net = jetson.inference.detectNet('ssd-mobilenet-v2', threshold=0.5)

# Set display width and height
dispW = 1280
dispH = 720
flip = 2
font = cv2.FONT_HERSHEY_SIMPLEX

# Gstreamer code for improved Raspberry Pi Camera Quality (commented out)
# camSet='nvarguscamerasrc wbmode=3 tnr-mode=2 tnr-strength=1 ee-mode=2 ee-strength=1 ! video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method='+str(flip)+' ! video/x-raw, width='+str(dispW)+', height='+str(dispH)+', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! videobalance contrast=1.5 brightness=-.2 saturation=1.2 ! appsink'

# Open a video capture stream from the camera at /dev/video1
cam = cv2.VideoCapture('/dev/video0')
cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

# Alternative camera setup using Jetson utilities (commented out)
# cam=jetson.utils.gstCamera(dispW, dispH, '/dev/video1')
# display=jetson.utils.glDisplay()

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
        
        # Draw a rectangle around the detected object and display its name
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 1)
        cv2.putText(img, item, (left, top + 20), font, 0.75, (0, 0, 255), 2)

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
