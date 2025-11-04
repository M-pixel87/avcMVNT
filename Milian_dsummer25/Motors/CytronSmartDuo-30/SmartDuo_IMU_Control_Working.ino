
// THIS IS THE CURRENTLY IN USE ARDUINO CODE  


#include <Cytron_SmartDriveDuo.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// --- IMU ---
Adafruit_BNO055 bno = Adafruit_BNO055(55);

// --- Motor driver pins ---
#define IN1 4
#define AN1 5
#define AN2 6
#define IN2 7

Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

// --- Motor speeds ---
int speedLeft = 0;
int speedRight = 0;

// --- Serial input buffer ---
String inputBuffer = "";

// --- Timing for IMU output ---
unsigned long lastIMUSend = 0;
const unsigned long imuInterval = 50; // 20 Hz

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(115200);

  if (!bno.begin()) {
    Serial.println("Ooops, no BNO055 detected ... Check wiring!");
    while (1);
  }
  bno.setExtCrystalUse(true);

  // Startup blink
  digitalWrite(13, HIGH);
  delay(500);
  digitalWrite(13, LOW);
}

void loop() {
  // --- Handle motor commands ---
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      processCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }

  // --- Send IMU data at fixed rate ---
  unsigned long now = millis();
  if (now - lastIMUSend >= imuInterval) {
    sendSensorData();
    lastIMUSend = now;
  }
}

void processCommand(String cmd) {
  // Expect format: "L:<val>,R:<val>"
  int lIndex = cmd.indexOf('L');
  int rIndex = cmd.indexOf('R');
  int commaIndex = cmd.indexOf(',');

  if (lIndex != -1 && rIndex != -1 && commaIndex != -1) {
    int leftVal = cmd.substring(lIndex + 2, commaIndex).toInt();
    int rightVal = cmd.substring(rIndex + 2).toInt();

    speedLeft = constrain(leftVal, -100, 100);
    speedRight = constrain(rightVal, -100, 100);

    smartDriveDuo30.control(speedLeft, speedRight);

    // Blink feedback
    digitalWrite(13, HIGH);
    delay(5);
    digitalWrite(13, LOW);
  }
}

void sendSensorData() {
  // --- Orientation ---
  sensors_event_t event;
  bno.getEvent(&event);

  // --- Linear acceleration (gravity removed) ---
  imu::Vector<3> linAccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);

  // Output both orientation and linear acceleration as a single CSV line:
  // Format: IMU,roll,pitch,yaw,ax,ay,az
  Serial.print("IMU,");
  Serial.print(event.orientation.x, 2); Serial.print(",");  // Roll
  Serial.print(event.orientation.y, 2); Serial.print(",");  // Pitch
  Serial.print(event.orientation.z, 2); Serial.print(",");  // Yaw
  Serial.print(linAccel.x(), 3); Serial.print(",");         // a_x (m/s^2)
  Serial.print(linAccel.y(), 3); Serial.print(",");         // a_y (m/s^2)
  Serial.println(linAccel.z(), 3);                          // a_z (m/s^2)
}