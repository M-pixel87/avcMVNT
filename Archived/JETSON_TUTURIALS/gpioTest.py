#this code turns on a light whenever the bucket is a set distance close
import numpy as np 
import cv2 
import Jetson.GPIO as GPIO  # Replace with appropriate GPIO library

# Set up GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.OUT)
GPIO.output(8, GPIO.LOW)  # Initially set GPIO pin 8 to low

# Function to measure width of blue object
def measure_blue_object_width(blue_mask):
    contours, _ = cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    max_width = 0
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > max_width:
            max_width = w
    return max_width

# Capturing video through webcam 
webcam = cv2.VideoCapture(0) 

while True:
    # Reading the video from the webcam
    _, imageFrame = webcam.read() 

    # Convert the imageFrame to HSV color space
    hsvFrame = cv2.cvtColor(imageFrame, cv2.COLOR_BGR2HSV) 

    # Set range for red color and define mask
    red_lower = np.array([0, 150, 100], np.uint8) 
    red_upper = np.array([10, 255, 255], np.uint8) 
    red_mask = cv2.inRange(hsvFrame, red_lower, red_upper) 

    # Set range for green color and define mask
    green_lower = np.array([25, 52, 72], np.uint8)
    green_upper = np.array([102, 255, 255], np.uint8)
    green_mask = cv2.inRange(hsvFrame, green_lower, green_upper)

    # Set range for yellow color and define mask
    yellow_lower = np.array([20, 100, 100], np.uint8) 
    yellow_upper = np.array([40, 255, 255], np.uint8) 
    yellow_mask = cv2.inRange(hsvFrame, yellow_lower, yellow_upper) 

    # Set range for blue color and define mask 
    blue_lower = np.array([110, 100, 100], np.uint8) 
    blue_upper = np.array([130, 255, 255], np.uint8) 
    blue_mask = cv2.inRange(hsvFrame, blue_lower, blue_upper) 

    # Morphological Transform, Dilation for each color and bitwise_and operator
    kernel = np.ones((5, 5), "uint8")

    # For red color
    red_mask = cv2.dilate(red_mask, kernel) 
    res_red = cv2.bitwise_and(imageFrame, imageFrame, mask=red_mask) 

    # For yellow color
    yellow_mask = cv2.dilate(yellow_mask, kernel) 
    res_yellow = cv2.bitwise_and(imageFrame, imageFrame, mask=yellow_mask) 

    # For blue color
    blue_mask = cv2.dilate(blue_mask, kernel) 
    res_blue = cv2.bitwise_and(imageFrame, imageFrame, mask=blue_mask) 

    # For green color
    green_mask = cv2.dilate(green_mask, kernel) 
    res_green = cv2.bitwise_and(imageFrame, imageFrame, mask=green_mask) 

    # Measure width of blue object and control GPIO pin 8
    blue_object_width = measure_blue_object_width(blue_mask)
    if blue_object_width >= 700:
        GPIO.output(8, GPIO.HIGH)  # Turn on GPIO pin 8
        print("Blue object is 700px wide. GPIO pin 8 turned on.")
    else:
        GPIO.output(8, GPIO.LOW)  # Ensure GPIO pin 8 is off

    # Display the frame with color detections
    cv2.imshow("Multiple Color Detection in Real-Time", imageFrame) 
    if cv2.waitKey(10) & 0xFF == ord('q'): 
        webcam.release() 
        cv2.destroyAllWindows() 
        GPIO.cleanup()  # Clean up GPIO on program termination
        break
