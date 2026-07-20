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
};

#endif