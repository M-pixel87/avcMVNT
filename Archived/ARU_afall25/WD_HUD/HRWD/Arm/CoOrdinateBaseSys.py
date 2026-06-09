from roarm_sdk.roarm import roarm
import math
import time
import random
import threading

# Initialize RoArm (with error handling so it doesn't crash if unplugged)
try:
    roarm_dev = roarm(roarm_type="roarm_m3", port="/dev/ttyUSB0", baudrate=115200)
    print("✅ RoArm Connected.")
except Exception as e:
    print(f"⚠️ RoArm Connection Failed: {e}")
    roarm_dev = None

#joint 5 is the jaw, keep open to 10 degrees
angles = [0, 0, 90, 0, 0, 10]

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

#random coordinate for tests
def generate_random_xyz(x_range, y_range, z_range):
    x = random.uniform(*x_range)
    y = random.uniform(*y_range)
    z = random.uniform(*z_range)
    return round(x, 2), round(y, 2), round(z, 2)

# Actual inverse kinematics calculations
def ik(x, y, z, angles, error):  
    errorI = error
    arm1 = 10
    arm2 = 14
    wrist = 7.5

    base_angle_rad = math.atan2(y, x)
    base_angle = math.degrees(base_angle_rad)
    angles[0] = base_angle

    rotated_x = math.hypot(x, y)  

    arm1_angle_deg = clamp(angles[1] + 90, -180, 180)
    arm1_rad = math.radians(arm1_angle_deg)
    arm1x = arm1 * math.cos(arm1_rad) * -1
    arm1z = arm1 * math.sin(arm1_rad)

    arm1_angle_world = math.degrees(math.atan2(arm1z, arm1x))

    dx = rotated_x - arm1x
    dz = z - arm1z

    desired_angle_rad = math.atan2(dz, dx)
    desired_angle_deg = math.degrees(desired_angle_rad)

    new_elbow = clamp(arm1_angle_world - desired_angle_deg, -70, 190)
    angles[2] = new_elbow

    arm2_angle_world = math.radians(arm1_angle_world - new_elbow)
    finalx = arm1x + arm2 * math.cos(arm2_angle_world)
    finalz = arm1z + arm2 * math.sin(arm2_angle_world)

    error = math.hypot(finalx - rotated_x, finalz - z)

    if error > 0.20:
        if rotated_x > finalx:
            angles[1] += 1 + (1 * error)
        else:
            angles[1] -= 1 + (1 * error)
        ik(x, y, z, angles, error)


# ==============================================================
# NEW: BACKGROUND ARM THREAD (Non-Blocking "Chasing" Engine)
# ==============================================================
class ArmControllerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True # Kills thread when main program exits
        self.lock = threading.Lock()
        
        # Current physical position tracking
        self.cx, self.cy, self.cz = 9.0, 0.0, 8.0
        
        # Desired target positions
        self.tx, self.ty, self.tz = 9.0, 0.0, 8.0
        
        self.speed = 300
        self.acc = 250
        self.force_send = False
        self.running = True

    def set_target(self, x, y, z, speed, acc):
        with self.lock:
            self.tx = x
            self.ty = y
            self.tz = z
            self.speed = speed
            self.acc = acc

    def trigger_joint_update(self, speed, acc):
        with self.lock:
            self.speed = speed
            self.acc = acc
            self.force_send = True

    def run(self):
        global angles
        while self.running:
            with self.lock:
                tx, ty, tz = self.tx, self.ty, self.tz
                sp, ac = self.speed, self.acc
                force = self.force_send
                self.force_send = False

            # Check how far we are from the target
            dist = math.hypot(tx - self.cx, ty - self.cy, tz - self.cz)
            needs_update = force
            
            # If we aren't at the target, take a micro-step toward it
            if dist > 0.1:
                # Max travel per loop (Higher = faster chase, Lower = smoother)
                # 1.0 units per 20ms is very fast and smooth
                step_size = min(1.0, dist) 
                fraction = step_size / dist
                
                # Update current position slightly closer to target
                self.cx += (tx - self.cx) * fraction
                self.cy += (ty - self.cy) * fraction
                self.cz += (tz - self.cz) * fraction
                
                # Calculate IK for this micro-step
                ik(self.cx, self.cy, self.cz, angles, 0)
                needs_update = True
                
            # Only push serial data if the arm actually needs to move
            if needs_update and roarm_dev:
                roarm_dev.joints_angle_ctrl(angles, sp, ac)
                
            # Maintain the ~50Hz hardware update rate
            time.sleep(0.02)

