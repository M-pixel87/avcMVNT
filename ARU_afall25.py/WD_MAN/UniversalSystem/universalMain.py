from Systems.InputSystem import XboxController
from Systems.InputSystem import Webcam
from Systems.InputSystem import cvWebcam
from Systems.InputSystem import AI
from Systems.InputSystem import AI_YOLO
from Systems.motorSystem import CytronMotor
from Systems.sensorSystem import sensorSystem
from Systems.displaySystem import DisplaySystem

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

# Initialize display system (use cam.camera to check if camera is available)  (Mode options: "GPU", "TK", "YOLO")
display = DisplaySystem(cam.camera, mode="YOLO")


#Handle how fast the program runs
max_fps = 60

last_time = 0
frame_delay = 1.0 / max_fps










#=============================================================================
# BLOCK: WAIT FOR AND VALIDATE VOICE COMMAND
#=============================================================================
# PURPOSE:
# This loop continuously reads from the serial port (self.ser which is a USB port I believe) 
# waiting for a specific voice recognition command.
#
# EXPECTED FORMAT:
# The code expects a string message in the format "Start: N", where N is a
# number from 0 to 8.
#
# PROCESS:
# 1. Read one line from the serial port.
#    - .readline() blocks (waits) until it sees a newline character ('\n')
#      or the 'timeout' period expires.
#
# 2. Check for empty data.
#    - If 'line' is empty, it means the timeout occurred before a full
#      line was received. We 'continue' to restart the loop and try reading again.
#
# 3. Validate the message format.
#    - Check if the line starts with the correct prefix: "Start: ".
#
# 4. Extract and validate the number.
#    - If the prefix matches, try to extract the part after it.
#    - Attempt to convert that part into an integer (the command number).
#    - Check if the number is within the valid range (0-8).
#    - A 'ValueError' will catch messages like "Start: hello".
#
# 5. Send acknowledgement and exit.
#    - If steps 3 & 4 pass, we have a valid command.
#    - Send the "StartMVMNT" message back to acknowledge.
#    - 'break' to exit this 'while' loop and proceed with the main work.
#
# 6. Handle bad messages.
#    - If the prefix is wrong, the number is out of range, or the number
#      isn't a number, print an error and loop again.
#
# --- The main code continues here after the loop is broken ---


print("Waiting for start signal ")
while True:
    line = self.ser.readline().decode(errors='ignore').strip()
    if not line:
        print("No code yet, still waiting...")
        time.sleep(0.1) 
        continue 
    if line.startswith("Start: "):
        try:
            number_str = line[len("Start: "):]
            number = int(number_str)
            if 0 <= number <= 8: #16 digits what we want
                print(f"We got our value ({number}), time to start!")
                ready = "StartMVMNT"
                self.ser.write(ready.encode("utf-8"))
                break 
            else:
                print(f"Got 'Start:', but number {number} is not in range 0-8.")
        except ValueError:
            print(f"Got 'Start:', but couldn't parse number from: '{line}'")
    else:
        print(f"Received wrong message: '{line}'")
print("Work is starting...")



first boot 
start

UnboundLocalError
2<_ code1  3<- preset

2 -
display this message
while true 
preset 












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

    display.update_display(
        img,
        detections,
        controller.get_axes(),  # show all axes
        ctrl_data["buttons"],
        (ctrl_data["L"], ctrl_data["R"]),
        sensors.readSensors()  # pass sensor data for display
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
