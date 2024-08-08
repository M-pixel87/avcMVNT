# Faster but might be more volatile to work with. It has a different color. is equivalent to test 5 from normal milan py
import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np
import serial
import math

# Initialize timestamp and FPS filter
timeStamp = time.time()
fpsFilt = 0

# Load the trained model with the correct paths
net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

# Initialize the serial communication (adjust the port and baud rate as needed)
ser = serial.Serial('/dev/ttyTHS0', 9600)

# Initialize the camera
cam = jetson.utils.videoSource("v4l2:///dev/video0")

# HSV Tracking Parameters
def nothing(x):
    pass

# Create a window for the trackbars, with the option to move and resize it
cv2.namedWindow('Trackbars', cv2.WINDOW_NORMAL)

# Create trackbars for adjusting HSV values
cv2.createTrackbar('hueLower', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('hueUpper', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('hue2Lower', 'Trackbars', 89, 179, nothing)
cv2.createTrackbar('hue2Upper', 'Trackbars', 124, 179, nothing)
cv2.createTrackbar('satLow', 'Trackbars', 146, 255, nothing)
cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('valLow', 'Trackbars', 106, 255, nothing)
cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, nothing)

# Create windows for display, with the option to move and resize them
cv2.namedWindow('detCam', cv2.WINDOW_NORMAL)
cv2.namedWindow('FGmaskComp', cv2.WINDOW_NORMAL)

while True:
    img = cam.Capture()
    width = img.width
    height = img.height

    # Convert image to RGBA and then to CUDA format
    frame = jetson.utils.cudaToNumpy(img)

    # Perform detection
    detections = net.Detect(img, width, height)

    # Check if any detections are made
    if detections:
        for detect in detections:
            # Using AI object detection 
            ID = detect.ClassID
            top = int(detect.Top)
            left = int(detect.Left)
            bottom = int(detect.Bottom)
            right = int(detect.Right)
            item = net.GetClassDesc(ID)
            w = right - left
            objx = left + (w / 2)

            # Draw rectangle and label
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 1)
            fontScale = width / 1280  # Adjust font scale based on the width of the window
            cv2.putText(frame, item, (left, top + 20), cv2.FONT_HERSHEY_SIMPLEX, fontScale, (0, 0, 255), 2)

            # Calculate error in pan
            errorPan = objx - width / 2

            # Define enum values for actions
            AvoidObstacle = 250
            Stop = 350

            # Initialize counter for avoided obstacles
            obsticalsAvoided = 0

            # Handle object position and send to serial
            print(f"Object: {item}, Off center by: ({errorPan}), Width of: {w}")

            # Alignment action
            if item == 'blue_bucket' and abs(errorPan) > 50 and w < 324:
                rounded_errorPan = math.ceil(errorPan / 15)
                SVal = rounded_errorPan + 150
                ser.write(f"{SVal}\n".encode())

            # Avoid obstacle action
            if item == 'blue_bucket' and abs(errorPan) < 50 and w <= 324 and w > 315:
                ser.write(f"{AvoidObstacle}\n".encode())
                obsticalsAvoided += 1

            # Stop action
            if obsticalsAvoided == 1:
                ser.write(f"{Stop}\n".encode())

    else:
        # HSV Tracking for Advance
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

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

        contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw contours and bounding box if contours are found
        if contours:
            for contour in contours:
                if cv2.contourArea(contour) > 700:  # Filter small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure these are integers
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
                    objX = x + w / 2
                    errorPan = objX - width / 2
                    print(f'ErrorPan: {errorPan}')  # Debugging statement
                    if abs(errorPan) > 50:
                        rounded_errorPan = math.ceil(errorPan / 15)
                        SVal = rounded_errorPan + 450
                        ser.write(f"{SVal}\n".encode())
                    break

    # Calculate FPS
    dt = time.time() - timeStamp
    timeStamp = time.time()
    fps = 1 / dt
    fpsFilt = .9 * fpsFilt + .1 * fps

    # Display FPS
    fontScale = width / 1280  # Adjust font scale based on the width of the window
    cv2.putText(frame, str(round(fpsFilt, 1)) + ' fps', (0, 30), cv2.FONT_HERSHEY_SIMPLEX, fontScale, (0, 0, 255), 2)

    # Display the frame and set an out switch to leave the program; you have to click on the frame being shown and press 'q' on the keyboard
    cv2.imshow('detCam', frame)
    if cv2.waitKey(1) == ord('q'):
        break

cam.Close()  # Close the camera
cv2.destroyAllWindows()
ser.close()  # Close the serial port
