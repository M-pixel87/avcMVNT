import jetson.inference
import jetson.utils
import cv2
import numpy as np
import time

# Set the width and height for the display window
width = 1280
height = 720
dispW = width
dispH = height
flip = 2

# Initialize the camera settings using OpenCV
# Uncomment the following lines if using GStreamer pipeline for better camera quality
# camSet = 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! nvvidconv flip-method='+str(flip)+' ! video/x-raw, width='+str(dispW)+', height='+str(dispH)+', format=BGRx ! videoconvert ! video/x-raw, format=BGR ! videobalance contrast=1.5 brightness=-.3 saturation=1.2 ! appsink'
# cam1 = cv2.VideoCapture(camSet)

# Open the video capture from the specified device
cam1 = cv2.VideoCapture('/dev/video1')
cam1.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam1.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

# Load the trained model with the correct paths
net = jetson.inference.imageNet(
    'alexnet',
    ['--model=/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six',
     '--input_blob=input_0',
     '--output_blob=output_0',
     '--labels=/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt']
)

# Set the font for displaying text on the image
font = cv2.FONT_HERSHEY_SIMPLEX

# Variables for calculating frames per second (FPS)
timeMark = time.time()
fpsFilter = 0

while True:
    # Capture a frame from the camera
    _, frame = cam1.read()
    
    # Convert the frame to RGBA format and then to CUDA format
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA).astype(np.float32)
    img = jetson.utils.cudaFromNumpy(img)
    
    # Classify the image using the loaded model
    classID, confidence = net.Classify(img, width, height)
    item = net.GetClassDesc(classID)
    
    # Calculate and display the FPS
    dt = time.time() - timeMark
    fps = 1 / dt
    fpsFilter = .95 * fpsFilter + .05 * fps
    timeMark = time.time()
    
    # Overlay the FPS and detected item on the frame
    cv2.putText(frame, str(round(fpsFilter, 1)) + ' fps ' + item, (0, 30), font, 1, (0, 0, 255), 2)
    cv2.imshow('recCam', frame)
    cv2.moveWindow('recCam', 0, 0)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break

# Release the camera and destroy all OpenCV windows
cam1.release()
cv2.destroyAllWindows()

