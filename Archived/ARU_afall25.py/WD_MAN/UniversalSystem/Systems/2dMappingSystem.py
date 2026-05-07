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



vehicle = locationObjects.vehicle(ar, total_width, total_height)

redBucket = locationObjects.bucket("red")
blueBucket = locationObjects.bucket("blue")
greenBucket = locationObjects.bucket("green")
yellowBucket = locationObjects.bucket("yellow")

objects = [redBucket, blueBucket, greenBucket, yellowBucket]


class Map():
    def __init__():
        self.ar = np.empty((rows, cols), dtype=object)
        pass

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

