import jetson_inference
import jetson_utils
import time

net = jetson_inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_sone/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_sone/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

# Initialize camera input and video output
camera = jetson_utils.videoSource("/dev/video0", argv=['--input-width=320', '--input-height=180'])
display = jetson_utils.videoOutput()  # Display output

while True:
    img = camera.Capture()
    detections = net.Detect(img)
    display.Render(img)

    width = img.width
    height = img.height

    if detections:
        for detect in detections:
            ID = detect.ClassID
            top = int(detect.Top)
            left = int(detect.Left)
            bottom = int(detect.Bottom)
            right = int(detect.Right)
            item = net.GetClassDesc(ID)
            w = right - left
            print(f'Width of object: {w}')  # Print error value for debugging

    time.sleep(0.001) # If not included, CudaEventElapsedTime , device not ready
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
