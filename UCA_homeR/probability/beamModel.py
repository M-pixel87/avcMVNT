"""
==============================================================================
ROBOT LOCALIZATION & NAVIGATION SYSTEM
==============================================================================
Overview:
    This module implements a dual-mode localization system (Markov Grid and 
    Monte Carlo Particle Filter) for a differential drive robot. It fuses 
    odometry data from wheel encoders with 2D LIDAR scans to estimate the 
    robot's global pose within a known map. (my tiny home is the default map HR)

Hardware Stack:
    - LIDAR: RPLidar (USB) for spatial mapping and obstacle detection.
    - Microcontroller: Handles low-level motor control and encoder tracking (Serial/ACM).
    - Kinematics: Left and Right encoded motors.

Software Stack:
    - Map Module: Custom map representation with raycasting.
    - Likelihood : Supports C-based calculations ("C_CALC") 
      or pre-compiled Look-Up Tables ("LUT_LOOKUP") for performance.
    - Visualization: Real-time belief state for markov localization and 
      particle tracking for monte carlo.

Usage:
    Ensure LIDAR and Serial ports are correctly assigned in the Hardware Config.
    Adjust MODE to switch between computation engines. 
==============================================================================
"""

import time
import numpy as np
import serial
from rplidar import RPLidar

# Custom / Local Modules
from map import map
import cWrapper 
import plottingBeleif


# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================

# General
LOCALIZATION_MODE = "particle"  # Options: "markov", "particle"
COMPUTATION_MODE = "LUT_LOOKUP" # Options: "C_CALC", "LUT_LOOKUP"

# Hardware / Serial Paths
SERIAL_PORT = "/dev/ttyACM0"
SERIAL_BAUD = 115200
LIDAR_PORT = "/dev/ttyUSB0"

# Kinematic Constants
WHEEL_RADIUS = 0.03175          # Meters
WHEEL_BASE = 0.2                # Meters (Distance between track centers)
TICKS_PER_REV = 2248.86         # Encoder resolution

# Sensor / Likelihood Model Tuning
SIGMA = 0.15
Z_RAND_WEIGHT = 0.05
Z_HIT_WEIGHT = 0.95
MAX_LIDAR_RANGE = 4.0           # Meters
MIN_LIDAR_RANGE = 0.1           # Meters

# Navigation & Control
DRIVE_DURATION_SEC = 2.0        # Timer: How long to drive
DRIVE_SPEED_LEFT = -0.180
DRIVE_SPEED_RIGHT = -0.180


# ============================================================================
# INITIALIZATION
# ============================================================================

# Initialize Serial Connection
ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)

# Initialize LIDAR & Map
lidar = RPLidar(LIDAR_PORT)
m1 = map(4, 2.4, 0.20)
m1.mapDefaultFill()

# Precompile lookup tables if required by mode
if COMPUTATION_MODE == "LUT_LOOKUP":
    m1.preCompile()


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def beam_range_finder_likelihood(scan, pose, m):
    """Calculates the likelihood of a given scan from a hypothetical pose."""
    x, y, theta = pose
    q = 0.0  
    gaussian_constant = 1.0 / (np.sqrt(2 * np.pi) * SIGMA)
    
    for ray in scan:
        actual_dist = ray[2] / 1000.0 
        if actual_dist >= MAX_LIDAR_RANGE or actual_dist <= MIN_LIDAR_RANGE:
            continue
            
        expected_dist = m.rayCast(ray, x, y, theta)
        
        # Sensor measurement models (Hit + Random noise)
        p_hit = gaussian_constant * np.exp(-(actual_dist - expected_dist)**2 / (2 * SIGMA**2))
        p_rand = 1.0 / MAX_LIDAR_RANGE
        p_total = (Z_HIT_WEIGHT * p_hit) + (Z_RAND_WEIGHT * p_rand)
        
        q += np.log(p_total)
        
    return q


