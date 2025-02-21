// This code is designed to output a '0' if an object in front of the sensor is too close. It’s up to the Orin to handle that trigger and decide how to respond.
// If the detected object is a blue bucket, the Orin will take care of moving the servo accordingly.
// This part of the code simply detects when an object is close, as you requested.
// To use the car place hand in front of lidar first to set a 0 
#include <Wire.h>
#include "LIDARLite_v4LED.h"
LIDARLite_v4LED myLidarLite;
#define FAST_I2C
float distance;
byte lidarLiteAddress = 0x62;
const int distanctAlertPin = 2;  
const int safteyPin = 3;  

void setup() {
  //this is the new testest stuff
  pinMode(distanctAlertPin, OUTPUT);
  pinMode(safteyPin, INPUT);
  digitalWrite(distanctAlertPin, LOW);  //makes the orin stay in the loop of not ready to start unless this was reset properly
  int setUpRead = digitalRead(safteyPin); 
  if (setUpRead == 0) {
    while (true) {
    }
  }
  digitalWrite(distanctAlertPin, HIGH);  
  //end of the RandD

  Serial.begin(115200);
  Wire.begin();
  
  // Set I2C frequency to 400kHz for compatible boards (e.g., Arduino Due)
#ifdef FAST_I2C
#if ARDUINO >= 157
  Wire.setClock(400000UL); // Set I2C frequency to 400kHz (for Arduino Due)
#else
  TWBR = ((F_CPU / 400000UL) - 16) / 2; // Set I2C frequency to 400kHz
#endif
#endif
  
  // Configure the LIDARLite device
  myLidarLite.configure(0);


  // Optional: Add an I2C address scan to ensure the device is connected
  Serial.println("Scanning I2C bus...");
  for (byte address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.print("Found device at address 0x");
      Serial.println(address, HEX);
    }
  }



}

void loop()
{
  if (myLidarLite.getBusyFlag() == 0)
  {
    myLidarLite.takeRange();
    distance = myLidarLite.readDistance();
    if (distance <= 170 )
    {
        digitalWrite(distanctAlertPin, LOW);  // Triggered
      }
    else{
        digitalWrite(distanctAlertPin, HIGH);  // No trigger

      }
  }
  
  Serial.print("Sensor distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  delay(100);
}
