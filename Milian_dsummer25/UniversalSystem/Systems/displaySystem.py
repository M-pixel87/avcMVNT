import tkinter as tk
import numpy as np
import jetson_utils
from PIL import Image, ImageTk
import jetson_utils


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
