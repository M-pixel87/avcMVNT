import jetson_inference
import jetson_utils

# Load the object detection model
net = jetson_inference.detectNet("ssd-mobilenet-v2", threshold=0.5)

# Initialize the camera
camera = jetson_utils.videoSource("/dev/video0")

# Initialize the display window
display = jetson_utils.videoOutput("display://0")

while display.IsStreaming():
    # Capture the image
    img = camera.Capture()
    
    # Perform object detection
    detections = net.Detect(img)
    
    # Render the image
    display.Render(img)
    
    # Update the status with the network FPS
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
