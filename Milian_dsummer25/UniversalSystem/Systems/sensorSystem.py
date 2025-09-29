

class sensorSystem:
    def __init__(self, ser ):
        self.ser = ser
        self.data = {}

    def readSensors(self):
        data = self.ser.readline().decode('utf-8').strip()
        if data:
            try:
                # Split by comma and convert to integers
                sensor_values = list(map(int, data.split(',')))

                # Automatically generate keys sensor1, sensor2, ...
                self.data = {f'sensor{i+1}': val for i, val in enumerate(sensor_values)}

            except ValueError:
                print(f"Invalid sensor data: {data}")
        return self.data

