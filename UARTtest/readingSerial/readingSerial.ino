#include <Servo.h>

// Create Servo objects for controlling the servos
Servo steeringServo; // Servo that controls the angle of the wheel
Servo motorServo;    // Servo that controls the speed of the motor

int defaultSpeed = 58; // Standard speed value (very slow, useful for testing)
int wheeldegree;
float filteredWheelDegree = 90; // Start with the center position (90 degrees)
const float alpha = 0.1; // Smoothing factor for the EMA (Exponential Moving Average)

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

  // Set the ESC to the neutral state (motor servo)
  motorServo.write(90); // 90 degrees corresponds to a neutral signal
  delay(5000);          // Wait for 5 seconds to ensure the ESC recognizes the neutral signal

  Serial.println("Setup complete. Waiting for commands...");
}

void loop() {
  // Example usage: perform different actions based on the received signal
  if (Serial.available() > 0) {
    String value = Serial.readStringUntil('\n');  // Read incoming data until newline
    int RecievedVal = value.toInt();             // Convert the received string to integer
    int calACTION = RecievedVal / 100;           // Extract action (from the first digits)
    int calACTIONAMOUNT = RecievedVal % 100 - 50; // Extract action amount (the degree to which to turn the wheel)

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
      wheeldegree = 90 - value; // Assuming value is offset from center (90)
      filteredWheelDegree = (alpha * wheeldegree) + ((1 - alpha) * filteredWheelDegree); // Apply smoothing filter
      steeringServo.write(filteredWheelDegree);
      Serial.print("Aligning wheels to: ");
      Serial.println(filteredWheelDegree);
      delay(40);
      break;

    case AvoidObstacle:
      // Perform avoid obstacle action
      {
        int pos = map(defaultSpeed, 0, 100, 10, 180); // Assuming 'value' represents a speed percentage
        motorServo.write(pos);
        steeringServo.write(115); // Turn the wheel to avoid obstacle
        Serial.println("Avoiding obstacle...");
        delay(4000);
        motorServo.write(90); // Stop motor after obstacle is avoided
        steeringServo.write(55); // Center the wheel
        delay(10000); // Pause before returning to a neutral state
      }
      break;

    case Stop:
      // Perform stop action
      motorServo.write(90); // Stop the motor
      Serial.println("Stopping the motor.");
      break;

    case Advance:
      // Perform the advance action (moving forward)
      {
        motorServo.write(120); // Move forward at a slow speed
        wheeldegree = 90 - value; // Assuming value is offset from center (90)
        filteredWheelDegree = (alpha * wheeldegree) + ((1 - alpha) * filteredWheelDegree); // Apply smoothing filter
        steeringServo.write(filteredWheelDegree);
        Serial.print("Aligning wheels to: ");
        Serial.println(filteredWheelDegree);
        delay(40);
      }
      break;
  }
}
