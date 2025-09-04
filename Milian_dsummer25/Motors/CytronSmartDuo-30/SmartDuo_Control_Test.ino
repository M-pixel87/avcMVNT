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
 #include <Cytron_SmartDriveDuo.h>

#define IN1 4 // Arduino pin 4 -> MDDS30 IN1
#define AN1 5 // Arduino pin 5 -> MDDS30 AN1
#define AN2 6 // Arduino pin 6 -> MDDS30 AN2
#define IN2 7 // Arduino pin 7 -> MDDS30 IN2

// Using independent PWM mode
Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

signed int speedLeft = 0, speedRight = 0;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600);   // Must match Jetson baud

  digitalWrite(13, HIGH);
  delay(2000);
  digitalWrite(13, LOW);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); // read a full line
    int commaIndex = cmd.indexOf(',');
    Serial.println("RECEIVED");
    if (commaIndex > 0) {
      speedLeft = cmd.substring(0, commaIndex).toInt();
      speedRight = cmd.substring(commaIndex + 1).toInt();
      Serial.println(speedLeft);
      Serial.println(speedRight);
      // clamp to -100 … 100
      speedLeft = constrain(speedLeft, -100, 100);
      speedRight = constrain(speedRight, -100, 100);

      // drive motors
      smartDriveDuo30.control(speedLeft, speedRight);

      digitalWrite(13, HIGH);  // indicate command received
      delay(50);
      digitalWrite(13, LOW);
    }
  }
}

 #include <Cytron_SmartDriveDuo.h>

#define IN1 4 // Arduino pin 4 -> MDDS30 IN1
#define AN1 5 // Arduino pin 5 -> MDDS30 AN1
#define AN2 6 // Arduino pin 6 -> MDDS30 AN2
#define IN2 7 // Arduino pin 7 -> MDDS30 IN2

// Using independent PWM mode
Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

signed int speedLeft = 0, speedRight = 0;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600);   // Must match Jetson baud

  digitalWrite(13, HIGH);
  delay(2000);
  digitalWrite(13, LOW);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); // read a full line
    int commaIndex = cmd.indexOf(',');
    Serial.println("RECEIVED");
    if (commaIndex > 0) {
      speedLeft = cmd.substring(0, commaIndex).toInt();
      speedRight = cmd.substring(commaIndex + 1).toInt();
      Serial.println(speedLeft);
      Serial.println(speedRight);
      // clamp to -100 … 100
      speedLeft = constrain(speedLeft, -100, 100);
      speedRight = constrain(speedRight, -100, 100);

      // drive motors
      smartDriveDuo30.control(speedLeft, speedRight);

      digitalWrite(13, HIGH);  // indicate command received
      delay(50);
      digitalWrite(13, LOW);
    }
  }
}
 #include <Cytron_SmartDriveDuo.h>

#define IN1 4 // Arduino pin 4 -> MDDS30 IN1
#define AN1 5 // Arduino pin 5 -> MDDS30 AN1
#define AN2 6 // Arduino pin 6 -> MDDS30 AN2
#define IN2 7 // Arduino pin 7 -> MDDS30 IN2

// Using independent PWM mode
Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

signed int speedLeft = 0, speedRight = 0;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600);   // Must match Jetson baud

  digitalWrite(13, HIGH);
  delay(2000);
  digitalWrite(13, LOW);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); // read a full line
    int commaIndex = cmd.indexOf(',');
    Serial.println("RECEIVED");
    if (commaIndex > 0) {
      speedLeft = cmd.substring(0, commaIndex).toInt();
      speedRight = cmd.substring(commaIndex + 1).toInt();
      Serial.println(speedLeft);
      Serial.println(speedRight);
      // clamp to -100 … 100
      speedLeft = constrain(speedLeft, -100, 100);
      speedRight = constrain(speedRight, -100, 100);

      // drive motors
      smartDriveDuo30.control(speedLeft, speedRight);

      digitalWrite(13, HIGH);  // indicate command received
      delay(50);
      digitalWrite(13, LOW);
    }
  }
}nd
 #include <Cytron_SmartDriveDuo.h>

#define IN1 4 // Arduino pin 4 -> MDDS30 IN1
#define AN1 5 // Arduino pin 5 -> MDDS30 AN1
#define AN2 6 // Arduino pin 6 -> MDDS30 AN2
#define IN2 7 // Arduino pin 7 -> MDDS30 IN2

// Using independent PWM mode
Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

signed int speedLeft = 0, speedRight = 0;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600);   // Must match Jetson baud

  digitalWrite(13, HIGH);
  delay(2000);
  digitalWrite(13, LOW);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); // read a full line
    int commaIndex = cmd.indexOf(',');
    Serial.println("RECEIVED");
    if (commaIndex > 0) {
      speedLeft = cmd.substring(0, commaIndex).toInt();
      speedRight = cmd.substring(commaIndex + 1).toInt();
      Serial.println(speedLeft);
      Serial.println(speedRight);
      // clamp to -100 … 100
      speedLeft = constrain(speedLeft, -100, 100);
      speedRight = constrain(speedRight, -100, 100);

      // drive motors
      smartDriveDuo30.control(speedLeft, speedRight);

      digitalWrite(13, HIGH);  // indicate command received
      delay(50);
      digitalWrite(13, LOW);
    }
  }
}
}#include <Cytron_SmartDriveDuo.h>

#define IN1 4 // Arduino pin 4 -> MDDS30 IN1
#define AN1 5 // Arduino pin 5 -> MDDS30 AN1
#define AN2 6 // Arduino pin 6 -> MDDS30 AN2
#define IN2 7 // Arduino pin 7 -> MDDS30 IN2

// Using independent PWM mode
Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

signed int speedLeft = 0, speedRight = 0;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600);   // Must match Jetson baud

  digitalWrite(13, HIGH);
  delay(2000);
  digitalWrite(13, LOW);
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); // read a full line
    int commaIndex = cmd.indexOf(',');
    Serial.println("RECEIVED");
    if (commaIndex > 0) {
      speedLeft = cmd.substring(0, commaIndex).toInt();
      speedRight = cmd.substring(commaIndex + 1).toInt();
      Serial.println(speedLeft);
      Serial.println(speedRight);
      // clamp to -100 … 100
      speedLeft = constrain(speedLeft, -100, 100);
      speedRight = constrain(speedRight, -100, 100);

      // drive motors
      smartDriveDuo30.control(speedLeft, speedRight);

      digitalWrite(13, HIGH);  // indicate command received
      delay(50);
      digitalWrite(13, LOW);
    }
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
