#include "cameras.hh"
#include <iostream>

cv_Webcam::cv_Webcam(int cam_ID) : cap(cam_ID) {
    if (!cap.isOpened()) {
        std::cerr << "[ERROR] No cam at ID: " << cam_ID << std::endl;
    }
}

bool cv_Webcam::update_frame(cv::Mat& frame) {
    if (!cap.isOpened()) {
        return false;
    }
    return cap.read(frame);
}

void cv_Webcam::display_frame(const cv::Mat& frame) {
    if (!frame.empty()) {
        cv::imshow("Camera Feed", frame);
        cv::waitKey(1); 
    }
}

void cv_Webcam::cleanup() {
    if (cap.isOpened()) {
        cap.release();
    }
    cv::destroyAllWindows();
}