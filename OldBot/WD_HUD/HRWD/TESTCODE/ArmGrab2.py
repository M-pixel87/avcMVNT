from Arm import CoOrdinateBaseSys as Arm
from Systems.InputSystem import AI_YOLO
from Systems.InputSystem import cvWebcam
from Systems.displaySystem import DisplaySystem
import time

infer = AI_YOLO(conf_threshold=0.3)
cam = cvWebcam(cam_id=0, width=640, height=480)
display = DisplaySystem(cam=cam, mode="YOLO")

targetId = "red_ball" 

targetX = 10
targetY = 0
targetZ = 10.0

#SET ARM TO INITIAL POSITION
Arm.move_arm_to(targetX,targetY,targetZ)



def test_arm_grab():
    global targetX, targetY, targetZ
    
    # --- Timer Setup ---
    last_command_time = 0
    command_delay = 0.1  # 0.5s = 2 times per second

    while(True):
        frame = cam.get_frame()
        detections = infer.detect(frame)
        
        # Get the current time for this loop iteration
        current_time = time.time()

        for det in detections:
            if det["label"] == targetId:
                x_center = (det["bbox"][0] + det["bbox"][2]) / 2
                
                # Logic updates can still happen fast if you want smooth variable tracking
                if(x_center <= 300 ):
                    targetY += 0.25
                elif(x_center >= 340):
                    targetY -= 0.25
                else:
                    print("CENTERED Y")
                    
                # --- Throttled Command ---
                # Only run IK/Move if 0.5 seconds have passed since the last time
                if current_time - last_command_time > command_delay:
                    Arm.move_arm_to(targetX,targetY,targetZ)
                    last_command_time = current_time

        # Display updates continue running at full speed
        display.update_display(img=frame, detections=detections)
        time.sleep(0.01)

def main():
    test_arm_grab()

if __name__ == "__main__":
    main()