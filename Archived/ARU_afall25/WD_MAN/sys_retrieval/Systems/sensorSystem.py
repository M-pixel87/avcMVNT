class sensorSystem:
    def __init__(self, ser):
        self.ser = ser
        self.data = {}

    def readSensors(self):
        while self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode(errors='ignore').strip()
            except Exception as e:
                print(f"Serial read error: {e}")
                return self.data

            if not line:
                continue

            # Handle IMU data line: "IMU,roll,pitch,yaw,ax,ay,az"
            if line.startswith("IMU,"):
                parts = line.split(',')
                if len(parts) == 9:
                    try:
                        _, roll, pitch, yaw, ax, ay, az, right, left = parts
                        self.data = {
                            "Roll": round(float(roll), 2),
                            "Pitch": round(float(pitch), 2),
                            "Yaw": round(float(yaw), 2),
                            "ax": round(float(ax), 3),
                            "ay": round(float(ay), 3),
                            "az": round(float(az), 3),
                            "RightUNO" : right,
                            "LeftUNO" : left

                        }
                    except ValueError:
                        print(f"Bad IMU data: {line}")

            elif line.startswith("ACK:"):
                # Optional: ignore acknowledgments
                continue

            else:
                print(f"Skipping unknown line: {line}")

        return self.data
