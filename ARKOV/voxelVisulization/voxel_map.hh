#ifndef VOXEL_MAP_HH
#define VOXEL_MAP_HH
#include <cstdint>
#include <vector>
#include "types.hh"

struct VoxelGrid {
    int sizeX, sizeY, sizeZ;
    double resolution;
    std::vector<uint8_t> data;

    VoxelGrid(int x, int y, int z, double res);

    int getIndex(int x, int y, int z) const {
        return (x * sizeY * sizeZ) + (y * sizeZ) + z;
    }

    void updateVoxelMiss(int x, int y, int z, uint8_t penalty);
    void updateVoxelHit(int x, int y, int z, uint8_t reward);
    void setVoxel(int x, int y, int z, uint8_t value);
    uint8_t getVoxel(int x, int y, int z) const;
    void metricToGrid(double x, double y, double z, int& gridX, int& gridY, int& gridZ) const;
    
    int getVoxelState(double x, double y, double z) const {
        int gx, gy, gz;
        metricToGrid(x, y, z, gx, gy, gz);
        if (gx >= 0 && gx < sizeX && gy >= 0 && gy < sizeY && gz >= 0 && gz < sizeZ) {
            uint8_t val = getVoxel(gx, gy, gz);
            if (val > 127) return 1; // 1 = OCCUPIED
            return 0; // 0 = EMPTY
        }
        return -1;
    }

    // Raytracing bridge used by slamManager.cpp
    void bresenham3D(double x1, double y1, double z1, double x2, double y2, double z2);
};



std::vector<GridCoord> brensenhamsLineAlgorithm(int x1, int y1, int z1, int x2, int y2, int z2);

#endif