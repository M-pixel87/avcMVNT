#this code is my most mighty fine code ive made and its import to remember the orienation of the cameras 
#the eleco rect looking one belongs on the top usb fnt port and other one on the bottom 

import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np
import serial
import math
import Jetson.GPIO as GPIO  # Import the GPIO library for controlling the GPIO pins on the Jetson
from adafruit_servokit import ServoKit # this a recent servo lib that i brought

#GPIO.setmode(GPIO.BOARD)  this was shown to be called already with high probability of adafruit calling it
GPIO.setup('SPI2_MISO', GPIO.IN)  # Set up the pin as an input pin which is pin 21 for now //newestupdate i found the data sheet and i think 'SPI2_MISO' is the right spelling of SPI1_MISO

myKit=ServoKit(channels=16)
myKit.servo[0].angle=110
myKit.servo[1].angle=0
xaxiscam = 110

# Constants
timeStamp = time.time()
fpsFilt = 0

# Initialize the object detection model (for Camera 0)
net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_fone/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_fone/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

# Initialize serial communication and cameras
ser = serial.Serial('/dev/ttyTHS0', 9600)

# Initialize video sources for both cameras
camera = jetson.utils.videoSource("/dev/video0", argv=["--resolution=1280x720", "--fps=30"])  # Camera 0 (Object Detection)
camera2 = jetson.utils.videoSource("/dev/video2", argv=["--resolution=1280x720", "--fps=30"])  # Camera 1 (Color Detection only)

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

steeringServoVal=0
pastSteeringServoVal =0
onbutton=0

# Define action codes
AvoidObstacle = 250
Stop = 350
Dconstant = .5
Pconstant = 1

# Initialize pan value
pan = 0  # Initialize pan variable

while onbutton==0:
    buttonstate_state = GPIO.input('SPI2_MISO')
    if buttonstate_state == GPIO.HIGH:
        print("Input pin is HIGH")
        onbutton = 1
    else:
        print("Input pin is LOW")
        myKit.servo[1].angle = 90
    time.sleep(1)  # Wait for 1 second before checking the pin again


