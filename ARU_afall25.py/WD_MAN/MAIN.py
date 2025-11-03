import tkinter as tk
from Systems.mapDisplay import MapDisplayGUI

#start up tinker and give it to a var
root = tk.Tk()

# start storing data to not rerun intire func
view = MapDisplayGUI(root)

# this function is going to collect my keyboard pressedn and then when I want to use it
#just type the function name and itll output what it collected
def on_key_press(event):
    """Takes a keyboard event and tells the view to move the player."""
    view.move_player(event.keysym)

#Tells this window to listen for any key press and call our function so that we can store it
root.bind("<KeyPress>", on_key_press)

# 5. Start the application's event loop.
root.mainloop()

