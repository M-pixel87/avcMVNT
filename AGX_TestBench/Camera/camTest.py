import os
import numpy
import cv2
import time

class cvWebcam:
    def __init__(self, cam_id=0, width=640, height=480):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.camera = None
        self.initialized = False

        try:
            path = f"/dev/video{cam_id}"
            if not os.path.exists(path):
                raise FileNotFoundError(f"No device found at {path}")

            self.camera = cv2.VideoCapture(cam_id)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera.set(cv2.CAP_PROP_FPS, 60)

            if not self.camera.isOpened():
                raise RuntimeError(f"Failed to open camera {cam_id}")

            print(f"cvWebcam initialized on {path} [{width}x{height}]")
            self.initialized = True

        except Exception as e:
            print(f"cvWebcam init failed: {e}")
            self.camera = None

    def get_frame(self):
        if not self.initialized or self.camera is None:
            return None

        ret, frame = self.camera.read()
        if not ret:
            print("Frame capture failed.")
            return None
        return frame

    def release(self):
        if self.camera:
            self.camera.release()
            self.initialized = False
            print("cvWebcam released.")

if __name__ == "__main__":
    cam = cvWebcam()
    cv2.namedWindow("camFeed", cv2.WINDOW_NORMAL)
    while(True):
        frame = cam.get_frame()
        time.sleep(0.05)
        cv2.imshow("camFeed", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cam.release()
            break