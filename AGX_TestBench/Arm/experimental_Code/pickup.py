from RoArmM3 import Arm
import time

def main():
    arm = Arm(port="/dev/ttyUSB0",baudrate=115200)
    arm.move_init()
    time.sleep(8)
    while(True):
        #grab and pickup
        arm.move_to_xyz(-69,16,0,-2)
        arm.gripper_angle_ctrl(45,100,50)
        time.sleep(2)
        arm.move_to_xyz(-69,16,-1,-3.5)
        time.sleep(2)
        arm.gripper_angle_ctrl(10,100,5)
        time.sleep(2)
        arm.move_to_xyz(-0,12,-1,12)
        time.sleep(2)

        arm.draw_line(0,12,12,12,12,-12,12)
        arm.move_to_xyz(45,0,0,16)



        #place back
        arm.move_to_xyz(-69,16.1,-1,-3.5)
        time.sleep(2)
        arm.gripper_angle_ctrl(45,100,50)
        time.sleep(1)
        arm.move_to_xyz(-69,16,-1,-1)
        time.sleep(1)
        arm.move_to_xyz(-0,12,-1,12)
        time.sleep(2)




if __name__ == "__main__":
    main()