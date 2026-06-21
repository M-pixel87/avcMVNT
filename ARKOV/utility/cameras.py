import cv2 as cv
import pyrealsense2 as rs 
import numpy as np

class cv_Webcam:
    def __init__ (self, cam_ID, size_X, size_Y, fps):
        self.cam = cv.VideoCapture(cam_ID,cv.CAP_V4L2)

        self.cam = cv.VideoCapture(cam_ID, cv.CAP_V4L2) 
        self.cam.set(cv.CAP_PROP_FRAME_WIDTH, size_X) 
        self.cam.set(cv.CAP_PROP_FRAME_HEIGHT, size_Y) 
        self.cam.set(cv.CAP_PROP_FPS, fps) 
        self.cam.set(cv.CAP_PROP_BUFFERSIZE, 1) 

        self.active = 0
    
    def toggle(self):
        '''
        Swaps value of active variable \n
        default state is 0
        '''
        if(self.active): self.active = 0
        else: self.active = 1

    def update(self):
        '''
        Returns a frame
        '''
        if(self.active):
            try:
                frame = self.cam.read()
                return frame
            except Exception as e:
                print(e)
        return "" #EMPTY FRAME WOULD BE BEST, LIKE BLACK SCREEN

    def release(self):
        self.active = 0
        self.cam.release()





class intel_Cam:
    def __init__(self, size_X, size_Y, fps):
        self.pipeline = rs.pipeline() 
        self.config = rs.config() 
        self.config.enable_stream(rs.stream.depth, size_X, size_Y, rs.format.z16, fps) 
        self.config.enable_stream(rs.stream.color, size_X, size_Y, rs.format.bgr8, fps) 

        self.active = 0

    def toggle(self):
        if(not self.active):
            try: 
                self.profile = self.pipeline.start(self.config) 
                print(f"Intel RealSense initialized [{self.size_X}x{self.size_Y}]") 
            except Exception as e: 
                print(f"Initial Intel Cam startup failed: {e}") 
        else: self.active = 0
    
    def update(self):
        if(self.active):
            try:
                frames = self.pipeline.wait_for_frames(timeout_ms=1000) 
                depth_frame = frames.get_depth_frame() 
                color_frame = frames.get_color_frame()
                if depth_frame and color_frame: 
                        d_img = np.asanyarray(depth_frame.get_data()) 
                        c_img = np.asanyarray(color_frame.get_data()) 
                return [d_img, c_img]
            except Exception as e:
                print(e)
        return ["",""]# NEED TO RETURN BLACK SCREEN AND 0'd or MAX RANGED IMAGES
    
    def release(self): 
        self.active = 0
        try: self.pipeline.stop() 
        except: pass 