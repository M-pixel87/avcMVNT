#this code is my most mighty fine code ive made and its important to remember the orienation of the cameras 
#the eleco rectangular looking one belongs on the top usb fnt port and other one on the bottom 
# Import the GPIO library for controlling the GPIO pins on the Jetson
# this a recent servo lib that i brought
import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np
import serial
import math
import Jetson.GPIO as GPIO  
from adafruit_servokit import ServoKit 

import threading



GPIO.setup('GP49_SPI1_MOSI', GPIO.IN) #flag: its phyisical pin 19 11th from the top left
GPIO.setup('GP48_SPI1_MISO', GPIO.IN) #saftey: and is pin 21 (10th from the top left)


#servo3 is for xaxis cam
#servo2 is for yaxis cam
#servo1 is for speed controll
#servo0 is for direction control
myKit=ServoKit(channels=16)
myKit.servo[3].angle=110 #center x wise
myKit.servo[2].angle=90 #center y wise
myKit.servo[1].angle=90 #hold the no mvmnt pwm
myKit.servo[0].angle=90 #hold the center wheels


# Constants
# the proportional steering value
# the dirivative past steering value
# xaxiscam belongs to the cam two x axis
# yaxiscam#this code is my most mighty fine code ive made and its important to remember the orienation of the cameras 
#the eleco rectangular looking one belongs on the top usb fnt port and other one on the bottom 
# Import the GPIO library for controlling the GPIO pins on the Jetson
# this a recent servo lib that i brought
import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np
import serial
import math
import Jetson.GPIO as GPIO  
from adafruit_servokit import ServoKit 

import threading



GPIO.setup('GP49_SPI1_MOSI', GPIO.IN) #flag: its phyisical pin 19 11th from the top left
GPIO.setup('GP48_SPI1_MISO', GPIO.IN) #saftey: and is pin 21 (10th from the top left)


#servo3 is for xaxis cam
#servo2 is for yaxis cam
#servo1 is for speed controll
#servo0 is for direction control
myKit=ServoKit(channels=16)
myKit.servo[3].angle=110 #center x wise
myKit.servo[2].angle=90 #center y wise
myKit.servo[1].angle=90 #hold the no mvmnt pwm
myKit.servo[0].angle=90 #hold the center wheels


# Constants
# the proportional steering value
# the dirivative past steering value
# xaxiscam belongs to the cam two x axis
# yaxiscam belongs to the cam two y axis
# make my flag unread so im in the look untill i read a 1
steeringServoVal=0
pastSteeringServoVal =0
xaxiscam = 110
yaxiscam =90
onbutton=0

pigsfly=0

# Logic variables for evasion && Search
lastItem = ''
evasionType = 0
evading = False
looking = False
bigContours = False
search_thread = None  # Global variable to store the thread reference

#remember to fix these as fit P constant is proportion and D is the derivative a fairly new part to my code
Dconstant = .1
Pconstant = 1


fpsFilt = 0
timeStamp = time.time()


# Initialize the object detection model (for Camera 0)
net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_mone/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_mone/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.1)

# Initialize serial communication and cameras
ser = serial.Serial('/dev/ttyTHS0', 9600)

# Initialize video sources for both cameras
camera = jetson.utils.videoSource("/dev/video2", argv=["--resolution=640x480", "--fps=30"]) 
camera2 = jetson.utils.videoSource("/dev/video0", argv=["--resolution=640x480", "--fps=30"])

# Create trackbars for color-based detection (for both cameras)
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

# Initialize windows for display
cv2.namedWindow('detCam', cv2.WINDOW_NORMAL)
cv2.namedWindow('FGmaskComp', cv2.WINDOW_NORMAL)

# Initialize display object
display = jetson.utils.videoOutput()



# This section is supposed to send a 1 constantly, and the Uno reads once.  
# If reset properly(python runs first then rest), then everything is fine.  
# GP48 is the output switch and is the tenth pin from the top left corner  
# of the GPIO pins on the Orin, feeding the Uno pin 3.  
# GP49 is the flag checker on the Orin that checks whether I'm close to obsticale.  
# It's the 11th pin from the top left (counting from left to right).  
# I say this because the pins are counted from right to left on the datasheet.  
# This feeds pin 2 on the Uno board.  


