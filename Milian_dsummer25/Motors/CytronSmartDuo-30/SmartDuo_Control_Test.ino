#include <Cytron_SmartDriveDuo.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

Adafruit_BNO055 bno = Adafruit_BNO055(55);

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

  Serial.println("Orientation Sensor Test"); Serial.println("");
  
  /* Initialise the sensor */
  if(!bno.begin())
  {
    /* There was a problem detecting the BNO055 ... check your connections */
    Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
    while(1);
  }
  bno.setExtCrystalUse(true);

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

    delay(10);
  }
}
void get_sensor_data() {
  /* Get a new sensor event */ 
  sensors_event_t event; 
  bno.getEvent(&event);
  
  /* Display the floating point data */
  Serial.print("X: ");
  Serial.print(event.orientation.x, 4);
  Serial.print(",")
  Serial.print("\tY: ");
  Serial.print(event.orientation.y, 4);
  Serial.print(",")
  Serial.print("\tZ: ");
  Serial.print(event.orientation.z, 4);
  Serial.println("");
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
