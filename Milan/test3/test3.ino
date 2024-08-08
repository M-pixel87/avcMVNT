#include <Servo.h>

// Create Servo objects for controlling the servos
Servo steeringServo;
Servo motorServo;

int defaultSpeed = 58;
int wheeldegree;
float filteredWheelDegree = 90; // Start with the center position (90 degrees)
const float alpha = 0.1; // Smoothing factor for the EMA

// Enum for different actions
enum RobotAction {
  Alignmentmv = 1,
  AvoidObstacle = 2,
  Stop = 3,
  Advance = 4
};

void performAction(RobotAction action, int value);

void setup() {
  steeringServo.attach(12);
  motorServo.attach(9);
  steeringServo.write(90);
  Serial.begin(9600);
  motorServo.write(90);
  delay(5000);
  Serial.println("Setup complete. Waiting for commands...");
}

void loop() {
  if (Serial.available() > 0) {
    String value = Serial.readStringUntil('\n');
    int RecievedVal = value.toInt();
    int calACTION = RecievedVal / 100;
    int calACTIONAMOUNT = RecievedVal % 100 - 50;

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
      wheeldegree = value + 90; // Assuming value is offset from center (90)
      filteredWheelDegree = (alpha * wheeldegree) + ((1 - alpha) * filteredWheelDegree);
      steeringServo.write(filteredWheelDegree);
      Serial.print("Aligning wheels to: ");
      Serial.println(filteredWheelDegree);
      delay(40);
      break;

    case AvoidObstacle:
      int pos = map(defaultSpeed, 0, 100, 10, 180);
      motorServo.write(pos);
      steeringServo.write(115);
      Serial.println("Avoiding obstacle...");
      delay(4000);
      motorServo.write(90);
      steeringServo.write(55);
      motorServo.write(pos);
      delay(10000);
      break;

    case Stop:
      motorServo.write(90);
      Serial.println("Stopping the motor.");
      break;

    case Advance:
      wheeldegree = value + 90; // Assuming value is offset from center (90)
      filteredWheelDegree = (alpha * wheeldegree) + ((1 - alpha) * filteredWheelDegree);
      steeringServo.write(filteredWheelDegree);
      Serial.print("Aligning wheels to: ");
      Serial.println(filteredWheelDegree);
      delay(40);
      break;
  }
}

