# This program demonstrates the trained model and outputs the error value.
import jetson.utils
import jetson.inference
import time
import cv2
import numpy as np
import serial
import Jetson.GPIO as GPIO
import math

# Initialize timestamp and FPS filter
timeStamp = time.time()
fpsFilt = 0

# Load the trained model with the correct paths
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
font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize the serial communication (adjust the port and baud rate as needed)
ser = serial.Serial('/dev/ttyTHS0', 9600)

# Initialize the camera
cam = cv2.VideoCapture(0)  # Use 0 for default camera
cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

while True:
    ret, img = cam.read()
    if not ret:
        break

    height = img.shape[0]
    width = img.shape[1]

    # Convert image to RGBA and then to CUDA format
    frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA).astype(np.float32)
    frame = jetson.utils.cudaFromNumpy(frame)

    # Perform detection
    detections = net.Detect(frame, width, height)
    for detect in detections:
        ID = detect.ClassID
        top = int(detect.Top)
        left = int(detect.Left)
        bottom = int(detect.Bottom)
        right = int(detect.Right)
        item = net.GetClassDesc(ID)
        w = right - left
        objx = left + (w / 2)

        # Draw rectangle and label
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 1)
        cv2.putText(img, item, (left, top + 20), font, .75, (0, 0, 255), 2)

        # Calculate error in pan
        errorPan = objx - width / 2

        # Define enum values for actions
        Alignmentmv = 1
        AvoidObstacle = 2
        Stop = 3
        Forward = 4

        # Initialize counter for avoided obstacles
        obsticalsAvoided = 0

        # Handle object position and send to serial
        print(f"Object: {item}, Off center by: ({errorPan}), Width of: {w}")

        # Alignment action
        if item == 'blue_bucket' and abs(errorPan) > 50 and w < 324:
            ser.write(f"{Alignmentmv}\n".encode())
            rounded_errorPan = math.ceil(errorPan / 15)
            ser.write(f"{rounded_errorPan}\n".encode())

        # Avoid obstacle action
        if item == 'blue_bucket' and abs(errorPan) < 50 and w < 324 and w > 315:
            ser.write(f"{AvoidObstacle}\n".encode())
            obsticalsAvoided += 1

        # Stop action
        if obsticalsAvoided == 1:
            ser.write(f"{Stop}\n".encode())
        else:
            ser.write(f"{Forward}\n".encode())

    # Calculate FPS
    dt = time.time() - timeStamp
    timeStamp = time.time()
    fps = 1 / dt
    fpsFilt = .9 * fpsFilt + .1 * fps

    # Display FPS
    cv2.putText(img, str(round(fpsFilt, 1)) + ' fps', (0, 30), font, 1, (0, 0, 255), 2)
    cv2.imshow('detCam', img)
    cv2.moveWindow('detCam', 0, 0)
    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()


