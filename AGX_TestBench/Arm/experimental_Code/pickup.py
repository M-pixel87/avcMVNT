from RoArmM3 import Arm
import time

def main():
    #creates an object of the arm class. This just has functions to send commands to the arm
    arm = Arm(port="/dev/ttyUSB1",baudrate=115200)

    #arm.move_init makes thje arm move to the neutral position
    arm.move_init()
    arm.move_to_xyz(-30,10,10,-2)
    time.sleep(8)

    while(True):
        # move_to_xyz is the function that utelizes our new inverse kinematics. 
        # This is the input for the function :(x,y,z,phi)

        #grab and pickup
        arm.move_to_xyz(-69,16,0,-2)
        #gripper angle ctrl controls the angle of the gripper with : (speed,acceleration,angle)
        arm.gripper_angle_ctrl(45,100,50) 
        time.sleep(2)
        arm.move_to_xyz(-69,16,-1,-3.5)
        time.sleep(2)
        arm.gripper_angle_ctrl(10,100,5)
        time.sleep(2)
        arm.move_to_xyz(-0,12,-1,12)
        time.sleep(2)
        #draw_line(phi,x1,y1,z1,x2,y2,z2)
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