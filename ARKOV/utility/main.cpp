#include "cameras.hh"



int main(){

    cv_Webcam cam(0);
    bool read_Con;
    cv::Mat frame;
    
    while(true){
        read_Con = cam.update_frame(frame);

        if(read_Con){
            cam.display_frame(frame);
        }

        int key = cv::waitKey(1);
        if (key == 27 || key == 'q') {
            break;
        }
    }

    cam.cleanup();
}