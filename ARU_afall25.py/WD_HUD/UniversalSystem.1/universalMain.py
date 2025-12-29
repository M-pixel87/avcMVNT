from Systems.InputSystem import XboxController, cvWebcam, AI_YOLO, AI_Inputs
from Systems.motorSystem import CytronMotor
from Systems.sensorSystem import sensorSystem
from Systems.displaySystem import DisplaySystem
from Systems.mode_State import modeState
from Arm import CoOrdinateBaseSys as Arm
import pygame
import time
import serial

inputState = modeState()

# Setup serial
PORT = "/dev/ttyACM0"
BAUD = 115200
ser = serial.Serial(PORT, BAUD, timeout=0.1)

# Init Pygame
pygame.init()
pygame.joystick.init()

# Create Objects
controller = XboxController(state=inputState)
cam = cvWebcam()
infer = AI_YOLO(conf_threshold=0.3)
motors = CytronMotor(in1=4, an1=5, in2=7, an2=6, ser=ser)
sensors = sensorSystem(ser)
display = DisplaySystem(cam.camera, mode="YOLO")

# AI Control
ai_Inputs = AI_Inputs(frame_width=cam.width, frame_height=cam.height, state=inputState)

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
        motors.set_power(0, 0)
        cam.release()
        infer.release()

def inputDisplay():
    active_Cmd = {"L": 0, "R": 0}
    
    # 1. READ SENSORS & UPDATE AI
    # This must happen first so AI knows distance
    data = sensors.readSensors()
    ai_Inputs.sensorData = data 

    # 2. READ CONTROLLER
    pygame.event.pump()
    ctrl_data = controller.poll()

    # 3. VISION INFERENCE
    img = cam.get_frame()
    detections = infer.detect(img)

    # 4. CONTROL LOGIC
    # Case A: Manual Mode (Controller connected AND AI Mode is OFF)
    if controller.connected and not inputState.mode:
        ai_Inputs.driving = False
        active_Cmd = {"L": ctrl_data["L"], "R": ctrl_data["R"]}
    
    # Case B: AI Mode (AI Mode is ON -OR- Controller disconnected)
    else:
        # Update target if we see something
        if detections:
            ai_Inputs.update_target(detections[0])
        else:
            # If nothing seen, we stop driving, BUT we still run move_command below
            ai_Inputs.driving = False

        # ALWAYS run move_command in AI mode. 
        # This ensures we check sensors even if the camera lost the object.
        ai_data = ai_Inputs.move_command()
        active_Cmd = {"L": ai_data["L"], "R": ai_data["R"]}

    # 5. SEND TO MOTORS
    motors.set_power(active_Cmd["L"], active_Cmd["R"])

    # 6. DISPLAY
    display.update_display(
        img,
        detections,
        controller.get_axes(),
        ctrl_data["buttons"],
        (active_Cmd["L"], active_Cmd["R"]),
        data,
        inputState
    )

if __name__ == "__main__":
    main()