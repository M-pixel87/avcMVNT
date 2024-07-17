import time
import cv2
import numpy as np
import serial  # Ensure this is installed and properly configured
import Jetson.GPIO as GPIO
import jetson.inference
import jetson.utils

# Load your trained model with the correct paths
net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

dispW = 1280
dispH = 720
flip = 2
font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize the serial communication (adjust the port and baud rate as needed)
try:
    ser = serial.Serial('/dev/ttyTHS0', 9600) # Adjust the serial port and baud rate as needed
except serial.SerialException as e:
    print(f"Error initializing serial communication: {e}")
    exit(1)

# Initialize the camera
cam = cv2.VideoCapture(0)  # Use 0 for default camera
cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

if not cam.isOpened():
    print("Error: Could not open camera.")
    exit(1)

timeStamp = time.time()
fpsFilt = 0

try:
    while True:
        ret, img = cam.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        height = img.shape[0]
        width = img.shape[1]

        frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA).astype(np.float32)
        frame = jetson.utils.cudaFromNumpy(frame)

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

            # Example: handle object position
            errorPan = objx - dispW / 2
            # Example: Print the position
            print(f"Object: {item}, Off center by: ({errorPan})")
            if item == 'blue_bucket' and abs(errorPan) > 90:
                turn = errorPan
                ser.write(f"{errorPan}\n".encode())

        dt = time.time() - timeStamp
        timeStamp = time.time()
        fps = 1 / dt
        fpsFilt = .9 * fpsFilt + .1 * fps
        cv2.putText(img, str(round(fpsFilt, 1)) + ' fps', (0, 30), font, 1, (0, 0, 255), 2)
        cv2.imshow('detCam', img)
        cv2.moveWindow('detCam', 0, 0)
        if cv2.waitKey(1) == ord('q'):
            break
finally:
    cam.release()
    cv2.destroyAllWindows()
    ser.close()
    GPIO.cleanup()
