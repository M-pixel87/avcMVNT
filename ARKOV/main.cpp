/*
This is the main file for ALL of arkov, AVC 2026-2027. This is the main script , atleast as of planned
on 7/18/26. This can be changed and may require a python main file. Reguardless for now this will call all
c++ systems.
*/
#include "types.hh"
#include "microControllerCom.h"
#include "pidController.hh"
#include "slamManager.hh"
#include "voxel_map.hh"
#include "lidar.hh"
#include "particleFilter.hh"
#include "driveOdometry.hh"



microcontroller stm32(); // create serial com with stm32
pidController leftPID(0.30, 0.05, 0.10); // create pid controller for left motor
pidController rightPID(0.30, 0.05, 0.10); // create pid controller for right motor
voxel_map map(); // Create 3d voxel map representation
lidar ld(); // lidar for unitree 4d l2
particleFilter pf(); // Create particle filter for localization
driveOdometry driveOdom(); // Drive odometry for counting tics
slamManager slamMan(&pf, &driveOdom, &map, &ld); // create and pass references to slam classes


int main(){


}