while True and onbutton==1:
    # Process the first camera (Camera 0: Object Detection + Color Detection)
    img = camera.Capture()
    width = img.width
    # Convert to numpy array for OpenCV processing
    frame = jetson.utils.cudaToNumpy(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

    # Perform object detection on Camera 0
    detections = net.Detect(img)
    
    # Render the image to the display
    display.Render(img)
    
    # Check if any objects were detected on Camera 0
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
            print(f"Object: {item}, Off center by: ({errorPan}), Width of: {w}")
            if item == 'blue_bucket' and abs(errorPan) > 50 :
                errorPan = math.ceil(errorPan / 15)
                steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                myKit.servo[0].angle = steeringServoVal
                pastSteeringServoVal= steeringServoVal
            buttonstate_state = GPIO.input('SPI2_MISO')
            if buttonstate_state == GPIO.LOW:
                #i need to start that evaiding action now servo 0 is streeing and 1 is esc
                myKit.servo[0].angle = 123#make it so that im turning left
                myKit.servo[1].angle = 115#set the speed to
                time.sleep(3)  # Wait for 3 second 
                myKit.servo[0].angle = 55#make it so that im turning right
                time.sleep(9)  # Wait for 9 seconds
                

    # Color Detection for Camera 0 (on top of Object Detection)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hueLow = cv2.getTrackbarPos('hueLower', 'Trackbars')
    hueUp = cv2.getTrackbarPos('hueUpper', 'Trackbars')
    hue2Low = cv2.getTrackbarPos('hue2Lower', 'Trackbars')
    hue2Up = cv2.getTrackbarPos('hue2Upper', 'Trackbars')
    Ls = cv2.getTrackbarPos('satLow', 'Trackbars')
    Us = cv2.getTrackbarPos('satHigh', 'Trackbars')
    Lv = cv2.getTrackbarPos('valLow', 'Trackbars')
    Uv = cv2.getTrackbarPos('valHigh', 'Trackbars')

    # Define lower and upper bounds for color mask
    l_b = np.array([hueLow, Ls, Lv])
    u_b = np.array([hueUp, Us, Uv])
    l_b2 = np.array([hue2Low, Ls, Lv])
    u_b2 = np.array([hue2Up, Us, Uv])
    
    # Create color masks
    FGmask = cv2.inRange(hsv, l_b, u_b)
    FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
    FGmaskComp = cv2.add(FGmask, FGmask2)

    cv2.imshow('FGmaskComp', FGmaskComp)

    contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Process color contours
    if not detections and contours:
        for contour in contours:
            if cv2.contourArea(contour) > 700:  # Filter out small contours
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure integer values for rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)  # Draw rectangle around object
                objX = x + w / 2  # Calculate object's center X-coordinate
                errorPan = objX - width / 2  # Calculate error in pan
                print(f'Width of object: {w}')  # Print error value for debugging
                if abs(errorPan) > 40:  # If the error is significant
                    errorPan = math.ceil(errorPan / 15)
                    steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
                    myKit.servo[0].angle = steeringServoVal
                    pastSteeringServoVal= steeringServoVal
                buttonstate_state = GPIO.input('SPI2_MISO')
                if buttonstate_state == GPIO.LOW:
                    #i need to start that evaiding action now servo 0 is streeing and 1 is esc
                    myKit.servo[0].angle = 123#make it so that im turning left
                    myKit.servo[1].angle = 115#set the speed to
                    time.sleep(3)  # Wait for 3 second 
                    myKit.servo[0].angle = 55#make it so that im turning right
                    time.sleep(9)  # Wait for 9 seconds
                break  # Process only the first large contour

    # Process the second camera (Camera 1: Only Color Detection)
    img2 = camera2.Capture()

    # Convert to numpy array for OpenCV processing
    frame2 = jetson.utils.cudaToNumpy(img2)
    frame2 = cv2.cvtColor(frame2, cv2.COLOR_RGBA2BGR)

    # Color Detection for Camera 1
    hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)
    l_b2 = np.array([90, 157, 140]) #logis hue lower satlower value lower
    u_b2 = np.array([179, 255, 215]) #logis  hue higher sat higher value higher
    FGmask2 = cv2.inRange(hsv2, l_b2, u_b2)
    FGmaskComp2 = FGmask2  # Avoid redundant addition to FGmaskComp

    cv2.imshow('FGmaskComp2', FGmaskComp2)

    contours2, _ = cv2.findContours(FGmaskComp2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Process color contours on Camera 1
    if contours2:
        for contour in contours2:
            if cv2.contourArea(contour) > 700:  # Filter out small contours
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure integer values for rectangle
                cv2.rectangle(frame2, (x, y), (x + w, y + h), (255, 0, 0), 3)  # Draw rectangle around object
                objX = x + w / 2  # Calculate object's center X-coordinate
                errorPan = objX - width / 2  # Calculate error in pan
                print(f'Width of object: {w}')  # Print error value for debugging
                if abs(errorPan) > 40:  # If the error is significant
                    if errorPan > 0 and xaxiscam < 180:
                        xaxiscam += 1
                    elif errorPan < 0 and xaxiscam > 0:
                        xaxiscam -= 1 
                    myKit.servo[3].angle = xaxiscam
                    print(f"xaxiscam value is: {xaxiscam}")  # Print the x axis angle
                break  # Process only the first large contour
    




        

    # Display the frames
    cv2.imshow('detCam', frame)
    cv2.imshow('detCam2', frame2)

    # Exit if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break

    # Display the FPS on the status bar
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))

# Clean up
camera.Close()
camera2.Close()
cv2.destroyAllWindows()
ser.close()  # Close the serial port