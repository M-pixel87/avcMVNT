# This program is similar to the original one but focuses on sending the object’s offset from the center through the UART pin.
# The program can switch between using a fixed HSV mask and an adjustable HSV mask by pressing the space bar.

import cv2
import numpy as np
# import serial  # Import the serial library for UART communication

# Initialize serial communication (currently commented out)
# ser = serial.Serial('/dev/ttyTHS0', 9600)

def nothing(x):
    pass  # Placeholder function for trackbar callbacks

# Create a window with trackbars for adjusting HSV values
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

# Set hardcoded HSV values for the fixed mask
hueLowFixed = 160
hueUpFixed = 269
hue2LowFixed = 160
hue2UpFixed = 269
satLowFixed = 146
satHighFixed = 255
valLowFixed = 64
valHighFixed = 255

# Initialize the camera
cam = cv2.VideoCapture(0)
width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
print('width:', width, 'height:', height)  # Print the camera resolution

# Initialize the pan variable
pan = 0
use_fixed_mask = True  # Flag to switch between the fixed and adjustable masks

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to capture image")
        break  # Exit the loop if image capture fails

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # Convert the frame to HSV color space

    if use_fixed_mask:
        # Use hardcoded HSV values to create a fixed mask
        l_b11 = np.array([hueLowFixed, satLowFixed, valLowFixed])
        u_b11 = np.array([hueUpFixed, satHighFixed, valHighFixed])
        FGmask11 = cv2.inRange(hsv, l_b11, u_b11)
        
        # Display the fixed mask
        cv2.imshow('FixedFGMask', FGmask11)

        # Find contours in the fixed mask
        contours, _ = cv2.findContours(FGmask11, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw contours and bounding boxes if contours are found
        if contours:
            for contour in contours:
                if cv2.contourArea(contour) > 1000:  # Filter out small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure integer values
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)  # Draw rectangle around the object
                    objX = x + w / 2  # Calculate the object's center X-coordinate
                    errorPan = objX - width / 2  # Calculate the pan error
                    print(f'ErrorPan: {errorPan}')  # Debugging statement
                    break  # Process only the first large contour

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

        # Define HSV bounds for two hue ranges
        l_b1 = np.array([hueLow, Ls, Lv])
        u_b1 = np.array([hueUp, Us, Uv])
        l_b2 = np.array([hue2Low, Ls, Lv])
        u_b2 = np.array([hue2Up, Us, Uv])

        # Create masks for the two hue ranges and combine them
        FGmask1 = cv2.inRange(hsv, l_b1, u_b1)
        FGmask2 = cv2.inRange(hsv, l_b2, u_b2)
        FGmaskComp = cv2.add(FGmask1, FGmask2)
        
        # Display the combined mask
        cv2.imshow('FGmaskComp', FGmaskComp)
        # cv2.moveWindow('FGmaskComp', 0, 530)  # Optional: reposition the mask window

        # Find contours in the combined mask
        contours, _ = cv2.findContours(FGmaskComp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw contours and bounding boxes if contours are found
        if contours:
            for contour in contours:
                if cv2.contourArea(contour) > 1000:  # Filter out small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure integer values
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 3)  # Draw rectangle around the object
                    objX = x + w / 2  # Calculate the object's center X-coordinate
                    errorPan = objX - width / 2  # Calculate the pan error
                    print(f'ErrorPan: {errorPan}')  # Debugging statement
                    # Uncomment the following lines to send commands via UART based on object position
                    # if abs(errorPan) > 50:
                    #     zwii = 2
                    #     eins = 1
                    #     if objX > 320:
                    #         ser.write(f"{zwii}\n".encode())
                    #     elif objX < 320:
                    #         ser.write(f"{eins}\n".encode())
                    break  # Process only the first large contour

    # Display the camera feed
    cv2.imshow('nanoCam', frame)
    cv2.moveWindow('nanoCam', 0, 0)

    # Switch between using the fixed mask and adjustable mask with the 'Space' key
    key = cv2.waitKey(1)
    if key == ord(' '):  # Space bar to toggle between masks
        use_fixed_mask = not use_fixed_mask

    # Exit the loop when 'q' is pressed
    if key == ord('q'):
        break

# Release the camera and close all OpenCV windows
cam.release()
cv2.destroyAllWindows()
# ser.close()  # Close the serial port (currently commented out)