def update_markov_localization(scan, belief_grid, m):
    """Grid-based Markov localization update over discrete states."""
    log_likelihood_grid = np.full_like(belief_grid, -np.inf)
    
    x_tests = np.arange(0.2, m.xSize * m.res, 0.2)
    y_tests = np.arange(0.2, m.ySize * m.res, 0.2)
    theta_tests = np.radians([0, 90, 180, 270]) 
    
    best_score = -np.inf
    best_pose = (1.27, 0.38, 0.0)

    for x in x_tests:
        for y in y_tests:
            for theta in theta_tests:
                # Convert global coordinates to map grid indices
                gx, gy = m.convertCoordes(x, y)
                gtheta = int(np.round(np.degrees(theta) / 90)) % 4
                
                gx = max(0, min(gx, m.xSize - 1))
                gy = max(0, min(gy, m.ySize - 1))
                
                if m.checkMap(gx, gy):
                    continue
                
                # Execute selected computation engine
                if COMPUTATION_MODE == "C_CALC":
                    log_p = cWrapper.run_c_likelihood(scan, (x, y, theta), m)
                else:
                    log_p = 0.0
                    gaussian_constant = 1.0 / (np.sqrt(2.0 * np.pi) * SIGMA)
                    for ray in scan:
                        actual_dist = ray[2] / 1000.0
                        if actual_dist >= MAX_LIDAR_RANGE or actual_dist <= MIN_LIDAR_RANGE:
                            continue
                            
                        ray_angle_deg = int(ray[1]) % 360
                        expected_dist = m.preCompiledMap[gx, gy, gtheta, ray_angle_deg]
                        delta = actual_dist - expected_dist
                        
                        p_hit = gaussian_constant * np.exp(-(delta * delta) / (2.0 * SIGMA * SIGMA))
                        p_total = (Z_HIT_WEIGHT * p_hit) + (Z_RAND_WEIGHT * (1.0 / 4.0))
                        log_p += np.log(p_total)

                log_likelihood_grid[gx, gy, gtheta] = log_p
                
                if log_p > best_score:
                    best_score = log_p
                    best_pose = (x, y, theta)
                    
    # Log-shift normalization to prevent underflow
    if best_score != -np.inf:
        current_scan_likelihood = np.exp(log_likelihood_grid - best_score)
    else:
        current_scan_likelihood = np.zeros_like(belief_grid)

    belief_grid *= current_scan_likelihood

    total_sum = np.sum(belief_grid)
    if total_sum > 0:
        belief_grid /= total_sum
    else:
        belief_grid[:] = 1.0 / belief_grid.size

    # Apply uniform diffusion noise
    noise_weight = 0.05
    belief_grid = ((1.0 - noise_weight) * belief_grid) + (noise_weight / belief_grid.size)
    
    return best_pose, belief_grid


def update_particle_localization(scan, particles, m, d_center, d_theta):
    """Monte Carlo (Particle Filter) localization update."""
    num_particles = len(particles)
    log_weights = np.zeros(num_particles)
    
    # 1. PREDICTION STEP (Odometry Motion Model)
    particles[:, 0] += d_center * np.cos(particles[:, 2])
    particles[:, 1] += d_center * np.sin(particles[:, 2])
    particles[:, 2] += d_theta
    
    # Add proportional kinematic noise
    noise_x_y = abs(d_center) * 0.10 + 0.01 
    noise_th = abs(d_theta) * 0.05 + np.radians(0.5) 
    
    noise_std = [noise_x_y, noise_x_y, noise_th]
    particles += np.random.normal(0, noise_std, size=(num_particles, 3))
    
    # Bound constraints within map dimensions
    particles[:, 0] = np.clip(particles[:, 0], 0.1, (m.xSize * m.res) - 0.1)
    particles[:, 1] = np.clip(particles[:, 1], 0.1, (m.ySize * m.res) - 0.1)
    particles[:, 2] = particles[:, 2] % (2 * np.pi)

    # 2. UPDATE STEP (Measurement Model)
    for i in range(num_particles):
        x, y, theta = particles[i]
    
        if COMPUTATION_MODE == "C_CALC":
            log_weights[i] = cWrapper.run_c_likelihood(scan, (x, y, theta), m)
        else:
            log_weights[i] = -np.inf # Fallback Placeholder
            
    # Normalize weights using log-shift
    max_log_weight = np.max(log_weights)
    if max_log_weight == -np.inf:
        weights = np.ones(num_particles) / num_particles 
    else:
        weights = np.exp(log_weights - max_log_weight)
        weights /= np.sum(weights) 
        
    # 3. RESAMPLING STEP (Roulette Wheel Selection)
    indices = np.random.choice(num_particles, size=num_particles, p=weights, replace=True)
    resampled_particles = particles[indices]
    
    best_idx = np.argmax(weights)
    estimated_pose = particles[best_idx]
    
    return estimated_pose, resampled_particles


