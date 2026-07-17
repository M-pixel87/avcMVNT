/*
We are going to utelize a 3d voxel based recreation of the enviornment. This is a basic test of the structure
to how it will be stored most likely. There may be more moifications we can make to make it smaller
and more efficent, but I beleive the major efficencies will come from how we handle ray tracing
aswell as the localization and loops.
*/

#include <iostream>
#include <vector>
#include <cstdint> // allows uint8_t
#include <cmath>
#include <cstdlib> // allows abs

// using struct for less boilerplate
struct Point {
    double x,y,z;
};

struct GridCoord {
    int x, y, z;
};

struct Particle {
    double x,y,z,theta;
};


struct VoxelGrid {
    int sizeX, sizeY, sizeZ;
    double resolution; 
    std::vector<uint8_t> data; 

    VoxelGrid(int x, int y, int z, double res) 
        : sizeX(x), sizeY(y), sizeZ(z), resolution(res), data(x * y * z, 0) {}

    // Inline hints tell the compiler to embed this math directly into loops for speed
    inline int getIndex(int x, int y, int z) const {
        return (x * sizeY * sizeZ) + (y * sizeZ) + z;
    }

    void setVoxel(int x, int y, int z, uint8_t value) {
        if (x >= 0 && x < sizeX && y >= 0 && y < sizeY && z >= 0 && z < sizeZ) {
            data[getIndex(x, y, z)] = value;
        }
    }

    uint8_t getVoxel(int x, int y, int z) const {
        if (x >= 0 && x < sizeX && y >= 0 && y < sizeY && z >= 0 && z < sizeZ) {
            return data[getIndex(x, y, z)];
        }
        return 0; 
    }
    
    void metricToGrid(double x, double y, double z , int& gridX, int& gridY, int& gridZ){
        gridX = static_cast<int>(std::round(x / resolution));
        gridY = static_cast<int>(std::round(y / resolution));
        gridZ = static_cast<int>(std::round(z / resolution));
    }
};



std::vector<GridCoord> brensenhamsLineAlgorithm(int x1, int y1, int z1, int x2, int y2, int z2){
    std::vector<GridCoord> traversedPoints;
    int dx = (x2-x1);
    int dy = (y2-y1);
    int dz = (z2-z1);
    int xs, ys, zs;
    
    //set directions for x,y,z to travel
    if(dx > 0){
        xs = 1;
    }else{
        xs = -1;
    }

    if(dy > 0){
        ys = 1;
    }else{
        ys = -1;
    }

    if(dz > 0){
        zs = 1;
    }else{
        zs = -1;
    }

    dx = std::abs(dx);
    dy = std::abs(dy);
    dz = std::abs(dz);

    traversedPoints.push_back({x1, y1, z1});

    // This determines whats the driving axis
    if(dx >= dy && dx >= dz){
        int p1 = 2*dy-dx; 
        int p2 = 2*dz-dx; 
        while(x2 != x1){
            x1 += xs; 
            if(p1 >= 0){
                y1 += ys; 
                p1 -= 2 * dx;
            }
            if(p2 >= 0){
                z1 += zs; 
                p2 -= 2 * dx;
            }
            p1 += 2 * dy;
            p2 += 2 * dz;
            traversedPoints.push_back({x1, y1, z1}); 
        }
    }else if(dy >= dx && dy >= dz){
        int p1 = 2*dx-dy; 
        int p2 = 2*dz-dy; 
        while(y2 != y1){ 
            y1 += ys; 
            if(p1 >= 0){
                x1 += xs; 
                p1 -= 2 * dy;
            }
            if(p2 >= 0){
                z1 += zs; 
                p2 -= 2 * dy;
            }
            p1 += 2 * dx;
            p2 += 2 * dz;
            traversedPoints.push_back({x1, y1, z1});
        }
    }else{
        int p1 = 2*dx-dz; 
        int p2 = 2*dy-dz; 
        while(z2 != z1){
            z1 += zs; 
            if(p1 >= 0){
                x1 += xs; 
                p1 -= 2 * dz;
            }
            if(p2 >= 0){
                y1 += ys; 
                p2 -= 2 * dz;
            }
            p1 += 2 * dx;
            p2 += 2 * dy;
            traversedPoints.push_back({x1, y1, z1}); 
        }
    }
    return traversedPoints;
}


int main() {
    VoxelGrid map(100, 100, 50, 0.1);

    std::vector<Point> fakeScan{
        {2.0, 0.1, 0.0},
        {3.0, 2.0, 0.0}
    }; 
    
    
    std::cout << "Is obstacle present: " << (int)map.getVoxel(50, 50, 10) << std::endl;
    return 0;
}