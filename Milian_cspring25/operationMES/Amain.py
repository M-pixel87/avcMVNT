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
from Balignment import AiAlignment, CVAlignment, AiCamTarget, CVCamTarget, AiTurnStopErly,CVTurnStopErly, AiHUDcamAlign, AisearchStopTrigger



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



ESCWaitFunction()

# Main loop
while True:




#____________________________________________________________________________________________________________________________________
#first Camera this cam only handels aligning the car with the bucket
    img = camera.Capture()
    frame = jetson.utils.cudaToNumpy(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    detections = net.Detect(img)
    display.Render(img)



#this is the filter
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
            if not shared.evading and not shared.looking:
                shared.AiHUDkey = False  # Fixed assignment
                AiAlignment(class_name, errorPan, shared.current_step)
            elif shared.evading and not shared.AiHUDkey:
                AiTurnStopErly(class_name, shared.current_step, errorPan)

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

    if shared.current_step % 2 != 0:  
        l_b = np.array([0, 146, 106])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([89, 146, 106])
        u_b2 = np.array([124, 255, 255])

    if shared.target_conditions['yellow_bucket'] == shared.current_step:
        l_b = np.array([0, 146, 106])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([10, 135, 221])
        u_b2 = np.array([68, 255, 255])

    if shared.target_conditions['ramp'] == shared.current_step:
        l_b = np.array([0, 146, 106])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([10, 135, 221])
        u_b2 = np.array([68, 255, 255]) 

    if shared.target_conditions['red_bucketArch'] == shared.current_step:  # Fixed key
        l_b = np.array([0, 146, 106])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([10, 135, 221])
        u_b2 = np.array([68, 255, 255])   

    FGmask = cv2.inRange(hsv, l_b, u_b)
    FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
    FGmaskComp = cv2.add(FGmask, FGmask2)
    contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not detections and contours and not shared.evading:
        for contour in contours:
            if cv2.contourArea(contour) > 100:  
                shared.bigContours = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
                objX = x + w / 2  
                errorPan = objX - (img.width / 2)
                if abs(errorPan) > 40 and shared.pigsfly == 0 and not shared.evading: 
                    shared.AiHUDkey = False  # Fixed assignment
                    CVAlignment(errorPan)
                elif shared.evading:  
                    CVTurnStopErly(errorPan)
                break  
            else:
                shared.bigContours = False  
                shared.myKit.servo[1].angle = 90  
    elif not detections and not contours and not shared.evading:  
        shared.myKit.servo[1].angle = 90  
        searching()

    # Second Camera
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
            if not shared.evading and shared.target_conditions['red_bucketArch'] != shared.current_step and not shared.AiHUDkey:
                AiCamTarget(class_name2, shared.current_step, errorPan2, errorTilt2)
            if abs(errorPan2) < 100 and not shared.AiHUDkey:  # Fixed variable name
                buttonstate_state = GPIO.input('GP49_SPI1_MOSI') # HANDLES The lidar detection
                if buttonstate_state == 1 and not shared.evading and not shared.looking and shared.target_conditions['red_bucket_arch'] != shared.current_step:
                    evasion(class_name2)
            if shared.looking==True or shared.AiHUDkey==True:  # Fixed syntax
                AisearchStopTrigger(class_name2, shared.current_step)  # Fixed variable name
                if shared.looking == False:
                    AiHUDcamAlign(shared.angle, class_name2, shared.current_step, errorPan2, errorTilt2)

    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)
    if shared.current_step % 2 != 0:  
        l_b = np.array([0, 108, 162])
        u_b = np.array([0, 205, 251])
        l_b2 = np.array([10, 108, 162])
        u_b2 = np.array([26, 205, 251])
    elif shared.target_conditions['yellow_bucket'] == shared.current_step:
        l_b = np.array([0, 198, 158])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([89, 198, 158])
        u_b2 = np.array([135, 255, 255])
    elif shared.target_conditions['ramp'] == shared.current_step:
        l_b = np.array([0, 198, 158])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([89, 198, 158])
        u_b2 = np.array([135, 255, 255])
    elif shared.target_conditions['red_bucketArch'] == shared.current_step:  # Fixed key
        l_b = np.array([0, 198, 158])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([89, 198, 158])
        u_b2 = np.array([135, 255, 255])

    FGmask3 = cv2.inRange(hsv2, l_b, u_b)
    FGmask4 = cv2.inRange(hsv2, l_b2, u_b2)
    FGmaskComp2 = cv2.add(FGmask3, FGmask4)
    contours2, _ = cv2.findContours(FGmaskComp2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not detections2 and contours2 and not shared.evading:  
        for contour in contours2:
            if cv2.contourArea(contour) > 100:
                shared.bigContours2 = True  
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)
                cv2.rectangle(frame2, (x, y), (x + w, y + h), (255, 0, 0), 3)
                objX = x + w / 2
                objY = y + h / 2
                errorPan2 = objX - width2 / 2
                errorTilt2 = objY - height2 / 2                
                if abs(errorPan2) > 40 and shared.pigsfly == 0 and not shared.evading and not shared.AiHUDkey:
                    CVCamTarget(errorPan2, errorTilt2)
                if w > 100 and shared.evading and not shared.looking and shared.target_conditions['red_bucketArch'] == shared.current_step and not shared.AiHUDkey:
                    evasion(class_name2) 
            else:
                shared.bigContours2 = False  
                shared.myKit.servo[1].angle = 90  
            break  # Fixed indentation

    # Status display
    try:
        current_target = [key for key, val in shared.target_conditions.items() if val == shared.current_step][0]
    except IndexError:
        current_target = "Unknown"
    print(f"""
    [STATUS] 
    Target: {current_target.replace('_', ' ').title()} 
    Step: {shared.current_step}
    Evading: {'YES' if shared.evading else 'NO'}
    Searching: {'YES' if shared.looking else 'NO'}
    Detections: {len(detections)} (Cam1), {len(detections2)} (Cam2)
    Contours: {len(contours)}
    Evasion Type: {shared.evasionType}
    Last Item: {shared.lastItem}
--------------------------------------""")

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