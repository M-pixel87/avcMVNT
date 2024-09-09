import jetson.inference
import jetson.utils
import cv2
import numpy as np
import time

# Initialize timestamp and FPS filter
timeStamp = time.time()
fpsFilt = 0

# Load the trained model
net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_aone/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_aone/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

# Initialize the camera
try:
    cam = jetson.utils.videoSource("/dev/video0")

except Exception as e:
    print(f"Error initializing camera: {e}")
    exit()

# Create windows for display
cv2.namedWindow('detCam', cv2.WINDOW_NORMAL)

while True:
    try:
        img = cam.Capture()
        if img is None:
            print("Failed to capture image from camera")
            continue

        width = img.width
        height = img.height

        # Perform detection
        detections = net.Detect(img, width, height)

        # Convert CUDA image to numpy array
        frame = jetson.utils.cudaToNumpy(img)

        # Convert from RGBA to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        if detections:
            for detect in detections:
                ID = detect.ClassID
                top = int(detect.Top)
                left = int(detect.Left)
                bottom = int(detect.Bottom)
                right = int(detect.Right)
                item = net.GetClassDesc(ID)

                # Draw rectangle around detected object
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 1)
                fontScale = width / 1280
                cv2.putText(frame, item, (left, top + 20), cv2.FONT_HERSHEY_SIMPLEX, fontScale, (0, 0, 255), 2)

        # Calculate FPS
        dt = time.time() - timeStamp
        timeStamp = time.time()
        fps = 1 / dt
        fpsFilt = .9 * fpsFilt + .1 * fps

        # Display FPS
        fontScale = width / 1280
        cv2.putText(frame, str(round(fpsFilt, 1)) + ' fps', (0, 30), cv2.FONT_HERSHEY_SIMPLEX, fontScale, (0, 0, 255), 2)

        # Display the frame
        cv2.imshow('detCam', frame)

        if cv2.waitKey(1) == ord('q'):
            break

    except Exception as e:
        print(f"Error during processing: {e}")
        continue

# Release resources
cam.Close()
cv2.destroyAllWindows()
