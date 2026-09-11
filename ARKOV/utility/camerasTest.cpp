#include "cameras.hh"

int main() {
    cv_Webcam cam(0);
    cv::Mat frame;

    while (true) {
        if (cam.update_frame(frame)) {
            cam.display_frame(frame);
        }
        
        if (cv::waitKey(1) == 27 || cv::waitKey(1) == 'q') {
            break;
        }
    }

    cam.cleanup();
    return 0;
}