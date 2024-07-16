import jetson_inference
import jetson_utils

# Load the object detection model
net = jetson_inference.detectNet("ssd-mobilenet-v2", threshold=0.5)

# Initialize the camera
camera = jetson_utils.videoSource("/dev/video0")

# Initialize the display window
display = jetson_utils.videoOutput("display://0")

def get_dominant_color(image, bbox):
    # Crop the bounding box area from the image
    cropped_img = jetson_utils.cudaCrop(image, bbox)
    # Convert to numpy array for color detection
    np_img = jetson_utils.cudaToNumpy(cropped_img)
    # Compute the mean color of the cropped area
    mean_color = np_img.mean(axis=(0, 1))
    return mean_color

while display.IsStreaming():
    # Capture the image
    img = camera.Capture()
    
    # Perform object detection
    detections = net.Detect(img)
    
    for detection in detections:
        if detection.ClassID == 41:  # Class ID for 'cup'
            bbox = (detection.Left, detection.Top, detection.Right, detection.Bottom)
            color = get_dominant_color(img, bbox)
            print(f"Cup detected at {bbox} with color: {color}")
            print(f"Edges of cup: Left: {detection.Left}, Top: {detection.Top}, Right: {detection.Right}, Bottom: {detection.Bottom}")
    
    # Render the image
    display.Render(img)
    
    # Update the status with the network FPS
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
