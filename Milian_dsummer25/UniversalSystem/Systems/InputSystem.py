import os
import pygame
from Arm import CoOrdinateBaseSys as Arm
import jetson_utils

#Libararies for AI Inference Class
import jetson_inference
import time
#import pycuda.driver as cuda  # Required for synchronization

# headless support (Jetson/Ubuntu without display)
os.environ["SDL_VIDEODRIVER"] = "dummy"

import os
import jetson_utils

# headless support (Jetson/Ubuntu without display)
os.environ["SDL_VIDEODRIVER"] = "dummy"

class AI:
    def __init__(self):
        self.net = jetson_inference.detectNet(
            model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_jone/ssd-mobilenet.onnx",
            labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_jone/labels.txt",
            input_blob="input_0",
            output_cvg="scores",
            output_bbox="boxes",
            threshold=0.5)
        

    def detect(self, img):
        if(img):
            detections = self.net.Detect(img)

            width = img.width
            height = img.height

            if detections:
                for detect in detections:
                    ID = detect.ClassID
                    top = int(detect.Top)
                    left = int(detect.Left)
                    bottom = int(detect.Bottom)
                    right = int(detect.Right)
                    item = self.net.GetClassDesc(ID)
                    w = right - left
                    print(f'Width of object: {w}')
        else:
            pass

class Webcam:
    def __init__(self, cam_id=0, width=640, height=480):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.camera = None  # will stay None if no cam
        self.display = None

        # try to open a display
        try:
            self.display = jetson_utils.videoOutput(
                "display://0",
                argv=[f"--output-width={width}", f"--output-height={height}"]
            )
        except Exception as e:
            print(f"⚠️ Display init failed: {e}")
            self.display = None

        # Now try to open camera
        try:
            path = f"/dev/video{cam_id}"
            if not os.path.exists(path):
                raise FileNotFoundError(f"No device at {path}")

            self.camera = jetson_utils.videoSource(
                path,
                argv=[f"--input-width={width}", f"--input-height={height}"]
            )
            print(f"✅ Camera initialized on {path}")
        except Exception as e:
            print(f"⚠️ Camera init failed: {e}")
            self.camera = None

    def get_frame(self):
        if self.camera is None:
            return None
        try:
            return self.camera.Capture()
        except Exception as e:
            print(f"⚠️ Capture failed: {e}")
            return None

    def show_frame(self, img):
        if self.display is not None and img is not None:
            self.display.Render(img)
            self.display.SetStatus("Webcam Stream")
        elif self.display is not None:
            # just keep window alive even if no image
            self.display.SetStatus("No Camera Feed")

    def release(self):
        if self.camera is not None:
            self.camera.Close()
        if self.display is not None:
            self.display.Close()



class XboxController:
    def __init__(self, deadzone=0.05):
        self.deadzone = deadzone
        self.data = {"L": 0, "R": 0, "buttons": []}
        self.mode = 0  # start in drive mode (0=drive, 1=arm)
        self.x = 10
        self.y = 0
        self.z = 10
        self.jawA = 5.0
        self.wristA = -90.0
        

        if pygame.joystick.get_count() == 0:
            self.controller = False
        else:
            self.controller = True
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"✅ Controller: {self.joystick.get_name()}")

    def scale_axis(self, val):
        return int(val * 100)

    def poll(self):
        """Poll controller state. Call this from the main thread after pygame.event.pump()."""
        if(self.controller is not False):
            #  in drive mode
            if(self.mode == 0):
                left_y = self.joystick.get_axis(1)
                right_y = self.joystick.get_axis(3)

                left_speed = self.scale_axis(left_y)
                right_speed = self.scale_axis(right_y)

                if abs(left_speed) < self.deadzone * 100:
                    left_speed = 0
                if abs(right_speed) < self.deadzone * 100:
                    right_speed = 0
            else:
            #arm mode controls
                left_speed = 0
                right_speed = 0
                left_x = self.joystick.get_axis(0)   # left stick horizontal
                left_y = self.joystick.get_axis(1)   # left stick vertical
                right_y = self.joystick.get_axis(3)  # right stick vertical

                # Deadzone (ignore small noise)
                deadzone = 0.2
                step_size = 0.5  # how much to move per tick
                # Move X with left stick horizontal
                if abs(left_x) > deadzone:
                    self.x += left_x * step_size

                # Move Z with left stick vertical (inverted so up = increase z)
                if abs(left_y) > deadzone:
                    self.z -= left_y * step_size

                # Move Y with right stick vertical
                if abs(right_y) > deadzone:
                    self.y -= right_y * step_size

                # ARM CONTROL
                Arm.move_arm_to(self.x, self.y, self.z, speed=200, acc=100)
                Arm.move_joint(5, self.jawA)
                Arm.move_joint(4, self.wristA)

            buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
            if buttons[0] == 1:
                print("A pressed")
                self.mode = 1 if self.mode == 0 else 0
                print(f"🔀 Mode: {'ARM' if self.mode == 1 else 'DRIVE'}")

            if buttons[4] == 1:
                self.jawA += 2

            if buttons[3] == 1:
                self.jawA -= 2

            if buttons[6] == 1:
                self.wristA -= 5

            if buttons[7] == 1:
                self.wristA += 5

            self.data = {"L": left_speed, "R": right_speed,  "buttons": buttons}
            return self.data
        else:
            self.data = {"L": 0, "R": 0, "buttons": []}
            return self.data

    def get_data(self):
        return self.data

    def get_axes(self):
        if(self.controller):
            return [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
        else:
            return [0]
