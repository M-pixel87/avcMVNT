import tkinter as tk
import numpy as np
import jetson_utils
from pil import Image, ImageTk

class DisplaySystem:
    ...
    def __init__(self):
        
        self.root = tk.Tk()
        self.root.geometry("400x300")
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

    def update_display(self, axes, buttons, motor_output, img=None):
        self.img = jetson_utils.cudaToNumpy(img) if img is not None else self.img
        if self.img is not None:
            img = Image.fromarray(self.img)
            imgtk = ImageTk.PhotoImage(image=img)
            if not hasattr(self, 'img_label'):
                self.img_label = tk.Label(self.root, image=imgtk)
                self.img_label.image = imgtk
                self.img_label.pack()
            else:
                self.img_label.configure(image=imgtk)
                self.img_label.image = imgtk
            
        self.axis_label.config(text=f"Axes: {['{:.2f}'.format(a) for a in axes]}")
        self.button_label.config(text=f"Buttons: {buttons}")
        self.motor_label.config(text=f"Motor Output: {motor_output[0]}, {motor_output[1]}")
        self.root.update_idletasks()
        