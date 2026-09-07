#include "driveOdometry.h"
#include <cmath>

/*! \addtogroup MOVEMENT */
OdometryDelta driveOdometry::calcDistanceTraveled(int curTicsL , int curTicsR){
    lDist = (CIRCUMFERENCE * static_cast<float>(curTicsL - lastTicsL)) / TICKS_PER_REVOLUTION;
    rDist = (CIRCUMFERENCE * static_cast<float>(curTicsR - lastTicsR)) / TICKS_PER_REVOLUTION;
    
    deltaDist = (lDist + rDist) / 2.0f;
    deltaAngle = (rDist - lDist) / WHEELBASE;
    
    lastTicsL = curTicsL;
    lastTicsR = curTicsR;
    
    return OdometryDelta{deltaDist, deltaAngle};
}