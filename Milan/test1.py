#this program is the genric program ive been using to show the trained model and give out the error
import jetson.utils
import time
import cv2
import numpy as np
import serial
import Jetson.GPIO as GPIO
import math


timeStamp = time.time()
fpsFilt = 0

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
ser = serial.Serial('/dev/ttyTHS0', 9600)  # Adjust the serial port and baud rate as needed

cam = cv2.VideoCapture(0)  # Use 0 for default camera
cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

while True:
    ret, img = cam.read()
    if not ret:
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
        errorPan = objx - width / 2 
        # Add your logic here based on object position
        # Example: Print the position
        zwii = 2
        eins = 1
        print(f"Object: {item}, Off center by: ({errorPan})")
        if item == 'blue_bucket' and abs(errorPan) > 50:
            rounded_errorPan = math.ceil(errorPan / 22)
            ser.write(f"{rounded_errorPan}\n".encode())
            #if errorPan>0:
            #    ser.write(f"{zwii}\n".encode())
            #elif errorPan<0:
            #    ser.write(f"{eins}\n".encode())
    dt = time.time() - timeStamp
    timeStamp = time.time()
    fps = 1 / dt
    fpsFilt = .9 * fpsFilt + .1 * fps
    cv2.putText(img, str(round(fpsFilt, 1)) + ' fps', (0, 30), font, 1, (0, 0, 255), 2)
    cv2.imshow('detCam', img)
    cv2.moveWindow('detCam', 0, 0)
    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()