#ifndef MICROCONTROLLERCOM_H
#define MICROCONTROLLERCOM_H

#include <string>
#include "serial/serial.h"

class microcontroller {
public:
    serial::Serial serialCom;

    // Constructor
    microcontroller(std::string port = "COM13", uint16_t baud = 115200);
    
    // Functions
    void send_Message(std::string message, std::string type);
    std::string read_Serial(uint8_t type);
};

#endif