# Start the background engine the moment this module is imported
arm_thread = ArmControllerThread()
arm_thread.start()


# ==============================================================
# REWRITTEN PUBLIC API (Instant, Non-Blocking)
# ==============================================================

def move_joint(joint_index, angle, speed=450, acc=250):
    global angles
    if joint_index < 0 or joint_index >= 6:
        print("Invalid joint index. Must be between 0 and 5.")
        return False

    # Instantly update the angles array and flag the thread to send it immediately
    angles[joint_index] = clamp(angle, -180, 180)
    arm_thread.trigger_joint_update(speed, acc)
    return True

def move_arm_to(x, y, z, speed=400, acc=300):
    arm1 = 10
    arm2 = 14
    max_reach = arm1 + arm2
    
    # 1. Height limits
    if abs(z) > max_reach:
        print(f"⚠️ Height {z} is impossible.")
        return False

    max_horizontal_reach = math.sqrt(max_reach**2 - z**2)
    target_dist = math.sqrt(x**2 + y**2)
    
    # 2. Reach limits
    if target_dist > max_horizontal_reach:
        print(f"⚠️ Target Unreachable! (Dist: {target_dist:.2f} > Max: {max_horizontal_reach:.2f})")
        return False 

    # 3. Fire-and-Forget Target Update
    # This takes 0.0001 seconds to run, leaving your main AI loop completely unblocked.
    arm_thread.set_target(x, y, z, speed, acc)
    return True




# ==============================================================
# GENERATED TEST SCRIPT
# ==============================================================
if __name__ == "__main__":
    print("🤖 Starting RoArm Threaded Controller Test...")
    time.sleep(1) # Let the thread spin up

    try:
        # --- TEST 1: Basic Movement ---
        print("\n▶ TEST 1: Moving to Home Position (10, 0, 10)")
        move_arm_to(10, 0, 10)
        time.sleep(2) # Wait for physical arm to arrive

        # --- TEST 2: Direct Joint Control (Jaw) ---
        print("\n▶ TEST 2: Testing Jaw (Joint 5)")
        print("Closing Jaw...")
        move_joint(5, 50) 
        time.sleep(1)
        print("Opening Jaw...")
        move_joint(5, 10)
        time.sleep(1)

        # --- TEST 3: Sequential Waypoints ---
        print("\n▶ TEST 3: Executing Waypoint Sequence (Drawing a Square)")
        waypoints = [
            (10, 5, 10),
            (15, 5, 10),
            (15, -5, 10),
            (10, -5, 10),
            (10, 0, 10) # Back to center
        ]
        
        for wx, wy, wz in waypoints:
            print(f"  -> Moving to X:{wx}, Y:{wy}, Z:{wz}")
            move_arm_to(wx, wy, wz)
            time.sleep(1.5) # Give it enough time to reach each point smoothly

        # --- TEST 4: Non-Blocking "Chase" Stress Test ---
        print("\n▶ TEST 4: Rapid 'Chase' Target Updates")
        print("Sending new coordinates faster than the arm can finish moving.")
        print("(Press Ctrl+C at any time to stop safely)")
        
        for i in range(10):
            rx, ry, rz = generate_random_xyz(x_range=(8, 15), y_range=(-10, 10), z_range=(5, 15))
            print(f"  [Update {i+1}/10] Chasing new target: X:{rx}, Y:{ry}, Z:{rz}")
            move_arm_to(rx, ry, rz)
            
            # Note: We only sleep for 0.5 seconds! The arm likely hasn't reached the 
            # target yet, but the background thread will gracefully intercept the 
            # new coordinates and redirect its path smoothly.
            time.sleep(0.5) 

        # --- CLEANUP ---
        print("\n✅ Tests Complete. Returning to safe Home position...")
        move_arm_to(10, 0, 10)
        time.sleep(2)

    except KeyboardInterrupt:
        print("\n⚠️ Test manually interrupted by user (Ctrl+C).")

    finally:
        print("Shutting down controller thread...")
        arm_thread.running = False
        print("Done.")