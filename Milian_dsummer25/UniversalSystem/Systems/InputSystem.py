import os
import pygame
import threading
import time

# headless support (Jetson/Ubuntu without display)
os.environ["SDL_VIDEODRIVER"] = "dummy"


class XboxControllerThread(threading.Thread):
    def __init__(self, deadzone=0.1, poll_delay=0.05):
        super().__init__(daemon=True)  # daemon thread will close with main
        self.deadzone = deadzone
        self.poll_delay = poll_delay
        self.running = True
        self.data = {"L": 0, "R": 0, "buttons": []}

        pygame.init()
        pygame.display.set_mode((1, 1))
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            raise RuntimeError("⚠️ No controller detected")

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"✅ Controller: {self.joystick.get_name()}")

    def scale_axis(self, val):
        return int(val * 100)

    def run(self):
        """Main loop of the thread: constantly update controller state."""
        while self.running:
            pygame.event.pump()

            left_y = self.joystick.get_axis(1)
            right_y = self.joystick.get_axis(3)

            left_speed = -self.scale_axis(left_y)
            right_speed = -self.scale_axis(right_y)

            if abs(left_speed) < self.deadzone * 100:
                left_speed = 0
            if abs(right_speed) < self.deadzone * 100:
                right_speed = 0

            # collect button states
            buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]

            self.data = {"L": left_speed, "R": right_speed, "buttons": buttons}

            time.sleep(self.poll_delay)

    def get_data(self):
        """Get the latest snapshot of controller input."""
        return self.data

    def stop(self):
        """Gracefully stop the thread."""
        self.running = False
