import tkinter as tk
import numpy as np
import jetson_utils
from PIL import Image, ImageTk
import jetson_utils
import cv2
import time


class DisplaySystem:
    def __init__(self, cam, mode="GPU"):
        self.mode = mode

        if self.mode == "GPU" and cam:
            self._impl = GPUDisplaySystem()
        elif self.mode == "TK" or cam is None:
            self._impl = TkDisplaySystem()
        elif self.mode == "YOLO" :
            self._impl = DisplaySystem_YOLO()
        else:
            raise ValueError(f"Unknown or unsupported display mode: {mode}")

    def update_display(self, img=None, detections=None, axes=None, buttons=None, motor_output=None, data=None):
        """Universal update_display interface for all display types."""
        if self.mode == "YOLO":
            self._impl.update_display(img, detections, axes, buttons, motor_output, data)
        elif self.mode == "GPU":
            self._impl.update_display(axes, buttons, motor_output, img, data)
        elif self.mode == "TK":
            self._impl.update_display(axes, buttons, motor_output, img, data)


    def __getattr__(self, name):
        """Forward all attribute/method access to chosen implementation"""
        return getattr(self._impl, name)
    



class DisplaySystem_YOLO:
    def __init__(self, window_name="YOLO Display"):
        self.window_name = window_name

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def update_display(self, frame, detections=None, axes=None, buttons=None, motor_output=None, data=None):
        if frame is None:
            return

        # Draw YOLO detections
        if detections:
            for det in detections:
                (x1, y1, x2, y2) = det["bbox"]
                label = det["label"]
                conf = det["confidence"]

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                text = f"{label} {conf:.2f}"
                cv2.putText(frame, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Overlay control data
        y = 20
        if axes is not None:
            cv2.putText(frame, f"Axes: {['%.2f' % a for a in axes]}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            y += 20
        if buttons is not None:
                cv2.putText(frame, f"Buttons: {buttons}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                y += 20
        if motor_output is not None:
            cv2.putText(frame, f"Motors: {motor_output[0]}, {motor_output[1]}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            y += 20
        if data is not None:
            for key, value in data.items():
                cv2.putText(frame, f"{key}: {value}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y += 20

      
        cv2.imshow(self.window_name, frame)

        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return "quit"

    def close(self):
        cv2.destroyAllWindows()





#FAST GPU SYSTEM : gpu accelerated,fast refresh and display, limited hud options
class GPUDisplaySystem:
    def __init__(self, width=800, height=600):
        # Create a GPU display window
        self.display = jetson_utils.videoOutput(
            "display://0",
            argv=[f"--output-width={width}", f"--output-height={height}"]
        )

        #scaledSize = 
        
        # Create font renderer(s) for text overlay
        self.smallFont = jetson_utils.cudaFont(size=16)
        self.font = jetson_utils.cudaFont()
        #self.scaledFont = jetson_utils.cudaFont(size=scaledSize)

    def update_display(self, axes, buttons, motor_output, img=None, data=None):
        if img is None or not self.display.IsStreaming():
            return

        # Format text for overlay
        axes_text = "Axes: " + ", ".join([f"{a:.2f}" for a in axes])
        buttons_text = "Buttons: " + ", ".join(map(str, buttons))
        motor_text = f"Motor Output: {motor_output[0]}, {motor_output[1]}"

        # Draw text overlays on the image
        self.smallFont.OverlayText(img, img.width, img.height, axes_text,
                              5, 5,      # (x,y) position
                              (255, 255, 0, 255), (0, 0, 0, 128))  # yellow text, black bg

        self.smallFont.OverlayText(img, img.width, img.height, buttons_text,
                              5, 35,      # (x,y) position
                              (0, 255, 255, 255), (0, 0, 0, 128))  # cyan text

        self.smallFont.OverlayText(img, img.width, img.height, motor_text,
                              5, 65,       # (x,y) position
                              (0, 255, 0, 255), (0, 0, 0, 128))  # green text
        
        # If additional data is provided, display it, particullarly sensor data
        if data:
            y_offset = 95
            for key, value in data.items():
                data_text = f"{key}: {value}"
                self.smallFont.OverlayText(img, img.width, img.height, data_text,
                                      5, y_offset,
                                      (255, 255, 255, 255), (0, 0, 0, 128))  # white text
                y_offset += 30  # Move down for next line
        
        # Render the image on GPU window
        self.display.Render(img)
        self.display.SetStatus("Robot GPU Display")

    def is_streaming(self):
        return self.display.IsStreaming()
    
    

#SLOW, needs to be limited to 15 fps, causes issues with trying to update so fast
class TkDisplaySystem:
    ...
    def __init__(self):
        
        self.root = tk.Tk()
        self.root.geometry("800x800")
        self.root.title("Robot Display")
        self.label = tk.Label(self.root, text="Robot Status", font=("Arial", 24))
        self.label.pack(pady=20)

        self.img = None  # Placeholder for image data if needed
        self.img_label = None

        # Labels for joystick data
        self.axis_label = tk.Label(self.root, text="Axes: []", font=("Arial", 12))
        self.axis_label.pack(pady=10)

        self.button_label = tk.Label(self.root, text="Buttons: []", font=("Arial", 12))
        self.button_label.pack(pady=10)

        # Label for motor output
        self.motor_label = tk.Label(self.root, text="Motor Output: 0, 0", font=("Arial", 14), fg="blue")
        self.motor_label.pack(pady=20)

        self.data_label = tk.Label(self.root, text="Sensor Data: N/A", font=("Arial", 12))
        self.data_label.pack(pady=10)

    def update_display(self, axes, buttons, motor_output, img=None, data=None):
        # Convert Jetson image to numpy if provided
        if img is not None:
            self.img = jetson_utils.cudaToNumpy(img)

        # Update image label only if we actually have an image
        if self.img is not None:
            pil_img = Image.fromarray(self.img)
            imgtk = ImageTk.PhotoImage(image=pil_img)

            if self.img_label is None:
                # First-time creation
                self.img_label = tk.Label(self.root, image=imgtk)
                self.img_label.image = imgtk  # prevent garbage collection
                self.img_label.pack()
            else:
                # Update existing label
                self.img_label.configure(image=imgtk)
                self.img_label.image = imgtk

        # Update controller/motor status text
        self.axis_label.config(text=f"Axes: {[f'{a:.2f}' for a in axes]}")
        self.button_label.config(text=f"Buttons: {buttons}")
        self.motor_label.config(text=f"Motor Output: {motor_output[0]}, {motor_output[1]}")

        # Process Tkinter events
        self.root.update_idletasks()
