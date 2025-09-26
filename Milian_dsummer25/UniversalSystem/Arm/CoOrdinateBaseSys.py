from roarm_sdk.roarm import roarm
import math
import time
import random

# https://github.com/waveshareteam/waveshare_roarm_sdk/tree/main

# Serial communication example
roarm = roarm(roarm_type="roarm_m3", port="/dev/ttyUSB0", baudrate=115200)

# Http communication example
# Note: HTTP communication needs to be connected to the same wifi first, and host is the IP address of the robotic arm.
#roarm = roarm(roarm_type="roarm_m3", host="192.168.4.1")

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def generate_random_xyz(x_range, y_range, z_range):
    x = random.uniform(*x_range)
    y = random.uniform(*y_range)
    z = random.uniform(*z_range)
    return round(x, 2), round(y, 2), round(z, 2)



angles = [0,0,90,0,0,0]

def ik(x, y, z, angles, error):  # angles = [theta1, theta2, theta3]
    errorI = error

    arm1 = 10
    arm2 = 14
    wrist = 7.5

    # Step 1: Solve base rotation (joint 0)
    base_angle_rad = math.atan2(y, x)
    base_angle = math.degrees(base_angle_rad)
    angles[0] = base_angle

    # Step 2: Project (x, y) into rotated base frame (XZ plane)
    rotated_x = math.hypot(x, y)  # This is the forward distance in the new base direction

    # Step 3: Get shoulder (arm1) angle and position
    arm1_angle_deg = clamp(angles[1] + 90, -180, 180)
    arm1_rad = math.radians(arm1_angle_deg)
    arm1x = arm1 * math.cos(arm1_rad) * -1
    arm1z = arm1 * math.sin(arm1_rad)

    # World angle of shoulder link
    arm1_angle_world = math.degrees(math.atan2(arm1z, arm1x))

    # Step 4: Calculate vector from arm1 tip to target
    dx = rotated_x - arm1x
    dz = z - arm1z

    # Desired direction for arm2
    desired_angle_rad = math.atan2(dz, dx)
    desired_angle_deg = math.degrees(desired_angle_rad)

    # Step 5: Set elbow (arm2) angle to aim toward target
    new_elbow = clamp(arm1_angle_world - desired_angle_deg, -70, 190)
    angles[2] = new_elbow

    # Step 6: Forward solve for new end-effector position
    arm2_angle_world = math.radians(arm1_angle_world - new_elbow)
    finalx = arm1x + arm2 * math.cos(arm2_angle_world)
    finalz = arm1z + arm2 * math.sin(arm2_angle_world)

    error = math.hypot(finalx - rotated_x, finalz - z)
    print("Distance error from target:", error)

    # Debug prints
    print("Base angle (deg):", base_angle)
    print("arm1x:", arm1x)
    print("arm1z:", arm1z)
    print("arm1Angle (deg):", arm1_angle_world)
    print("arm2Angle (deg):", math.degrees(arm2_angle_world))
    print("FinalX:", finalx)
    print("FinalZ:", finalz)
    print("TargetX:", rotated_x)
    print("TargetZ:", z)
    print("Elbow angle (deg):", new_elbow)

    # Step 7: Adjust shoulder to reduce error
    if error > 0.20:
        if rotated_x > finalx:
            angles[1] += 1 + (1 * error)
            print("PLUS")
        else:
            angles[1] -= 1 + (1 * error)
            print("MINUS")
        ik(x, y, z, angles, error)




def main():
    #xyzTest()
    ik(12,0,-1, angles, 0)
    roarm.joints_angle_ctrl(angles, 300, 100)



if __name__ == "__main__":
    main()

#method to move specific joint by angles EX: jaw 
def move_joint(joint_index, angle, speed=450, acc=250):
    if joint_index < 0 or joint_index >= 6:
        print("Invalid joint index. Must be between 0 and 5.")
        return False

    angles[joint_index] = clamp(angle, -180, 180)
    roarm.joints_angle_ctrl(angles, speed, acc)
    return True

#Method to move arm position using ik to xyz
def move_arm_to(x, y, z, speed=300, acc=250):
    arm1 = 10
    arm2 = 14
    max_reach = arm1 + arm2

    # Distance from base to target (ignoring vertical offset of base joint)
    distance = math.sqrt(x**2 + y**2 + z**2)

    if distance > max_reach:
        print(f"⚠️ Target ({x:.2f}, {y:.2f}, {z:.2f}) is out of reach! (dist={distance:.2f}, max={max_reach})")
        return False  # don’t move

    ik(x, y, z, angles, 0)
    roarm.joints_angle_ctrl(angles, speed, acc)
    return True  # success
