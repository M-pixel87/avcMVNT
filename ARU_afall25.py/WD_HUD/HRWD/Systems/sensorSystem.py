import threading
import time

class sensorSystem:
    def __init__(self, ser):
        self.ser = ser
        # Initialize with default safe values
        self.data = {
            "Roll": 0.0, "Pitch": 0.0, "Yaw": 0.0,
            "ax": 0.0, "ay": 0.0, "az": 0.0,
            "RightUNO": 999.0, "LeftUNO": 999.0,
            "CMDID": None
        }
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        """Spins up the background thread to handle serial reading."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._read_loop)
            self.thread.daemon = True  # Ensures thread dies when the main script closes
            self.thread.start()
            print("✅ Background Sensor Thread Started.")

    def _read_loop(self):
        """The infinite loop running in the background."""
        while self.running:
            if self.ser and getattr(self.ser, 'in_waiting', 0) > 0:
                try:
                    line = self.ser.readline().decode(errors='ignore').strip()
                except Exception as e:
                    print(f"Serial read error: {e}")
                    continue

                if not line:
                    continue

                # Handle IMU data line: "IMU,roll,pitch,yaw,ax,ay,az,right,left,cmdid"
                if line.startswith("IMU,"):
                    parts = line.split(',')
                    if len(parts) == 10:
                        try:
                            _, roll, pitch, yaw, ax, ay, az, right, left, cmdid = parts
                            
                            # Lock the data briefly while we update it
                            with self.lock:
                                self.data = {
                                    "Roll": round(float(roll), 2),
                                    "Pitch": round(float(pitch), 2),
                                    "Yaw": round(float(yaw), 2),
                                    "ax": round(float(ax), 3),
                                    "ay": round(float(ay), 3),
                                    "az": round(float(az), 3),
                                    "RightUNO": right,
                                    "LeftUNO": left,
                                    "CMDID": cmdid
                                }
                        except ValueError:
                            print(f"Bad IMU data: {line}")

                elif line.startswith("ACK:"):
                    # Optional: ignore acknowledgments
                    pass

                else:
                    pass # Silently skip unknown lines to avoid spamming console
            else:
                # Sleep for 5 milliseconds if buffer is empty to prevent maxing out the CPU core
                time.sleep(0.005) 

    def get_data(self):
        """Called by your main loop to instantly grab the latest data."""
        with self.lock:
            # Return a copy so the main loop doesn't accidentally hold the lock
            return self.data.copy()

    def stop(self):
        """Cleanly shuts down the thread."""
        self.running = False
        if self.thread is not None:
            self.thread.join()
            print("🛑 Sensor Thread Stopped.")