#pragma once
#include "types.hh"

class driveOdometry{
private:
    static constexpr float PI = 3.14159265f;
    static constexpr float DIAMETER = 0.25f;       
    static constexpr float WHEELBASE = 0.50f;      
    static constexpr float CIRCUMFERENCE = PI * DIAMETER;

    int lastTicsL = 0;
    int lastTicsR = 0;
    float rDist,lDist;
    float deltaDist;
    float deltaAngle;
public:
    driveOdometry() = default; // makes compiler default constructor
    OdometryDelta calcDistanceTraveled(int curTicsL , int curTicsR);
    
};
