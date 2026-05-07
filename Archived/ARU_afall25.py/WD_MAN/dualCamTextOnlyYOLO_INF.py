import cv2
from ultralytics import YOLO
import time
import threading
from queue import Queue

# --- Configuration ---
MODEL_PATH = '/home/uafs/Downloads/YOLO-inference/runs/detect/train/weights/best.engine' 
# List of camera indices to use. Add more numbers for more cameras (e.g., [0, 1, 2])
CAMERA_INDICES = [0, 2] 
# ---------------------

# A thread-safe class to handle camera reading (No changes needed here)
class CameraStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        if not self.stream.isOpened():
            print(f"Error: Could not open camera {src}.")
            # Set a flag to indicate failure
            self.failed = True
            return
        self.failed = False
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        # Use a queue to store frames, with a max size of 1 to always get the latest frame
        self.q = Queue(maxsize=1) 

    def start(self):
        # Start the thread to read frames from the video stream
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        # Keep looping infinitely until the thread is stopped
        while not self.stopped:
            if not self.grabbed:
                self.stop()
                return
            (self.grabbed, frame) = self.stream.read()
            # If the queue is full, the oldest frame is dropped, and the new one is added.
            if not self.q.full():
                self.q.put(frame)

    def read(self):
        # Return the latest frame from the queue
        return self.q.get()

    def stop(self):
        # Indicate that the thread should be stopped
        self.stopped = True
        if not self.failed:
            self.stream.release()

# --- NEW: Dedicated function to run inference for a single camera ---
def run_camera_inference(model, camera_stream, camera_id):
    """
    Reads frames from a camera stream, runs YOLO inference, and prints formatted results.
    """
    # Variables for calculating FPS
    frame_count = 0
    start_time = time.time()
    current_fps = 0

    while not camera_stream.stopped:
        frame = camera_stream.read()
        if frame is None:
            continue

        # Get frame dimensions for deviation calculation
        frame_height, frame_width, _ = frame.shape
        frame_center_x = frame_width // 2

        # Run inference
        results = model(frame, verbose=False)

        # --- Process the results ---
        for result in results:
            for box in result.boxes:
                # Extract data from the bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                class_id = int(box.cls[0])
                class_name = model.names[class_id]

                # Calculate the center of the bounding box and its deviation
                box_center_x = (x1 + x2) // 2
                deviation_px = box_center_x - frame_center_x

                # --- NEW: Formatted print statement ---
                print(
                    f"CAM {camera_id:<2} | "
                    f"FPS: {current_fps:<5.1f} | "
                    f"Obj: {class_name:<15} | "
                    f"Conf: {confidence:.2f} | "
                    f"Deviation: {deviation_px: 4d}px"
                )
        
        # --- Update FPS counter ---
        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time > 1.0: # Update FPS value every second
            current_fps = frame_count / elapsed_time
            frame_count = 0
            start_time = time.time()


# --- Main Program ---
if __name__ == "__main__":
    print("Loading YOLO model...")
    model = YOLO(MODEL_PATH)
    print("Model loaded.")

    streams = []
    threads = []

    # --- Initialize and start a thread for each camera ---
    for i, cam_index in enumerate(CAMERA_INDICES):
        print(f"Starting camera stream for index {cam_index}...")
        stream = CameraStream(src=cam_index)
        if stream.failed:
            print(f"Skipping failed camera index {cam_index}.")
            continue
        
        stream.start()
        streams.append(stream)
        
        # We use i+1 for a human-friendly camera ID (e.g., CAM 1, CAM 2)
        camera_id = i + 1 
        thread = threading.Thread(target=run_camera_inference, args=(model, stream, camera_id), daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(2.0) # Give each camera stream time to initialize properly

    print("\nRunning live inference on all cameras...")
    print("Press Ctrl+C to quit.")

    try:
        # Keep the main thread alive while the daemon threads run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping program...")
    finally:
        # Clean up all camera streams
        for stream in streams:
            stream.stop()
        cv2.destroyAllWindows()
        print("All streams stopped. Exiting.")