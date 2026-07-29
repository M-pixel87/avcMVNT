#include "voxel_map.hh"
#include <cmath>
#include <cstdlib>

/*!
    \addtogroup SLAM
*/

//! Voxel Struct constructor, compiled values using member list initalizer
VoxelGrid::VoxelGrid(int x, int y, int z, double res) 
    : sizeX(x), sizeY(y), sizeZ(z), resolution(res), data(x * y * z, 0) {}

//! set voxel occupancy value to value
void VoxelGrid::setVoxel(int x, int y, int z, uint8_t value) {
    if (x >= 0 && x < sizeX && y >= 0 && y < sizeY && z >= 0 && z < sizeZ) {
        data[getIndex(x, y, z)] = value;
    }
}

//! Update voxel occupancy value with penalty value
void updateVoxelMiss(int x, int y, int z, uint8_t penalty) {
    if (x >= 0 && x < sizeX && y >= 0 && y < sizeY && z >= 0 && z < sizeZ) {
        uint8_t& voxel = data[getIndex(x, y, z)];
        voxel = (voxel > penalty) ? (voxel - penalty) : 0;
    }
}
//! Update voxel occupancy value with reward value
void updateVoxelHit(int x, int y, int z, uint8_t reward) {
    if (x >= 0 && x < sizeX && y >= 0 && y < sizeY && z >= 0 && z < sizeZ) {
        uint8_t& voxel = data[getIndex(x, y, z)];
        voxel = (255 - voxel > reward) ? (voxel + reward) : 255;
    }
}

//! Return voxel occupancy value
uint8_t VoxelGrid::getVoxel(int x, int y, int z) const {
    if (x >= 0 && x < sizeX && y >= 0 && y < sizeY && z >= 0 && z < sizeZ) {
        return data[getIndex(x, y, z)];
    }
    return 0; 
}

//! Convert meters to grid space
void VoxelGrid::metricToGrid(double x, double y, double z, int& gridX, int& gridY, int& gridZ) {
    gridX = static_cast<int>(std::round(x / resolution));
    gridY = static_cast<int>(std::round(y / resolution));
    gridZ = static_cast<int>(std::round(z / resolution));
}

std::vector<GridCoord> brensenhamsLineAlgorithm(int x1, int y1, int z1, int x2, int y2, int z2) {
    std::vector<GridCoord> traversedPoints;
    int dx = (x2 - x1);
    int dy = (y2 - y1);
    int dz = (z2 - z1);
    int xs, ys, zs;
    
    if (dx > 0) xs = 1; else xs = -1;
    if (dy > 0) ys = 1; else ys = -1;
    if (dz > 0) zs = 1; else zs = -1;

    dx = std::abs(dx);
    dy = std::abs(dy);
    dz = std::abs(dz);

    traversedPoints.push_back({x1, y1, z1});

    if (dx >= dy && dx >= dz) {
        int p1 = 2 * dy - dx; 
        int p2 = 2 * dz - dx; 
        while (x2 != x1) {
            x1 += xs; 
            if (p1 >= 0) { y1 += ys; p1 -= 2 * dx; }
            if (p2 >= 0) { z1 += zs; p2 -= 2 * dx; }
            p1 += 2 * dy;
            p2 += 2 * dz;
            traversedPoints.push_back({x1, y1, z1}); 
        }
    } else if (dy >= dx && dy >= dz) {
        int p1 = 2 * dx - dy; 
        int p2 = 2 * dz - dy; 
        while (y2 != y1) { 
            y1 += ys; 
            if (p1 >= 0) { x1 += xs; p1 -= 2 * dy; }
            if (p2 >= 0) { z1 += zs; p2 -= 2 * dy; }
            p1 += 2 * dx;
            p2 += 2 * dz;
            traversedPoints.push_back({x1, y1, z1});
        }
    } else {
        int p1 = 2 * dx - dz; 
        int p2 = 2 * dy - dz; 
        while (z2 != z1) {
            z1 += zs; 
            if (p1 >= 0) { x1 += xs; p1 -= 2 * dz; }
            if (p2 >= 0) { y1 += ys; p2 -= 2 * dz; }
            p1 += 2 * dx;
            p2 += 2 * dy;
            traversedPoints.push_back({x1, y1, z1}); 
        }
    }
    return traversedPoints;
}
//! @}