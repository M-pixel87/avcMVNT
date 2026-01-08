#the reading of this pythong file is as goes
#In the import section im bringing in revalenent libs for our project jetson.(i and u) are libs that have cuda tools for capturing imgs and 
#using ai in our file and time gives me pre set function that count time could be from counting from a crystal osilatora and the amount of periods passed
#Ill skip the rest as itll be understood in the file 
#delclare my vars incldued in this file i have a fps text box so ive add a fps text to see how much the ai is slowing down my system
#

import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np
import serial
import Jetson.GPIO as GPIO


net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)



timeStamp = time.time()
fpsFilt = 0
dispW = 1280
dispH = 720
flip = 2
font = cv2.FONT_HERSHEY_SIMPLEX
zwii = 2
eins = 1
ser = serial.Serial('/dev/ttyTHS0', 9600)  
cam = cv2.VideoCapture(0)  
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
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 1)
        cv2.putText(img, item, (left, top + 20), font, .75, (0, 0, 255), 2)
        errorPan = objx - width / 2 
        print(f"Object: {item}, Off center by: ({errorPan})")
        if item == 'blue_bucket' and abs(errorPan) > 50:
            if errorPan>0:
                ser.write(f"{zwii}\n".encode())
            elif errorPan<0:
                ser.write(f"{eins}\n".encode())
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
