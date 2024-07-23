#include <Servo.h>

// Create a Servo object for panning the camera
Servo panServo;
int moveon = 0;  // Added semicolon to end the statement

// Define the pin number for the pan servo
const int panServoPin = 12;

// Define the initial and movement range for the pan servo
const int initialPanPosition = 90;  // Center position (0-180 degrees)
const int panMin = 65;
const int panMax = 115;
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
  // Example for testing the servo movement
  for (int i = panMin; i <= panMax; i++) {
    positioncrnt = i;
    panServo.write(positioncrnt);
    Serial.print("Position: ");
    Serial.println(positioncrnt);
    delay(10);  // Small delay to avoid overwhelming the servo
  }
  
  for (int i = panMax; i >= panMin; i--) {
    positioncrnt = i;
    panServo.write(positioncrnt);
    Serial.print("Position: ");
    Serial.println(positioncrnt);
    delay(10);  // Small delay to avoid overwhelming the servo
  }
}
