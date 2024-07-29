#include <Servo.h>

// Create Servo objects for controlling the servos
Servo steeringServo; // Servo that controls the angle of the wheel
Servo motorServo;    // Servo that controls the speed of the motor

int defaultSpeed = 58; // Standard speed value is very slow and made for testing anything under 90mapped is backwards 

// Enum for different actions
enum RobotAction {
  Alignmentmv = 1,
  AvoidObstacle = 2,
  Stop = 3,
  Advance = 4
};

// Function declaration for performing actions based on the enum
void performAction(RobotAction action, int value);

void setup() {
  // Attach the servos to their respective pins
  steeringServo.attach(12);
  motorServo.attach(9);

  // Initialize the steering servo to the center position (90 degrees)
  steeringServo.write(90);

  // Start serial communication at 9600 baud rate
  Serial.begin(9600);

  // Set the ESC to the neutral state
  motorServo.write(90); // 90 degrees corresponds to a neutral signal
  delay(5000);          // Wait for 5 seconds to ensure the ESC recognizes the neutral signal
}

void loop() {
  // Example usage: perform different actions based on the received signal
  if (Serial.available() > 0) {
    String value = Serial.readStringUntil('\n');
    int RecievedVal = value.toInt(); //raw revieved value from UART pin
    int calACTION = RecievedVal / 100; //Raw value caltulated to find action found in transmition
    int calACTIONAMOUNT = RecievedVal % 100 - 50; //Raw value caltulated to find action amount such as the degree to which to turn the wheel

    switch (action) {
      case Alignmentmv:
        performAction(Alignmentmv, calACTIONAMOUNT);
        break;
      case AvoidObstacle:
        performAction(AvoidObstacle, calACTIONAMOUNT);
        break;
      case Stop:
        performAction(Stop, calACTIONAMOUNT);
        break;
      case Advance:
        performAction(Advance, calACTIONAMOUNT);
        break;
      default:
        break;
    }
  }
}

void performAction(RobotAction action, int value) {
  switch (action) {
    case Alignmentmv:
      // Perform Alignmentmv action
      int wheeldegree = 90 + value;
      steeringServo.write(wheeldegree);
      delay(40);
      break;

    case AvoidObstacle:
      // Perform avoid obstacle action
      {
        int pos = map(defaultSpeed, 0, 100, 10, 180); // Assuming 'value' represents a speed percentage
        motorServo.write(pos);
        steeringServo.write(115);
        delay(4000);
        motorServo.write(90);
        steeringServo.write(55);
        motorServo.write(pos);
        delay(10000);
      }
      break;

    case Stop:
      // Perform stop action
      motorServo.write(90); // Stop the motor
      break;

    case Advance:
      // Moving forward
      {
        int pos = map(defaultSpeed, 0, 100, 10, 180); // Assuming 'value' represents a speed percentage
        motorServo.write(pos);
        steeringServo.write(90);
        delay(50);
      }
      break;
  }
}
