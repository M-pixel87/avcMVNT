#include <Cytron_SmartDriveDuo.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// IMU
Adafruit_BNO055 bno = Adafruit_BNO055(55);

// Motor driver pins
#define IN1 4
#define AN1 5
#define AN2 6
#define IN2 7

Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

// Motor speeds
int speedLeft = 0;
int speedRight = 0;

// Serial input buffer
String inputBuffer = "";

// Timing for IMU output
unsigned long lastIMUSend = 0;
const unsigned long imuInterval = 50; // 20Hz

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
  // --- Handle motor commands (non-blocking parse) ---
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

   

    // Blink
    digitalWrite(13, HIGH);
    delay(5);
    digitalWrite(13, LOW);
  }
}

void sendSensorData() {
  sensors_event_t event;
  bno.getEvent(&event);

  // Clean CSV
  Serial.print("IMU,");
  Serial.print(event.orientation.x, 2);
  Serial.print(",");
  Serial.print(event.orientation.y, 2);
  Serial.print(",");
  Serial.println(event.orientation.z, 2);
}