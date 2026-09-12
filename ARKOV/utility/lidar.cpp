#include "lidar.hh"

lidar::lidar(std::string port){
    ld = unilidar_sdk2::createUnitreeLidarReader();
    p = port
}

lidar::initalize(){
    ld->initializeSerial(p); 
    ld->setLidarWorkMode(8); 
    ld->startLidarRotation();
    get_pointcloud();
}

lidar::get_pointcloud(){
    ld->runParse();
    ld->getPointCloud(cloud);
}

lidar::cleanup(){
    return void;
}

