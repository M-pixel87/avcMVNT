# This program, built on July 30, 2024, switches between AI detection and color-based tracking (HSV).
# Future improvements could include adding commands for handling various obstacles.

# Import necessary libraries for image processing, AI detection, time handling, and serial communication
import jetson.utils
import jetson.inference
import time
import cv2
import numpy as np
import serial
import math

# Initialize timestamp and FPS filter for calculating and displaying frames per second
timeStamp = time.time()
fpsFilt = 0

# Load the trained AI model and specify the paths to the model and labels
net = jetson.inference.detectNet(
    model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/ssd-mobilenet.onnx",
    labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt",
    input_blob="input_0",
    output_cvg="scores",
    output_bbox="boxes",
    threshold=0.5
)

# Set display width and height for the camera feed
dispW = 1280
dispH = 720
font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize serial communication with the appropriate port and baud rate
ser = serial.Serial('/dev/ttyTHS0', 9600)

# Initialize the camera with the specified resolution
cam = cv2.VideoCapture(0)  # Use 0 for the default camera
cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

# Function used as a placeholder for trackbar callback
def nothing(x):
    pass

# Create and position a window for HSV trackbars to control color detection parameters
cv2.namedWindow('Trackbars')
cv2.moveWindow('Trackbars', 1320, 0)

# Create trackbars for adjusting the HSV ranges for color detection
cv2.createTrackbar('hueLower', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('hueUpper', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('hue2Lower', 'Trackbars', 89, 179, nothing)
cv2.createTrackbar('hue2Upper', 'Trackbars', 124, 179, nothing)
cv2.createTrackbar('satLow', 'Trackbars', 146, 255, nothing)
cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('valLow', 'Trackbars', 106, 255, nothing)
cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, nothing)

# Main loop to continuously capture and process frames
while True:
    # Capture a frame from the camera
    ret, img = cam.read()
    if not ret:
        break

    height = img.shape[0]
    width = img.shape[1]

    # Convert the captured frame to RGBA format and then to CUDA format
    frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA).astype(np.float32)
    frame = jetson.utils.cudaFromNumpy(frame)

    # Perform AI detection on the frame
    detections = net.Detect(frame, width, height)

    # Check if any detections are made
    if detections:
        for detect in detections:
            ID = detect.ClassID
            top = int(detect.Top)
            left = int(detect.Left)
            bottom = int(detect.Bottom)
            right = int(detect.Right)
            item = net.GetClassDesc(ID)
            w = right - left
            objx = left + (w / 2)

            # Draw a rectangle around the detected object and label it
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 1)
            cv2.putText(img, item, (left, top + 20), font, .75, (0, 0, 255), 2)

            # Calculate the error in pan (horizontal offset from the center)
            errorPan = objx - width / 2

            # Define enum values for different actions
            AvoidObstacle = 250
            Stop = 350

            # Initialize a counter for obstacles avoided
            obsticalsAvoided = 0

            # Log the detected object's details
            print(f"Object: {item}, Off center by: ({errorPan}), Width of: {w}")

            # Align the camera to the object if it is a 'blue_bucket' and out of center
            if item == 'blue_bucket' and abs(errorPan) > 50 and w < 324:
                rounded_errorPan = math.ceil(errorPan / 15)
                SVal = rounded_errorPan + 150
                ser.write(f"{SVal}\n".encode())

            # Send command to avoid obstacle if the object is centered and within a specific width range
            if item == 'blue_bucket' and abs(errorPan) < 50 and w <= 324 and w > 315:
                ser.write(f"{AvoidObstacle}\n".encode())
                obsticalsAvoided += 1

            # Send command to stop if an obstacle has been avoided
            if obsticalsAvoided == 1:
                ser.write(f"{Stop}\n".encode())
    else:
        # HSV color detection if no AI detection is made
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        hueLow = cv2.getTrackbarPos('hueLower', 'Trackbars')
        hueUp = cv2.getTrackbarPos('hueUpper', 'Trackbars')
        hue2Low = cv2.getTrackbarPos('hue2Lower', 'Trackbars')
        hue2Up = cv2.getTrackbarPos('hue2Upper', 'Trackbars')
        Ls = cv2.getTrackbarPos('satLow', 'Trackbars')
        Us = cv2.getTrackbarPos('satHigh', 'Trackbars')
        Lv = cv2.getTrackbarPos('valLow', 'Trackbars')
        Uv = cv2.getTrackbarPos('valHigh', 'Trackbars')

        l_b = np.array([hueLow, Ls, Lv])
        u_b = np.array([hueUp, Us, Uv])
        l_b2 = np.array([hue2Low, Ls, Lv])
        u_b2 = np.array([hue2Up, Us, Uv])

        FGmask = cv2.inRange(hsv, l_b, u_b)
        FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
        FGmaskComp = cv2.add(FGmask, FGmask2)

        cv2.imshow('FGmaskComp', FGmaskComp)
        cv2.moveWindow('FGmaskComp', 0, 530)

        contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw contours and bounding box if contours are found
        if contours:
            for contour in contours:
                if cv2.contourArea(contour) > 700:  # Filter out small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure these are integers
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3)
                    objX = x + w / 2
                    errorPan = objX - width / 2
                    print(f'ErrorPan: {errorPan}')  # Debugging statement
                    if abs(errorPan) > 50:
                        rounded_errorPan = math.ceil(errorPan / 15)
                        SVal = rounded_errorPan + 450
                        ser.write(f"{SVal}\n".encode())
                    break

    # Calculate the frames per second (FPS)
    dt = time.time() - timeStamp
    timeStamp = time.time()
    fps = 1 / dt
    fpsFilt = .9 * fpsFilt + .1 * fps

    # Display the FPS on the frame
    cv2.putText(img, str(round(fpsFilt, 1)) + ' fps', (0, 30), font, 1, (0, 0, 255), 2)

    # Show the frame and set a key to exit the loop ('q' key)
    cv2.imshow('detCam', img)
    cv2.moveWindow('detCam', 0, 0)
    if cv2.waitKey(1) == ord('q'):
        break

# Release the camera and close all windows
cam.release()
cv2.destroyAllWindows()
ser.close()  # Close the serial port

