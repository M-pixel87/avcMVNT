# locationObjects.py
import math

# --- No changes needed for Square or bucket classes ---
class Square:
    def __init__(self, i, j, area):
        side_length = math.sqrt(area)
        self.i = i
        self.j = j
        self.area = area
        self.side_length = side_length
        self.x = self.side_length * j 
        self.y = self.side_length * i
        self.objects = []
    
    def __repr__(self):
        return '1' if (len(self.objects) > 0) else '0'
    def add_object(self, obj):
        self.objects.append(obj)
    def remove_object(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

class bucket:
    # ... (same as before)
    def __init__(self, color):
        self.color = color
        self.full = False
    def fill(self):
        self.full = True

# --- All changes are in the vehicle class ---
class vehicle:
    # The vehicle needs to know the world's properties
    def __init__(self, matrix, total_width, total_height):
        self.matrix = matrix
        
        # World dimensions
        self.total_width = total_width
        self.total_height = total_height
        num_rows = len(matrix)
        num_cols = len(matrix[0])
        self.cell_height = total_height / num_rows
        self.cell_width = total_width / num_cols

        # The vehicle's primary state is continuous x, y
        self.x = 0.0
        self.y = 0.0
        self.rotation = 0.0  # In degrees, 0 = facing "right"
        self.velocityx = 0.0  # Current speed in ft/s
        self.velocityy = 0.0  # Current speed in ft/s
        # Grid state (which square it's in)
        self.square = None
        self.i = None
        self.j = None

    def set_initial_position(self, x, y):
        """Places the vehicle at a starting coordinate and updates the grid."""
        self.x = x
        self.y = y
        self._update_grid_association()




    def update_position(self, dax, day, rot, dt =0.0166):
        """
        Updates the vehicle's continuous position based on sensor data (dx, dy)
        and re-evaluates which grid square it's in.
        """

        if(abs(dax) <= 0.05):
            dax = 0
        
        if(abs(day) <= 0.05):
            day = 0

        self.velocityx += dax*dt
        self.velocityy += day*dt
        self.velocityx *= 0.99
        self.velocityy *= 0.99

        if(abs(self.velocityx) <= 0.005):
            self.velocityx = 0
        
        if(abs(self.velocityy) <= 0.005):
            self.velocityy = 0

        self.rotation = rot
        new_x = self.x + self.velocityx*dt
        new_y = self.y + self.velocityy*dt
        print(self.velocityx)
        print(self.velocityy)

        # Boundary check to keep the vehicle on the map
        if not (0 <= new_x < self.total_width and 0 <= new_y < self.total_height):
            print("Movement would go out of bounds. Ignoring.")
            return

        # Update the real x, y position
        self.x = new_x
        self.y = new_y

        # Now, figure out which grid cell this new position corresponds to
        self._update_grid_association()
        
        print(f"Updated position to (x={self.x:.2f}, y={self.y:.2f}) -> Grid Cell ({self.i}, {self.j})")





    def _update_grid_association(self):
        """
        Calculates the vehicle's grid square based on its continuous x, y
        position and updates the matrix if it has changed squares.
        """
        # Calculate the new grid indices
        new_j = int(self.x // self.cell_width)
        new_i = int(self.y // self.cell_height)

        # If the vehicle is still in the same square, do nothing
        if new_i == self.i and new_j == self.j:
            return

        # --- The vehicle has moved to a new square ---
        # 1. Remove vehicle from the old square
        if self.square:
            self.square.remove_object(self)

        # 2. Get the new square object from the matrix
        new_square = self.matrix[new_i][new_j]

        # 3. Add vehicle to the new square
        new_square.add_object(self)
        
        # 4. Update the vehicle's internal state
        self.square = new_square
        self.i = new_i
        self.j = new_j