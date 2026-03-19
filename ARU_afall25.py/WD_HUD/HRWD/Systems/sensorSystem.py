import threading
import time

class sensorSystem:
    def __init__(self, ser):
        self.ser = ser
        
        # ==============================================================
        # 🛠️ HARDWARE TOGGLE: Set to True while sensors are unplugged!
        # This prevents the "ghost obstacles" from stopping the robot.
        # ==============================================================
        self.IGNORE_ULTRASONICS = True 
        
        # Initialize with default safe values
        self.data = {
            "Roll": 0.0, "Pitch": 0.0, "Yaw": 0.0,
            "ax": 0.0, "ay": 0.0, "az": 0.0,
            "LeftUNO": 999.0, "RightUNO": 999.0, 
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
            print(" Background Sensor Thread Started.")

    def _read_loop(self):
        """The infinite loop running in the background."""
        while self.running:
            if self.ser and getattr(self.ser, 'in_waiting', 0) > 0:
                try:
                    # Read and decode the raw bytes
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                except Exception:
                    continue

           
                if not line or not line.startswith("IMU,"):
                    continue 

  
                parts = line.split(',')
                if len(parts) == 10:
                    try:
                        _, roll, pitch, yaw, ax, ay, az, left, right, cmdid = parts
                        
                        # Handle the floating pin noise (Ghost obstacles)
                        if self.IGNORE_ULTRASONICS:
                            final_left = 999.0
                            final_right = 999.0
                        else:
                            final_left = float(left)
                            final_right = float(right)

                        # Lock the data briefly while we update it safely
                        with self.lock:
                            self.data = {
                                "Roll": round(float(roll), 2),
                                "Pitch": round(float(pitch), 2),
                                "Yaw": round(float(yaw), 2),
                                "ax": round(float(ax), 3),
                                "ay": round(float(ay), 3),
                                "az": round(float(az), 3),
                                "LeftUNO": final_left,
                                "RightUNO": final_right,
                                "CMDID": cmdid
                            }
                    except ValueError:
                        pass
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