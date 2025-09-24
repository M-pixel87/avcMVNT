import os
import pygame
from Arm import CoOrdinateBaseSys as Arm


# headless support (Jetson/Ubuntu without display)
os.environ["SDL_VIDEODRIVER"] = "dummy"


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
            self.wristA -= 2

        if buttons[7] == 1:
            self.wristA += 2

        self.data = {"L": left_speed, "R": right_speed,  "buttons": buttons}
        return self.data

    def get_data(self):
        return self.data
