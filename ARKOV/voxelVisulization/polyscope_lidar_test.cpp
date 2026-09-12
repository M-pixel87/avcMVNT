#include "voxel_map.hh"
#include "polyscope/polyscope.h"
#include "polyscope/point_cloud.h"
#include "unitree_lidar_sdk.h"
#include <vector>
#include <array>
#include <random>
#include <thread>
#include <chrono>
#include <iostream>

/*
    9/11/2026
    This is just to serve as an example use of the unilidar sdk working in some custom code and 
    also showing polyscope updating from lidar with the voxel map. This does NOT work great, This
    will NOT be used on anything more than a test.

    What to take from this code:
    - Calling unilidar sdk code to succesfully parse clouds
    - calling bresenhams 3d line algorithm and interfacing with it
    - updating a polyscope map every frame with the updateMatrix function
*/

unilidar_sdk2::UnitreeLidarReader *ld = unilidar_sdk2::createUnitreeLidarReader();
VoxelGrid map(100, 100, 100, 0.05);
unilidar_sdk2::PointCloudUnitree cloud;

void initialize(){
    std::cout << "--- HARDWARE DIAGNOSTIC START ---" << std::endl;
    std::string port = "/dev/ttyACM0"; 
    
    // 1. Open the serial port FIRST
    std::cout << "1. Opening port " << port << "..." << std::endl;
    int success = ld->initializeSerial(port); 
    
    if (success != 0) {
        std::cerr << "CRITICAL ERROR: Could not connect to LiDAR on " << port << "!" << std::endl;
        exit(1); 
    }
    
    // 2. Now that the port is open, configure the work mode and start rotation
    std::cout << "2. Configuring LiDAR to Serial Mode (workMode = 8)..." << std::endl;
    ld->setLidarWorkMode(8); 
    ld->startLidarRotation();
  
    std::cout << "3. Waiting up to 5 seconds for data stream..." << std::endl;
    int attempts = 0;
    
    while(true) {
        // Must call runParse() so the SDK reads incoming bytes from the port buffer
        ld->runParse();
        ld->getPointCloud(cloud);
        
        if (cloud.points.size() > 0) {
            std::cout << ">>> SUCCESS: Received " << cloud.points.size() << " points!" << std::endl;
            std::cout << ">>> Launching Polyscope..." << std::endl;
            break;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        attempts++;
        
        if (attempts > 100) { 
            std::cout << "!!! ERROR: Port open, but no point cloud data arrived. Check power/baudrate. !!!" << std::endl;
            exit(1); 
        }
    }
}

void updateMatrix(){
    // Crucial: Keep pumping the parser every frame during visualization
    ld->runParse();
    ld->getPointCloud(cloud);
    
    if (cloud.points.empty()) return; 
    
    for (int i = static_cast<int>(cloud.points.size()) - 1; i >= 0; --i) {
        map.bresenham3D(0, 0, 0, cloud.points[i].x, cloud.points[i].y, cloud.points[i].z);
    }

    std::vector<std::array<double, 3>> voxelPoints;
    for (int x = 0; x < map.sizeX; ++x) {
        for (int y = 0; y < map.sizeY; ++y) {
            for (int z = 0; z < map.sizeZ; ++z) {
                if (map.getVoxel(x, y, z) > 0) { 
                    voxelPoints.push_back({
                        (x - map.sizeX / 2.0) * map.resolution,
                        (y - map.sizeY / 2.0) * map.resolution,
                        (z - map.sizeZ / 2.0) * map.resolution
                    });
                }
            }
        }
    }

    if (!voxelPoints.empty()) {
        auto* pc = polyscope::registerPointCloud("Voxel Grid Demo", voxelPoints);
        pc->setPointRenderMode(polyscope::PointRenderMode::Sphere);
        pc->setPointRadius(map.resolution * 0.25);
    }
}

int main() {
    initialize();
    polyscope::init();
    polyscope::state::userCallback = updateMatrix;
    polyscope::show();
    return 0;
}