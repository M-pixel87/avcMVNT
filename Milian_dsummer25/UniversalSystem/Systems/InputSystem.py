import time
import pygame

class InputSystem:
    def __init__(self, name):
        self.name = name

    def get_input(self):
        raise NotImplementedError("Override in subclass")
    
class XboxController(InputSystem):
    
    def __init__(self):
        # Initialize controller, e.g., using pygame or other library
        super().__init__("Xbox Controller")
        joystick = None

    def scale_axis(val):
        """Convert joystick axis (-1.0 to 1.0) to motor speed (-100 to 100)."""
        return int(val * 100)

    def initalizeController(self):
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("⚠️ No controller detected.")
            return False
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"✅ Connected to controller: {self.joystick.get_name()}")
        return True

    def get_input(self):
        pygame.event.pump()
         # Joystick axes for driving
        left_y = self.joystick.get_axis(1)
        right_y = self.joystick.get_axis(3)
        left_speed = -self.scale_axis(left_y)
        right_speed = -self.scale_axis(right_y)

        if abs(left_speed) < 10:
            left_speed = 0
        if abs(right_speed) < 10:
            right_speed = 0

        return {"L": -left_speed, "R": -right_speed, "buttons": []}