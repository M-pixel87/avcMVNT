#this code is meant to be a first run at running the AI code that we made on a terminal 
import jetson.inference
import jetson.utils
import time
import cv2
import numpy as np 

timeStamp = time.time()
fpsFilt = 0

# Load your trained model with the correct paths
net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

dispW = 1280
dispH = 720
flip = 2
font = cv2.FONT_HERSHEY_SIMPLEX

cam = cv2.VideoCapture('/dev/video0')
cam.set(cv2.CAP_PROP_FRAME_WIDTH, dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, dispH)

while True:
    _, img = cam.read()
    height = img.shape[0]
    width = img.shape[1]

    frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA).astype(np.float32)
    frame = jetson.utils.cudaFromNumpy(frame)

    detections = net.Detect(frame, width, height)
    for detect in detections:
        ID = detect.ClassID
        top = int(detect.Top)
        left = int(detect.Left)
        bottom = int(detect.Bottom)
        right = int(detect.Right)
        item = net.GetClassDesc(ID)
        
        # Draw rectangle and label
        cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 1)
        cv2.putText(img, item, (left, top + 20), font, .75, (0, 0, 255), 2)

        # Example: handle object position
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        
        # Add your logic here based on object position
        # Example: Print the position
        print(f"Object: {item}, Center position: ({center_x})")

    dt = time.time() - timeStamp
    timeStamp = time.time()
    fps = 1 / dt
    fpsFilt = .9 * fpsFilt + .1 * fps
    cv2.putText(img, str(round(fpsFilt, 1)) + ' fps', (0, 30), font, 1, (0, 0, 255), 2)
    cv2.imshow('detCam', img)
    cv2.moveWindow('detCam', 0, 0)
    if cv2.waitKey(1) == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
