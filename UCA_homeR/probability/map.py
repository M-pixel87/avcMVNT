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

    def rayCast(self, ray, x, y, theta):
        quality, angle, dist = ray
        globalRot = np.radians(theta + angle)
        
        dx = (self.res*0.25) * np.cos(globalRot)
        dy = (self.res*0.25) * np.sin(globalRot)
     
        cx = x
        cy = y
        
        grid_x, grid_y = self.convertCoordes(cx, cy)
      
        while self.inBounds(cx, cy):
            # --- ADD THE SAFETY CLIPPING HERE INSIDE THE RAY CASTER ---
            safe_grid_x = max(0, min(grid_x, self.xSize - 1))
            safe_grid_y = max(0, min(grid_y, self.ySize - 1))
            
            # Check the map using our guaranteed safe grid indices
            if self.checkMap(safe_grid_x, safe_grid_y):
                break # We hit a wall, stop casting!
                
            # Take a step forward in continuous space
            cx += dx
            cy += dy
            
            # Recalculate grid indices for the next iteration round
            grid_x, grid_y = self.convertCoordes(cx, cy)
            
        dist = np.sqrt((cx-x)**2 + (cy-y)**2)
        return dist
    
    def preCompile(self):
        for i in range(self.xSize):
            for j in range(self.ySize):
                x = i * self.res + (self.res / 2.0)
                y = j * self.res + (self.res / 2.0)
                for k in range(self.layers):
                    for n in range(360):
                        tempRay = (1,n,0)
                        self.preCompiledMap[i][j][k][n] = self.rayCast(tempRay,x,y,k)