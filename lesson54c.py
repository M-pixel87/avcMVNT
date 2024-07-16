import jetson.inference
import jetson.utils
import time
import cv2

net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_six/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

cam = jetson.utils.videoSource("v4l2:///dev/video0")
timeStamp = time.time()
fpsFilt = 0

while True:
    img = cam.Capture()
    width = img.width
    height = img.height

    detections = net.Detect(img, width, height)
    
    for detect in detections:
        left, top, right, bottom = int(detect.Left), int(detect.Top), int(detect.Right), int(detect.Bottom)
        item = net.GetClassDesc(detect.ClassID)
        jetson.utils.cudaDrawRect(img, (left, top, right, bottom), (255, 0, 0, 255))
        print(f"Object: {item}, Coordinates: ({left},{top},{right},{bottom})")

    dt = time.time() - timeStamp
    timeStamp = time.time()
    fps = 1 / dt
    fpsFilt = .9 * fpsFilt + .1 * fps
    print("FPS: ", round(fpsFilt, 1))

    output = jetson.utils.cudaToNumpy(img)
    cv2.imshow('detCam', output)
    if cv2.waitKey(1) == ord('q'):
        break

 #cam.Close()  # Uncomment if using Jetson utils for video source
