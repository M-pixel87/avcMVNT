#this program tracks a bucket and dose it by incrementing the angle by one with abilty to change the color being tracked
import cv2
import numpy as np
import serial  # Import the serial library

# Initialize serial communication
ser = serial.Serial('/dev/ttyTHS0', 9600)

def nothing(x):
    pass

# Create a window with trackbars for HSV adjustments
cv2.namedWindow('Adjustments')
cv2.moveWindow('Adjustments', 1320, 0)

# Create trackbars for adjusting hue, saturation, and value ranges
cv2.createTrackbar('hueLower', 'Adjustments', 82, 179, nothing)
cv2.createTrackbar('hueUpper', 'Adjustments', 179, 179, nothing)
cv2.createTrackbar('hue2Lower', 'Adjustments', 82, 179, nothing)
cv2.createTrackbar('hue2Upper', 'Adjustments', 179, 179, nothing)
cv2.createTrackbar('satLow', 'Adjustments', 146, 255, nothing)
cv2.createTrackbar('satHigh', 'Adjustments', 255, 255, nothing)
cv2.createTrackbar('valLow', 'Adjustments', 64, 255, nothing)
cv2.createTrackbar('valHigh', 'Adjustments', 255, 255, nothing)

# Set the hardcoded values for the FixedFGMask
hueLowFixed = 82
hueUpFixed = 179
hue2LowFixed = 82
hue2UpFixed = 179
satLowFixed = 146
satHighFixed = 255
valLowFixed = 64
valHighFixed = 255

# Initialize camera
cam = cv2.VideoCapture(0)
width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
print('width:', width, 'height:', height)

# Initialize the pan variable
pan = 0
use_fixed_mask = True  # Flag to switch between masks

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to capture image")
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    if use_fixed_mask:
        # Hardcoded values for the FixedFGMask
        l_b11 = np.array([hueLowFixed, satLowFixed, valLowFixed])
        u_b11 = np.array([hueUpFixed, satHighFixed, valHighFixed])
        FGmask11 = cv2.inRange(hsv, l_b11, u_b11)
        
        # Show the FixedFGMask window
        cv2.imshow('FixedFGMask', FGmask11)

        # Find contours in the fixed mask
        contours, _ = cv2.findContours(FGmask11, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw contours and bounding box if contours are found
        if contours:
            for contour in contours:
                if cv2.contourArea(contour) > 1000:  # Filter small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure these are integers
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
                    objX = x + w / 2
                    errorPan = objX - width / 2
                    print(f'ErrorPan: {errorPan}')  # Debugging statement
                    if abs(errorPan) > 50:
                        zwii = 2
                        eins = 1
                        if objX > 320:
                            ser.write(f"{zwii}\n".encode())
                        elif objX < 320:
                            ser.write(f"{eins}\n".encode())
                    break

    else:
        # Get HSV range values from trackbars
        hueLow = cv2.getTrackbarPos('hueLower', 'Adjustments')
        hueUp = cv2.getTrackbarPos('hueUpper', 'Adjustments')
        hue2Low = cv2.getTrackbarPos('hue2Lower', 'Adjustments')
        hue2Up = cv2.getTrackbarPos('hue2Upper', 'Adjustments')
        Ls = cv2.getTrackbarPos('satLow', 'Adjustments')
        Us = cv2.getTrackbarPos('satHigh', 'Adjustments')
        Lv = cv2.getTrackbarPos('valLow', 'Adjustments')
        Uv = cv2.getTrackbarPos('valHigh', 'Adjustments')

        # Define lower and upper bounds for the two hue ranges
        l_b1 = np.array([hueLow, Ls, Lv])
        u_b1 = np.array([hueUp, Us, Uv])
        l_b2 = np.array([hue2Low, Ls, Lv])
        u_b2 = np.array([hue2Up, Us, Uv])

        # Create masks for the two hue ranges and combine them
        FGmask1 = cv2.inRange(hsv, l_b1, u_b1)
        FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
        FGmaskComp = cv2.add(FGmask1, FGmask2)
        
        # Show the combined mask
        cv2.imshow('FGmaskComp', FGmaskComp)
        cv2.moveWindow('FGmaskComp', 0, 530)

        # Find contours in the combined mask
        contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw contours and bounding box if contours are found
        if contours:
            for contour in contours:
                if cv2.contourArea(contour) > 1000:  # Filter small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure these are integers
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)
                    objX = x + w / 2
                    errorPan = objX - width / 2
                    print(f'ErrorPan: {errorPan}')  # Debugging statement
                    if abs(errorPan) > 50:
                        zwii = 2
                        eins = 1
                        if objX > 320:
                            ser.write(f"{zwii}\n".encode())
                        elif objX < 320:
                            ser.write(f"{eins}\n".encode())
                    break

    # Show the camera feed
    cv2.imshow('nanoCam', frame)
    cv2.moveWindow('nanoCam', 0, 0)

    # Switch between masks using the 'Space' key
    key = cv2.waitKey(1)
    if key == ord(' '):  # Space bar to switch between masks
        use_fixed_mask = not use_fixed_mask

    # Exit the loop when 'q' is pressed
    if key == ord('q'):
        break

# Release the camera and close all windows
cam.release()
cv2.destroyAllWindows()
ser.close()  # Close the serial port

