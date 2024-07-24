#include <Servo.h>

// Create a Servo object for panning the camera
Servo panServo;
int moveon = 0;  // Added semicolon to end the statement

// Define the pin number for the pan servo
const int panServoPin = 12;

//const int panMin = 65;
//const int panMax = 115;
int positioncrnt = 90;
int wheeldegree=0;
void setup() {
  // Attach the servo to the pin
  panServo.attach(panServoPin);

  // Initialize the servo to the center position
  panServo.write(90);

  // Start serial communication at 9600 baud rate
  Serial.begin(9600);
}

void loop() {
  String value = Serial.readStringUntil('\n');
  int intValue = value.toInt();
  wheeldegree= 90 + intValue;
  panServo.write(wheeldegree);
  delay(10);
}
