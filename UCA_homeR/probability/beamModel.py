from rplidar import RPLidar
from map import map
import numpy as np
import cWrapper 
import plottingBeleif
import serial
import random

# --- System Configuration ---
MODE = "LUT_LOOKUP" # Set to "C_CALC" or "LUT_LOOKUP"

# --- Hardware Configuration ---
ser = serial.Serial("/dev/ttyACM0", 115200, timeout=0.1)

# Robot Kinematic Constants
WHEEL_RADIUS = 0.033     # Meters 
WHEEL_BASE = 0.15        # Meters (distance between track centers)
TICKS_PER_REV = 360      # Encoder resolution

# Create a map from map.py as well as communication w lidar
lidar = RPLidar('/dev/ttyUSB0')
m1 = map(4, 2.4, 0.20)
m1.mapDefaultFill()

# Trigger precompilation if we are running in table lookup mode
if MODE == "LUT_LOOKUP":
    m1.preCompile()


def beam_range_finder_likelihood(scan, pose, m):
    x, y, theta = pose
    q = 0.0  
    
    sigma = 0.15          
    z_rand_weight = 0.05  
    z_hit_weight = 0.95   
    max_range = 4.0       
    
    gaussian_constant = 1.0 / (np.sqrt(2 * np.pi) * sigma)
    
    for ray in scan:
        actualDist = ray[2] / 1000.0 
        if actualDist >= max_range or actualDist <= 0.1:
            continue
            
        exspectedDist = m.rayCast(ray, x, y, theta)
        p_hit = gaussian_constant * np.exp(-(actualDist - exspectedDist)**2 / (2 * sigma**2))
        p_rand = 1.0 / max_range
        p_total = (z_hit_weight * p_hit) + (z_rand_weight * p_rand)
        q += np.log(p_total)
        
    return q


def update_markov_localization(scan, belief_grid, m):
    log_likelihood_grid = np.full_like(belief_grid, -np.inf)
    
    x_tests = np.arange(0.2, m.xSize * m.res, 0.2)
    y_tests = np.arange(0.2, m.ySize * m.res, 0.2)
    theta_tests = np.radians([0, 90, 180, 270]) 
    
    best_score = -np.inf
    best_pose = (1.27, 0.38, 0.0)

    for x in x_tests:
        for y in y_tests:
            for theta in theta_tests:
                gx, gy = m.convertCoordes(x, y)
                gtheta = int(np.round(np.degrees(theta) / 90)) % 4
                
                gx = max(0, min(gx, m.xSize - 1))
                gy = max(0, min(gy, m.ySize - 1))
                
                if m.checkMap(gx, gy):
                    continue
                
                if MODE == "C_CALC":
                    log_p = cWrapper.run_c_likelihood(scan, (x, y, theta), m)
                else:
                    log_p = 0.0
                    sigma = 0.15
                    gaussian_constant = 1.0 / (np.sqrt(2.0 * np.pi) * sigma)
                    for ray in scan:
                        actualDist = ray[2] / 1000.0
                        if actualDist >= 4.0 or actualDist <= 0.1:
                            continue
                        ray_angle_deg = int(ray[1]) % 360
                        expectedDist = m.preCompiledMap[gx, gy, gtheta, ray_angle_deg]
                        delta = actualDist - expectedDist
                        p_hit = gaussian_constant * np.exp(-(delta * delta) / (2.0 * sigma * sigma))
                        p_total = (0.95 * p_hit) + (0.05 * (1.0 / 4.0))
                        log_p += np.log(p_total)

                log_likelihood_grid[gx, gy, gtheta] = log_p
                
                if log_p > best_score:
                    best_score = log_p
                    best_pose = (x, y, theta)
                    
    # Log-shift normalization
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

    # Apply diffusion 
    noise_weight = 0.05
    belief_grid = ((1.0 - noise_weight) * belief_grid) + (noise_weight / belief_grid.size)
    
    return best_pose, belief_grid


