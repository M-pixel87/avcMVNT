// This code is designed to output a '1' if an object in front of the sensor is too close. It’s up to the Orin to handle that trigger and decide how to respond.
// If the detected object is a blue bucket, the Orin will take care of moving the servo accordingly.
// This part of the code simply detects when an object is close, as you requested.

#include <Wire.h>
#include "LIDARLite_v4LED.h"
LIDARLite_v4LED myLidarLite;
#define FAST_I2C
float distance;
byte lidarLiteAddress = 0x62;
const int ledPin = 2;  

void setup()
{
  pinMode(ledPin, OUTPUT);  
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
        digitalWrite(ledPin, HIGH);  // Triggered
      }
    else{
        digitalWrite(ledPin, LOW);  // No trigger

      }
  }
  
  Serial.print("Sensor distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  delay(100);
}
