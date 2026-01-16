from Arm import CoOrdinateBaseSys as Arm
from Systems.InputSystem import AI_YOLO
from Systems.InputSystem import cvWebcam
from Systems.displaySystem import DisplaySystem
import time


infer = AI_YOLO(conf_threshold=0.3)
cam = cvWebcam(cam_id=0, width=640, height=480)
display = DisplaySystem(cam=cam, mode="YOLO")

targetId = "blue_ball"  # Change this to the desired target object label

targetX = 0
targetY = 0
targetZ = 10.0  # Fixed height for simplicity



def test_arm_grab():
    while(True):
        frame = cam.get_frame()
        detections = infer.run_inference(frame)

        for det in detections:
            if det["label"] == targetId:
                x_center = (det["bbox"][0] + det["bbox"][2]) / 2
                y_center = (det["bbox"][1] + det["bbox"][3]) / 2

                if(x_center <= 300 ):
                    targetY -= 0.2
                elif(x_center >= 340):
                    targetY += 0.2
                else:
                    print("CENTERED Y")
                    return True
                
                
                    
                
        Arm.ik(targetX, targetY, targetZ, [0,0,90,0,0,0], error=0.3)
        display.update_display(frame=frame, detections=detections)
        time.sleep(0.25)


def main():
    test_arm_grab()

