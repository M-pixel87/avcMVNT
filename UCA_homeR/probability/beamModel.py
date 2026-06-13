

from rplidar import RPLidar
from map import map
import numpy as np
import cWrapper 
import plottingBeleif

# Create a map from map.py aswell as communication w lidar
lidar = RPLidar('/dev/ttyUSB0')
m1 = map(5, 3, 0.20)
m1.mapDefaultFill()



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
    #This should give us a even spread of beleif across the grid. 
    current_scan_likelihood = np.zeros_like(belief_grid)
    
    #creates all x and y locations to test, based on step, size, and resolution: creates arrays
    x_tests = np.arange(0.2, m.xSize * m.res, 0.2)
    y_tests = np.arange(0.2, m.ySize * m.res, 0.2)
    #the dif angles to test
    theta_tests = np.radians([0, 90, 180, 270]) 
    
    #initalizes the best score as the worst possible score
    best_score = -np.inf
    best_pose = (1.27, 0.38, 0.0)

    #Loop through all x,y, and theta locations to test.
    for x in x_tests:
        for y in y_tests:
            for theta in theta_tests:
                #convert coordes to match the grid
                gx, gy = m.convertCoordes(x, y)
                gtheta = int(np.round(np.degrees(theta) / 90)) % 4
                
                #make sure the grid locations are only valid cases
                gx = max(0, min(gx, m.xSize - 1))
                gy = max(0, min(gy, m.ySize - 1))
                
                if m.checkMap(gx, gy):
                    continue
                
                #Run the c compiled likelihood calculator
                log_p = cWrapper.run_c_likelihood(scan, (x, y, theta), m)
                #Update the beleif grid with the scores
                current_scan_likelihood[gx, gy, gtheta] = np.exp(log_p)
                
                #Update best score with the newest best score
                if log_p > best_score:
                    best_score = log_p
                    best_pose = (x, y, theta)
    #Multiply the likelihoods from scan to scan to have a continuingly updated and weighted map
    belief_grid *= current_scan_likelihood

    total_sum = np.sum(belief_grid)
    if total_sum > 0:
        #Scales the beleif
        belief_grid /= total_sum
    else:
        belief_grid[:] = 1.0 / belief_grid.size
    
    #Return the best pose and the beleifGrid
    return best_pose, belief_grid


def main():
    #Run the tkinter visualizer (WIP)
    viz = plottingBeleif.LocalizerVisualizer(m1)

    # Initialize a 3D grid matrix: 100 x 60 x 4 layers deep
    num_headings = 4
    belief_grid = np.zeros((m1.xSize, m1.ySize, num_headings))
    
    # Initialize uniformly (Equal chance of being anywhere at startup)
    belief_grid[:] = 1.0 / (m1.xSize * m1.ySize * num_headings)

    #main loop
    try:
        lidar.clean_input()
        iter = lidar.iter_scans()
        print("Markov Function Active. Streaming LiDAR data...")
        #get and loop through each ray per scan
        for scan in iter:
            #Reduce scan count to only 1/10 of original size for performance reasons
            shortscan = scan[::10]
            
            # oass the scans, beleif grid we made, and out map into the localization func. Returns pose and grid
            robot_pose, belief_grid = update_markov_localization(shortscan, belief_grid, m1)
            
            # Extract values, and update the visualizer
            rx, ry, rtheta = robot_pose
            viz.update(belief_grid)

            
            print(f"Estimated Pose -> X: {rx:.2f}m, Y: {ry:.2f}m, Heading: {int(np.degrees(rtheta))}°")
        
    except KeyboardInterrupt:
        print("\nClosing connection safely...")
        lidar.stop()
        lidar.disconnect()


if __name__ == "__main__":
    main()