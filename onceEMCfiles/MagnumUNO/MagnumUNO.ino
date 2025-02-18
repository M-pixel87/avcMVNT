// Define motor control pins
#define PIN_Motor_PWMA 5 // PWM pulse for left motor
#define PIN_Motor_PWMB 6 // PWM pulse for right motor
#define PIN_Motor_BIN_1 8 // Digital signal for right motor
#define PIN_Motor_AIN_1 7 // Digital signal for left motor
#define PIN_Motor_STBY 3  // Standby pin

// Function to initialize motor control pins as outputs
void initializeMotorPins() {
  Serial.begin(9600);
  pinMode(PIN_Motor_PWMA, OUTPUT);
  pinMode(PIN_Motor_PWMB, OUTPUT);
  pinMode(PIN_Motor_AIN_1, OUTPUT);
  pinMode(PIN_Motor_BIN_1, OUTPUT);
  pinMode(PIN_Motor_STBY, OUTPUT);
}

void straightenCar() {
  digitalWrite(PIN_Motor_STBY, HIGH);
  digitalWrite(PIN_Motor_AIN_1, low);
  analogWrite(PIN_Motor_PWMA, 150);
  digitalWrite(PIN_Motor_BIN_1, HIGH);
  analogWrite(PIN_Motor_PWMB, 0);
  delay(1800);
}

void setup() {
  // Call the function to initialize motor pins
  initializeMotorPins();

  // Set initial motor direction and speed
  digitalWrite(PIN_Motor_STBY, HIGH);
  digitalWrite(PIN_Motor_AIN_1, HIGH);
  analogWrite(PIN_Motor_PWMA, 255);
  digitalWrite(PIN_Motor_BIN_1, HIGH);
  analogWrite(PIN_Motor_PWMB, 255);

  // Wait for 1 second
  delay(1000);

  // Stop the motor
  analogWrite(PIN_Motor_PWMA, 0);
  digitalWrite(PIN_Motor_STBY, LOW);
  analogWrite(PIN_Motor_PWMB, 0);
}

void loop() {
  if (Serial.available() > 0) {
    // Read the incoming data as a string
    String data = Serial.readStringUntil('\n');
    int value = data.toInt();

    // Turn bot 90 degrees and start realigning with the object
    digitalWrite(PIN_Motor_STBY, HIGH);
    digitalWrite(PIN_Motor_AIN_1, HIGH);
    analogWrite(PIN_Motor_PWMA, 150);
    digitalWrite(PIN_Motor_BIN_1, HIGH);
    analogWrite(PIN_Motor_PWMB, 0);
    delay(1800);

    if (value > 0) {
      digitalWrite(PIN_Motor_AIN_1, LOW);  // Set right to LOW to go backward
      digitalWrite(PIN_Motor_BIN_1, LOW);  // Set left to LOW to go backward
      analogWrite(PIN_Motor_PWMA, 50);
      analogWrite(PIN_Motor_PWMB, 50);
    } else if (value < 0) {
      digitalWrite(PIN_Motor_AIN_1, HIGH);  // Set right to HIGH
      digitalWrite(PIN_Motor_BIN_1, HIGH);  // Set left to HIGH
      analogWrite(PIN_Motor_PWMA, 50);
      analogWrite(PIN_Motor_PWMB, 50);
    }

    // After processing the received data, straighten the car
    straightenCar();
  }
}
