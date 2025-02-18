import jetson.inference
import jetson.utils
import cv2
import numpy as np
import time

# Initialize timestamp and FPS filter
timeStamp = time.time()
fpsFilt = 0

# Load the trained model
net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_aone/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_aone/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

# Initialize the camera
try:
    cam = jetson.utils.videoSource("/dev/video0")
except Exception as e:
    print(f"Error initializing camera: {e}")
    exit()

# HSV Tracking Parameters
def nothing(x):
    pass

# Create a window for the trackbars
cv2.namedWindow('Trackbars', cv2.WINDOW_NORMAL)

# Create trackbars for adjusting HSV values
cv2.createTrackbar('hueLower', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('hueUpper', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('hue2Lower', 'Trackbars', 89, 179, nothing)
cv2.createTrackbar('hue2Upper', 'Trackbars', 124, 179, nothing)
cv2.createTrackbar('satLow', 'Trackbars', 146, 255, nothing)
cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('valLow', 'Trackbars', 106, 255, nothing)
cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, nothing)

# Create windows for display
cv2.namedWindow('detCam', cv2.WINDOW_NORMAL)
cv2.namedWindow('FGmaskComp', cv2.WINDOW_NORMAL)

while True:
    try:
        img = cam.Capture()
        if img is None:
            print("Failed to capture image from camera")
            continue

        width = img.width
        height = img.height

        # Perform detection
        detections = net.Detect(img, width, height)

        # Convert CUDA image to numpy array
        frame = jetson.utils.cudaToNumpy(img)

        # Convert from RGBA to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        # Draw bounding boxes for detected objects
        if detections:
            for detect in detections:
                ID = detect.ClassID
                top = int(detect.Top)
                left = int(detect.Left)
                bottom = int(detect.Bottom)
                right = int(detect.Right)
                item = net.GetClassDesc(ID)

                # Draw rectangle around detected object
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 1)
                fontScale = width / 1280
                cv2.putText(frame, item, (left, top + 20), cv2.FONT_HERSHEY_SIMPLEX, fontScale, (0, 0, 255), 2)

        # HSV Tracking
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
                    x, y, w, h = int(x), int(y), int(w), int(h)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)

        # Calculate FPS
        dt = time.time() - timeStamp
        timeStamp = time.time()
        fps = 1 / dt
        fpsFilt = .9 * fpsFilt + .1 * fps

        # Display FPS
        fontScale = width / 1280
        cv2.putText(frame, str(round(fpsFilt, 1)) + ' fps', (0, 30), cv2.FONT_HERSHEY_SIMPLEX, fontScale, (0, 0, 255), 2)

        # Display the frame
        cv2.imshow('detCam', frame)

        if cv2.waitKey(1) == ord('q'):
            break

    except Exception as e:
        print(f"Error during processing: {e}")
        continue

# Release resources
cam.Close()
cv2.destroyAllWindows()
