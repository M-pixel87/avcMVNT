import cv2
from ultralytics import YOLO
import time
import threading
from queue import Queue

# --- Configuration ---
MODEL_PATH = '/home/uafs/Downloads/YOLO-inference/runs/detect/train/weights/best.engine' 
# List of camera indices to use.
CAMERA_INDICES = [0, 2] 
# ---------------------

# A thread-safe class to handle camera reading (No changes needed here)
class CameraStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        if not self.stream.isOpened():
            print(f"Error: Could not open camera {src}.")
            self.failed = True
            return
        self.failed = False
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        self.q = Queue(maxsize=1) 

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
                return
            (self.grabbed, frame) = self.stream.read()
            if not self.q.full():
                self.q.put(frame)

    def read(self):
        return self.q.get()

    def stop(self):
        self.stopped = True
        if not self.failed:
            self.stream.release()

# --- MODIFIED: Inference function now also handles frame annotation and queuing for display ---
def run_camera_inference(model, camera_stream, camera_id, display_queue):
    """
    Reads frames, runs YOLO inference, prints results, and puts annotated frames in a queue for display.
    """
    frame_count = 0
    start_time = time.time()
    current_fps = 0

    while not camera_stream.stopped:
        frame = camera_stream.read()
        if frame is None:
            continue

        frame_height, frame_width, _ = frame.shape
        frame_center_x = frame_width // 2

        # Run inference
        results = model(frame, verbose=False)

        # --- NEW: Draw bounding boxes on the frame ---
        # The results[0].plot() method conveniently returns the frame with boxes drawn on it.
        annotated_frame = results[0].plot()
        
        # --- Put the annotated frame into the queue for the main thread to display ---
        if not display_queue.full():
            display_queue.put(annotated_frame)

        # Process the results for printing to console (same as before)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                box_center_x = (x1 + x2) // 2
                deviation_px = box_center_x - frame_center_x
                
                print(
                    f"CAM {camera_id:<2} | "
                    f"FPS: {current_fps:<5.1f} | "
                    f"Obj: {class_name:<15} | "
                    f"Conf: {confidence:.2f} | "
                    f"Deviation: {deviation_px: 4d}px"
                )
        
        # Update FPS counter
        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time > 1.0:
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
    # --- NEW: Create a dictionary of queues to hold frames for display ---
    display_queues = {}

    for i, cam_index in enumerate(CAMERA_INDICES):
        camera_id = i + 1  # Human-friendly ID (CAM 1, CAM 2)
        print(f"Starting camera stream for index {cam_index} (CAM {camera_id})...")
        
        stream = CameraStream(src=cam_index)
        if stream.failed:
            print(f"Skipping failed camera index {cam_index}.")
            continue
        
        stream.start()
        streams.append(stream)
        
        # Create a display queue for this camera
        display_queues[camera_id] = Queue(maxsize=1)
        
        thread = threading.Thread(
            target=run_camera_inference, 
            args=(model, stream, camera_id, display_queues[camera_id]), 
            daemon=True
        )
        thread.start()
        threads.append(thread)
        time.sleep(2.0)

    print("\nRunning live inference... Press 'q' in any camera window to quit.")

    # --- NEW: Main loop for displaying frames ---
    try:
        while True:
            # Loop through each camera's display queue
            for cam_id, dq in display_queues.items():
                if not dq.empty():
                    # Get the annotated frame and show it
                    frame_to_show = dq.get()
                    cv2.imshow(f"CAM {cam_id}", frame_to_show)
            
            # Check for 'q' key press to exit. waitKey is essential for imshow to work.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping program...")
    finally:
        print("Stopping all streams...")
        for stream in streams:
            stream.stop()
        cv2.destroyAllWindows()
        print("All windows closed. Exiting.")