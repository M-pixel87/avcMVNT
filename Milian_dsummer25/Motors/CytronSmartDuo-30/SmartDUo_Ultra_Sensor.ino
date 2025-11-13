#include <Cytron_SmartDriveDuo.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

// --- Sensor Pin Definitions ---
const int RIGHT_TRIG_PIN = 11;
const int RIGHT_ECHO_PIN = 10;
const int LEFT_TRIG_PIN = 9;
const int LEFT_ECHO_PIN = 8;

// --- Sensor Constants ---
const float MICROSECONDS_TO_MILLIMETERS = 0.1715;
// We want to cap at 220mm.
// Time = (2 * 220mm) / 0.343 mm/us = ~1283 us.
// We'll use 2000us (2ms) as a safe timeout.
const long SENSOR_TIMEOUT_US = 2000;
const int MAX_DISTANCE_MM = 220; // Your 220mm cap

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

// --- Timing for Sensor output ---
unsigned long lastSensorSend = 0;
const unsigned long sensorInterval = 50; // 20 Hz (was imuInterval)

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(115200);

  // --- Initialize Ultrasonic Sensor Pins ---
  pinMode(RIGHT_TRIG_PIN, OUTPUT);
  pinMode(RIGHT_ECHO_PIN, INPUT);
  pinMode(LEFT_TRIG_PIN, OUTPUT);
  pinMode(LEFT_ECHO_PIN, INPUT);

  // --- Initialize IMU ---
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
  // --- Handle incoming motor commands ---
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      processCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }

  // --- Send Sensor data (IMU + Ultrasonic) at a fixed rate ---
  unsigned long now = millis();
  if (now - lastSensorSend >= sensorInterval) {
    sendSensorData();
    lastSensorSend = now;
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




//sending that message here
    smartDriveDuo30.control(speedLeft, speedRight);

    // Blink feedback
    digitalWrite(13, HIGH);
    delay(5); // This is still a small blocking delay, but okay
    digitalWrite(13, LOW);
  }
}

/**
 * @brief Triggers a sensor and measures the distance with a timeout.
 * @param trigPin The sensor's TRIGGER pin.
 * @param echoPin The sensor's ECHO pin.
 * @return The distance in millimeters (mm). Returns 0 if timeout.
 */
long getDistanceInMillimeters(int trigPin, int echoPin) {
  // --- Trigger Pulse ---
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // --- Read Echo with Timeout ---
  // This is the CRITICAL change.
  // We wait a maximum of SENSOR_TIMEOUT_US microseconds.
  long duration_microseconds = pulseIn(echoPin, HIGH, SENSOR_TIMEOUT_US);

  // --- Calculate Distance ---
  long distance_mm = duration_microseconds * MICROSECONDS_TO_MILLIMETERS;
  return distance_mm;
}

/**
 * @brief Reads all sensors (IMU, Ultrasonics) and sends them via UART.
 */
void sendSensorData() {
  // --- 1. Read Ultrasonic Sensors ---
  long leftDistance_mm = getDistanceInMillimeters(LEFT_TRIG_PIN, LEFT_ECHO_PIN);
  long rightDistance_mm = getDistanceInMillimeters(RIGHT_TRIG_PIN, RIGHT_ECHO_PIN);





  // --- 2. Apply Capping Logic ---
  // If distance is 0 (from timeout) or > MAX_DISTANCE_MM,
  // cap it to MAX_DISTANCE_MM.
  if (leftDistance_mm == 0 || leftDistance_mm > MAX_DISTANCE_MM) {
    leftDistance_mm = MAX_DISTANCE_MM;
  }
  if (rightDistance_mm == 0 || rightDistance_mm > MAX_DISTANCE_MM) {
    rightDistance_mm = MAX_DISTANCE_MM;
  }
  // Now, leftDistance_mm and rightDistance_mm are 3-digit-friendly
  // (or at least capped at 220).





  // --- 3. Read IMU ---
  sensors_event_t event;
  bno.getEvent(&event);
  imu::Vector<3> linAccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);

  // --- 4. Send Combined UART Message ---
  // Format: IMU,roll,pitch,yaw,ax,ay,az,left_mm,right_mm
  Serial.print("IMU,");
  Serial.print(event.orientation.x, 2); Serial.print(","); // Roll
  Serial.print(event.orientation.y, 2); Serial.print(","); // Pitch
  Serial.print(event.orientation.z, 2); Serial.print(","); // Yaw
  Serial.print(linAccel.x(), 3); Serial.print(",");       // a_x
  Serial.print(linAccel.y(), 3); Serial.print(",");       // a_y
  Serial.print(linAccel.z(), 3); Serial.print(",");       // a_z
  
  // Add the ultrasonic data to the end of the line
  Serial.print(leftDistance_mm); Serial.print(",");       // Left MM
  Serial.println(rightDistance_mm);                      // Right MM (ends the line)
}