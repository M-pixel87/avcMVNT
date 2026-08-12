import numpy as np

curx = 0
cury = 0

index = 0

xsize = 10
ysize = 10

map = np.zeros((xsize,ysize))

def set_points():
    map[][] = 

def check_neihbors():
    rightVal , leftVal, botVal, topVal = 0
    curBest = (curx,cury)

    if (curx+1 < xsize):
        rightVal = map[curx+1][cury]
        if(rightVal >= map[curBest[0],curBest[1]]):
            curBest = (curx+1,cury)

    if (curx-1 >= 0):
        leftVal = map[curx-1][cury]
        if(leftVal >= map[curBest[0],curBest[1]]):
            curBest = (curx-1,cury)

    if (cury+1 < ysize):
        botVal = map[curx][cury+1]
        if(botVal >= map[curBest[0],curBest[1]]):
            curBest = (curx,cury+1)

    if (cury-1 >= 0):
        topVal = map[curx][cury-1]
        if(topVal >= map[curBest[0],curBest[1]]):
            curBest = (curx,cury-1)

    
    
