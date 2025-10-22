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

#create and initialize map
map = mapSys.Map(w=30, h=30, r=20, c=20)
map.fill_matrix()
map.place_objects_on_map()

# Initialize display system (use cam.camera to check if camera is available)  (Mode options: "GPU", "TK", "YOLO")
display = DisplaySystem(cam.camera, mode="YOLO")


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

    # Get input values
    ctrl_data = controller.poll()
    
    motors.set_power(ctrl_data["L"], ctrl_data["R"])
    
    img = cam.get_frame()
    detections = infer.detect(img)

    data = sensors.read_sensors()
    map.vehicle.update_position(data["roll"], data["ax"], data["ay"])

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