while onbutton==0:
    buttonstate_state = GPIO.input('GP48_SPI1_MISO')
    if buttonstate_state == GPIO.HIGH:
        print("Input pin is HIGH! MVMNT start")
        onbutton = 1
        myKit.servo[1].angle=126 #start the movement

    else:
        print("Input pin is LOW dont move yet")
        myKit.servo[1].angle = 90
        time.sleep(5)

#i want to start defining a bunch of more functions/ conditions
target_conditions = {
    'blue_bucket_firstime': 1,
    'yellow_bucket': 2,
    'blue_bucket_secondtime': 3,
    'ramp': 4,
    'blue_bucket_thirdtime': 5,
    'red_bucket_arch': 6,
    'blue_bucket_lasttime': 7,
}
current_step = 1 

def searching():
    global looking, search_thread

    # Check if a search thread is already running
    if search_thread and search_thread.is_alive():
        print("Search thread already running. Skipping new search.")
        return  

    def look_Around():
        global looking, search_thread
        looking = True
        angle = 0
        anglechng = 10
        myKit.servo[3].angle = 0  # Reset camera X position
        myKit.servo[2].angle = 90  # Reset camera Y position
        print(":STARTING SEARCH:")

        while looking:
            if not looking:  # Immediately exit if looking is set to False
                print(":SEARCH STOPPED EARLY:")
                break

            print(f"Looking around at angle: {angle}")
            myKit.servo[3].angle = angle
            time.sleep(1)
            angle += anglechng

            if angle == 190 or angle == -10:
                anglechng *= -1


        #iwill need these two set to turn of the thread
        #looking = False
        #search_thread = None 
    
    search_thread = threading.Thread(target=look_Around)
    search_thread.start()
    

# Evasion functions, hard coded turns for now...(or forever)
def turning(angle, speed, duration):
    def turn_and_stop():
        global evading
        myKit.servo[0].angle = angle
        myKit.servo[1].angle = speed
        time.sleep(duration)
        myKit.servo[0].angle = 90
        myKit.servo[1].angle = 90
        evading = False
        print('')
        print('DONE EVADING')
        print('')
    threading.Thread(target=turn_and_stop).start()

def turning2(angle, speed, duration, angle2, speed2, duration2):
    def turn_and_stop():
        global evading
        myKit.servo[0].angle = angle
        myKit.servo[1].angle = speed
        time.sleep(duration)
        myKit.servo[0].angle = angle2
        myKit.servo[1].angle = speed2
        # In between the time of the second turn it will make evading false, meaning object detection can start
        time.sleep(duration2/2)
        time.sleep(duration2/2)
        myKit.servo[0].angle = 90
        myKit.servo[1].angle = 90
        evading = False
        print('')
        print('DONE EVADING')
        print('')
    threading.Thread(target=turn_and_stop).start()
    

def blueEvade():
    turning2(180, 126, 3, 30, 126, 11)

def yellowEvade():
    turning2(33, 126, 4, 180, 126, 4)

def redEvade():
    myKit.servo[1].angle = 90#this is in the meantime to test the code

def defaultEvade():
    pigsfly = 1
    #makes the vehicle stop
    myKit.servo[1].angle = 90#this is in the meantime to test the code
    print("**DEFAULT EVASION**")
#-------------------------------------------------------------------------

def checkType(localItem):
    global evading, evasionType, current_step
    evading = True
    if(localItem == 'blue_bucket'):
        print("Evading BlueBucket")
        current_step += 1
        evasionType = 1
        blueEvade()
    elif(localItem == 'yellow_bucket'):
        print("Evading YellowBucket")
        current_step += 1
        evasionType = 2
        yellowEvade()
    elif(localItem == 'red_bucketArch'):
        print("Evading RedBucket")
        current_step += 1
        evasionType = 3
        redEvade()
    else:
        print("I see something else")
        evasionType = 0
        defaultEvade()


