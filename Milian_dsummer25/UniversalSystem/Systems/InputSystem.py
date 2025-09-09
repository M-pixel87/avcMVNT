import os
import pygame
import threading
import time

# headless support (Jetson/Ubuntu without display)
os.environ["SDL_VIDEODRIVER"] = "dummy"


class XboxController:
    def __init__(self, deadzone=0.05):
        self.deadzone = deadzone
        self.data = {"L": 0, "R": 0, "buttons": []}

        

        if pygame.joystick.get_count() == 0:
            raise RuntimeError("⚠️ No controller detected")

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"✅ Controller: {self.joystick.get_name()}")

    def scale_axis(self, val):
        return int(val * 100)

    def poll(self):
        """Poll controller state. Call this from the main thread after pygame.event.pump()."""
        left_y = self.joystick.get_axis(1)
        right_y = self.joystick.get_axis(3)

        left_speed = self.scale_axis(left_y)
        right_speed = self.scale_axis(right_y)

        if abs(left_speed) < self.deadzone * 100:
            left_speed = 0
        if abs(right_speed) < self.deadzone * 100:
            right_speed = 0

        buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]

        self.data = {"L": left_speed, "R": right_speed, "buttons": buttons}
        return self.data

    def get_data(self):
        return self.data
