from Systems.InputSystem import XboxController
from Systems.motorSystem import CytronMotor
from Systems.displaySystem import DisplaySystem
from Arm import CoOrdinateBaseSys as Arm

import pygame
import time
import serial
PORT = "/dev/ttyACM0"
BAUD = 9600
ser = serial.Serial(PORT, BAUD, timeout=1)

pygame.init()
pygame.joystick.init()
controller = XboxController()
motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
display = DisplaySystem()

def main():
    try:
        while True:
            pygameHandle()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping...")

def pygameHandle():
     # MAIN PYGAME EVENT PROCESSING : CONTROLLER INPUTS
    pygame.event.pump()
    ctrl_data = controller.poll()
    # Get raw axes for display
    joystick = controller.joystick
    axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
    print(ctrl_data)
    motors.set_power(ctrl_data["L"], ctrl_data["R"])
    display.update_display(
        axes,  # show all axes
        ctrl_data["buttons"],
        (ctrl_data["L"], ctrl_data["R"])
    )

if __name__ == "__main__":
    main()
