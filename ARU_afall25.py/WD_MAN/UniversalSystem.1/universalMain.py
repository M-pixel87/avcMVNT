from Systems.InputSystem import XboxController
from Systems.InputSystem import Webcam
from Systems.InputSystem import cvWebcam
from Systems.InputSystem import AI
from Systems.InputSystem import AI_YOLO
from Systems.motorSystem import CytronMotor
from Systems.sensorSystem import sensorSystem
from Systems.displaySystem import DisplaySystem
from Systems import MappingSystem as mapSys
from Systems import locationObjects
from Systems.InputSystem import AI_Inputs

from Arm import CoOrdinateBaseSys as Arm

import pygame
import time
import serial

# Setup serial for Arduino communication
PORT = "/dev/ttyACM0"
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=0.1)

# Initialize Pygame and joystick
pygame.init()
pygame.joystick.init()

# Create system objects
controller = XboxController()
cam = cvWebcam()
infer = AI_YOLO(conf_threshold=0.3)

#create motor object to send commands
motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
sensors = sensorSystem(ser)

'''FAILED ACCELEROMETER CODE'''
#create and initialize map
#map = mapSys.Map(w=30, h=30, r=20, c=20)

# Initialize display system (use cam.camera to check if camera is available)  (Mode options: "GPU", "TK", "YOLO")
display = DisplaySystem(cam.camera, mode="YOLO")

#AI CONTROL
ai_Inputs = AI_Inputs(frame_width=cam.width, frame_height=cam.height)

#Handle how fast the program runs
max_fps = 60

last_time = 0
frame_delay = 1.0 / max_fps


def main():
    global last_time
    try:
        while True:
            now = time.time()
            if now - last_time >= frame_delay:
                inputDisplay()
                last_time = now
            
    except KeyboardInterrupt:
        print("Stopping...")

def inputDisplay():
     # MAIN PYGAME EVENT PROCESSING : CONTROLLER INPUTS
    pygame.event.pump()

    ctrl_data = controller.poll()
    # Get input values if controller is connected
    if(controller.connected):
        ai_Inputs.driving = False
        motors.set_power(ctrl_data["L"], ctrl_data["R"])
    
    img = cam.get_frame()
    detections = infer.detect(img)
    
    # AI DRIVING MODE
    if(detections and controller.connected is False):
        ai_Inputs.update_target(detections[0])
        ai_data = ai_Inputs.move_command()
        motors.set_power(ai_data["L"], ai_data["R"])
    elif(controller.connected is False):
        ai_Inputs.driving = False
        ai_data = ai_Inputs.move_command()
        motors.set_power(ai_data["L"], ai_data["R"])

     # SENSOR READING
    data = sensors.readSensors()
    print(data)
    '''FAILED ACCELEROMETER CODE'''
    #map.vehicle.update_position( data["ax"], data["ay"],data["Roll"])

    display.update_display(
        img,
        detections,
        controller.get_axes(),  # show all axes
        ctrl_data["buttons"],
        (ctrl_data["L"], ctrl_data["R"]),
        data
    )

def testPickup():
    arm = Arm.CoOrdinateBaseSys(ser)
    time.sleep(1)
    arm.moveTo(10,10,0)
    time.sleep(2)
    arm.moveTo(10,2,0)
    arm.move_joint(4, 90)
    arm.move_joint(5, 60)
    time.sleep(2)
    arm.move_joint(5, 10)
    time.sleep(2)
    arm.moveTo(10,10,0)
    time.sleep(2)

if __name__ == "__main__":
    main()