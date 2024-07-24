#include <Servo.h>

// Create a Servo object for panning the camera
Servo panServo;

// Define the pin number for the pan servo
const int panServoPin = 10;

// Define the initial and movement range for the pan servo
const int initialPanPosition = 90;  // Center position (0-180 degrees)
int position = 90;
const int panMin = 0;
const int panMax = 180;

void setup() {
  // Attach the servo to the pin
  panServo.attach(panServoPin);

  // Initialize the servo to the center position
  panServo.write(initialPanPosition);

  // Start serial communication at 9600 baud rate
  Serial.begin(9600);
}

void loop() {
  // Check if data is available on the serial port
  if (Serial.available() > 0) {
    // Read the incoming string
    String incomingString = Serial.readStringUntil('\n');
    int incomingDeg = incomingString.toInt(); // Convert string to integer

    // Update the position based on the incoming degree value
    if (incomingDeg > 0 && position < panMax) {
      position++;
    } else if (incomingDeg < 0 && position > panMin) {
      position--;
    }
    
    // Write the new position to the servo
    panServo.write(position);
  }

  // Add a small delay to avoid overwhelming the serial buffer
  delay(10);
}
