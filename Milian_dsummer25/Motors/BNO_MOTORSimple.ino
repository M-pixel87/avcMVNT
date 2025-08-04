#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// === Motor Control Pin Definitions ===
#define IN1 8
#define IN2 7
#define EN 9   // PWM-capable

#define IN3 5
#define IN4 4
#define EN2 6  // PWM-capable

// === Settings ===
const int rampDelay = 10;
const int deadZoneDelay = 250;

// === IMU Setup ===
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Initialize IMU
  if (!bno.begin()) {
    Serial.println("Failed to initialize BNO055. Check wiring or I2C address.");
    while (1);
  }
  bno.setExtCrystalUse(true);
  Serial.println("BNO055 initialized.");

  // Initialize motor pins
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(EN, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(EN2, OUTPUT);
}

void loop() {
  // === Read BNO055 orientation ===
  imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
  Serial.print("Heading: ");
  Serial.print(euler.x());
  Serial.print(" | Roll: ");
  Serial.print(euler.y());
  Serial.print(" | Pitch: ");
  Serial.println(euler.z());

  // === Run motors forward ===
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  setSpeed(EN, 255);
  setSpeed(EN2, 255);
  delay(3000);

  // === Stop motors ===
  setSpeed(EN, 0);
  setSpeed(EN2, 0);
  delay(2000);
}

void setSpeed(int motor, int speed) {
  analogWrite(motor, speed);
  delay(rampDelay);
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
