#ifndef VOXEL_MAP_HH
#define VOXEL_MAP_HH


#include <cstdint>
#include "types.hh"

/*!
    \addtogroup SLAM
*/


//! Voxel Grid Structure Definition
struct VoxelGrid {
    int sizeX, sizeY, sizeZ;
    double resolution; 
    std::vector<uint8_t> data; 

    VoxelGrid(int x, int y, int z, double res);

    // inline in the header for compiler optimization loop performance, define in here for compiler
    inline int getIndex(int x, int y, int z) const {
        return (x * sizeY * sizeZ) + (y * sizeZ) + z;
    }

    void updateVoxelMiss(int x, int y, int z, uint8_t penalty);
    void updateVoxelHit(int x, int y, int z, uint8_t reward);
    void setVoxel(int x, int y, int z, uint8_t value);
    uint8_t getVoxel(int x, int y, int z) const;
    void metricToGrid(double x, double y, double z, int& gridX, int& gridY, int& gridZ);
};

//! Line algorithm for getting what voxels have been passed through
std::vector<GridCoord> brensenhamsLineAlgorithm(int x1, int y1, int z1, int x2, int y2, int z2);

#endif 
//! @}