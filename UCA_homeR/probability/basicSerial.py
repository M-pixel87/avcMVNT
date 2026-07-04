'''
This code is just for sending basic commands to a microcontroller, primarily to the pico2
on the homer robat for motor control commands in the format : speed_right speed_left
'''


import serial
import time

reading = False

# Connect to the Pico
try:
    ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
    print("Connected to Pico. Listening for data...")
except Exception as e:
    print(f"Could not open port: {e}")
    exit()

while True:
    try:
        command = input() + "\n"
        bcommand = command.encode("utf-8")
        ser.write(bcommand)
        
        # Read whatever the Pico spits back
        if ser.in_waiting > 0 and reading:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"PICO SAYS: {line}")
            
        time.sleep(0.1)
        
    except KeyboardInterrupt:
        print("Closing...")
        ser.close()
        break