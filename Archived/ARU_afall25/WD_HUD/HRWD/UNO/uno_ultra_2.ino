/*
    This is the newest version as of 02/18/2026 for the uno code, including where it no longer needs the accelerometer present
    and utelizing new connections for an2 and an1
*/


#include <Cytron_SmartDriveDuo.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#include "DFRobot_DF2301Q.h"
#include <SoftwareSerial.h>

// -----------------------------------------------------------------------------
// --------------------------- VOICE MODULE SETUP ------------------------------
// -----------------------------------------------------------------------------

SoftwareSerial softSerial(2, 3); // RX, TX
DFRobot_DF2301Q_UART asr(&softSerial);

// -----------------------------------------------------------------------------
// --------------------------- SENSOR + MOTOR SETUP ----------------------------
// -----------------------------------------------------------------------------

const int RIGHT_TRIG_PIN = 11;
const int RIGHT_ECHO_PIN = 10;
const int LEFT_TRIG_PIN = 13;
const int LEFT_ECHO_PIN = 12;

const float MICROSECONDS_TO_MILLIMETERS = 0.1715;
const long SENSOR_TIMEOUT_US = 2000;
const int MAX_DISTANCE_MM = 220;

Adafruit_BNO055 bno = Adafruit_BNO055(55);
bool bnoOK = false; // <<< ADDED >>>

#define IN1 4
#define AN1 6
#define AN2 5
#define IN2 7

Cytron_SmartDriveDuo smartDriveDuo30(PWM_INDEPENDENT, IN1, IN2, AN1, AN2);

int speedLeft = 0;
int speedRight = 0;
String inputBuffer = "";

// ---- Voice command latch ----
uint8_t activeCMD = 0;

unsigned long lastSensorSend = 0;
const unsigned long sensorInterval = 50;

// -----------------------------------------------------------------------------
// ----------------------------------- SETUP -----------------------------------
// -----------------------------------------------------------------------------

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(115200);
  Serial.println("*Startup serial print test*");
  softSerial.begin(9600);

  // Initialize Voice
  while (!(asr.begin())) {
    delay(500);
  }

  asr.settingCMD(DF2301Q_UART_MSG_CMD_SET_MUTE, 0);
  asr.settingCMD(DF2301Q_UART_MSG_CMD_SET_VOLUME, 10);
  asr.settingCMD(DF2301Q_UART_MSG_CMD_SET_WAKE_TIME, 5);
  asr.playByCMDID(23);
  Serial.println("*Startup serial print test2*");

  // Initialize Sensors
  pinMode(RIGHT_TRIG_PIN, OUTPUT); 
  pinMode(RIGHT_ECHO_PIN, INPUT);
  pinMode(LEFT_TRIG_PIN, OUTPUT); 
  pinMode(LEFT_ECHO_PIN, INPUT);

  Serial.println("*Startup serial print test3*");

  // --------- BNO055 SAFE INIT ---------
  unsigned long startTry = millis();                     // <<< ADDED >>>
  while (!bno.begin() && millis() - startTry < 1500) {   // <<< ADDED >>>
    delay(100);                                          // <<< ADDED >>>
  }

  if (bno.begin()) {                                     // <<< ADDED >>>
    bnoOK = true;                                        // <<< ADDED >>>
    bno.setExtCrystalUse(true);                          // <<< ADDED >>>
    Serial.println("BNO055 detected");                   // <<< ADDED >>>
  } else {                                               // <<< ADDED >>>
    bnoOK = false;                                       // <<< ADDED >>>
    Serial.println("BNO055 NOT detected - running without IMU"); // <<< ADDED >>>
  }
  // -----------------------------------

  digitalWrite(13, HIGH); 
  delay(500); 
  digitalWrite(13, LOW);
  Serial.println("*Startup serial print test5*");
}

// -----------------------------------------------------------------------------
// ----------------------------------- LOOP ------------------------------------
// -----------------------------------------------------------------------------

void loop() {

  // 1. CHECK SERIAL MOTOR COMMANDS
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      processCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }

  // 2. TIMED SENSOR + VOICE UPDATE
  unsigned long now = millis();
  if (now - lastSensorSend >= sensorInterval) {

    // ---- Read DF2301Q ONLY here ----
    uint8_t incomingCMD = asr.getCMDID();
    if (incomingCMD != 0) {
      activeCMD = incomingCMD;
    }

    sendSensorData();
    lastSensorSend = now;
  }

  delay(5);
}

// -----------------------------------------------------------------------------
// --------------------------- FUNCTIONS ---------------------------------------
// -----------------------------------------------------------------------------

void processCommand(String cmd) {
  int lIndex = cmd.indexOf('L');
  int rIndex = cmd.indexOf('R');
  int commaIndex = cmd.indexOf(',');

  if (lIndex != -1 && rIndex != -1 && commaIndex != -1) {
    int leftVal = cmd.substring(lIndex + 2, commaIndex).toInt();
    int rightVal = cmd.substring(rIndex + 2).toInt();

    speedLeft = constrain(leftVal, -100, 100);
    speedRight = constrain(rightVal, -100, 100);

    smartDriveDuo30.control(speedLeft, speedRight);

    digitalWrite(13, HIGH); 
    delay(2); 
    digitalWrite(13, LOW);
  }
}

void sendSensorData() {

  long leftDistance_mm = getDistanceInMillimeters(LEFT_TRIG_PIN, LEFT_ECHO_PIN);
  long rightDistance_mm = getDistanceInMillimeters(RIGHT_TRIG_PIN, RIGHT_ECHO_PIN);

  if (leftDistance_mm == 0 || leftDistance_mm > MAX_DISTANCE_MM)
    leftDistance_mm = MAX_DISTANCE_MM;
  if (rightDistance_mm == 0 || rightDistance_mm > MAX_DISTANCE_MM)
    rightDistance_mm = MAX_DISTANCE_MM;

  sensors_event_t event;
  imu::Vector<3> linAccel;

  if (bnoOK) {                                           // <<< ADDED >>>
    bno.getEvent(&event);                                // <<< ADDED >>>
    linAccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL); // <<< ADDED >>>
  } else {                                               // <<< ADDED >>>
    event.orientation.x = 0;                             // <<< ADDED >>>
    event.orientation.y = 0;                             // <<< ADDED >>>
    event.orientation.z = 0;                             // <<< ADDED >>>
    linAccel = imu::Vector<3>(0, 0, 0);                  // <<< ADDED >>>
  }

  Serial.print("IMU,");
  Serial.print(event.orientation.x, 2); Serial.print(",");
  Serial.print(event.orientation.y, 2); Serial.print(",");
  Serial.print(event.orientation.z, 2); Serial.print(",");

  Serial.print(linAccel.x(), 3); Serial.print(",");
  Serial.print(linAccel.y(), 3); Serial.print(",");
  Serial.print(linAccel.z(), 3); Serial.print(",");

  Serial.print(leftDistance_mm); Serial.print(",");
  Serial.print(rightDistance_mm); Serial.print(",");

  Serial.println(activeCMD);
  activeCMD = 0;
}

long getDistanceInMillimeters(int trigPin, int echoPin) {

  digitalWrite(trigPin, LOW); 
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH); 
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration_microseconds = pulseIn(echoPin, HIGH, SENSOR_TIMEOUT_US);
  return duration_microseconds * MICROSECONDS_TO_MILLIMETERS;
}