import Jetson.GPIO as GPIO  # Import the GPIO library for controlling the GPIO pins on the Jetson
import time  # Import the time library for sleep function
import sys  # Import sys for handling system exit

# Set the pin numbering mode to the physical pin numbers on the Jetson board
GPIO.setmode(GPIO.BOARD)

# Pin Definitions
output_pin = 18  # Using physical pin number 18 for output (BCM pin 18 corresponds to physical pin 12)

# Pin Setup
GPIO.setup(output_pin, GPIO.OUT, initial=GPIO.LOW)  # Set up the pin as an output pin and initialize it to LOW

print("Starting GPIO pin test. Press 'q' to quit.")

try:
    while True:
        print("Setting pin HIGH")
        GPIO.output(output_pin, GPIO.HIGH)  # Set the pin to HIGHq
        time.sleep(1)  # Wait for 1 second

        print("Setting pin LOW")
        GPIO.output(output_pin, GPIO.LOW)  # Set the pin to LOW
        time.sleep(1)  # Wait for 1 second
        print("Setting pin HIGH")
        GPIO.output(output_pin, GPIO.HIGH)  # Set the pin to HIGHq
        time.sleep(1)  # Wait for 1 second

        print("Setting pin LOW")
        GPIO.output(output_pin, GPIO.LOW)  # Set the pin to LOW
        time.sleep(1)  # Wait for 1 second
        print("Setting pin HIGH")
        GPIO.output(output_pin, GPIO.HIGH)  # Set the pin to HIGHq
        time.sleep(1)  # Wait for 1 second

        print("Setting pin LOW")
        GPIO.output(output_pin, GPIO.LOW)  # Set the pin to LOW
        time.sleep(1)  # Wait for 1 second
        print("Setting pin HIGH")
        GPIO.output(output_pin, GPIO.HIGH)  # Set the pin to HIGHq
        time.sleep(1)  # Wait for 1 second

        print("Setting pin LOW")
        GPIO.output(output_pin, GPIO.LOW)  # Set the pin to LOW
        time.sleep(1)  # Wait for 1 second
        print("Setting pin HIGH")
        GPIO.output(output_pin, GPIO.HIGH)  # Set the pin to HIGHq
        time.sleep(1)  # Wait for 1 second

        print("Setting pin LOW")
        GPIO.output(output_pin, GPIO.LOW)  # Set the pin to LOW
        time.sleep(1)  # Wait for 1 second


        # Check if user pressed 'q' to quit
        user_input = input("Press 'q' to quit or any other key to continue: ")
        if user_input.lower() == 'q':
            print("Exiting...")
            break

except KeyboardInterrupt:
    print("Exiting...")  # Message when exiting the loop due to Ctrl+C

finally:
    GPIO.cleanup()  # Clean up all GPIO settings and reset the pins
    print("GPIO cleanup completed.")  # Confirm that cleanup is complete
