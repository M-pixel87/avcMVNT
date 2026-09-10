#ifndef TYPES_HH
#define TYPES_HH
#include <vector>

struct OdometryDelta{
    double deltaDist;
    double deltaAngle;
};

struct Point {
    double x, y, z;
};

struct GridCoord {
    int x, y, z;
};

struct Particle {
    double x, y, z, theta;
    float weight; // Added to fix compile error in particleFilter.cpp
};

struct LiDARPoint {
    float x, y, z;
    float world_x, world_y, world_z; // Added to fix compile error in slamManager.cpp
};

#endif