# ============================================================================
# MAIN EXECUTION LOOP
# ============================================================================

def main():
    prev_ticks_left = 0
    prev_ticks_right = 0
    
    # State Initialization based on Mode
    if LOCALIZATION_MODE == "markov":
        viz = plottingBeleif.LocalizerVisualizer(m1)
        num_headings = 4
        belief_grid = np.zeros((m1.xSize, m1.ySize, num_headings))
        belief_grid[:] = 1.0 / (m1.xSize * m1.ySize * num_headings)
        
    elif LOCALIZATION_MODE == "particle":
        num_particles = 500
        particles = np.zeros((num_particles, 3))
        particles[:, 0] = np.random.uniform(0.2, (m1.xSize * m1.res) - 0.2, num_particles)
        particles[:, 1] = np.random.uniform(0.2, (m1.ySize * m1.res) - 0.2, num_particles)
        particles[:, 2] = np.random.uniform(0, 2 * np.pi, num_particles)
        viz = plottingBeleif.ParticleVisualizer(m1)  # <-- ENABLED PARTICLE VISUALIZER

    # Start Motor Timer
    start_time = time.time()

    try:
        lidar.clean_input()
        scan_iterator = lidar.iter_scans()
        print(f"Streaming LiDAR data in {LOCALIZATION_MODE.upper()} mode...")
        
        for scan in scan_iterator:
            shortscan = scan[::10]
            d_center = 0.0
            d_theta = 0.0
            
            # --- Odometry Parsing ---
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                try:
                    curr_ticks_left_str, curr_ticks_right_str = line.split()
                    curr_ticks_left = float(curr_ticks_left_str)
                    curr_ticks_right = float(curr_ticks_right_str)
                    
                    delta_left = curr_ticks_left - prev_ticks_left
                    delta_right = curr_ticks_right - prev_ticks_right
                    
                    prev_ticks_left = curr_ticks_left
                    prev_ticks_right = curr_ticks_right
                    
                    dist_left = 2 * np.pi * WHEEL_RADIUS * (delta_left / TICKS_PER_REV)
                    dist_right = 2 * np.pi * WHEEL_RADIUS * (delta_right / TICKS_PER_REV)
                    
                    d_center = (dist_left + dist_right) / 2.0
                    d_theta = (dist_right - dist_left) / WHEEL_BASE
                    
                except ValueError:
                    pass # Ignore malformed serial reads
            
            # --- State Estimation ---
            if LOCALIZATION_MODE == "markov":
                robot_pose, belief_grid = update_markov_localization(shortscan, belief_grid, m1)
                rx, ry, rtheta = robot_pose
                viz.update(belief_grid)
                
            elif LOCALIZATION_MODE == "particle":
                robot_pose, particles = update_particle_localization(shortscan, particles, m1, d_center, d_theta)
                rx, ry, rtheta = robot_pose
                viz.update_particles(particles, best_pose=robot_pose) # <-- SENDING DATA TO VISUALIZER
            
            print(f"Pose Est -> X: {rx:.2f}m, Y: {ry:.2f}m, Heading: {int(np.degrees(rtheta))}°")
            
            # --- Motor Control with Timer ---
            elapsed_time = time.time() - start_time
            if elapsed_time <= DRIVE_DURATION_SEC:
                left_speed = DRIVE_SPEED_LEFT
                right_speed = DRIVE_SPEED_RIGHT
            else:
                left_speed = 0.0 
                right_speed = 0.0 
                
            command_str = f"{left_speed} {right_speed}\n"
            ser.write(command_str.encode('utf-8'))
            
    except KeyboardInterrupt:
        print("\nShutting down safely...")
    finally:
        # Guarantee safe shutdown regardless of how the script ends
        lidar.stop()
        lidar.disconnect()
        ser.write(b"0.0 0.0\n") 
        ser.close()

if __name__ == "__main__":
    main()