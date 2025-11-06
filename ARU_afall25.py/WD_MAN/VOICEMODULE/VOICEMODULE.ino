#include "DFRobot_DF2301Q.h"

/**
@brief DFRobot_URM13_RTU constructor
@param serial - serial ports for communication, supporting hard and soft serial ports
@param rx - UART The pin for receiving data
@param tx - UART The pin for transmitting data
*/
#if (defined(ARDUINO_AVR_UNO) || defined(ESP8266)) // Use software serial
SoftwareSerial softSerial(/*rx =*/0, /*tx =*/1);
DFRobot_DF2301Q_UART asr(/*softSerial =*/&softSerial);
#elif defined(ESP32) // Use the hardware serial with remappable pin: Serial1
DFRobot_DF2301Q_UART asr(/*hardSerial =*/&Serial1, /*rx =*/11, /*tx =*/12);
#else // Use hardware serial: Serial1
DFRobot_DF2301Q_UART asr(/*hardSerial =*/&Serial1);

#endif

void setup() {
  // This is the UART connection to your computer (Serial Monitor)
  Serial.begin(115200);

  // Init the sensor
  while (!(asr.begin())) {
    delay(300);
  }
  //Serial.println("Begin ok!");

  /**
  @brief Set commands of the module
  */
  asr.settingCMD(DF2301Q_UART_MSG_CMD_SET_MUTE, 0);
  asr.settingCMD(DF2301Q_UART_MSG_CMD_SET_VOLUME, 8);
  // Set wake time to 5 seconds to give time for confirmation
  asr.settingCMD(DF2301Q_UART_MSG_CMD_SET_WAKE_TIME, 5); 

  /**
  @brief Play the corresponding reply audio according to the command word ID
  */
  asr.playByCMDID(23); // Plays a startup sound
}

void loop() {
  /**
  @brief Get the ID corresponding to the command word
  @return Return the obtained command word ID, returning 0 means no valid ID is obtained
  */
  uint8_t CMDID = asr.getCMDID();

  // --- Step 1: Listen for the initial command (5-13) ---
  if (CMDID >= 5 && CMDID <= 13) {
    
    // Calculate the number you want to send.
    // (ID 5 becomes 1, ID 6 becomes 2, etc.)
    int numberToSend = CMDID - 4;

    // 1. Create the message
    String message = "Start: ";
    message += String(numberToSend);

    // Let user know we are waiting for confirmation
    //Serial.println("Waiting for confirmation (ID 22)...");
    
    // Play a sound to ask for confirmation (e.g., a "beep?" sound if you have one)
    // asr.playByCMDID(YOUR_CONFIRM_BEEP_ID); 

    unsigned long startTime = millis(); // Start a timeout timer

    //This while loop is a checker for the validating command if you say anything other then CMND 22 (go forward) 
    //Ill take it we pronounced the message wrong or something and i want to retry the phrase if there is no problem then well send the message


    // --- Step 2: Wait for the confirmation command (ID 22) ---
    while (true) {
      // Poll the module for the *next* command
      uint8_t confirmCMDID = asr.getCMDID();

      // --- Step 3: Check the confirmation command ---
      if (confirmCMDID == 22) { // This is your "go forward" command
        // CONFIRMED! Send the message.
        Serial.println(message);
        break; // Exit the "waiting for confirmation" loop
      }

      // --- Step 4: Check for a *different* command (cancellation) ---
      // (confirmCMDID != 0) means a command was heard
      // (confirmCMDID != 255) means it's not an invalid command
      if (confirmCMDID != 0 && confirmCMDID != 255 && confirmCMDID != 22) {
        // CANCELLED! A different command was spoken.
        Serial.println("Cancelled.");
        break; // Exit the "waiting for confirmation" loop
      }

      // --- Step 5: Check for a timeout ---
      if (millis() - startTime > 10000) { // 10-second timeout
        // TIMED OUT!
        Serial.println("Confirmation timed out. Cancelling.");
        break; // Exit the "waiting for confirmation" loop
      }
      
      delay(100); // Wait a little before polling again
      
    } // --- End of "waiting for confirmation" loop ---

  } // --- End of initial command check ---

  delay(200); // Wait a moment before checking for the *next* initial command
}