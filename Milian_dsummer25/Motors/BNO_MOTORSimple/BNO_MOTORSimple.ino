#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// Motor pins
#define IN1 8
#define IN2 7
#define EN 9
#define IN3 5
#define IN4 4
#define EN2 6

// IMU
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

// Timing variables
unsigned long lastIMURead = 0;
unsigned long imuInterval = 100;  // read IMU every 100ms


bool motorsRunning = false;

void setup() {
  Serial.begin(115200);
  delay(1000);

  if (!bno.begin()) {
    Serial.println("BNO055 not detected.");
    while (1);
  }
  bno.setExtCrystalUse(true);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(EN, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(EN2, OUTPUT);
  
  delay(100);
  
}

void loop() {
  unsigned long now = millis();

  // === Read IMU on schedule ===
  if (now - lastIMURead >= imuInterval) {
    lastIMURead = now;
    imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);
    Serial.print("Heading: ");
    Serial.print(euler.x());
    Serial.print(" | Roll: ");
    Serial.print(euler.y());
    Serial.print(" | Pitch: ");
    Serial.println(euler.z());
    
    setMotors(map(euler.z(),-180,180,0,255),map(euler.z(),-180,180,0,255));
  }

  
}

// === Motor control ===
void setMotors(int spd1 , int spd2) {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  delay(100);
  analogWrite(EN, spd1);
  analogWrite(EN2, spd2);
}

void stopMotors() {
  analogWrite(EN, 0);
  analogWrite(EN2, 0);
}
