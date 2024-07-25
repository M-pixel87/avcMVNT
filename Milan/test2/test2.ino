#include <Servo.h>

// Create Servo objects for controlling the servos
Servo wangleServo; // Servo that controls the angle the wheel is on
Servo motorServo;  // Servo that controls the speed of the motor

// Enum for different actions
enum RobotAction {
  Alignmentmv = 1,
  AvoidObstacle = 2,
  Stop = 3,
  Forward = 4
};

// Function declaration for performing actions based on the enum
void performAction(RobotAction action);

void setup() {
  // Attach the servos to their respective pins
  wangleServo.attach(12);
  motorServo.attach(9);

  // Initialize the wheel angle servo to the center position (90 degrees)
  wangleServo.write(90);

  // Start serial communication at 9600 baud rate
  Serial.begin(9600);

  // Set the ESC to the neutral state
  motorServo.write(90); // 90 degrees corresponds to a neutral signal (1500 microsecond pulse width)
  delay(5000);          // Wait for 5 seconds to ensure the ESC recognizes the neutral signal
}

void loop() {
  // Example usage: perform different actions based on the received signal
  if (Serial.available() > 0) {
    String value = Serial.readStringUntil('\n');
    int action = value.toInt();
    switch (action) {
      case Alignmentmv:
        performAction(Alignmentmv);
        break;
      case AvoidObstacle:
        performAction(AvoidObstacle);
        break;
      case Stop:
        performAction(Stop);
        break;
      case Forward:
        performAction(Forward);
        break;
      default:
        break;
    }
  }
}

void performAction(RobotAction action) {
  switch (action) {

    //ANOTHERCASE  
    case Alignmentmv:
      if (Serial.available() > 0) {
        // Perform Alignmentmv action
        // Read a string from the serial input until a newline character
        String value = Serial.readStringUntil('\n');
        // Convert the string value to an integer
        int intValue = value.toInt();
        // Adjust the wheeldegree based on the input value
        int wheeldegree = 90 + intValue;
        // Write the adjusted wheeldegree to the wangle servo
        wangleServo.write(wheeldegree);
        // Wait for 40 milliseconds before the next loop iteration
        delay(40);
      }
      break;

    //ANOTHERCASE  
    case AvoidObstacle:
      // Perform avoid obstacle action
      {
        int val = 58;
        int pos = map(val, 0, 100, 10, 180); // 95 is the zero position of 50 speed
        motorServo.write(pos);               // Write the mapped position to the motor servo
        wangleServo.write(115);
        delay(4000);
        motorServo.write(90);
        wangleServo.write(55);
        motorServo.write(pos);
        delay(10000);
      }
      break;
      
    //ANOTHERCASE  
    case Stop:
      // Perform stop action
      motorServo.write(90); // Stop the motor
      break;
      
    //ANOTHERCASE  
    case Forward:
      // Moving forward
      {
        int val = 58;
        int pos = map(val, 0, 100, 10, 180);
        motorServo.write(pos);
        wangleServo.write(90);
        delay(50);
      }
      break;
  }
}
