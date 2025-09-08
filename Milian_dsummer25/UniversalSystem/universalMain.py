from systems.inputSystem import XboxController
from systems.motorSystem import CytronMotor

#port to talk over serial
import serial
PORT = "/dev/ttyACM0"
BAUD = 9600
ser = serial.Serial(PORT, BAUD, timeout=1)


def main():

    # Initialize modules
    controller = XboxController()
    motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)

    while True:
        # Read inputs
        ctrl_data = controller.get_input()

        motors.set_power(ctrl_data["L"], ctrl_data["R"])

if __name__ == "__main__":
    main()
