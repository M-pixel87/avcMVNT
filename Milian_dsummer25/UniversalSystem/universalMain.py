from Systems.InputSystem import XboxController
from Systems.InputSystem import Webcam
from Systems.InputSystem import AI
from Systems.motorSystem import CytronMotor
from Systems.sensorSystem import sensorSystem
from Systems.displaySystem import DisplaySystem

from Arm import CoOrdinateBaseSys as Arm

import pygame
import time
import serial
PORT = "/dev/ttyACM0"
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=0.1)

pygame.init()
pygame.joystick.init()

controller = XboxController()
cam = Webcam()
infer = AI()

#create motor object to send commands
motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
sensors = sensorSystem(ser)

display = DisplaySystem(cam.camera)

def main():
    try:
        while True:
            inputDisplay()
            time.sleep(0.050)
            
    except KeyboardInterrupt:
        print("Stopping...")

def inputDisplay():
     # MAIN PYGAME EVENT PROCESSING : CONTROLLER INPUTS
    pygame.event.pump()

    # Get input values
    ctrl_data = controller.poll()
    
    motors.set_power(ctrl_data["L"], ctrl_data["R"])
    
    img = cam.get_frame()
    infer.detect(img)

    display.update_display(
        controller.get_axes(),  # show all axes
        ctrl_data["buttons"],
        (ctrl_data["L"], ctrl_data["R"]),
        img,
        sensors.readSensors()  # pass sensor data for display
    )


if __name__ == "__main__":
    main()
