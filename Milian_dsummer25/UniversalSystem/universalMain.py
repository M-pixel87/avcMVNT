from systems.inputSystem import XboxController
from systems.sensorSystem import UltrasonicSensor
from systems.motorSystem import CytronMotor

def main():
    # Initialize modules
    controller = XboxController()
    ultrasonic = UltrasonicSensor(trig_pin=17, echo_pin=18)
    motors = CytronMotor(in1=4, an1=5, in2=7, an2=6)

    while True:
        # Read inputs
        ctrl_data = controller.get_input()
        distance = ultrasonic.read()

        # Example: obstacle stop
        if distance < 20:
            motors.set_power(0, 0)
        else:
            motors.set_power(ctrl_data["y"], ctrl_data["y"])

if __name__ == "__main__":
    main()
