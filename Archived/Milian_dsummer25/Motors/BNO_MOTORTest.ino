#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// BNO055 setup
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

// Motor pins (adjust to your actual wiring)
const int EN_PIN = 3;     // Enable pin (PWM)
const int IN1_PIN = 4;    // Direction input 1
const int IN2_PIN = 5;    // Direction input 2

void setup() {
  Serial.begin(115200);
  delay(1000);

  // BNO055 Initialization
  if (!bno.begin()) {
    Serial.println("Failed to initialize BNO055!");
    while (1);
  }
  bno.setExtCrystalUse(true);
  Serial.println("BNO055 initialized.");

  // Motor control pins
  pinMode(EN_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  // Initialize motor off
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(EN_PIN, 0);  // 0% duty cycle = motor off
}

void loop() {
  // === Read BNO055 data ===
  imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
  Serial.print("Heading: ");
  Serial.print(euler.x());
  Serial.print(" | Roll: ");
  Serial.print(euler.y());
  Serial.print(" | Pitch: ");
  Serial.println(euler.z());

  // === Motor control logic ===
  // For example, move forward slowly if pitch is level
  if (abs(euler.z()) < 10) {  // If pitch ~ 0 deg
    digitalWrite(IN1_PIN, HIGH);
    digitalWrite(IN2_PIN, LOW);
    analogWrite(EN_PIN, 100);  // 100/255 PWM
  } else {
    // Stop or reverse if tilted
    digitalWrite(IN1_PIN, LOW);
    digitalWrite(IN2_PIN, LOW);
    analogWrite(EN_PIN, 0);
  }

  delay(500);  // Adjust refresh rate as needed
}
