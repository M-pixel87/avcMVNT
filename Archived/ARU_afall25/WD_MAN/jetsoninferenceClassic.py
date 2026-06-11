This script uses the NVIDIA Jetson Inference libraries for optimized performance.

# VERSION: PURE INFERENCE - All color detection has been removed.

# This script runs jetson.inference.detectNet on two cameras simultaneously.


import jetson.inference

import jetson.utils

import cv2

import numpy as np

import time


# --- Model Configuration ---

MODEL_PATH = "/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_t/ssd-mobilenet.onnx"

LABELS_PATH = "/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_t/labels.txt"


# --- Camera Configuration ---

CAMERA_1_INDEX = "/dev/video0"

CAMERA_2_INDEX = "/dev/video2"


# --- Main Program ---

print("Initializing Jetson Inference model...")

# The model is loaded once and will be used for both streams.

net = jetson.inference.detectNet(

model=MODEL_PATH,

labels=LABELS_PATH,

input_blob="input_0",

output_cvg="scores",

output_bbox="boxes",

threshold=0.5

)


print("Initializing video sources...")

# These camera objects are optimized to keep video frames in GPU memory

camera = jetson.utils.videoSource(CAMERA_1_INDEX, argv=["--input-width=640", "--input-height=480", "--fps=30"])

camera2 = jetson.utils.videoSource(CAMERA_2_INDEX, argv=["--input-width=640", "--input-height=480", "--fps=30"])


# This display object is used only for showing the FPS status in the window title

display = jetson.utils.videoOutput()


print("Starting main loop. Press 'q' in a camera window to quit.")


# --- FPS Calculation Initialization ---

cam1_startTime = time.time()

cam1_frameCount = 0

cam1_fps = 0

cam2_startTime = time.time()

cam2_frameCount = 0

cam2_fps = 0


try:

while True:

# --- Process Camera 1 ---

img = camera.Capture() # Captures frame directly into GPU memory

if img is None: continue

# Run inference on the first camera's frame

detections = net.Detect(img)


# Convert to NumPy for OpenCV display. This is a CPU/GPU copy operation.

frame = jetson.utils.cudaToNumpy(img)


# Manually draw the detection boxes on the numpy frame

for detect in detections:

ID = detect.ClassID

left, top, right, bottom = int(detect.Left), int(detect.Top), int(detect.Right), int(detect.Bottom)

cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

class_name = net.GetClassDesc(ID)

cv2.putText(frame, class_name, (left, top - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

center_x = detect.Center[0]

confidence = detect.Confidence

print(f"CAM 1 (NN) | Obj: {class_name:<15} | Conf: {confidence:.2f} | Center X: {center_x:.0f}px")


# --- Process Camera 2 ---

img2 = camera2.Capture()

if img2 is None: continue

# Run inference on the second camera's frame using the same network

detections2 = net.Detect(img2)

frame2 = jetson.utils.cudaToNumpy(img2)


# Manually draw the detection boxes on the second frame

for detect in detections2:

ID = detect.ClassID

left, top, right, bottom = int(detect.Left), int(detect.Top), int(detect.Right), int(detect.Bottom)

cv2.rectangle(frame2, (left, top), (right, bottom), (0, 255, 0), 2)

class_name = net.GetClassDesc(ID)

cv2.putText(frame2, class_name, (left, top - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


center_x = detect.Center[0]

confidence = detect.Confidence

print(f"CAM 2 (NN) | Obj: {class_name:<15} | Conf: {confidence:.2f} | Center X: {center_x:.0f}px")

# --- FPS Calculation and Display ---

# Camera 1 FPS

cam1_frameCount += 1

cam1_elapsedTime = time.time() - cam1_startTime

if cam1_elapsedTime > 1.0:

cam1_fps = cam1_frameCount / cam1_elapsedTime

cam1_frameCount = 0

cam1_startTime = time.time()

# Camera 2 FPS

cam2_frameCount += 1

cam2_elapsedTime = time.time() - cam2_startTime

if cam2_elapsedTime > 1.0:

cam2_fps = cam2_frameCount / cam2_elapsedTime

cam2_frameCount = 0

cam2_startTime = time.time()


# Draw FPS on frames

cv2.putText(frame, f"FPS: {cam1_fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

cv2.putText(frame2, f"FPS: {cam2_fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)



# --- Display Results ---

# Update the status bar, which will appear on the window title

# This shows the combined FPS of the neural network across both streams.

display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))

cv2.imshow('Camera 1 - Jetson Inference', frame)

cv2.imshow('Camera 2 - Jetson Inference', frame2)

if cv2.waitKey(1) == ord('q'):

break


finally:

# --- Cleanup ---

print("Closing cameras and cleaning up...")

camera.Close()

camera2.Close()

cv2.destroyAllWindows()

print("Cleanup complete.") 