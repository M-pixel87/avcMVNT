from Systems.InputSystem import XboxControllerThread
from Systems.motorSystem import CytronMotor

#port to talk over serial
import pygame
import time
import serial
PORT = "/dev/ttyACM0"
BAUD = 9600
ser = serial.Serial(PORT, BAUD, timeout=1)


def main():

    # Initialize modules
    controller = XboxControllerThread()
    controller.start()
    motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
    try:
        while True:
            ctrl_data = controller.get_data()
            print(ctrl_data)   # you can send this to motors, etc.
            motors.set_power(ctrl_data["L"], ctrl_data["R"])
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Stopping...")
        controller.stop()
        controller.join()

    
        

if __name__ == "__main__":
    main()
