#include <Wire.h>
#include "LIDARLite_v4LED.h"
LIDARLite_v4LED myLidarLite;

#define FAST_I2C
float distance;
byte lidarLiteAddress = 0x62;

void setup()
{
  // Initialize Arduino serial port
  Serial.begin(115200);
  // Initialize Arduino I2C (for communication to LidarLite)
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
    // Trigger the next range measurement
    myLidarLite.takeRange();
    // Read new distance data from device registers
    distance = myLidarLite.readDistance();
  }
  
  Serial.print("Sensor distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  delay(100);
}
