import jetson.inference
import jetson.utils
import cv2
import numpy as np
import serial
import time
import math
import Jetson.GPIO as GPIO
from adafruit_servokit import ServoKit
import threading
from globals import shared
from genericFunctions import ESCWaitFunction, searching, turning, evasion
from Balignment import AiAlignment, CVAlignment, AiCamTarget, CVCamTarget, AiTurnStopErly,CVTurnStopErly



# Initialize hardware once
GPIO.setmode(GPIO.TEGRA_SOC)
GPIO.setup('GP49_SPI1_MOSI', GPIO.IN)
GPIO.setup('GP48_SPI1_MISO', GPIO.IN)

shared.myKit = ServoKit(channels=16)
shared.myKit.servo[3].angle = 110
shared.myKit.servo[2].angle = 90
shared.myKit.servo[1].angle = 90
shared.myKit.servo[0].angle = 90

# Initialize network and cameras
net = jetson.inference.detectNet(
    model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_hone/ssd-mobilenet.onnx",
    labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_hone/labels.txt",
    input_blob="input_0",
    output_cvg="scores",
    output_bbox="boxes",
    threshold=0.1
)

ser = serial.Serial('/dev/ttyTHS0', 9600)
camera = jetson.utils.videoSource("/dev/video2", argv=["--resolution=640x480", "--fps=30"]) 
camera2 = jetson.utils.videoSource("/dev/video0", argv=["--resolution=640x480", "--fps=30"])
display = jetson.utils.videoOutput()

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

def checkType(localItem):
    shared.evading = True
    if localItem == 'blue_bucket':
        print("Evading BlueBucket")
        shared.current_step += 1
        shared.evasionType = 1
        blueEvade()
    elif localItem == 'yellow_bucket':
        print("Evading YellowBucket")
        shared.current_step += 1
        shared.evasionType = 2
        yellowEvade()
    elif localItem == 'red_bucketArch':
        print("Evading RedBucket")
        shared.current_step += 1
        shared.evasionType = 3
        redEvade()
    else:
        print("I see something else")
        shared.evasionType = 0
        defaultEvade()

ESCWaitFunction()

