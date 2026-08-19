from Arm import CoOrdinateBaseSys as Arm
from Systems.InputSystem import AI_YOLO
from Systems.InputSystem import cvWebcam
from Systems.displaySystem import DisplaySystem
import time

#arm = Arm.CoOrdinateBaseSys()
infer = AI_YOLO(conf_threshold=0.3)
cam = cvWebcam(cam_id=0, width=640, height=480)
display = DisplaySystem(cam=cam, mode="YOLO")

targetId = "red_ball"  # Change this to the desired target object label

def test_arm_grab():
    while(True):
        frame = cam.get_frame()
        detections = infer.detect(frame)

        for det in detections:
            if det["label"] == targetId:
                x_center = (det["bbox"][0] + det["bbox"][2]) / 2
                y_center = (det["bbox"][1] + det["bbox"][3]) / 2

                # Convert pixel coordinates to world coordinates (example conversion)
                world_x = (x_center - 320) / 10.0
                world_y = (y_center - 240) / 10.0
                world_z = 10.0  # Fixed height for simplicity

                angles = [0, 0, 90, 0, 0, 0]
                ik_angles = Arm.ik(world_x, world_y, world_z, angles, error=0.5)

                print(world_x)
                print(world_y)
                print(world_z)

                Arm.move_to_angles(ik_angles)

        display.update_display(img=frame, detections=detections)
        time.sleep(0.01)


def main():
    test_arm_grab()

if __name__ == "__main__":
    main()

