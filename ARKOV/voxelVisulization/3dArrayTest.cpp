/*
We are going to utelize a 3d voxel based recreation of the enviornment. This is a basic test of the structure
to how it will be stored most likely. There may be more moifications we can make to make it smaller
and more efficent, but I beleive the major efficencies will come from how we handle ray tracing
aswell as the localization and loops.
*/



#include <iostream>
#include <vector>
#include <cstdint> 

// using struct for less boilerplate
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
};

int main() {
    VoxelGrid map(100, 100, 50, 0.1);
    
    // Example: LiDAR point registers an obstacle hit
    map.setVoxel(50, 50, 10, 1);
    
    std::cout << "Is obstacle present: " << (int)map.getVoxel(50, 50, 10) << std::endl;
    return 0;
}