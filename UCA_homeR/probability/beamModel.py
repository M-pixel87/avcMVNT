from rplidar import RPLidar
from map import map
import numpy as np
import cWrapper 
import plottingBeleif

# Global configuration mode: Set to "C_CALC" or "LUT_LOOKUP", this will either use c code or pre compile our map
MODE = "LUT_LOOKUP"

# Create a map from map.py aswell as communication w lidar
lidar = RPLidar('/dev/ttyUSB0')
m1 = map(4, 2.4, 0.20)
m1.mapDefaultFill()

# Trigger precompilation if we are running in table lookup mode
if MODE == "LUT_LOOKUP":
    m1.preCompile()

#This function is old and unused, replace by c code
#This represents the beam model from the book, taking a scan , a pose to test, and a occupancy map for walls.
def beam_range_finder_likelihood(scan, pose, m):
    x, y, theta = pose
    #q is the returned likeilhood
    q = 0.0  
    
    #These represent some of the variables for the guassian, aswell as the added noise
    sigma = 0.15          
    z_rand_weight = 0.05  
    z_hit_weight = 0.95   
    max_range = 4.0       
    
    #This is the normalizer/guassian constant
    gaussian_constant = 1.0 / (np.sqrt(2 * np.pi) * sigma)
    
    #Loops through each ray from a single rotation, running our raycast.
    for ray in scan:
        #gets the distance to the wall from the scan
        actualDist = ray[2] / 1000.0 
        if actualDist >= max_range or actualDist <= 0.1:
            continue
        #calculates/determines the dist to the wall from the maps view (as it should be)
        exspectedDist = m.rayCast(ray, x, y, theta)
        
        #p_hit calculates the guassian probability for the error between the expected and actual
        p_hit = gaussian_constant * np.exp(-(actualDist - exspectedDist)**2 / (2 * sigma**2))
        p_rand = 1.0 / max_range
        #This scales the hit chance and random noise based on the variables listed above
        p_total = (z_hit_weight * p_hit) + (z_rand_weight * p_rand)
        
        # Utelizing log makes the numbers much easier to use, adds up all of the probabilities (closer to 0 better)
        q += np.log(p_total)
        
    return q
#----------------------------------------------------------------------------------------------



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
                
                # Dynamic mode check
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
                    
    # THE LOG-SHIFT TRICK: Subtract the best score before calculating exp()
    # This forces the absolute best cell to evaluate to np.exp(0.0) -> 1.0!
    if best_score != -np.inf:
        current_scan_likelihood = np.exp(log_likelihood_grid - best_score)
    else:
        current_scan_likelihood = np.zeros_like(belief_grid)

    belief_grid *= current_scan_likelihood

    # Normalize BEFORE applying diffusion so the signal is safely established
    total_sum = np.sum(belief_grid)
    if total_sum > 0:
        belief_grid /= total_sum
    else:
        belief_grid[:] = 1.0 / belief_grid.size

    #apply a 5% diffusion to keep the map fluid, this can be replaced by odometry
    noise_weight = 0.05
    belief_grid = ((1.0 - noise_weight) * belief_grid) + (noise_weight / belief_grid.size)
    
    return best_pose, belief_grid




def update_particle_localization(scan, particles, m):
    """
    particles: A numpy array of shape (N, 3) representing [x, y, theta]
    """
    num_particles = len(particles)
    log_weights = np.zeros(num_particles)
    
    # 1. PREDICTION STEP (Motion Model)
    # Ideally, add odometry (delta x, y, theta) here. 
    # For now, im adding Gaussian noise to simulate movement/diffusion.
    noise_std = [0.05, 0.05, np.radians(2.0)] # 5cm and 2 degrees of noise
    particles += np.random.normal(0, noise_std, size=(num_particles, 3))
    
    # Keep particles within map bounds and wrap angles
    particles[:, 0] = np.clip(particles[:, 0], 0.1, (m.xSize * m.res) - 0.1)
    particles[:, 1] = np.clip(particles[:, 1], 0.1, (m.ySize * m.res) - 0.1)
    particles[:, 2] = particles[:, 2] % (2 * np.pi)

    # 2. UPDATE STEP (Measurement Model)
    for i in range(num_particles):
        x, y, theta = particles[i]
    
        if MODE == "C_CALC":
            # Call C wrapper for maximum speed, utelizing same c likelihood as markov 
            log_weights[i] = cWrapper.run_c_likelihood(scan, (x, y, theta), m)
        else:
            # Fallback Python calculation (Highly recommended to use C_CALC for particles)
            # could implement python portion from markov again, but for now no
            log_weights[i] = -np.inf # Placeholder
            
    # Normalize weights using the log-shift trick to prevent underflow ( rounding down to 0 for really small numbers)
    # Minusing all log_weights by the best causes the best score to = 0.0 , then , ^0 = 1 , and then devididing all weights
    # by the total of the weights then the total will add up to 1. Normalizing
    max_log_weight = np.max(log_weights)
    if max_log_weight == -np.inf:
        weights = np.ones(num_particles) / num_particles # Fallback if all are terrible
    else:
        weights = np.exp(log_weights - max_log_weight)
        weights /= np.sum(weights) # Normalize to sum to 1.0
        
    # 3. RESAMPLING STEP
    # Draw indices with replacement, weighted by calculated probabilities
    indices = np.random.choice(num_particles, size=num_particles, p=weights, replace=True)
    
    # Create the new generation of particles
    resampled_particles = particles[indices]
    
    # Estimate the robot's pose (We can just take the mean of the particles)
    # Note: Mean of angles requires circular mean, but for simplicity, we'll take 
    # the pose of the highest weighted particle before resampling.
    best_idx = np.argmax(weights)
    estimated_pose = particles[best_idx]
    
    return estimated_pose, resampled_particles



def main():
    mode = "particle" # Switched to particle mode
    
    if mode == "markov":
        viz = plottingBeleif.LocalizerVisualizer(m1)
        num_headings = 4
        belief_grid = np.zeros((m1.xSize, m1.ySize, num_headings))
        belief_grid[:] = 1.0 / (m1.xSize * m1.ySize * num_headings)
    elif mode == "particle":
        # Initialize N particles randomly spread across the map
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
            
            if mode == "markov":
                robot_pose, belief_grid = update_markov_localization(shortscan, belief_grid, m1)
                rx, ry, rtheta = robot_pose
                viz.update(belief_grid)
                
            elif mode == "particle":
                robot_pose, particles = update_particle_localization(shortscan, particles, m1)
                rx, ry, rtheta = robot_pose
                # viz.update_particles(particles) # Update visualizer
            
            print(f"Estimated Pose -> X: {rx:.2f}m, Y: {ry:.2f}m, Heading: {int(np.degrees(rtheta))}°")
            
    except KeyboardInterrupt:
        print("\nClosing connection safely...")
        lidar.stop()
        lidar.disconnect()

if __name__ == "__main__":
    main()