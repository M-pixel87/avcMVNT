import os
import pygame
from Arm import CoOrdinateBaseSys as Arm
import jetson_utils


# headless support (Jetson/Ubuntu without display)
os.environ["SDL_VIDEODRIVER"] = "dummy"

class webcam:
    def __init__(self, cam_id=0, width=640, height=480):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        camera = jetson_utils.videoSource("/dev/video[{}]".format(cam_id), argv=["--input-width={}".format(width), "--input-height={}".format(height)])
        display = jetson_utils.videoOutput("display://0", argv=["--output-width={}".format(width), "--output-height={}".format(height)])

    def get_frame(self):
        img = self.camera.Capture()
        return img
    
    def show_frame(self, img):
        self.display.Render(img)
        self.display.SetStatus("Object Detection | Network {:.0f} FPS".format(self.network.GetNetworkFPS()))

    def release(self):
        self.camera.Close()
        self.display.Close()



class XboxController:
    def __init__(self, deadzone=0.05):
        self.deadzone = deadzone
        self.data = {"L": 0, "R": 0, "buttons": []}
        self.mode = 0  # start in drive mode (0=drive, 1=arm)
        self.x = 10
        self.y = 0
        self.z = 10
        

        if pygame.joystick.get_count() == 0:
            raise RuntimeError("⚠️ No controller detected")

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"✅ Controller: {self.joystick.get_name()}")

    def scale_axis(self, val):
        return int(val * 100)

    def poll(self):
        """Poll controller state. Call this from the main thread after pygame.event.pump()."""
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

        buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
        if buttons[0] == 1:
            print("A pressed")
            self.mode = 1 if self.mode == 0 else 0
            print(f"🔀 Mode: {'ARM' if self.mode == 1 else 'DRIVE'}")


        self.data = {"L": left_speed, "R": right_speed,  "buttons": buttons}
        return self.data

    def get_data(self):
        return self.data
