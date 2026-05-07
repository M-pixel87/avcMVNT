/*
  HC-SR04 Ultrasonic Sensor + Arduino Uno R4 WiFi LED Matrix Display

  This sketch measures distance using an HC-SR04 ultrasonic sensor
  and displays the result in millimeters (mm) on the built-in
  12x8 LED matrix.

  It displays the numeric value and will show "MAX" if the distance
  is greater than 220mm, as requested.

  Wiring the HC-SR04 Sensor:
  - VCC pin -> 5V on Arduino
  - GND pin -> GND on Arduino
  - Trig pin -> Digital Pin 7 on Arduino
  - Echo pin -> Digital Pin 8 on Arduino
  
  [Image of HC-SR04 ultrasonic sensor wiring to an Arduino]
*/

// Include the libraries for the LED Matrix
#include "ArduinoGraphics.h"
#include "Arduino_LED_Matrix.h"

// Create an instance of the LED matrix
Arduino_LED_Matrix matrix;

// Define the pins for the ultrasonic sensor
const int trigPin = 7; // Trigger pin
const int echoPin = 8; // Echo pin

// Define the maximum distance to display a number for
const int maxDistanceMm = 220;

void setup() {
  // Initialize Serial Monitor for debugging (optional)
  // You can open the Serial Monitor (Tools > Serial Monitor)
  // to see the raw distance values.
  Serial.begin(9600);

  // Set the pin modes for the sensor
  pinMode(trigPin, OUTPUT); // Trig pin sends a pulse
  pinMode(echoPin, INPUT);  // Echo pin reads the return pulse

  // Initialize the LED matrix
  matrix.begin();
}

void loop() {
  // Get the current distance in millimeters from our function
  long distance = getDistanceInMm();

  // Print the distance to the Serial Monitor for debugging
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" mm");

  // Create the text string to display
  String displayText;
  if (distance > maxDistanceMm) {
    displayText = "MAX"; // Display "MAX" if over 220mm
  } else {
    displayText = String(distance); // Convert the number to a String
  }

  // Clear the matrix display before writing new text
  matrix.clear();

  /*
    Display the text.
    We use matrix.textScroll() because numbers with 3 digits
    (like "220") won't fit on the 12x8 matrix statically.
    textScroll() will scroll the text across the display.

    The second parameter (80) is the scroll speed in milliseconds.
    A lower number is faster.
  */
  matrix.textScroll(displayText, 80);
  
  // Wait for 200 milliseconds before taking the next reading
  // This prevents the display from flickering too fast.
  delay(200);
}

/**
   @brief Measures distance using the HC-SR04 sensor.
   @return The distance in millimeters (mm).
*/
long getDistanceInMm() {
  // --- Send the Trigger Pulse ---
  // Ensure the trigger pin is low for a clean pulse
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Send a 10-microsecond HIGH pulse to trigger the sensor
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // --- Read the Echo Pulse ---
  // Read the duration of the HIGH pulse on the echo pin
  // pulseIn() waits for the pin to go HIGH, times the pulse, 
  // and waits for it to go LOW.
  // The duration is in microseconds.
  long duration = pulseIn(echoPin, HIGH);

  // --- Calculate the Distance ---
  // Speed of sound is approx 343 meters/second.
  // This is 0.343 millimeters/microsecond.
  // The pulse travels there and back, so we divide the total time by 2.
  // Distance = (Duration * 0.343) / 2
  //
  // To avoid using floating-point math, we can rewrite:
  // Distance = (Duration * 343) / 2000
  long distance = (duration * 343) / 2000;

  return distance;
}
