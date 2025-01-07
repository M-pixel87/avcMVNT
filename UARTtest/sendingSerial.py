import serial
import time

# Initialize the serial communication with the desired settings
ser = serial.Serial(
    port='/dev/ttyTHS0',     # Change this to the appropriate port
    baudrate=9600,           # Baud rate: 9600
    parity=serial.PARITY_EVEN,  # Set parity to even
    stopbits=serial.STOPBITS_ONE,  # 1 stop bit
    bytesize=8,              # 8 data bits
)

AvoidObstacle = 250
Stop = 350
obsticalsAvoided = 0
SVal = 150  # Example value

def count_up_to_999():
    global obsticalsAvoided  # Indicate that we're modifying the global variable
    counter = 0
    while True:
        print(counter)  # Print current count
        counter += 1
        if counter > 999:  # Reset counter after 999
            counter = 0

        # Send the current counter value over serial
        ser.write(f"{counter}\n".encode())  # Send as bytes

        time.sleep(0.08)  # Wait for 80 milliseconds

        # Example of condition to trigger actions (AvoidObstacle and Stop)
        if counter == 500:  # For example, send AvoidObstacle action at count 500
            ser.write(f"{AvoidObstacle}\n".encode())
            obsticalsAvoided += 1

        if obsticalsAvoided == 1:  # Stop action after 1 obstacle avoided
            ser.write(f"{Stop}\n".encode())
            break  # Exit loop after stopping action

# Call the function to start counting
count_up_to_999()

# After the loop or when done, close the serial port
ser.close()
