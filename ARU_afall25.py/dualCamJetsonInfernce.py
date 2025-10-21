# This script uses the NVIDIA Jetson Inference libraries for optimized performance.
# VERSION: HEADLESS & GPU-NATIVE DISPLAY - All OpenCV dependencies have been removed.
# This script can run jetson.inference.detectNet on one or two cameras.

import jetson.inference
import jetson.utils
import time
import sys

# --- User Configuration ---
try:
    # Try to get the number of cameras from the command line (e.g., python3 your_script.py 2)
    num_cameras = int(sys.argv[1])
except (IndexError, ValueError):
    # If no command line argument is provided, prompt the user
    try:
        num_cameras = int(input("Enter the number of cameras to use (1 or 2): "))
    except ValueError:
        num_cameras = 1 # Default to 1 if input is not a number

if num_cameras not in [1, 2]:
    print("Invalid input. Defaulting to 1 camera.")
    num_cameras = 1

print(f"Running with {num_cameras} camera(s)...")

# --- Model Configuration ---
MODEL_PATH = "/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_t/ssd-mobilenet.onnx"
LABELS_PATH = "/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_t/labels.txt"

# --- Camera Configuration ---
CAMERA_1_INDEX = "/dev/video0"
CAMERA_2_INDEX = "/dev/video2"

# --- Main Program ---
print("Initializing Jetson Inference model...")
net = jetson.inference.detectNet(
    argv=[
        f"--model={MODEL_PATH}",
        f"--labels={LABELS_PATH}",
        "--input-blob=images",    # Your model's input layer
        "--output-blob=output0"   # Your model's output layer
    ],
    threshold=0.5
)

print("Initializing video sources...")
# Initialize the first camera
camera1 = jetson.utils.videoSource(CAMERA_1_INDEX, argv=["--input-width=640", "--input-height=480", "--fps=30"])
display1 = jetson.utils.videoOutput() # Creates an OpenGL window for display

# Initialize the second camera and display only if requested
camera2 = None
display2 = None
if num_cameras == 2:
    camera2 = jetson.utils.videoSource(CAMERA_2_INDEX, argv=["--input-width=640", "--input-height=480", "--fps=30"])
    display2 = jetson.utils.videoOutput()

print("Starting main loop. Close the display window to quit.")

# Add a frame counter to skip FPS calculation on the first few frames
frame_count = 0 

try:
    # The loop continues as long as the display window is open
    while display1.IsStreaming() and (num_cameras == 1 or (display2 and display2.IsStreaming())):
        frame_count += 1 # Increment the counter each loop

        # --- Process Camera 1 ---
        img1 = camera1.Capture() # Captures frame directly into GPU memory
        if img1 is None: continue
        
        # Detections are performed, and bounding boxes are drawn on img1 automatically
        detections1 = net.Detect(img1)
        
        # Print detections to the terminal
        for detect in detections1:
            class_name = net.GetClassDesc(detect.ClassID)
            print(f"CAM 1 | Obj: {class_name:<15} | Conf: {detect.Confidence:.2f} | Center X: {detect.Center[0]:.0f}px")

        # Render the image with overlays to the first display window
        display1.Render(img1)
        
        # Only start updating the status bar after a few frames to let the GPU warm up
        if frame_count > 5:
            display1.SetStatus(f"Camera 1 | {net.GetNetworkFPS():.0f} FPS")

        # --- Process Camera 2 (Only if enabled) ---
        if num_cameras == 2 and camera2 is not None:
            img2 = camera2.Capture()
            if img2 is None: continue
            
            detections2 = net.Detect(img2)

            for detect in detections2:
                class_name = net.GetClassDesc(detect.ClassID)
                print(f"CAM 2 | Obj: {class_name:<15} | Conf: {detect.Confidence:.2f} | Center X: {detect.Center[0]:.0f}px")
            
            # Render the second image to its own display window
            display2.Render(img2)
            
            # Update status bar for the second window
            if frame_count > 5:
                display2.SetStatus(f"Camera 2 | {net.GetNetworkFPS():.0f} FPS")

finally:
    # --- Cleanup ---
    # The camera and display objects are automatically released
    print("Closing application...")