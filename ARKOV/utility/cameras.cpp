#include "cameras.hh"

cameras::cv_Webcam(int cam_ID){
    cap(cam_ID)
}

bool cameras::cv_Webcam::update_frame(cv::Mat& frame){
    return cap.read(frame);
}

void cameras::cv_Webcam::display_frame(cv::Mat& frame){
    cv::imshow(frame)
}

void cameras::cv_Webcam::cleanup(){
    cap.release();
    cv::destroyAllWindows();
}