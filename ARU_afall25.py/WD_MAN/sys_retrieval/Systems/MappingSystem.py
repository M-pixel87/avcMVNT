from Systems import locationObjects
import numpy as np
import math
import time


class Map():
    def __init__(self, w = 30, h = 30, r=20, c=20):
        self.total_width = w
        self.total_height = h
        self.rows = r
        self.cols = c
        self.sqft_per_cell = (self.total_width * self.total_height) / (self.rows * self.cols)
        print(f"width of each cell: {self.total_width/self.cols:.2f} ft")
        print(f"height of each cell: {self.total_height/self.rows:.2f} ft")
        print(f"Each cell covers {self.sqft_per_cell:.2f} sqft")

        self.ar = np.empty((self.rows, self.cols), dtype=object)
        self.fill_matrix()
        self.vehicle = locationObjects.vehicle(self.ar, self.total_width, self.total_height)
        #This will hold all the objects that will be placed on the map, aka the buckets mainly
        redBucket = locationObjects.bucket("red")
        blueBucket = locationObjects.bucket("blue")
        greenBucket = locationObjects.bucket("green")
        yellowBucket = locationObjects.bucket("yellow")

        self.objects = [redBucket, blueBucket, greenBucket, yellowBucket]
        self.vehicle.set_initial_position(15,15)
        self.place_objects_on_map()
        

    #Setup Functions
    def fill_matrix(self):
        """Fills the grid with empty squares."""
        for i in range(self.rows):
            for j in range(self.cols):
                self.ar[i][j] = locationObjects.Square(i, j, self.sqft_per_cell)


    def place_objects_on_map(self):
        """Places the corner buckets on the map."""
        self.ar[0][0].add_object(self.objects[0])                  # red
        self.ar[0][self.cols-1].add_object(self.objects[1])             # blue
        self.ar[self.rows-1][0].add_object(self.objects[2])             # green
        self.ar[self.rows-1][self.cols-1].add_object(self.objects[3])        # yellow
    #------------------------------------------------------------------------------

