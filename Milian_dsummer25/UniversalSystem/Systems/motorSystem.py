#PLACEHOLDERS/UNDERDEVELOPED

class MotorSystem:
    def __init__(self, name):
        self.name = name

    def set_power(self, left, right):
        raise NotImplementedError("Override in subclass")

class CytronMotor(MotorSystem):
    def __init__(self, in1, an1, in2, an2):
        super().__init__("Cytron MDDS30")
        self.in1, self.an1, self.in2, self.an2 = in1, an1, in2, an2
        # Setup PWM pins etc.

    def set_power(self, left, right):
        print(f"[{self.name}] L={left}, R={right}")
        # actually send PWM here
