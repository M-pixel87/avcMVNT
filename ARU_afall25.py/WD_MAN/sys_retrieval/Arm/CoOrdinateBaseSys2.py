from roarm_sdk.roarm import roarm
import math
import time
import random

# ========================
# Arm setup
# ========================

# Connect to arm (adjust port if needed)
roarm = roarm(roarm_type="roarm_m3", port="/dev/ttyUSB0", baudrate=115200)

# Arm link lengths (in inches)
L1 = 10.0  # first arm segment
L2 = 14.0  # second arm segment

# Track current arm position
current_arm_pos = [10.0, 0.0, 10.0]  # start = home position [x, y, z] in inches
HOME_POS = (10.0, 0.0, 10.0)


# ========================
# Helpers
# ========================

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def generate_random_xyz(x_range, y_range, z_range):
    x = random.uniform(*x_range)
    y = random.uniform(*y_range)
    z = random.uniform(*z_range)
    return round(x, 2), round(y, 2), round(z, 2)


def get_current_arm_pos():
    global current_arm_pos
    return tuple(current_arm_pos)


def set_current_arm_pos(x, y, z):
    global current_arm_pos
    current_arm_pos = [x, y, z]


# ========================
# Inverse Kinematics
# ========================

def ik_closed_form(x, y, z, elbow_up=False):
    """
    Closed-form IK solver for a 2-link arm in 3D space.
    Returns [base, shoulder, elbow, 0, 0, 0] joint angles in degrees.
    """

    # Step 1: Base rotation (XY plane)
    theta0 = math.degrees(math.atan2(y, x))

    # Step 2: Work in the radial plane
    r = math.sqrt(x**2 + y**2)   # horizontal distance in XY
    h = z                        # vertical height
    d = math.hypot(r, h)         # distance from shoulder to target

    # Step 3: Check reachability
    if d > (L1 + L2) or d < abs(L1 - L2):
        print(f"⚠️ Target ({x:.2f}, {y:.2f}, {z:.2f}) unreachable! "
              f"(dist={d:.2f}, range={abs(L1-L2):.2f}–{L1+L2:.2f})")
        return None

    # Step 4: Elbow angle (law of cosines)
    cos_angle2 = (L1**2 + L2**2 - d**2) / (2 * L1 * L2)
    cos_angle2 = clamp(cos_angle2, -1.0, 1.0)
    theta2 = math.pi - math.acos(cos_angle2)

    # Step 5: Shoulder angle
    cos_angle1 = (d**2 + L1**2 - L2**2) / (2 * d * L1)
    cos_angle1 = clamp(cos_angle1, -1.0, 1.0)
    angle_to_target = math.atan2(h, r)
    angle_offset = math.acos(cos_angle1)

    if elbow_up:
        theta1 = angle_to_target + angle_offset
    else:
        theta1 = angle_to_target - angle_offset

    # Convert to degrees
    theta1_deg = math.degrees(theta1)
    theta2_deg = math.degrees(theta2)

    # Return joint array
    return [theta0, theta1_deg, theta2_deg, 0, 0, 0]


# ========================
# Movement functions
# ========================

def move_arm_to(x, y, z, speed=200, acc=100, elbow_up=False):
    # Simple distance check using full 3D distance
    d = math.sqrt((x)**2 + (y)**2 + (z)**2)

    if d > (L1 + L2) or d < abs(L1 - L2):
        print(f"⚠️ Target out of reach (dist={d:.2f}, "
              f"range={abs(L1-L2):.2f}–{L1+L2:.2f})")
        return False

    angles = ik_closed_form(x, y, z, elbow_up=elbow_up)
    if angles is None:
        return False

    roarm.joints_angle_ctrl(angles, speed, acc)
    set_current_arm_pos(x, y, z)
    return True



def move_arm_to_parts(x, y, z, n, speed=200, acc=100, elbow_up=False):
    # ✅ FIX: use radial plane distance instead of full 3D distance
    r = math.sqrt(x**2 + y**2)
    d = math.hypot(r, z)

    if d > (L1 + L2) or d < abs(L1 - L2):
        print(f"⚠️ Target out of reach (dist={d:.2f}, "
              f"range={abs(L1-L2):.2f}–{L1+L2:.2f})")
        return False

    # Get current position
    start_x, start_y, start_z = get_current_arm_pos()

    for i in range(1, n + 1):
        xi = start_x + (x - start_x) * i / n
        yi = start_y + (y - start_y) * i / n
        zi = start_z + (z - start_z) * i / n
        print(f"Moving to part {i}/{n}: ({xi:.2f}, {yi:.2f}, {zi:.2f})")

        angles = ik_closed_form(xi, yi, zi, elbow_up=elbow_up)
        if angles is None:
            return False

        roarm.joints_angle_ctrl(angles, speed, acc)
        set_current_arm_pos(xi, yi, zi)
        time.sleep(0.1)

    set_current_arm_pos(x, y, z)
    return True


def move_home(speed=200, acc=100, elbow_up=False):
    """Move arm to home position (10 in forward, 10 in up)."""
    print("🏠 Moving to HOME position...")
    return move_arm_to(*HOME_POS, speed=speed, acc=acc, elbow_up=elbow_up)


# ========================
# Main program
# ========================

def main():
    # Always go to home first
    move_home()

    # Example: then move in 4 parts to (5, 0, 12)
    move_arm_to_parts(5, 0, 12, n=4, elbow_up=False)


if __name__ == "__main__":
    main()
