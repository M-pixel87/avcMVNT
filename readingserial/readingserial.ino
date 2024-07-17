void setup() {
  Serial.begin(9600);  // Start serial communication at 9600 baud rate
}

void loop() {
  if (Serial.available() > 0) {
    // Read the incoming byte:
    int incomingNumber = Serial.parseInt();
    
    // Print the received number to the Serial Monitor
    Serial.print("Received: ");
    Serial.println(incomingNumber);
    
    // Do something with the received number
    // For example, you can use it to control a servo motor
  }
}
