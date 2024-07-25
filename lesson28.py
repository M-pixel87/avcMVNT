# This program shows how to create an outline (silhouette) around the largest blue object in a video feed.
import cv2
print(cv2.__version__)
import numpy as np

def nothing(x):
    pass

# Create a window for trackbars and position it on the screen
cv2.namedWindow('Trackbars')
cv2.moveWindow('Trackbars', 1320, 0)

# Create trackbars for adjusting the HSV range
cv2.createTrackbar('hueLower', 'Trackbars', 82, 179, nothing)
cv2.createTrackbar('hueUpper', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('hue2Lower', 'Trackbars', 82, 179, nothing)
cv2.createTrackbar('hue2Upper', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('satLow', 'Trackbars', 146, 255, nothing)
cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('valLow', 'Trackbars', 64, 255, nothing)
cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, nothing)

# Display settings
dispW = 640
dispH = 480
flip = 2

# Uncomment these lines for Pi Camera
# camSet = 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method=' + str(flip) + ' ! video/x-raw, width=' + str(dispW) + ', height=' + str(dispH) + ', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
# cam = cv2.VideoCapture(camSet)

# For a webcam, uncomment the following line
# (If it does not work, try setting to '1' instead of '0')
cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to capture image")
        break

    # Convert the frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Get current positions of the trackbars for HSV range
    hueLow = cv2.getTrackbarPos('hueLower', 'Trackbars')
    hueUp = cv2.getTrackbarPos('hueUpper', 'Trackbars')
    hue2Low = cv2.getTrackbarPos('hue2Lower', 'Trackbars')
    hue2Up = cv2.getTrackbarPos('hue2Upper', 'Trackbars')
    Ls = cv2.getTrackbarPos('satLow', 'Trackbars')
    Us = cv2.getTrackbarPos('satHigh', 'Trackbars')
    Lv = cv2.getTrackbarPos('valLow', 'Trackbars')
    Uv = cv2.getTrackbarPos('valHigh', 'Trackbars')

    # Define lower and upper bounds for the HSV range
    l_b = np.array([hueLow, Ls, Lv])
    u_b = np.array([hueUp, Us, Uv])
    l_b2 = np.array([hue2Low, Ls, Lv])
    u_b2 = np.array([hue2Up, Us, Uv])

    # Create masks for the specified HSV range
    FGmask = cv2.inRange(hsv, l_b, u_b)
    FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
    FGmaskComp = cv2.add(FGmask, FGmask2)

    # Display the combined mask
    cv2.imshow('FGmaskComp', FGmaskComp)
    cv2.moveWindow('FGmaskComp', 0, 530)

    # Find contours in the mask
    contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    
    # Draw the largest contour (if any) on the frame
    if contours:
        cv2.drawContours(frame, contours, 0, (255, 0, 0), 3)

    # Display the frame with the contour
    cv2.imshow('nanoCam', frame)
    cv2.moveWindow('nanoCam', 0, 0)

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
