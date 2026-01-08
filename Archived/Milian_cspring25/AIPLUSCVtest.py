import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np
import serial
import math
import Jetson.GPIO as GPIO
from adafruit_servokit import ServoKit

GPIO.setup('GP49_SPI1_MOSI', GPIO.IN) #flag: its phyisical pin 19 11th from the top left
GPIO.setup('GP48_SPI1_MISO', GPIO.IN) #saftey: and is pin 21 (10th from the top left)

myKit = ServoKit(channels=16)
myKit.servo[3].angle = 110
myKit.servo[2].angle = 90
myKit.servo[1].angle = 90
myKit.servo[0].angle = 90

steeringServoVal = 0
pastSteeringServoVal = 0
xaxiscam = 110
yaxiscam = 90
onbutton = 0
pigsfly = 0

Dconstant = .1
Pconstant = 1

net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_fone/ssd-mobilenet.onnx",
                               labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_fone/labels.txt",
                               input_blob="input_0",
                               output_cvg="scores",
                               output_bbox="boxes",
                               threshold=0.5)

ser = serial.Serial('/dev/ttyTHS0', 9600)
camera = jetson.utils.videoSource("/dev/video2", argv=["--resolution=640x480", "--fps=30"])
camera2 = jetson.utils.videoSource("/dev/video0", argv=["--resolution=640x480", "--fps=30"])

def nothing(x):
    pass

cv2.namedWindow('Trackbars', cv2.WINDOW_NORMAL)
cv2.createTrackbar('hueLower', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('hueUpper', 'Trackbars', 0, 179, nothing)
cv2.createTrackbar('hue2Lower', 'Trackbars', 89, 179, nothing)
cv2.createTrackbar('hue2Upper', 'Trackbars', 124, 179, nothing)
cv2.createTrackbar('satLow', 'Trackbars', 146, 255, nothing)
cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('valLow', 'Trackbars', 106, 255, nothing)
cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, nothing)

cv2.namedWindow('detCam', cv2.WINDOW_NORMAL)
cv2.namedWindow('FGmaskComp', cv2.WINDOW_NORMAL)
display = jetson.utils.videoOutput()

while onbutton == 0 and pigsfly == 1:
    buttonstate_state = GPIO.input('GP48_SPI1_MISO')
    if buttonstate == GPIO.HIGH:
        onbutton = 1
        myKit.servo[1].angle = 115
    else:
        myKit.servo[1].angle = 90
        time.sleep(5)

while True:
    img = camera.Capture()
    width = img.width
    frame = jetson.utils.cudaToNumpy(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    detections = net.Detect(img)
    display.Render(img)
    
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
            errorPan = objx - img.width / 2
            if item == 'blue_bucket' and abs(errorPan) > 50 and pigsfly == 1:
                errorPan = math.ceil(errorPan / 15)
                steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                myKit.servo[0].angle = steeringServoVal
                pastSteeringServoVal = steeringServoVal
                print(f"CAM1AI steeringServoVal: {steeringServoVal}")


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
    contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not detections and contours:
        for contour in contours:
            if cv2.contourArea(contour) > 700:
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
                objX = x + w / 2
                errorPan = objX - width / 2
                if abs(errorPan) > 40 and pigsfly == 1:
                    errorPan = math.ceil(errorPan / 15)
                    steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                    myKit.servo[0].angle = steeringServoVal
                    pastSteeringServoVal = steeringServoVal
                    print(f"CAM1color steeringServoVal: {steeringServoVal}")

                break

    img2 = camera2.Capture()
    width2 = img2.width
    height2 = img2.height
    frame2 = jetson.utils.cudaToNumpy(img2)
    frame2 = cv2.cvtColor(frame2, cv2.COLOR_RGBA2BGR)
    detections2 = net.Detect(img2)
    display.Render(img2)
    
    if detections2:
        for detect2 in detections2:
            ID2 = detect2.ClassID
            top2 = int(detect2.Top)
            left2 = int(detect2.Left)
            bottom2 = int(detect2.Bottom)
            right2 = int(detect2.Right)
            item2 = net.GetClassDesc(ID2)
            w2 = right2 - left2
            h2 = bottom2 - top2
            objx2 = left2 + (w2 / 2)
            objy2 = top2 + (h2 / 2)
            errorPan2 = objx2 - img2.width / 2
            errorTilt2 = objy2 - img2.height / 2
            
            if item2 == 'blue_bucket' and abs(errorPan2) > 50:
                if errorPan2 > 0 and xaxiscam < 180:
                    xaxiscam += 1
                elif errorPan2 < 0 and xaxiscam > 0:
                    xaxiscam -= 1
                myKit.servo[3].angle = xaxiscam

            if item2 == 'blue_bucket' and abs(errorTilt2) > 50:
                if errorTilt2 > 0 and yaxiscam < 180:
                    yaxiscam += 1
                elif errorTilt2 < 0 and yaxiscam > 0:
                    yaxiscam -= 1
                myKit.servo[2].angle = yaxiscam

            print(f"CAM2AI CAMVALPAN: {xaxiscam}  CAM2AI CAMVALTILT: {yaxiscam}")



    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)
    FGmask3 = cv2.inRange(hsv2, l_b, u_b)
    FGmask4 = cv2.inRange(hsv2, l_b2, u_b2)
    FGmaskComp2 = cv2.add(FGmask3, FGmask4)
    contours2, _ = cv2.findContours(FGmaskComp2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not detections2 and contours2:
        for contour in contours2:
            if cv2.contourArea(contour) > 100:
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)
                cv2.rectangle(frame2, (x, y), (x + w, y + h), (255, 0, 0), 3)
                objX = x + w / 2
                objY = y + h / 2
                errorPan2 = objX - width2 / 2
                errorTilt2 = objY - height2 / 2
                if abs(errorPan2) > 40 and pigsfly == 0:
                    if errorPan2 > 0 and xaxiscam < 180:
                        xaxiscam += 1
                    elif errorPan2 < 0 and xaxiscam > 0:
                        xaxiscam -= 1
                    myKit.servo[3].angle = xaxiscam

                    if errorTilt2 > 0 and yaxiscam < 180:
                        yaxiscam += 1
                    elif errorTilt2 < 0 and yaxiscam > 0:
                        yaxiscam -= 1
                    myKit.servo[2].angle = yaxiscam
                    print(f"CAM2CLR CAMVALPAN: {xaxiscam}  CAM2CLR CAMVALTILT: {yaxiscam}")


                break

    cv2.imshow('FGmaskComp', FGmaskComp)
    cv2.imshow('FGmaskComp2', FGmaskComp2)
    cv2.imshow('detCam', frame)
    cv2.imshow('detCam2', frame2)

    if cv2.waitKey(1) == ord('q'):
        break

    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))

camera.Close()
camera2.Close()
cv2.destroyAllWindows()
ser.close()