# Main loop
while True:
    img = camera.Capture()
    frame = jetson.utils.cudaToNumpy(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    detections = net.Detect(img)
    display.Render(img)

    if detections:
        best_detections = {}
        for detect in detections:
            class_name = net.GetClassDesc(detect.ClassID)
            confidence = detect.Confidence
            if class_name not in best_detections or confidence > best_detections[class_name].Confidence:
                best_detections[class_name] = detect
        
        for class_name, best_detect in best_detections.items():
            ID = best_detect.ClassID
            top = int(best_detect.Top)
            left = int(best_detect.Left)
            bottom = int(best_detect.Bottom)
            right = int(best_detect.Right)
            confidence = best_detect.Confidence 
            w = right - left
            objx = left + (w / 2)
            errorPan = objx - img.width / 2
            
            print(f"Best {class_name} ({confidence:.1f}%), Center Error: {errorPan}, Width: {w}")

            if not shared.evading:
                AiAlignment(class_name, errorPan, shared.current_step)
            else:
                AiTurnStopErly(class_name, shared.current_step, errorPan)

    # Image processing
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

    if shared.current_step % 2 != 0:  # Fixed: added shared. prefix
        l_b = np.array([0, 146, 106])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([89, 146, 106])
        u_b2 = np.array([124, 255, 255])

    if shared.target_conditions['yellow_bucket'] == shared.current_step:  # Fixed: added shared. prefix
        l_b = np.array([0, 146, 106])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([10, 135, 221])
        u_b2 = np.array([68, 255, 255])

    FGmask = cv2.inRange(hsv, l_b, u_b)
    FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
    FGmaskComp = cv2.add(FGmask, FGmask2)
    contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not detections and contours and not shared.evading:  # Fixed: added shared. prefix
        for contour in contours:
            if cv2.contourArea(contour) > 100:  
                shared.bigContours = True  # Fixed: added shared. prefix
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
                objX = x + w / 2  
                errorPan = objX - (frame.shape[1] / 2)
                if abs(errorPan) > 40 and shared.pigsfly == 0 and not shared.evading:  # Fixed: added shared. prefix
                    CVAlignment(errorPan)
                elif shared.evading:  # Fixed: added shared. prefix
                    CVTurnStopErly()
                break  
            else:
                shared.bigContours = False  # Fixed: added shared. prefix
                shared.myKit.servo[1].angle = 90  # Fixed: added shared. prefix
    elif not detections and not contours and not shared.evading:  # Fixed: added shared. prefix
        shared.myKit.servo[1].angle = 90  # Fixed: added shared. prefix

    # Process the second camera
    img2 = camera2.Capture()
    width2 = img2.width
    height2 = img2.height
    frame2 = jetson.utils.cudaToNumpy(img2)
    frame2 = cv2.cvtColor(frame2, cv2.COLOR_RGBA2BGR)
    detections2 = net.Detect(img2)
    display.Render(img2)

    if detections2:
        best_detections2 = {}  
        for detect2 in detections2:
            class_name2 = net.GetClassDesc(detect2.ClassID)
            confidence2 = detect2.Confidence
            if class_name2 not in best_detections2 or confidence2 > best_detections2[class_name2].Confidence:
                best_detections2[class_name2] = detect2
        for class_name2, best_detect2 in best_detections2.items():
            ID2 = best_detect2.ClassID
            top2 = int(best_detect2.Top)
            left2 = int(best_detect2.Left)
            bottom2 = int(best_detect2.Bottom)
            right2 = int(best_detect2.Right)
            confidence2 = best_detect2.Confidence 
            w2 = right2 - left2
            h2 = bottom2 - top2  
            objx2 = left2 + (w2 / 2)
            objy2 = top2 + (h2 / 2)          
            errorPan2 = objx2 - img2.width / 2
            errorTilt2 = objy2 - img2.height / 2
            #print(f"Object: {class_name2}, Off center by: ({errorPan2}), Width of: {w2}")
            if not shared.evading:  # Fixed: added shared. prefix
                AiCamTarget(class_name2, shared.current_step, errorPan2, errorTilt2)  # Fixed: added shared. prefix
            

            if abs(errorPan) <100
                buttonstate_state = GPIO.input('GP49_SPI1_MOSI')
                if buttonstate_state == 1 and not evading and not looking:
                    evasion(class_name2)



            #if shared.turningleft:  # Fixed: added shared. prefix
                #turning(180, 126, 3, 30, 126, 11)
            #elif shared.turnright:  # Fixed: added shared. prefix
                #turning(33, 126, 4, 180, 126, 4)

    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)
    if shared.current_step % 2 != 0:  # Fixed: added shared. prefix
        l_b = np.array([0, 108, 162])
        u_b = np.array([0, 205, 251])
        l_b2 = np.array([10, 108, 162])
        u_b2 = np.array([26, 205, 251])
    if shared.target_conditions['yellow_bucket'] == shared.current_step:  # Fixed: added shared. prefix
        l_b = np.array([0, 198, 158])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([89, 198, 158])
        u_b2 = np.array([135, 255, 255])
    FGmask3 = cv2.inRange(hsv2, l_b, u_b)
    FGmask4 = cv2.inRange(hsv2, l_b2, u_b2)
    FGmaskComp2 = cv2.add(FGmask3, FGmask4)
    contours2, _ = cv2.findContours(FGmaskComp2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not detections2 and contours2 and not shared.evading:  # Fixed: added shared. prefix
        for contour in contours2:
            if cv2.contourArea(contour) > 100:
                shared.bigContours2 = True  # Fixed: added shared. prefix
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)
                cv2.rectangle(frame2, (x, y), (x + w, y + h), (255, 0, 0), 3)
                objX = x + w / 2
                objY = y + h / 2
                errorPan2 = objX - width2 / 2
                errorTilt2 = objY - height2 / 2
#added
                
                if abs(errorPan2) > 40 and shared.pigsfly == 0 and not shared.evading:  # Fixed: added shared. prefix
                    CVCamTarget(errorPan2, errorTilt2)
                elif shared.searching:  # Fixed: added shared. prefix
                    #print(f"we are searching this area is underconstruction")
                break

        #print(f"xaxiscam value is: {shared.xaxiscam}")  # Fixed: added shared. prefix
        #print(f"yaxiscam value is: {shared.yaxiscam}")  # Fixed: added shared. prefix
        #buttonstate_state = GPIO.input('GP49_SPI1_MOSI')
        #print(f"GPIO pin value: {buttonstate_state}  CurrentStep: {shared.current_step}")  # Fixed: added shared. prefix
        #if buttonstate_state == 1 and not shared.evading and not shared.looking:  # Fixed: added shared. prefix
            #print(shared.lastItem)  # Fixed: added shared. prefix
            #checkType(shared.lastItem)  # Fixed: added shared. prefix
    
    if not detections2 and not shared.evading and not detections and not shared.looking and not shared.bigContours:  # Fixed: added shared. prefix
        searching()

    print(" ")
    print(f"{shared.lastItem} : {len(detections)} : {len(detections2)} : {len(contours)} : {shared.evading} : {shared.looking} : {shared.evasionType} : {shared.current_step}")
    print(" ")

    frame_resized = cv2.resize(frame, (320, 240))
    frame2_resized = cv2.resize(frame2, (320, 240))
    FGmaskComp_resized = cv2.resize(FGmaskComp, (320, 240))
    FGmaskComp2_resized = cv2.resize(FGmaskComp2, (320, 240))
    cv2.imshow('FGmaskComp', FGmaskComp_resized)
    cv2.imshow('FGmaskComp2', FGmaskComp2_resized)        
    cv2.imshow('detCam', frame_resized)
    cv2.imshow('detCam2', frame2_resized)

    if cv2.waitKey(1) == ord('q'):
        break
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))

camera.Close()
camera2.Close()
cv2.destroyAllWindows()
ser.close()