import numpy as np
import math
import random
import tkinter as tk
import time

# --- Configuration ---
TOTAL_WIDTH_FT = 30.0  
TOTAL_HEIGHT_FT = 30.0
ROWS = 30
COLS = 30
CELL_SIZE_PX = 20  # Size of each square on screen (pixels)
WINDOW_SIZE = ROWS * CELL_SIZE_PX

# --- Simulation Classes ---
class Vehicle:
    def __init__(self):
        self.r = 0
        self.c = 0
    
    def set_grid_pos(self, r, c):
        self.r = r
        self.c = c

# --- Global Map Data ---
grid_objects = np.zeros((ROWS, COLS)) # 0 = Empty, 1 = Obstacle

def setup_map():
    # Place Obstacles (Walls/Buckets)
    grid_objects[0][0] = 1         # Corner
    grid_objects[0][COLS-1] = 1    # Corner
    grid_objects[ROWS-1][0] = 1    # Corner
    grid_objects[ROWS-1][COLS-1] = 1 # Corner
    
    # Block in the middle
    grid_objects[16][18] = 1
    grid_objects[17][18] = 1
    grid_objects[18][18] = 1
    grid_objects[16][15] = 1
    grid_objects[17][15] = 1
    grid_objects[18][15] = 1
    grid_objects[15][15] = 1 
    grid_objects[15][16] = 1 
    grid_objects[14][15] = 1 
    grid_objects[14][16] = 1
    grid_objects[13][15] = 1
    grid_objects[13][16] = 1
    grid_objects[12][18] = 1
    grid_objects[12][19] = 1
    


# --- pathfinding algorithm ---
def generate_random_greedy_path(start_pos, target_pos, max_steps=400):
    current_r, current_c = start_pos
    target_r, target_c = target_pos
    path = [(current_r, current_c)]
    
    visited = set()
    visited.add((current_r, current_c))
    
    steps = 0
    
    while (current_r, current_c) != (target_r, target_c):
        steps += 1
        if steps > max_steps: return None, float('inf')

        dist_current = math.sqrt((current_c - target_c)**2 + (current_r - target_r)**2)
        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(moves)
        
        moved = False
        
        # 1. Try to get Strictly Closer
        for dr, dc in moves:
            nr, nc = current_r + dr, current_c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if grid_objects[nr][nc] == 0 and (nr, nc) not in visited:
                    dist_next = math.sqrt((nc - target_c)**2 + (nr - target_r)**2)
                    if dist_next < dist_current:
                        current_r, current_c = nr, nc
                        path.append((current_r, current_c))
                        visited.add((current_r, current_c))
                        moved = True
                        break
        
        # 2. If stuck, allow Side-Step (Equal Distance or slightly worse)
        if not moved:
            for dr, dc in moves:
                nr, nc = current_r + dr, current_c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    if grid_objects[nr][nc] == 0 and (nr, nc) not in visited:
                        dist_next = math.sqrt((nc - target_c)**2 + (nr - target_r)**2)
                        # Allow slightly worse moves (sliding along wall)
                        if dist_next <= dist_current + 0.5: 
                            current_r, current_c = nr, nc
                            path.append((current_r, current_c))
                            visited.add((current_r, current_c))
                            moved = True
                            break
                            
        if not moved: return None, float('inf') # Dead end

    return path, len(path)

def find_best_path(start, target, tries=50):
    best_path = None
    min_cost = float('inf')
    for _ in range(tries):
        path, cost = generate_random_greedy_path(start, target)
        if path and cost < min_cost:
            min_cost = cost
            best_path = path
    return best_path




# --- Visualizer Class --- and following drawing helpers
class Visualizer:
    def __init__(self, root, path, start, target):
        self.root = root
        self.path = path
        self.step_index = 0
        
        self.canvas = tk.Canvas(root, width=WINDOW_SIZE, height=WINDOW_SIZE, bg="white")
        self.canvas.pack()
        
        self.draw_grid()
        
        # Draw Start and Target
        self.draw_cell(start[0], start[1], "green") # Start
        self.draw_cell(target[0], target[1], "red") # Goal
        
        # Create Vehicle Object (Blue Circle)
        x1 = start[1] * CELL_SIZE_PX + 2
        y1 = start[0] * CELL_SIZE_PX + 2
        x2 = x1 + CELL_SIZE_PX - 4
        y2 = y1 + CELL_SIZE_PX - 4
        self.vehicle_id = self.canvas.create_oval(x1, y1, x2, y2, fill="blue")

        # Start Animation
        self.animate()

    def draw_grid(self):
        for r in range(ROWS):
            for c in range(COLS):
                x1 = c * CELL_SIZE_PX
                y1 = r * CELL_SIZE_PX
                x2 = x1 + CELL_SIZE_PX
                y2 = y1 + CELL_SIZE_PX
                
                # If obstacle, fill black
                color = "black" if grid_objects[r][c] == 1 else "white"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#ddd")

    def draw_cell(self, r, c, color):
        x1 = c * CELL_SIZE_PX
        y1 = r * CELL_SIZE_PX
        x2 = x1 + CELL_SIZE_PX
        y2 = y1 + CELL_SIZE_PX
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#ddd")

    def animate(self):
        if self.step_index < len(self.path):
            r, c = self.path[self.step_index]
            
            # Update vehicle position
            x1 = c * CELL_SIZE_PX + 2
            y1 = r * CELL_SIZE_PX + 2
            x2 = x1 + CELL_SIZE_PX - 4
            y2 = y1 + CELL_SIZE_PX - 4
            self.canvas.coords(self.vehicle_id, x1, y1, x2, y2)
            
            # Mark the path trail
            if self.step_index > 0:
                prev_r, prev_c = self.path[self.step_index-1]
                # Draw a light gray dot where we were
                self.draw_cell(prev_r, prev_c, "#eee") 
                # Redraw start point so it doesn't disappear
                if self.step_index == 1: 
                    self.draw_cell(self.path[0][0], self.path[0][1], "green")

            self.step_index += 1
            # Schedule next frame in 50ms
            self.root.after(50, self.animate)
        else:
            print("Animation Complete")


if __name__ == "__main__":
    setup_map()
    
    start_grid = (15, 0)   # Start (Row, Col)
    target_grid = (15, 29) # End (Row, Col)
    
    print("Calculating Path...")
    final_path = find_best_path(start_grid, target_grid, tries=100)
    
    if final_path:
        print(f"Path Found! Length: {len(final_path)}")
        root = tk.Tk()
        root.title("Vehicle Path Visualizer")
        app = Visualizer(root, final_path, start_grid, target_grid)
        root.mainloop()
    else:
        print("Failed to find path.")