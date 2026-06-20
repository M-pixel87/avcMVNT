// make sure to use vckpg to make library management easier , or cmake (which we used)
#include "microControllerCom.h"
#include <iostream>

microcontroller::microcontroller(std::string port, uint16_t baud)
    : serialCom(port, baud, serial::Timeout::simpleTimeout(1000))
{
    if (serialCom.isOpen()){
        std::cout << "The com is open: " << port << std::endl;
    } else {
        std::cout << "The com is not open on: " << port << std::endl;
    }
}

void microcontroller::send_Message(std::string message, std::string type) {
    if (serialCom.isOpen()) {
        if (type == "DMA") {
            serialCom.write(message); // Raw write for DMA
        } else {
            message += "\n";          // Append EOL for standard text
            serialCom.write(message);
        }
    }
}

std::string microcontroller::read_Serial(uint8_t type) {
    if (serialCom.isOpen()) {
        std::string message = serialCom.readline(65536, "\n");
        return message;
    }
    return "";
}