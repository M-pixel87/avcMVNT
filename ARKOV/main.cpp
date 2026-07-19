/*
This is the main file for ALL of arkov, AVC 2026-2027. This is the main script , atleast as of planned
on 7/18/26. This can be changed and may require a python main file. Reguardless for now this will call all
c++ systems.
*/
#include "types.hh"
#include "voxel_map.hh"
#include "microControllerCom.h"
#include "driveOdometry.h"

microcontroller stm32(); // create serial com with stm32
VoxelGrid map(100,100,50,0.1); // create voxel map
driveOdometry encoderHandler(); // create math calculator for odometry

int main(){


}