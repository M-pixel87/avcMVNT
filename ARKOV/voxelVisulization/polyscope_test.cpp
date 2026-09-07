#include "voxelVisulization/voxel_map.hh"
#include "polyscope/polyscope.h"
#include "polyscope/point_cloud.h"
#include <vector>
#include <array>

int main() {
    VoxelGrid map(20, 20, 20, 0.1);

    for (int i = 0; i < 20; ++i) {
        map.setVoxel(i, i, i, 255);
        map.setVoxel(i, 19 - i, 0, 255);
    }

    std::vector<std::array<double, 3>> voxelPoints;
    for (int x = 0; x < map.sizeX; ++x) {
        for (int y = 0; y < map.sizeY; ++y) {
            for (int z = 0; z < map.sizeZ; ++z) {
                if (map.getVoxel(x, y, z) > 127) {
                    voxelPoints.push_back({
                        x * map.resolution,
                        y * map.resolution,
                        z * map.resolution
                    });
                }
            }
        }
    }

    polyscope::init();
    auto* pc = polyscope::registerPointCloud("Voxel Grid Demo", voxelPoints);
    pc->setPointStyle(polyscope::PointStyle::Cube);
    pc->setPointRadius(map.resolution * 0.5);
    polyscope::show();

    return 0;
}