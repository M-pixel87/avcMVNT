import time
import serial


class microcontroller:
    '''
    Defines all functions related to a microcontroller and com
    '''
    def __init__(self,port = "COM13", baud = "115200"):
        self.serialCom = serial.Serial(port,baud,timeout=1)
    

    
    def read_Serial(self, type):
        '''
        Reads from serialcom port \n
        type 0 = basic reading, grabs from buffer \n
        type 1 = reads through buffer and grabs latest \n
        '''
        if(type == 0):
            return(self.serialCom.readline().decode('utf-8').strip())
        if(type == 1):
            latest_Message = ""

            while(self.serialCom.in_waiting > 0):
                try:
                    latest_Message = self.serialCom.readline().decode('utf-8').strip()

                except UnicodeDecodeError:
                    pass

            return latest_Message


    def send_Message(self,message,type):
        '''
        sends message over serial com port \n
        type "DMA" = sends message without newline char to conform to DMA standard \n
        type (anything else) = sends message with trailing newline, for other reading standard \n
        '''
        if(type == "DMA"):
            self.serialCom.write(message.encode('utf-8'))
        else:
            message += "\n"
            self.serialCom.write(message.encode('utf-8'))

    def parse_Sensor_Data(packet,seperator):
        '''
        parses received sensor data stream and seperates by sensor \n
        '''
        parts = packet.split(seperator)
        return parts # Instead of return parts, will update this to seperate by sensor label and put in dict or list/arr



def main():

    stm32 = microcontroller()
    while(True):
        stm32.send_Message("Hello World","DMA")
        time.sleep(1)
        print(stm32.read_Serial(1))

if __name__ == "__main__":
    main()