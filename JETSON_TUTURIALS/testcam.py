import cv2

# Display the OpenCV version
print(cv2.__version__)

# Set display width and height
dispW = 320
dispH = 240

# Uncomment these next two lines for Pi Camera
# camSet = 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method=' + str(flip) + ' ! video/x-raw, width=' + str(dispW) + ', height=' + str(dispH) + ', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'
# cam = cv2.VideoCapture(camSet)

# Or, if you have a webcam, uncomment the next line
# (If it does not work, try setting to '1' instead of '0')
cam = cv2.VideoCapture(0)

# Set the width and height for the capture
cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

# Check if the width and height are set correctly
actualW = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
actualH = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Requested resolution: {dispW}x{dispH}")
print(f"Actual resolution: {actualW}x{actualH}")

while True:
    # Capture frame-by-frame
    ret, frame = cam.read()

    if not ret:
        print("Error: Could not read frame.")
        break

    # Display the resulting frame
    cv2.imshow('Webcam Feed', frame)
    cv2.moveWindow('Webcam Feed', 0, 10)

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('Gray Video', gray)
    cv2.moveWindow('Gray Video', 700, 10)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) == ord('q'):
        break

# When everything is done, release the capture
cam.release()
cv2.destroyAllWindows()




