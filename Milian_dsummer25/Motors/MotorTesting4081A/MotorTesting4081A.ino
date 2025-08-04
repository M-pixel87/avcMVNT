/*
This code is for testing two DC motors using an Arduino.
It allows for changing direction, and speed control using PWM.

*/


#define IN1 8
#define IN2 7
#define EN 9  // Must be a PWM-capable pin

#define IN3 5
#define IN4 4
#define EN2 6  // Must be a PWM-capable pin for second motor

// Settings
const int rampDelay = 10;       // Time between PWM steps (ms)
const int deadZoneDelay = 250;  // Delay after stopping motor (ms)

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(EN, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(EN2, OUTPUT);
}

void loop() {
    // Rotate forward
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);

    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
  
    setSpeed(EN, 255);
    setSpeed(EN2, 255);
    delay(3000);
    setSpeed(EN, 0);
    setSpeed(EN2, 0);
  
    delay(2000);
  
}

void setSpeed(int motor ,int speed) {
    analogWrite(motor, speed);
    delay(rampDelay);
}

void setDirection(int motor, bool forward) {
    if (motor == EN) {
        digitalWrite(IN1, forward ? HIGH : LOW);
        digitalWrite(IN2, forward ? LOW : HIGH);
    } else if (motor == EN2) {
        digitalWrite(IN3, forward ? HIGH : LOW);
        digitalWrite(IN4, forward ? LOW : HIGH);
    }
}
void speedTest(int motor) {
    for (int speed = 0; speed <= 255; speed += 5) {
        analogWrite(motor, speed);
        delay(rampDelay);
    }
    for (int speed = 255; speed >= 0; speed -= 5) {
        analogWrite(motor, speed);
        delay(rampDelay);
    }
}
