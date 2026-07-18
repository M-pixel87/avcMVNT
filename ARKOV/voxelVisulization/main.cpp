#include "voxel_map.hh"
#include <iostream>

int main() {
    VoxelGrid map(100, 100, 50, 0.1);
    std::vector<GridCoord> positionsTraversed = brensenhamsLineAlgorithm(0, 0, 0, 3, 3, 3);
    
    for (size_t i = 0; i < positionsTraversed.size()-1; i++) {
        map.updateVoxelMiss(positionsTraversed[i].x, positionsTraversed[i].y, positionsTraversed[i].z, 10);
    }
    map.updateVoxelHit(positionsTraversed[i].x, positionsTraversed[i].y, positionsTraversed[i].z, 10);
    
    std::cout << "Is obstacle present: " << (int)map.getVoxel(3, 3, 3) << std::endl;
    return 0;
}