import cv2
import numpy as np
import serial  # Import the serial library

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

# Uncomment these lines for Pi Camera
# camSet = 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method=' + str(flip) + ' ! video/x-raw, width=' + str(dispW) + ', height=' + str(dispH) + ', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
# cam = cv2.VideoCapture(camSet)

# Or, if you have a WEB cam, uncomment the next line
# (If it does not work, try setting to '1' instead of '0')
cam = cv2.VideoCapture(0)
width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
print('width:', width, 'height:', height)

# Initialize the pan variable
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

    cv2.imshow('FGmaskComp', FGmaskComp)
    cv2.moveWindow('FGmaskComp', 0, 530)

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
                if abs(errorPan) > 40:
                    pan = pan - errorPan / 100
                    ser.write(f"{pan}\n".encode())
                    print(f"Sent: {pan}")
                    
                break

    cv2.imshow('nanoCam', frame)
    cv2.moveWindow('nanoCam', 0, 0)

    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
ser.close()  # Close the serial port
