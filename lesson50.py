# This code demonstrates the initial setup for using AI models with the Jetson platform.
import jetson_inference
import jetson_utils
import time

width = 1280
height = 720

# Initialize the camera with the specified resolution
cam = jetson_utils.gstCamera(width, height, '/dev/video0')
# Uncomment the line below and comment the above line if using a different camera index
# cam = jetson_utils.gstCamera(width, height, '0')

# Create a display window for rendering the camera feed
display = jetson_utils.glDisplay()

# Load a pre-trained image classification model (GoogLeNet)
net = jetson_inference.imageNet('googlenet')

# Initialize variables for FPS calculation
timeMark = time.time()
fpsFilter = 0

while display.IsOpen():
    # Capture a frame from the camera
    frame, width, height = cam.CaptureRGBA()
    
    # Classify the captured frame using the AI model
    classID, confidence = net.Classify(frame, width, height)
    item = net.GetClassDesc(classID)
    
    # Calculate and filter FPS
    dt = time.time() - timeMark
    fps = 1 / dt
    fpsFilter = 0.95 * fpsFilter + 0.05 * fps
    timeMark = time.time()
    
    # Overlay text on the frame displaying the FPS and classified item
    font = jetson_utils.cudaFont()
    font.OverlayText(frame, width, height, str(round(fpsFilter, 1)) + ' fps ' + item, 5, 5, font.Magenta, font.Blue)
    
    # Render the frame in the display window
    display.RenderOnce(frame, width, height)
