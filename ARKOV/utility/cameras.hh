#ifndef CAMERAS_HH
#define CAMERAS_HH

#include <opencv2/opencv.hpp>

class cv_Webcam {
public:
    explicit cv_Webcam(int cam_ID);
    ~cv_Webcam() { cleanup(); } 

    bool update_frame(cv::Mat& frame);
    void display_frame(const cv::Mat& frame);
    void cleanup();

private:
    cv::VideoCapture cap;
};

#endif // CAMERAS_HH