import cv2

print(cv2.__version__)

dispW = 640
dispH = 480
flip = 2

cam = cv2.VideoCapture(0)

# Check if camera opened successfully
if not cam.isOpened():
    print("Error: Could not open camera.")
    exit()

# Define the codec and create a VideoWriter object correctly
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
outVid = cv2.VideoWriter('videos/myCam.avi', fourcc, 20.0, (dispW, dispH))

while True:
    ret, frame = cam.read()
    if not ret:
        break
    
    cv2.imshow('nanoCam', frame)
    outVid.write(frame)
    
    if cv2.waitKey(1) == ord('q'):
        break

# Release resources
cam.release()
outVid.release()
cv2.destroyAllWindows()
