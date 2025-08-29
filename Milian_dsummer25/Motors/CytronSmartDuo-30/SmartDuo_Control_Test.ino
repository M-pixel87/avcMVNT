#include <Cytron_SmartDriveDuo.h>

#define IN1 4
#define AN1 5
#define AN2 6
#define IN2 7

Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

signed int speedLeft = 0, speedRight = 0;

String inputString = "";   // buffer for serial input
bool stringComplete = false;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600);

  digitalWrite(13, HIGH);
  delay(2000);
  digitalWrite(13, LOW);
}

void loop() {
  // Process command only when a full line is ready
  if (stringComplete) {
    int commaIndex = inputString.indexOf(',');
    if (commaIndex > 0) {
      int left = inputString.substring(0, commaIndex).toInt();
      int right = inputString.substring(commaIndex + 1).toInt();

      // clamp -100 … 100
      speedLeft = constrain(left, -100, 100);
      speedRight = constrain(right, -100, 100);

      smartDriveDuo30.control(speedLeft, speedRight);

      digitalWrite(13, HIGH);
      delay(20);  // small blink
      digitalWrite(13, LOW);
    }

    inputString = "";
    stringComplete = false; // ready for next command
  }
}

// This runs whenever serial data comes in
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}
