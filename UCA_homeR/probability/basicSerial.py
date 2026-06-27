import serial
import time

# Connect to the Pico
try:
    ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
    print("Connected to Pico. Listening for data...")
except Exception as e:
    print(f"Could not open port: {e}")
    exit()

while True:
    try:
        # Send a dummy motor command so the Pico's read buffer doesn't freeze
        ser.write(b"0.5 0.5\n")
        
        # Read whatever the Pico spits back
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"PICO SAYS: {line}")
            
        time.sleep(0.1)
        
    except KeyboardInterrupt:
        print("Closing...")
        ser.close()
        break