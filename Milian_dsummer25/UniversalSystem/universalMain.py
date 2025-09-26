from Systems.InputSystem import XboxController
from Systems.InputSystem import Webcam
from Systems.motorSystem import CytronMotor
from Systems.displaySystem import GPUDisplaySystem
from Systems.displaySystem import TkDisplaySystem
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
cam = Webcam()
motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)

if(cam.camera == None):
    display = TkDisplaySystem()
else:
    display = GPUDisplaySystem()

def main():
    try:
        while True:
            inputDisplay()
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Stopping...")

def inputDisplay():
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
        (ctrl_data["L"], ctrl_data["R"]),
        cam.get_frame()
    )

if __name__ == "__main__":
    main()
