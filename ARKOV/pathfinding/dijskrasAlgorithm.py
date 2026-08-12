import numpy as np
import time

map = np.zeros((xsize,ysize))

curx = 0
cury = 0

index = 0

xsize = 10
ysize = 10


def make_obstacles():
    map[0][0] = 1 # place start
    map[9][9] = 3 # place end

    map[4][0] = 2 # obstacles 
    map[4][1] = 2
    map[4][2] = 2
    map[4][3] = 2
    map[4][4] = 2