import jetson_inference
import jetson_utils
import time

width = 1280
height = 720
cam = jetson_utils.gstCamera(width, height, '/dev/video0')
# cam = jetson_utils.gstCamera(width, height, '0')
display = jetson_utils.glDisplay()
net = jetson_inference.imageNet('googlenet')

timeMark = time.time()
fpsFilter = 0

while display.IsOpen():
    frame, width, height = cam.CaptureRGBA()
    classID, confidence = net.Classify(frame, width, height)
    item = net.GetClassDesc(classID)
    
    dt = time.time() - timeMark
    fps = 1 / dt
    fpsFilter = 0.95 * fpsFilter + 0.05 * fps
    timeMark = time.time()
    
    font = jetson_utils.cudaFont()
    font.OverlayText(frame, width, height, str(round(fpsFilter, 1)) + ' fps ' + item, 5, 5, font.Magenta, font.Blue)
    display.RenderOnce(frame, width, height)
