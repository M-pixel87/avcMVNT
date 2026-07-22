#pragma once


class voxel_map;
class particleFilter;
class driveOdometry;
class lidar;

class slamManager {
public:
    slamManager(particleFilter* p_filter, driveOdometry* d_odom, voxel_map* v_map, lidar* l_sensor);

    void startUp();
    void update();

private:
    particleFilter* pf;
    driveOdometry* driveOdom;
    voxel_map* map;
    lidar* ld;
};