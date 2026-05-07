import cv2
from ultralytics import YOLO
import time
import threading
from queue import Queue

# --- Configuration ---
MODEL_PATH = '/home/uafs/Downloads/YOLO-inference/runs/detect/train/weights/best.engine' 
CAMERA_INDICES = [0, 2] 
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30
# ---------------------

# --- NEW: GStreamer Pipeline Function ---
def get_gstreamer_pipeline(camera_id, width, height, fps):
    return (
        f"v4l2src device=/dev/video{camera_id} ! "
        f"video/x-raw, width=(int){width}, height=(int){height}, framerate=(fraction){fps}/1 ! "
        "nvvidconv ! "
        f"video/x-raw(memory:NVMM), width=(int){width}, height=(int){height} ! "
        "nvvidconv ! "
        "video/x-raw, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink drop=true"
    )

# --- MODIFIED: CameraStream now accepts a GStreamer pipeline string ---
class CameraStream:
    def __init__(self, pipeline):
        # self.stream = cv2.VideoCapture(src) # Old way
        self.stream = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER) # New, fast way
        if not self.stream.isOpened():
            print("Error: Could not open camera with GStreamer pipeline.")
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

# --- Inference function (no changes needed) ---
def run_camera_inference(model, camera_stream, camera_id, display_queue):
    frame_count = 0
    start_time = time.time()
    current_fps = 0
    while not camera_stream.stopped:
        frame = camera_stream.read()
        if frame is None: continue
        results = model(frame, verbose=False)
        annotated_frame = results[0].plot()
        if not display_queue.full():
            display_queue.put(annotated_frame)
        for result in results:
            for box in result.boxes:
                class_name = model.names[int(box.cls[0])]
                print(f"CAM {camera_id} | FPS: {current_fps:.1f} | Obj: {class_name}")
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
    display_queues = {}

    for i, cam_index in enumerate(CAMERA_INDICES):
        camera_id = i + 1
        print(f"Starting camera stream for index {cam_index} (CAM {camera_id})...")
        
        # --- NEW: Create the pipeline and pass it to CameraStream ---
        pipeline = get_gstreamer_pipeline(cam_index, FRAME_WIDTH, FRAME_HEIGHT, FPS)
        print(f"Using pipeline: {pipeline}")
        
        stream = CameraStream(pipeline=pipeline)
        if stream.failed:
            print(f"Skipping failed camera index {cam_index}.")
            continue
        
        stream.start()
        streams.append(stream)
        
        display_queues[camera_id] = Queue(maxsize=1)
        
        thread = threading.Thread(target=run_camera_inference, args=(model, stream, camera_id, display_queues[camera_id]), daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(2.0)

    print("\nRunning live inference... Press 'q' in any camera window to quit.")
    try:
        while True:
            for cam_id, dq in display_queues.items():
                if not dq.empty():
                    frame_to_show = dq.get()
                    cv2.imshow(f"CAM {cam_id}", frame_to_show)
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