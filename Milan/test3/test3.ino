#include <Servo.h>

// Create Servo objects for controlling the servos
Servo steeringServo; // Servo that controls the angle of the wheel
Servo motorServo;    // Servo that controls the speed of the motor

int defaultSpeed = 58; // Standard speed value is very slow and made for testing anything under 90mapped is backwards 

int wheeldegree;
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

  Serial.println("Setup complete. Waiting for commands...");
}

void loop() {
  // Example usage: perform different actions based on the received signal
  if (Serial.available() > 0) {
    String value = Serial.readStringUntil('\n');
    int RecievedVal = value.toInt(); //raw received value from UART pin
    int calACTION = RecievedVal / 100; // Raw value calculated to find action found in transmission
    int calACTIONAMOUNT = RecievedVal % 100 - 50; // Raw value calculated to find action amount such as the degree to which to turn the wheel

    Serial.print("Received value: ");
    Serial.println(RecievedVal);
    Serial.print("Calculated action: ");
    Serial.println(calACTION);
    Serial.print("Calculated action amount: ");
    Serial.println(calACTIONAMOUNT);

    RobotAction action = static_cast<RobotAction>(calACTION);

    switch (action) {
      case Alignmentmv:
        Serial.println("Performing Alignmentmv action...");
        performAction(Alignmentmv, calACTIONAMOUNT);
        break;
      case AvoidObstacle:
        Serial.println("Performing AvoidObstacle action...");
        performAction(AvoidObstacle, calACTIONAMOUNT);
        break;
      case Stop:
        Serial.println("Performing Stop action...");
        performAction(Stop, calACTIONAMOUNT);
        break;
      case Advance:
        Serial.println("Performing Advance action...");
        performAction(Advance, calACTIONAMOUNT);
        break;
      default:
        Serial.println("Unknown action received.");
        break;
    }
  }
}

void performAction(RobotAction action, int value) {
  switch (action) {
    case Alignmentmv:
      // Perform Alignmentmv action
      wheeldegree = 90 + value;
      steeringServo.write(wheeldegree);
      Serial.print("Aligning wheels to: ");
      Serial.println(wheeldegree);
      delay(40);
      break;

    case AvoidObstacle:
      // Perform avoid obstacle action
      {
        int pos = map(defaultSpeed, 0, 100, 10, 180); // Assuming 'value' represents a speed percentage
        motorServo.write(pos);
        steeringServo.write(115);
        Serial.println("Avoiding obstacle...");
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
      Serial.println("Stopping the motor.");
      break;

    case Advance:
      // Moving forward
      {
        int pos = map(defaultSpeed, 0, 100, 10, 180); // Assuming 'value' represents a speed percentage
        motorServo.write(pos);
        steeringServo.write(90);
        Serial.println("Advancing...");
        delay(50);
      }
      break;
  }
}
