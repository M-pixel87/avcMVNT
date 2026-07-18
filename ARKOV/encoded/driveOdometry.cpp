#include "driveOdometry.h"

OdometryDelta driveOdometry::calcDistanceTraveled(int curTicsL , int curTicsR){
    lDist = (CIRCUMFERENCE*(curTicsL-lastTicsL));
    rDist = (CIRCUMFERENCE*(curTicsR-lastTicsR));
    deltaDist = (lDist + rDist)/2;
    deltaAngle = (rDist - lDist)/WHEELBASE;
    return OdometryDelta{deltaDist,deltaAngle};
}