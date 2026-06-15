import tkinter as tk
import numpy as np

# 1. Create a basic 2D NumPy array (0 = white/empty, 1 = black/wall)
# Change these values to edit the grid layout!
grid_array = np.array([
    [1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1],
    [1, 0, 1, 0, 1],
    [1, 0, 0, 0, 1],
    [1, 1, 1, 1, 1]
])

# 2. Setup the root Tkinter window
root = tk.Tk()
root.title("Basic Grid Visualizer")

rows, cols = grid_array.shape
ui_cells = []

# 3. Build the visual grid using standard Tkinter Labels
for r in range(rows):
    row_cells = []
    for c in range(cols):
        # Determine color based on initial array value
        cell_color = "black" if grid_array[r, c] == 1 else "white"
        
        # Create a tiny block label
        cell = tk.Label(root, width=6, height=3, bg=cell_color, relief="solid", bd=1)
        cell.grid(row=r, column=c, padx=1, pady=1)
        row_cells.append(cell)
    ui_cells.append(row_cells)

# 4. Simple function to refresh the UI colors after you modify the array data
def update_visualizer():
    for r in range(rows):
        for c in range(cols):
            cell_color = "black" if grid_array[r, c] == 1 else "white"
            ui_cells[r][c].config(bg=cell_color)

# Example Modification: Switch the middle cell (2, 2) to empty after 2 seconds
# You can remove or replace this with your actual layout loops!
root.after(2000, lambda: [grid_array.itemset((2, 2), 0), update_visualizer()])

root.mainloop()