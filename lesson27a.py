# This program shows 2 frames with different masks on them
import cv2
print(cv2.__version__)
import numpy as np

def nothing(x):
    pass

# Create and position trackbars for HSV range adjustment
cv2.namedWindow('Trackbars')
cv2.moveWindow('Trackbars', 1320, 0)

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

# Camera setup: Uncomment one of the following sections
# Pi Camera
# camSet = 'nvarguscamerasrc !  video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method=' + str(flip) + ' ! video/x-raw, width=' + str(dispW) + ', height=' + str(dispH) + ', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
# cam = cv2.VideoCapture(camSet)

# Web Camera
cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    if not ret:
        break

    # Show the original frame
    cv2.imshow('nanoCam', frame)
    cv2.moveWindow('nanoCam', 0, 0)

    # Convert frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Get trackbar positions for HSV thresholds
    hueLow = cv2.getTrackbarPos('hueLower', 'Trackbars')
    hueUp = cv2.getTrackbarPos('hueUpper', 'Trackbars')
    hue2Low = cv2.getTrackbarPos('hue2Lower', 'Trackbars')
    hue2Up = cv2.getTrackbarPos('hue2Upper', 'Trackbars')
    satLow = cv2.getTrackbarPos('satLow', 'Trackbars')
    satHigh = cv2.getTrackbarPos('satHigh', 'Trackbars')
    valLow = cv2.getTrackbarPos('valLow', 'Trackbars')
    valHigh = cv2.getTrackbarPos('valHigh', 'Trackbars')

    # Create lower and upper bounds for the masks
    lower_bound1 = np.array([hueLow, satLow, valLow])
    upper_bound1 = np.array([hueUp, satHigh, valHigh])
    lower_bound2 = np.array([hue2Low, satLow, valLow])
    upper_bound2 = np.array([hue2Up, satHigh, valHigh])

    # Create masks based on the HSV bounds
    FGmask1 = cv2.inRange(hsv, lower_bound1, upper_bound1)
    FGmask2 = cv2.inRange(hsv, lower_bound2, upper_bound2)
    FGmaskComp = cv2.add(FGmask1, FGmask2)

    # Apply masks to the frame
    FG = cv2.bitwise_and(frame, frame, mask=FGmaskComp)

    # Create background mask and apply it
    bgMask = cv2.bitwise_not(FGmaskComp)
    BG = cv2.cvtColor(bgMask, cv2.COLOR_GRAY2BGR)

    # Combine foreground and background
    final = cv2.add(FG, BG)

    # Show the final output
    cv2.imshow('final', final)
    cv2.moveWindow('final', 1400, 530)

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
