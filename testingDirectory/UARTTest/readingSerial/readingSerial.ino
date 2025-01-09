
void setup() {
  Serial.begin(9600);     
  Serial.println("Setup complete. Waiting for commands...");
}

void loop() {
  if (Serial.available() > 0) {
    String value = Serial.readStringUntil('\n');
    int RecievedVal = value.toInt();
            
    Serial.print("Received value: ");
    Serial.println(value);
    Serial.print("Received value to int: ");
    Serial.println(RecievedVal);

  }
}
