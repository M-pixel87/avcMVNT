/*
This is the main file for ALL of arkov, AVC 2026-2027. This is the main script , atleast as of planned
on 7/18/26. This can be changed and may require a python main file. Reguardless for now this will call all
c++ systems.
*/
#include "types.hh"
#include "microControllerCom.h"
#include "pidController.hh"
#include "particleFilter.hh"

microcontroller stm32(); // create serial com with stm32
pidController leftPID(0.30, 0.05, 0.10); // create pid controller for left motor
pidController rightPID(0.30, 0.05, 0.10); // create pid controller for right motor
particleFilter(500, 10, 10, 0);

int main(){


}