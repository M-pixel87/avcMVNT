// How this is read:
// - Bring in the library to control the default frequency/PWM mapping for servos and create an object that uses it.
// - Declare my variables, including using PWM pin 10 for the servo.
// - Set pan max and min as a precaution—sometimes the servo makes noises if maxed out.
// - Create a variable for the current position, which will update with input.  
//   - This also doubles as the initial position (90 degrees), since the range is 0-180.  
// - For those new to the Uno: `void setup()` is the initial code that runs once.  

// Inside `setup()`:
// - Attach the servo object to pin 10, which basically handles the math for converting my input into an output position.
// - Move the servo to the center position (90 degrees) with the first write to pin 10.  
// - The value I’m sending is in ASCII, followed by `\n`, so `incomingDeg.trim();` removes the `\n` at the end.
// - After that:  
//   - If the value is "1" (ASCII), turn right.  
//   - If the value is "2" (ASCII), turn left.  

// The rest of the code is just for debugging and adding a delay to prevent jittering or moving the servo too fast.  
// Author MM

#include <Servo.h>
Servo panServo;

const int panServoPin = 10;
const int panMin = 0;
const int panMax = 180;
int positioncrnt = 90;

void setup() {
  panServo.attach(panServoPin);
  panServo.write(positioncrnt);
  Serial.begin(9600);
}

void loop() {
  while (Serial.available() > 0) {
    String incomingDeg = Serial.readStringUntil('\n');
    incomingDeg.trim();
    if (incomingDeg == "1" && positioncrnt < panMax) {
      positioncrnt++;
    } else if (incomingDeg == "2" && positioncrnt > panMin) {
      positioncrnt--;
    }
    
    Serial.print("Received number: ");
    Serial.println(incomingDeg);
    Serial.println(positioncrnt);
    panServo.write(positioncrnt);
    delay(10); 
  }

