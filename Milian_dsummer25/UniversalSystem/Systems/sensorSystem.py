class sensorSystem:
    def __init__(self, ser):
        self.ser = ser
        self.data = {}

    def readSensors(self):
        while self.ser.in_waiting > 0:  # flush backlog
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
            except Exception as e:
                print(f"Serial read error: {e}")
                return self.data

            if not line:
                continue

            # Only handle IMU lines
            if line.startswith("IMU,"):
                parts = line.split(',')
                if len(parts) == 4:
                    try:
                        values = list(map(float, parts[1:]))
                        self.data = {f'sensor{i+1}': val for i, val in enumerate(values)}
                    except ValueError:
                        print(f"Bad IMU data: {line}")

            # Ignore lines starting with a specific tag
            elif line.startswith("ACK:"):
                pass

            else:
                print(f"Skipping unknown line: {line}")

        return self.data
