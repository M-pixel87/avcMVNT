#ifndef CAMERAS_HH
#define CAMERAS_HH

#include <opencv2/opencv.hpp>

class cv_Webcam{

public:
cv_Webcam(int cam_ID);
bool update_frame(cv::Mat& frame);
void display_frame(cv::Mat& frame);
void cleanup();

    
private:
cv::VideoCapture cap;

};

#endif 