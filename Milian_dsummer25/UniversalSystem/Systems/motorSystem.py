

class MotorSystem:
    def __init__(self, name):
        self.name = name

    def set_power(self, left, right):
        raise NotImplementedError("Override in subclass")

class CytronMotor(MotorSystem):
    def __init__(self, in1, an1, in2, an2, ser):
        super().__init__("Cytron MDDS30")
        self.in1, self.an1, self.in2, self.an2, self.ser = in1, an1, in2, an2, ser
        # Setup PWM pins, serial port, etc.

    def set_power(self, left_speed, right_speed):
        command = f"L:{left_speed},R:{right_speed}\n"
        self.ser.write(command.encode("utf-8"))
        #print(f"Sent: {command.strip()}")
