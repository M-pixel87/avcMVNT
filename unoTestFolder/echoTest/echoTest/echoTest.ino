#define TRIG_PIN 9  // Define trigger pin
#define ECHO_PIN 10 // Define echo pin

#define FLAG_PIN 13  // Optional: Use this pin for an LED or indicator when flag is set
#define TARGET_DISTANCE_CM 100  // 1 meter = 100 cm
#define DISTANCE_TOLERANCE_CM 5  // +/- 5 cm tolerance range around 1 meter

bool flag = false;  // Flag for 1-meter distance

void setup() {
  Serial.begin(9600);  // Initialize serial communication
  pinMode(TRIG_PIN, OUTPUT);  // Set trigger pin as output
  pinMode(ECHO_PIN, INPUT);   // Set echo pin as input
  pinMode(FLAG_PIN, OUTPUT);  // Set FLAG_PIN as output for indicator (optional)
}

void loop() {
  long duration, distance;

  // Send a 10 microsecond pulse to trigger the sensor
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Measure the duration of the echo pulse
  duration = pulseIn(ECHO_PIN, HIGH); // Time the echo pulse is HIGH

  // Calculate the distance (duration in microseconds)
  distance = (duration / 2) / 29.1;  // Divide by 2 for round trip and then by 29.1 to convert to cm

  // Print the distance to the Serial Monitor
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  // Check if the object is approximately 1 meter (100 cm) away
  if (distance >= TARGET_DISTANCE_CM - DISTANCE_TOLERANCE_CM && distance <= TARGET_DISTANCE_CM + DISTANCE_TOLERANCE_CM) {
    flag = true;  // Set flag when distance is close to 1 meter
    digitalWrite(FLAG_PIN, HIGH);  // Turn on the FLAG_PIN (optional, for LED or indicator)
  } else {
    flag = false;  // Reset flag when distance is not near 1 meter
    digitalWrite(FLAG_PIN, LOW);  // Turn off the FLAG_PIN (optional)
  }

  delay(500);  // Wait for half a second before taking another reading
}