while True:
    # Process the first camera and adjust the wheels
    img = camera.Capture()
    width = img.width
    height = img.height
    frame = jetson.utils.cudaToNumpy(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    detections = net.Detect(img)
    display.Render(img)


#constuction 
#objective make a array to keep the best objects and throw out the rest
#first filter the obj found 




    if detections:
        best_detections = {}
    for detect in detections:
        class_name = net.GetClassDesc(detect.ClassID)
        confidence = detect.Confidence
        if class_name not in best_detections or confidence > best_detections[class_name].Confidence:
            best_detections[class_name] = detect
        
        for class_name, best_detect in best_detections.items():  # fixed
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

            if class_name == 'blue_bucket' and abs(errorPan) > 50 and pigsfly == 0 and not evading and  current_step%2 != 0:
                errorPan = math.ceil(errorPan / 14)
                steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                myKit.servo[0].angle = steeringServoVal
                myKit.servo[1].angle = 126
                pastSteeringServoVal= steeringServoVal
                looking = False
                search_thread = None
            
            if class_name == 'yellow_bucket' and abs(errorPan) > 50  and not evading and  target_conditions['yellow_bucket'] == current_step:
                errorPan = math.ceil(errorPan / 14)
                steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                myKit.servo[0].angle = steeringServoVal
                myKit.servo[1].angle = 126
                pastSteeringServoVal= steeringServoVal
                looking = False
                search_thread = None

            if class_name == 'red_buckerArch' and abs(errorPan) > 50  and not evading and  target_conditions['red_buckerArch'] == current_step:
                errorPan = math.ceil(errorPan / 14)
                steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                myKit.servo[0].angle = steeringServoVal
                myKit.servo[1].angle = 126
                pastSteeringServoVal= steeringServoVal
                looking = False
                search_thread = None

            if class_name == 'ramp' and abs(errorPan) > 50  and not evading and  target_conditions['ramp'] == current_step:
                errorPan = math.ceil(errorPan / 14)
                steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                myKit.servo[0].angle = steeringServoVal
                myKit.servo[1].angle = 126
                pastSteeringServoVal= steeringServoVal
                looking = False
                search_thread = None
            
            
    else:
        lastItem = 'NONE'
        
                

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    #DEFAULT : THIS SETS TARGET COLOR FROM TRACKBARS MANUALLY
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

    if current_step%2 != 0:  # checks if current step is odd , which is when blue bucket evasion is needed
        l_b = np.array([0, 146, 106])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([89, 146, 106])
        u_b2 = np.array([124, 255, 255])

    if target_conditions['yellow_bucket'] == current_step:
        l_b = np.array([0, 146, 106])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([10, 135, 221])
        u_b2 = np.array([68, 255, 255])

    FGmask = cv2.inRange(hsv, l_b, u_b)
    FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
    FGmaskComp = cv2.add(FGmask, FGmask2)
    contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    # Process color contours of the first camera if it never caught anything with AI
    if not detections and contours and not evading:
        for contour in contours:
            if cv2.contourArea(contour) > 100:  # Filter out small contours
                bigContours = True
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure integer values for rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)  # Draw rectangle around object
                objX = x + w / 2  # Calculate object's center X-coordinate
                errorPan = objX - width / 2  # Calculate error in pan
                print(f'Width of object: {w}')  # Print error value for debugging
                if abs(errorPan) > 40 and pigsfly == 0 : 
                    errorPan = math.ceil(errorPan / 14)
                    steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                    myKit.servo[0].angle = steeringServoVal
                    myKit.servo[1].angle = 126
                    pastSteeringServoVal= steeringServoVal
                    looking = False
                break  
            #This code runs if there is color detection but its not large
            else:
                bigContours = False
                myKit.servo[1].angle = 90
    # This runs if there is absolutely no detection
    elif(not detections and not contours and not evading):
        #NO DETECTION : SITS STILL
        myKit.servo[1].angle = 90


    

    # Process the second camera using object dection and this camera by the way moves
    img2 = camera2.Capture()
    width2 = img2.width
    height2 = img2.height 
    frame2 = jetson.utils.cudaToNumpy(img2)
    frame2 = cv2.cvtColor(frame2, cv2.COLOR_RGBA2BGR)
    detections2 = net.Detect(img2)
    display.Render(img2)

