# This program is designed to align a camera with a blue object.
# The primary use of this program is to adjust the parameters for detecting the correct shade of blue (or any other color) 
# by modifying the HSV (Hue, Saturation, Value) range.
# Additionally, it allows you to determine the optimal width of the object, 
# which is useful when using the static "avoid" function to track or avoid obstacles.


import cv2
import numpy as np
import serial  

ser = serial.Serial('/dev/ttyTHS0', 9600)

def nothing(x):
    pass  

cv2.namedWindow('Trackbars')
cv2.moveWindow('Trackbars', 1320, 0)
cv2.createTrackbar('hueLower', 'Trackbars', 82, 179, nothing)
cv2.createTrackbar('hueUpper', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('hue2Lower', 'Trackbars', 82, 179, nothing)
cv2.createTrackbar('hue2Upper', 'Trackbars', 179, 179, nothing)
cv2.createTrackbar('satLow', 'Trackbars', 146, 255, nothing)
cv2.createTrackbar('satHigh', 'Trackbars', 255, 255, nothing)
cv2.createTrackbar('valLow', 'Trackbars', 64, 255, nothing)
cv2.createTrackbar('valHigh', 'Trackbars', 255, 255, nothing)

dispW = 640  
dispH = 480  
flip = 2  


cam = cv2.VideoCapture(0)
width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
print('width:', width, 'height:', height)  

pan = 0

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to capture image")
        break  

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

    cv2.imshow('FGmaskComp', FGmaskComp)  # Display the combined mask
    cv2.moveWindow('FGmaskComp', 0, 530)  # Position the mask window

    contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # If contours are found, process them
    if contours:
        for contour in contours:
            if cv2.contourArea(contour) > 1000:  # Filter out small contours
                x, y, w, h = cv2.boundingRect(contour)
                x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure integer values for rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)  # Draw rectangle around object
                objX = x + w / 2  # Calculate object's center X-coordinate
                errorPan = objX - width / 2  # Calculate error in pan
                print(f'Width of object: {w}')  # Print error value for debugging
                #print(f'ErrorPan: {errorPan}')  # Print error value for debugging
                if abs(errorPan) > 40:  # If the error is significant
                    pan = pan - errorPan / 100  # Adjust pan value
                    ser.write(f"{pan}\n".encode())  # Send pan value via UART
                    #print(f"Sent: {pan}")  # Print the sent pan value
                break  # Process only the first large contour

    cv2.imshow('nanoCam', frame)  # Display the frame with detected object
    cv2.moveWindow('nanoCam', 0, 0)  # Position the video feed window

    if cv2.waitKey(1) == ord('q'):  # Exit loop if 'q' is pressed
        break

# Release the camera and close all OpenCV windows
cam.release()
cv2.destroyAllWindows()
ser.close()  # Close the serial port
