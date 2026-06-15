import numpy as np

class map:
    def __init__(self, xSize:int, ySize:int, res):
        self.res = res
        self.xSize = int(xSize/res)
        self.ySize = int(ySize/res)
        self.mapAr = np.zeros((self.xSize,self.ySize),dtype= int)

        self.layers = 4
        self.preCompiledMap = np.zeros((self.xSize,self.ySize,self.layers,360),dtype= np.float32)
        self.thetaArray = [0,90,180,270]

        self.mapDefaultFill()
    
    def updateMap(self,x,y,value):
        self.mapAr[x][y] = value

    def mapDefaultFill(self):
        # Drop the hardcoded inch calculations so walls line up with array edges
        max_grid_x = self.xSize - 1
        max_grid_y = self.ySize - 1

        # Paint outer edge bounds cleanly
        for gx in range(0, max_grid_x + 1):
            self.updateMap(gx, 0, 1)           # Bottom Wall
            self.updateMap(gx, max_grid_y, 1)    # Top Wall

        for gy in range(0, max_grid_y + 1):
            self.updateMap(0, gy, 1)           # Left Wall
            self.updateMap(max_grid_x, gy, 1)    # Right Wall

    def checkMap(self,x,y):
        return self.mapAr[x,y] != 0

    def convertCoordes(self,x,y):
        nx = int(x/self.res)
        ny = int(y/self.res)
        newCoords = [nx,ny]
        return newCoords

    def inBounds(self,x,y):
        convertXY = self.convertCoordes(x,y)
        return((convertXY[0] >= 0 and convertXY[0] <= self.xSize)and(convertXY[1] >= 0 and convertXY[1] <= self.ySize))
