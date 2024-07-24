//this code aligns a servo mounted cam to the center of a bucket
#include <Servo.h>

// Create a Servo object for panning the camera
Servo panServo;
int moveon = 0;  // Added semicolon to end the statement

// Define the pin number for the pan servo
const int panServoPin = 10;

// Define the initial and movement range for the pan servo
const int initialPanPosition = 90;  // Center position (0-180 degrees)
const int panMin = 0;
const int panMax = 180;
int positioncrnt = 90;

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
  while (Serial.available() > 0) {
    // Read the incoming string until a newline character
    String incomingDeg = Serial.readStringUntil('\n');
    
    // Trim any leading or trailing whitespace
    incomingDeg.trim();

    // Update the position based on the incoming degree value
    if (incomingDeg == "1" && positioncrnt < panMax) {
      positioncrnt++;
    } else if (incomingDeg == "2" && positioncrnt > panMin) {
      positioncrnt--;
    }
    
    Serial.print("Received number: ");
    Serial.println(incomingDeg);
    Serial.println(positioncrnt);
    
    // Write the new position to the servo
    panServo.write(positioncrnt);
    delay(10);  // Small delay to avoid overwhelming the serial buffer
  }

  // This line will always execute, incrementing `moveon` continuously if no serial data is available
}
