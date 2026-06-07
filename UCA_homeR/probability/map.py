import numpy as np

class map:
    def __init__(self, xSize:int, ySize:int, res):
        self.res = res
        self.xSize = int(xSize/res)
        self.ySize = int(ySize/res)
        self.mapAr = np.zeros((self.xSize,self.ySize),dtype= int)

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

    def rayCast(self, ray, x, y, theta):
        quality, angle, dist = ray
        globalRot = np.radians(theta + angle)
        
        dx = self.res * np.cos(globalRot)
        dy = self.res * np.sin(globalRot)
     
        cx = x
        cy = y
        
        grid_x, grid_y = self.convertCoordes(cx, cy)
      
        while self.inBounds(cx, cy) and not self.checkMap(grid_x, grid_y):
            cx += dx
            cy += dy
            grid_x, grid_y = self.convertCoordes(cx, cy)
        dist = np.sqrt((cx-x)**2 + (cy-y)**2)
        return dist