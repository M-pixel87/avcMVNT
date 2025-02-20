#include <Servo.h>

#define PIN_Servo 10

// Create servo object to control a servo
Servo myservo;

// Define motor control pins
#define PIN_Motor_PWMA 5 // PWM pulse for left motor
#define PIN_Motor_PWMB 6 // PWM pulse for right motor
#define PIN_Motor_BIN_1 8 // Digital signal for right motor
#define PIN_Motor_AIN_1 7 // Digital signal for left motor
#define PIN_Motor_STBY 3  // Standby pin

int trnd = 0; // Initialize the turn indicator

// Function to initialize motor control pins as outputs
void initializeMotorPins() {
  Serial.begin(9600);
  pinMode(PIN_Motor_PWMA, OUTPUT);
  pinMode(PIN_Motor_PWMB, OUTPUT);
  pinMode(PIN_Motor_AIN_1, OUTPUT);
  pinMode(PIN_Motor_BIN_1, OUTPUT);
  pinMode(PIN_Motor_STBY, OUTPUT);
}

// Function to initialize the servo
void initializeServo(int initialAngle) {
  myservo.attach(PIN_Servo, 500, 2400); // 500: 0 degree, 2400: 180 degree
  myservo.write(initialAngle); // Set the servo to the initial angle
  delay(500);
}

// Function to control the servo
void controlServo(int angle) {
  myservo.attach(PIN_Servo);
  myservo.write(angle); // Set the servo to the desired angle
  delay(450);
  myservo.detach();
}

// Function to straighten the car
void straightenCar() {
  digitalWrite(PIN_Motor_STBY, HIGH);
  digitalWrite(PIN_Motor_AIN_1, LOW);
  analogWrite(PIN_Motor_PWMA, 150);
  digitalWrite(PIN_Motor_BIN_1, HIGH);
  analogWrite(PIN_Motor_PWMB, 0);
  delay(1800);
  digitalWrite(PIN_Motor_STBY, LOW); // Stop the motor after straightening
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

  // Initialize servo at 90 degrees
  initializeServo(90);
}

void loop() {
  if (Serial.available() > 0) {
    // Read the incoming data as an integer
    int value = Serial.parseInt();
    Serial.print(value);

    if (trnd == 0) {
      // Turn bot 90 degrees and start realigning with the object
      digitalWrite(PIN_Motor_STBY, HIGH);
      digitalWrite(PIN_Motor_AIN_1, HIGH);
      analogWrite(PIN_Motor_PWMA, 150);
      digitalWrite(PIN_Motor_BIN_1, HIGH);
      analogWrite(PIN_Motor_PWMB, 0);
      controlServo(180); // Rotate to 180 degrees
      delay(1800);
      // Stop motors after turn
      digitalWrite(PIN_Motor_AIN_1, HIGH);
      analogWrite(PIN_Motor_PWMA, 0);
      digitalWrite(PIN_Motor_BIN_1, HIGH);
      analogWrite(PIN_Motor_PWMB, 0);

      trnd = 1; // Set turn indicator
    }

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
  }

  if (trnd == 1) {
    straightenCar();
    trnd = 0; // Reset turn indicator
  }
}
