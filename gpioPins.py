import Jetson.GPIO as GPIO  # Import the GPIO library for controlling the GPIO pins on the Jetson
import time  # Import the time library for sleep function

# Set the pin numbering mode to the physical pin numbers on the Jetson board
# Using GPIO.BOARD allows us to reference the physical pin numbers directly
# This is more intuitive as it corresponds to the actual pin layout on the board
GPIO.setmode(GPIO.BOARD)

# Pin Definitions
output_pin = 7  # Using physical pin number 12 for output (BCM pin number is 18, which is less relevant here)

# Pin Setup
GPIO.setup(output_pin, GPIO.OUT, initial=GPIO.LOW)  # Set up the pin as an output pin and initialize it to LOW

print("Starting GPIO pin test. Press CTRL+C to exit.")

try:
    while True:
        print("Setting pin HIGH")
        GPIO.output(output_pin, GPIO.HIGH)  # Set the pin to HIGH
        time.sleep(1)  # Wait for 1 second
        print("Setting pin LOW")
        GPIO.output(output_pin, GPIO.LOW)  # Set the pin to LOW
        time.sleep(1)  # Wait for 1 second
except KeyboardInterrupt:
    print("Exiting...")  # Message when exiting the loop

finally:
    GPIO.cleanup()  # Clean up all GPIO settings and reset the pins
    print("GPIO cleanup completed.")  # Confirm that cleanup is complete

# Note: The SPI (Serial Peripheral Interface) is a communication protocol that is indeed available on the Jetson AGX Xavier.
# You can use the Jetson.GPIO library to control SPI pins if needed.

