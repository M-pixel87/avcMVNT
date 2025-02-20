# This is the faster version of lesson54b, optimized for performance.

import jetson.inference
import jetson.utils
import time
import cv2

# Load the trained model with the correct paths
net = jetson.inference.detectNet(
    model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/ssd-mobilenet.onnx",
    labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt",
    input_blob="input_0",
    output_cvg="scores",
    output_bbox="boxes",
    threshold=0.5
)

# Initialize the video source using Jetson utils for faster performance
cam = jetson.utils.videoSource("v4l2:///dev/video0")

# Variables for calculating frames per second (FPS)
timeStamp = time.time()
fpsFilt = 0

while True:
    # Capture an image from the camera
    img = cam.Capture()
    width = img.width
    height = img.height

    # Perform object detection on the image
    detections = net.Detect(img, width, height)
    
    for detect in detections:
        left, top, right, bottom = int(detect.Left), int(detect.Top), int(detect.Right), int(detect.Bottom)
        item = net.GetClassDesc(detect.ClassID)
        
        # Draw a rectangle around the detected object
        jetson.utils.cudaDrawRect(img, (left, top, right, bottom), (255, 0, 0, 255))
        
        # Print the detected object and its coordinates
        print(f"Object: {item}, Coordinates: ({left},{top},{right},{bottom})")

    # Calculate and print the frames per second (FPS)
    dt = time.time() - timeStamp
    timeStamp = time.time()
    fps = 1 / dt
    fpsFilt = .9 * fpsFilt + .1 * fps
    print("FPS: ", round(fpsFilt, 1))

    # Convert the CUDA image to a NumPy array for display with OpenCV
    output = jetson.utils.cudaToNumpy(img)
    cv2.imshow('detCam', output)
    
    # Exit the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break

# Uncomment the line below if using Jetson utils for video source
# cam.Close()
