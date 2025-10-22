// 1. INCLUDE ALL LIBRARIES
// ===================================
#include "Arduino_LED_Matrix.h" // For the 12x8 LED grid
#include <Wire.h>               // For I2C communication
#include "LIDARLite_v4LED.h"    // For the LIDAR sensor

// 2. DEFINE ALL GLOBAL VARIABLES
// ===================================

// --- Project Comments ---
// This code is designed to output a '0' if an object in front of the sensor is too close. It’s up to the Orin to handle that trigger and decide how to respond.
// If the detected object is a blue bucket, the Orin will take care of moving the servo accordingly.
// This part of the code simply detects when an object is close, as you requested.
// To use the car place hand in front of lidar first to set a 0

// --- LIDAR Variables ---
LIDARLite_v4LED myLidarLite;
float distance;
byte lidarLiteAddress = 0x62;
const int distanceAlertPin = 2; // This pin will act as the triger for the lidar
const int safteyPin = 3; // We set this pin as a VAR to act as the turn on signal initally for the orin

// --- LED Matrix Variables ---
ArduinoLEDMatrix matrix; 

// Define all frames (digits 0-9 and a blank screen)
const uint32_t BLANK[3] = { 0x0, 0x0, 0x0 };
const uint32_t DIGIT_0[3] = { 0x1c0701c, 0x0, 0x0 };
const uint32_t DIGIT_1[3] = { 0x4040404, 0x0, 0x0 };
const uint32_t DIGIT_2[3] = { 0x1c0201c, 0x1, 0x0 };
const uint32_t DIGIT_3[3] = { 0x1c0201c, 0x2, 0x0 };
const uint32_t DIGIT_4[3] = { 0x7040704, 0x0, 0x0 };
const uint32_t DIGIT_5[3] = { 0x1c0101c, 0x2, 0x0 };
const uint32_t DIGIT_6[3] = { 0x1c0101c, 0x1, 0x0 };
const uint32_t DIGIT_7[3] = { 0x4040404, 0x1c, 0x0 };
const uint32_t DIGIT_8[3] = { 0x1c0701c, 0x1c, 0x0 };
const uint32_t DIGIT_9[3] = { 0x7040704, 0x1c, 0x0 };

// Store all the digit frames in a single "lookup" array 
// Something that might not be clear is that these addresses for LEDS
// Can be shown in a Matrix so these with out a regi shift will only show the
// First 3 leds changing
const uint32_t FONT[10][3] = {
  { 0x1c0701c, 0x0, 0x0 }, // 0
  { 0x4040404, 0x0, 0x0 }, // 1
  { 0x1c0201c, 0x1, 0x0 }, // 2
  { 0x1c0201c, 0x2, 0x0 }, // 3
  { 0x7040704, 0x0, 0x0 }, // 4
  { 0x1c0101c, 0x2, 0x0 }, // 5
  { 0x1c0101c, 0x1, 0x0 }, // 6
  { 0x4040404, 0x1c, 0x0 }, // 7
  { 0x1c0701c, 0x1c, 0x0 }, // 8
  { 0x7040704, 0x1c, 0x0 }  // 9
};



// 3. SINGLE SETUP FUNCTION
// ===================================
void setup() {
  // --- Serial and Pin Setup ---
  Serial.begin(115200);
  pinMode(distanceAlertPin, OUTPUT);
  pinMode(safteyPin, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(safteyPin, HIGH); // this tells my orin to start

  // --- I2C and LIDAR Setup ---
  Wire.begin();

  // Set I2C to 400kHz
#if ARDUINO >= 157
  Wire.setClock(400000UL);
#else
  TWBR = ((F_CPU / 400000UL) - 16) / 2;
#endif

  // Configure the LIDARLite device
  myLidarLite.configure(0);

  // --- I2C Scan (for debugging, can be removed later) ---
  Serial.println("Scanning I2C bus...");
  for (byte address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.print("Found device at address 0x");
      Serial.println(address, HEX);
    }
  }
  Serial.println("I2C Scan Complete.");

  // --- LED Matrix Setup ---
  matrix.begin();
  Serial.println("Setup Complete. Starting loop...");
}

// 4. MAIN LOOP
// ===================================
void loop() {
  if (myLidarLite.getBusyFlag() == 0) {
    // 1. Take LIDAR measurement
    myLidarLite.takeRange();
    distance = myLidarLite.readDistance();

    // 2. Check distance and set alert pins
    if (distance <= 170) {
      digitalWrite(distanceAlertPin, HIGH); // Triggered
      digitalWrite(LED_BUILTIN, HIGH);    // Turn on built-in LED
    } else {
      digitalWrite(distanceAlertPin, LOW); // No trigger
      digitalWrite(LED_BUILTIN, LOW);     // Turn off built-in LED
    }

    // 3. Display the distance on the LED Matrix
    // We cast the 'float' distance to an 'int' for the display function
    displayDigits((int)distance);

    // 4. Print distance to Serial Monitor
    Serial.print("Sensor distance: ");
    Serial.print(distance);
    Serial.println(" cm");
  }

  delay(100);
}


// 5. HELPER FUNCTION (Unchanged)
// ===================================
/**
 * @brief Displays a 3-digit number on the 12x8 LED grid.
 * @param number The number to display. If > 999 or < 0, shows a blank screen.
 */
void displayDigits(int number) {

  // --- This is your "out of bounds" check ---
  if (number < 0 || number > 999) {
    matrix.loadFrame(BLANK); // Load the all-off frame
    return;                  // Exit the function
  }

  // Break the number into its three digits
  // Example: number = 365
  int d1 = (number / 100) % 10; // Hundreds digit: 3
  int d2 = (number / 10) % 10;  // Tens digit: 6
  int d3 = (number / 1) % 10;   // Ones digit: 5

  // Create a new, blank frame to draw our 3 digits onto
  uint32_t frame[3] = { 0, 0, 0 };

  // Combine the digit for the first position (hundreds)
  frame[0] = FONT[d1][0];
  frame[1] = FONT[d1][1];
  frame[2] = FONT[d1][2];

  // Combine the digit for the second position (tens), shifted 4 pixels to the left
  frame[0] |= (FONT[d2][0] << 4);
  frame[1] |= (FONT[d2][1] << 4);
  frame[2] |= (FONT[d2][2] << 4);

  // Combine the digit for the third position (ones), shifted 8 pixels to the left
  frame[0] |= (FONT[d3][0] << 8);
  frame[1] |= (FONT[d3][1] << 8);
  frame[2] |= (FONT[d3][2] << 8);

  // Finally, display the combined frame
  matrix.loadFrame(frame);
}