import cv2
import numpy as np
import jetson_utils
import jetson_inference

# Initialize the display window for Jetson inference
display = jetson_utils.videoOutput("display://0")
net = jetson_inference.detectNet("ssd-mobilenet-v2", threshold=0.5)  # Change to your model and parameters

# OpenCV capture setup
dispW = 640
dispH = 480
flip = 2
camSet = 'nvarguscamerasrc !  video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method=' + str(flip) + ' ! video/x-raw, width=' + str(dispW) + ', height=' + str(dispH) + ', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
cam = cv2.VideoCapture(camSet)

# Trackbars setup
cv2.namedWindow('Trackbars')
cv2.createTrackbar('hueLower', 'Trackbars', 82, 179, lambda x: None)
cv2.createTrackbar('hueUpper', 'Trackbars', 179, 179, lambda x: None)
cv2.createTrackbar('hue2Lower', 'Trackbars', 82, 179, lambda x: None)
cv2.createTrackbar('hue2Upper', 'Trackbars', 179, 179, lambda x: None)
cv2.createTrackbar('satLow', 'Trackbars', 146, 255, lambda x: None)
cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, lambda x: None)
cv2.createTrackbar('valLow', 'Trackbars', 64, 255, lambda x: None)
cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, lambda x: None)

while True:
    ret, frame = cam.read()
    if not ret:
        break
    
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

    FG = cv2.bitwise_and(frame, frame, mask=FGmaskComp)
    bgMask = cv2.bitwise_not(FGmaskComp)
    BG = cv2.cvtColor(bgMask, cv2.COLOR_GRAY2BGR)
    final = cv2.add(FG, BG)

    # Convert the final OpenCV image to a format compatible with jetson_utils
    img_cuda = jetson_utils.cudaFromNumpy(final)

    # Perform object detection using Jetson inference
    detections = net.Detect(img_cuda)

    # Render the image
    display.Render(img_cuda)

    # Update the status with the network FPS
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()

