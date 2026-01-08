# jetson_to_arduino.py
import serial
import time

# Arduino port, baud, amd serial setup
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

if __name__ == "__main__":
    while True:
        # Example: backward
        set_motors(50, 50)
        time.sleep(2)

        # Example: turn left
        set_motors(-50, 50)
        time.sleep(2)

        # Example: forward
        set_motors(-50, -50)
        time.sleep(2)

        # Stop
        set_motors(0, 0)
        time.sleep(2)
