import jetson.inference
import jetson.utils

net = jetson.inference.detectNet(model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_done/ssd-mobilenet.onnx",
                                 labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_done/labels.txt",
                                 input_blob="input_0",
                                 output_cvg="scores",
                                 output_bbox="boxes",
                                 threshold=0.5)

# Initialize camera input and video output
camera = jetson.utils.videoSource("/dev/video0")  # Camera input
display = jetson.utils.videoOutput()  # Display output

while True:
    # Capture image from the camera
    img = camera.Capture()

    # Run detection on the image
    detections = net.Detect(img)

    # Render the image to display
    display.Render(img)

    # Display the FPS in the status bar
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
