import locationObjects
import numpy as np
import math
import time

total_width = 30.0  
total_height = 30.0
rows = 20
cols = 20

sqft_per_cell = (total_width * total_height) / (rows * cols)
print(f"width of each cell: {total_width/cols:.2f} ft")
print(f"height of each cell: {total_height/rows:.2f} ft")
print(f"Each cell covers {sqft_per_cell:.2f} sqft")

ar = np.empty((rows, cols), dtype=object)


vehicle = locationObjects.vehicle(ar, total_width, total_height)

redBucket = locationObjects.bucket("red")
blueBucket = locationObjects.bucket("blue")
greenBucket = locationObjects.bucket("green")
yellowBucket = locationObjects.bucket("yellow")

objects = [redBucket, blueBucket, greenBucket, yellowBucket]




#Setup Functions
def fill_matrix(matrix):
    """Fills the grid with empty squares."""
    for i in range(rows):
        for j in range(cols):
            matrix[i][j] = locationObjects.Square(i, j, sqft_per_cell)


def place_objects_on_map(matrix, objects):
    """Places the corner buckets on the map."""
    matrix[0][0].add_object(objects[0])                  # red
    matrix[0][cols-1].add_object(objects[1])             # blue
    matrix[rows-1][0].add_object(objects[2])             # green
    matrix[rows-1][cols-1].add_object(objects[3])        # yellow
#------------------------------------------------------------------------------

def random_movement():
    """Generates a small random movement value."""
    return (np.random.rand() - 0.5) * 3.0  # Random float in range [-1.5, 1.5]


def main():
    fill_matrix(ar)
    place_objects_on_map(ar, objects)
    
    # Place the vehicle at the center of the 30x30 area
    vehicle.set_initial_position(15.0, 15.0)


    print("--- Initial Map ---")
    print(ar)
    print(f"\nVehicle starting at: (x={vehicle.x:.2f}, y={vehicle.y:.2f})")
    print("---------------------\n")
    

    # --- Simulate movement from sensor data (dx, dy) ---
    print("Simulating movement...")
    while(True):
        time.sleep(1)       
        vehicle.update_position(dx = random_movement(), dy = random_movement(), rot = 180)
        print(ar)
        print(f"Vehicle now at: (x={vehicle.x:.2f}, y={vehicle.y:.2f})")

    


if __name__ == "__main__":
    main()