# jetson_to_arduino.py
import serial
import time
import pygame

# Arduino serial setup
PORT = "/dev/ttyACM0"
BAUD = 9600
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # wait for Arduino reset

def set_motors(left_speed, right_speed):
    """
    left_speed, right_speed: range -100 to 100 (percentage of max speed)
    """
    command = f"{left_speed},{right_speed}\n"
    ser.write(command.encode("utf-8"))
    print(f"Sent: {command.strip()}")

def scale_axis(val):
    """Convert joystick axis (-1.0 to 1.0) to motor speed (-100 to 100)."""
    return int(val * 100)

def main():
    # Initialize pygame for controller
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("⚠️ No controller detected. Make sure Xbox controller is paired over Bluetooth.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"✅ Connected to controller: {joystick.get_name()}")

    try:
        while True:
            pygame.event.pump()  # update events

            # Read joystick values
            left_y = joystick.get_axis(1)   # Left stick vertical
            right_y = joystick.get_axis(3)  # Right stick vertical
            but1 = joystick.get_axis(5)
            but2 = joystick.get_axis(6)
            # In many controllers, pushing stick forward = -1.0
            left_speed = -scale_axis(left_y)
            right_speed = -scale_axis(right_y)

            # Send to Arduino
            if(abs(left_speed) < 10):
                left_speed = 0
            
            if(abs(right_speed) < 10):
                right_speed = 0

            set_motors(-left_speed, -right_speed)
            time.sleep(0.1)  # adjust refresh rate

    except KeyboardInterrupt:
        print("\nStopping motors...")
        set_motors(0, 0)

if __name__ == "__main__":
    main()

