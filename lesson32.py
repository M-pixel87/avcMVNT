# This program aligns a camera with a blue object of a specific shade
# by sending control commands through a UART pin.

import cv2
import numpy as np
import serial  # Import the serial library for UART communication

# Initialize serial communication with the UART port
ser = serial.Serial('/dev/ttyTHS0', 9600)

def nothing(x):
    pass  # Placeholder function for trackbar callbacks

# Create a window for trackbars and position it
cv2.namedWindow('Trackbars')
cv2.moveWindow('Trackbars', 1320, 0)

# Create trackbars to adjust the HSV range for blue object detection
cv2.createTrackbar('hueLower', 'Trackbars', 82, 179, nothing)
cv2.createTrackbar('hueUpper', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('hue2Lower', 'Trackbars', 82, 179, nothing)
cv2.createTrackbar('hue2Upper', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('satLow', 'Trackbars', 146, 255, nothing)
cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('valLow', 'Trackbars', 64, 255, nothing)
cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, nothing)

dispW = 640  # Display width
dispH = 480  # Display height
flip = 2  # Flip method for the camera (if using Pi Camera)

# Uncomment the lines below if using a Raspberry Pi Camera
# camSet = 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method=' + str(flip) + ' ! video/x-raw, width=' + str(dispW) + ', height=' + str(dispH) + ', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
# cam = cv2.VideoCapture(camSet)

# If using a USB webcam, uncomment the next line
# If it does not work, try changing '0' to '1'
cam = cv2.VideoCapture(0)
width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
print('width:', width, 'height:', height)  # Print camera resolution

# Initialize the pan variable
pan = 0

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to capture image")
        break  # Exit loop if image capture fails

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # Convert frame to HSV color space

    # Retrieve trackbar positions for HSV range
    hueLow = cv2.getTrackbarPos('hueLower', 'Trackbars')
    hueUp = cv2.getTrackbarPos('hueUpper', 'Trackbars')
    hue2Low = cv2.getTrackbarPos('hue2Lower', 'Trackbars')
    hue2Up = cv2.getTrackbarPos('hue2Upper', 'Trackbars')
    Ls = cv2.getTrackbarPos('satLow', 'Trackbars')
    Us = cv2.getTrackbarPos('satHigh', 'Trackbars')
    Lv = cv2.getTrackbarPos('valLow', 'Trackbars')
    Uv = cv2.getTrackbarPos('valHigh', 'Trackbars')

    # Define lower and upper bounds for blue color
    l_b = np.array([hueLow, Ls, Lv])
    u_b = np.array([hueUp, Us, Uv])
    l_b2 = np.array([hue2Low, Ls, Lv])
    u_b2 = np.array([hue2Up, Us, Uv])

    # Create masks for detecting blue objects within the specified HSV range
    FGmask = cv2.inRange(hsv, l_b, u_b)
    FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
    FGmaskComp = cv2.add(FGmask, FGmask2)

    cv2.imshow('FGmaskComp', FGmaskComp)  # Display the combined mask
    cv2.moveWindow('FGmaskComp', 0, 530)  # Position the mask window

    contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # If contours are found, process them
    if contours:
        for contour in contours:
            if cv2.contourArea(contour) > 1000:  # Filter out small contours
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure integer values for rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)  # Draw rectangle around object
                objX = x + w / 2  # Calculate object's center X-coordinate
                errorPan = objX - width / 2  # Calculate error in pan
                print(f'ErrorPan: {errorPan}')  # Print error value for debugging
                if abs(errorPan) > 40:  # If the error is significant
                    pan = pan - errorPan / 100  # Adjust pan value
                    ser.write(f"{pan}\n".encode())  # Send pan value via UART
                    print(f"Sent: {pan}")  # Print the sent pan value
                break  # Process only the first large contour

    cv2.imshow('nanoCam', frame)  # Display the frame with detected object
    cv2.moveWindow('nanoCam', 0, 0)  # Position the video feed window

    if cv2.waitKey(1) == ord('q'):  # Exit loop if 'q' is pressed
        break

# Release the camera and close all OpenCV windows
cam.release()
cv2.destroyAllWindows()
ser.close()  # Close the serial port