##






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
            print(f"height2: {height2}, Off center by: ({height2}), Width of: {w2}")
            if class_name2 == 'blue_bucket' and not evading and current_step%2 != 0:
                looking = False
                if(abs(errorPan2) > 50):
                    if errorPan2 > 0 and xaxiscam < 180:
                        xaxiscam += 1
                    elif errorPan2 < 0 and xaxiscam > 0:
                        xaxiscam -= 1 
                    myKit.servo[3].angle = xaxiscam

                if(abs(errorTilt2)>50):
                    if errorTilt2 > 0 and yaxiscam < 180:
                        yaxiscam += 1
                    elif errorTilt2 <0 and yaxiscam >0: 
                        yaxiscam -= 1 
                    myKit.servo[2].angle = yaxiscam
                
            if class_name2 == 'yellow_bucket' and not evading and target_conditions['yellow_bucket'] == current_step:
                looking = False
                if(abs(errorPan2) > 50):
                    if errorPan2 > 0 and xaxiscam < 180:
                        xaxiscam += 1
                    elif errorPan2 < 0 and xaxiscam > 0:
                        xaxiscam -= 1 
                    myKit.servo[3].angle = xaxiscam

                    if errorTilt2 > 0 and yaxiscam < 180:
                        yaxiscam += 1
                    elif errorTilt2 <0 and yaxiscam >0: 
                        yaxiscam -= 1 
                    myKit.servo[2].angle = yaxiscam




##this section is new MM march 26


    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)
    if current_step%2 != 0:
        l_b = np.array([0, 108, 162])
        u_b = np.array([0, 205, 251])
        l_b2 = np.array([10, 108, 162])
        u_b2 = np.array([26, 205, 251])

    if target_conditions['yellow_bucket'] == current_step:
        l_b = np.array([0, 198, 158])
        u_b = np.array([0, 255, 255])
        l_b2 = np.array([89, 198, 158])
        u_b2 = np.array([135, 255, 255])

    FGmask3 = cv2.inRange(hsv2, l_b, u_b)
    FGmask4 = cv2.inRange(hsv2, l_b2, u_b2)
    FGmaskComp2 = cv2.add(FGmask3, FGmask4)
    contours2, _ = cv2.findContours(FGmaskComp2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not detections2 and contours2:
        for contour in contours2:
            if cv2.contourArea(contour) > 100:
                bigContours2 = True
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

##this area ends construction

            

            print(f"xaxiscam value is: {xaxiscam}")  # Print the x-axis camera angle
            print(f"yaxiscam value is: {yaxiscam}")  # Print the y-axis camera angle


            buttonstate_state = GPIO.input('GP49_SPI1_MOSI')
            print(f"GPIO pin value: {buttonstate_state}  CurrentStep: {current_step}")             
            if buttonstate_state == 1 and not evading and not looking:
                #This checks what bucket was last detected , and runs evasion code
                #The check type is here so it doesnt waste resources checking the same thing, it only checks once close what this does is checks my value
                #from the pin and does an action depending on it 
                print(lastItem)
                checkType(lastItem) 

        #Should be correct detection logic ...
    if(not detections2 and not evading  and not detections and not looking and not bigContours):
        searching()


#disableled since it dosent seem nesci
#    if(not detections2 and not evading  and detections2 and not looking and not bigContours2):
#        myKit.servo[3].angle = 90
#        myKit.servo[2].angle = 90
#        time.sleep(0.5)
        
    print(" ")
    print(f"{lastItem} : {len(detections)} : {len(detections2)} : {len(contours)} : {evading} : {looking} : {evasionType} : {current_step}")
    print(" ")

    # Display the frames 
    #mask
    #mask2
    #normal1
    #normal2
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