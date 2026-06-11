from rplidar import RPLidar
from map import map
import numpy as np

lidar = RPLidar('/dev/ttyUSB0')
m1 = map(5, 3, 0.05)
m1.mapDefaultFill()


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
    """
    Executes a clean, simple Markov Localization cycle across a set of 
    test coordinates, updates the belief grid, and returns the best estimated pose.
    """
    # 1. Define search bounds strictly inside the actual size of your map.
    # Because m1 has dimensions 5.0m x 3.0m, we clip tests safely inside those walls.
    x_tests = np.arange(0.4, m.xSize * m.res, 0.4)
    y_tests = np.arange(0.4, m.ySize * m.res, 0.4)
    theta_tests = np.radians([0, 90, 180, 270])
    
    best_score = -np.inf
    best_pose = (1.27, 0.38, 0.0) # Default fallback

    # 2. Sweep the test area (The "for all x_t do" from the book)
    for x in x_tests:
        for y in y_tests:
            for theta in theta_tests:
                # Convert our continuous test position to map grid coordinates
                gx, gy = m.convertCoordes(x, y)
                gtheta = int(np.degrees(theta) / 90) % 4
                
                # --- BOUNDARY SAFETY PROTECTION ---
                # Forces indices to stay strictly within legal 0 to (size - 1) limits
                gx = max(0, min(gx, m.xSize - 1))
                gy = max(0, min(gy, m.ySize - 1))
                # ----------------------------------
                
                # Skip computing if this guess lands inside a solid wall
                if m.checkMap(gx, gy):
                    belief_grid[gx, gy, gtheta] = 0.0
                    continue
                
                # Book Line 2 & 3: Multiply sensor likelihood by the historical cell probability
                log_p = beam_range_finder_likelihood(scan, (x, y, theta), m)
                p_z_given_x = np.exp(log_p)
                
                belief_grid[gx, gy, gtheta] *= p_z_given_x
                
                # Track the highest performing score to extract the robot's state instantly
                if log_p > best_score:
                    best_score = log_p
                    best_pose = (x, y, theta)
                    
    # 3. Apply Normalizer (η) to keep the total probability array sum equal to 1.0
    total_sum = np.sum(belief_grid)
    if total_sum > 0:
        belief_grid /= total_sum
        
    return best_pose, belief_grid


def main():
    # Initialize a 3D grid matrix: 100 x 60 x 4 layers deep
    num_headings = 4
    belief_grid = np.zeros((m1.xSize, m1.ySize, num_headings))
    
    # Initialize uniformly (Equal chance of being anywhere at startup)
    belief_grid[:] = 1.0 / (m1.xSize * m1.ySize * num_headings)
    
    try:
        lidar.clean_input()
        iter = lidar.iter_scans()
        print("Markov Function Active. Streaming LiDAR data...")
        
        for scan in iter:
            # Drop ray overhead by keeping every 15th laser line
            shortscan = scan[::15]
            
            # Pass everything directly into your standalone function
            robot_pose, belief_grid = update_markov_localization(shortscan, belief_grid, m1)
            
            # Extract continuous values cleanly
            rx, ry, rtheta = robot_pose
            print(f"Estimated Pose -> X: {rx:.2f}m, Y: {ry:.2f}m, Heading: {int(np.degrees(rtheta))}°")
        
    except KeyboardInterrupt:
        print("\nClosing connection safely...")
        lidar.stop()
        lidar.disconnect()


if __name__ == "__main__":
    main()