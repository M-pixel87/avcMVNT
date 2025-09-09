from Systems.InputSystem import XboxController
from Systems.motorSystem import CytronMotor

import pygame
import time
import serial
PORT = "/dev/ttyACM0"
BAUD = 9600
ser = serial.Serial(PORT, BAUD, timeout=1)


def main():
    pygame.init()
    pygame.joystick.init()
    controller = XboxController()
    motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
    try:
        while True:
            pygame.event.pump()  # Must be called in main thread
            ctrl_data = controller.poll()
            print(ctrl_data)
            motors.set_power(ctrl_data["L"], ctrl_data["R"])
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping...")

if __name__ == "__main__":
    main()
