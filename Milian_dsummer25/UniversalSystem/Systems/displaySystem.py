import tkinter as tk

class DisplaySystem:
    ...
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("400x300")
        self.root.title("Robot Display")
        self.label = tk.Label(self.root, text="Robot Status", font=("Arial", 24))
        self.label.pack(pady=20)
        # Labels for joystick data
        self.axis_label = tk.Label(self.root, text="Axes: []", font=("Arial", 12))
        self.axis_label.pack(pady=10)

        self.button_label = tk.Label(self.root, text="Buttons: []", font=("Arial", 12))
        self.button_label.pack(pady=10)

        # Label for motor output
        self.motor_label = tk.Label(self.root, text="Motor Output: 0, 0", font=("Arial", 14), fg="blue")
        self.motor_label.pack(pady=20)

    def update_display(self, axes, buttons, motor_output):
        self.axis_label.config(text=f"Axes: {['{:.2f}'.format(a) for a in axes]}")
        self.button_label.config(text=f"Buttons: {buttons}")
        self.motor_label.config(text=f"Motor Output: {motor_output[0]}, {motor_output[1]}")
        self.root.update_idletasks()
        