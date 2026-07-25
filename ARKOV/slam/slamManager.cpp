#include "slamManager.hh"

// Constructor takes pointers to the components it needs to coordinate
slamManager::slamManager(particleFilter* p_filter, driveOdometry* d_odom, VoxelMap* v_map, Lidar* l_sensor) {
    pf = p_filter;
    driveOdom = d_odom;
    map = v_map;
    ld = l_sensor;
}

void slamManager::startUp() {
    // 1. Grab the very first LiDAR scan
    std::vector<LiDARPoint> scan = ld->getLatestScan();
    
    // 2. Get the initialized starting pose
    Particle bestP = pf->getBestPose();
    
    // 3. Seed the map with the first scan
    for (const auto& pt : scan) {
        // You'll need to transform the raw point based on bestP (like we did in updateWeights)
        // Then pass the sensor origin and the point endpoint to Bresenham
        map->bresenham3D(bestP.x, bestP.y, SENSOR_Z_OFFSET, pt.world_x, pt.world_y, pt.world_z); // Ray end (Hit point)
    }
}

void slamManager::update() {
    float dx, dy, dtheta;

    driveOdom->getDeltas(&dx, &dy, &dtheta);

    pf->predict(dx, dy, dtheta);
    std::vector<LiDARPoint> scan = ld->getLatestScan();
    pf->updateWeights(*map, scan);
    pf->resample();
    
    Particle bestP = pf->getBestPose();
    for (const auto& pt : scan) {
        // Transform point based on bestP, then raytrace:
        // map->bresenham3D(...);
    }
}