def update_particle_localization(scan, particles, m, d_center, d_theta):
    num_particles = len(particles)
    log_weights = np.zeros(num_particles)
    
    # 1. PREDICTION STEP (Odometry Motion Model)
    particles[:, 0] += d_center * np.cos(particles[:, 2])
    particles[:, 1] += d_center * np.sin(particles[:, 2])
    particles[:, 2] += d_theta
    
    # Add proportional noise based on movement
    noise_x_y = abs(d_center) * 0.10 + 0.01 
    noise_th = abs(d_theta) * 0.05 + np.radians(0.5) 
    
    noise_std = [noise_x_y, noise_x_y, noise_th]
    particles += np.random.normal(0, noise_std, size=(num_particles, 3))
    
    # Bound constraints
    particles[:, 0] = np.clip(particles[:, 0], 0.1, (m.xSize * m.res) - 0.1)
    particles[:, 1] = np.clip(particles[:, 1], 0.1, (m.ySize * m.res) - 0.1)
    particles[:, 2] = particles[:, 2] % (2 * np.pi)

    # 2. UPDATE STEP (Measurement Model)
    for i in range(num_particles):
        x, y, theta = particles[i]
    
        if MODE == "C_CALC":
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
        
    # 3. RESAMPLING STEP
    indices = np.random.choice(num_particles, size=num_particles, p=weights, replace=True)
    resampled_particles = particles[indices]
    
    best_idx = np.argmax(weights)
    estimated_pose = particles[best_idx]
    
    return estimated_pose, resampled_particles


def main():
    mode = "particle"
    
    prev_ticks_left = 0
    prev_ticks_right = 0
    
    if mode == "markov":
        viz = plottingBeleif.LocalizerVisualizer(m1)
        num_headings = 4
        belief_grid = np.zeros((m1.xSize, m1.ySize, num_headings))
        belief_grid[:] = 1.0 / (m1.xSize * m1.ySize * num_headings)
    elif mode == "particle":
        num_particles = 500
        particles = np.zeros((num_particles, 3))
        particles[:, 0] = np.random.uniform(0.2, (m1.xSize * m1.res) - 0.2, num_particles)
        particles[:, 1] = np.random.uniform(0.2, (m1.ySize * m1.res) - 0.2, num_particles)
        particles[:, 2] = np.random.uniform(0, 2 * np.pi, num_particles)
        
        # viz = plottingBeleif.ParticleVisualizer(m1) 

    try:
        lidar.clean_input()
        iter = lidar.iter_scans()
        print(f"Streaming LiDAR data in {mode} mode...")
        
        for scan in iter:
            shortscan = scan[::10]
            
            # Odometry Delta Parsing
            d_center = 0.0
            d_theta = 0.0
            

            # read any data that has been sent
            
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                try:
                    curr_ticks_left, curr_ticks_right = (line.split())
                    print(curr_ticks_left)
                    curr_ticks_left_f = float(curr_ticks_left)
                    curr_ticks_right_f = float(curr_ticks_right)
                    delta_left = curr_ticks_left_f - prev_ticks_left
                    delta_right = curr_ticks_right_f - prev_ticks_right
                    
                    prev_ticks_left = curr_ticks_left_f
                    prev_ticks_right = curr_ticks_right_f
                    
                    dist_left = 2 * np.pi * WHEEL_RADIUS * (delta_left / TICKS_PER_REV)
                    dist_right = 2 * np.pi * WHEEL_RADIUS * (delta_right / TICKS_PER_REV)
                    
                    d_center = (dist_left + dist_right) / 2.0
                    d_theta = (dist_right - dist_left) / WHEEL_BASE
                    
                except ValueError:
                    pass # Ignore malformed serial reads
            


            if mode == "markov":
                robot_pose, belief_grid = update_markov_localization(shortscan, belief_grid, m1)
                rx, ry, rtheta = robot_pose
                viz.update(belief_grid)
                
            elif mode == "particle":
                robot_pose, particles = update_particle_localization(shortscan, particles, m1, d_center, d_theta)
                rx, ry, rtheta = robot_pose
                # viz.update_particles(particles)
            
            print(f"Estimated Pose -> X: {rx:.2f}m, Y: {ry:.2f}m, Heading: {int(np.degrees(rtheta))}°")
            
            # Transmit Motor Commands (Placeholder logic)
            left_speed = 0.5 
            right_speed = 0.5
            command_str = f"{left_speed} {right_speed}\n"
            ser.write(command_str.encode('utf-8'))
            
    except KeyboardInterrupt:
        print("\nClosing connection safely...")
        lidar.stop()
        lidar.disconnect()
        ser.write(b"0.0 0.0\n") 
        ser.close()

if __name__ == "__main__":
    main()