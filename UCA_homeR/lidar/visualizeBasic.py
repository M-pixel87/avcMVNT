#!/usr/bin/env python3
'''Animates distances and measurement quality'''
import matplotlib
# Force a standard GUI backend (TkAgg works out-of-the-box on most Pi OS setups)
matplotlib.use('TkAgg') 

from rplidar import RPLidar
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
import sys

PORT_NAME = '/dev/ttyUSB0'
DMAX = 4000
IMIN = 0
IMAX = 50

def update_line(num, iterator, line):
    try:
        scan = next(iterator)
        offsets = np.array([(np.radians(meas[1]), meas[2]) for meas in scan])
        line.set_offsets(offsets)
        intens = np.array([meas[0] for meas in scan])
        line.set_array(intens)
    except StopIteration:
        pass
    except Exception as e:
        print(f"Stream warning: {e}")
    return line,

# Keep anim in the global module scope from the start
anim = None

def run():
    global anim
    
    try:
        lidar = RPLidar(PORT_NAME)
    except Exception as e:
        print(f"Could not connect to LiDAR on {PORT_NAME}: {e}")
        sys.exit(1)
        
    fig = plt.figure()
    ax = plt.subplot(111, projection='polar')
    line = ax.scatter([0, 0], [0, 0], s=5, c=[IMIN, IMAX],
                       cmap=plt.cm.Greys_r, lw=0)
    ax.set_rmax(DMAX)
    ax.grid(True)

    iterator = lidar.iter_scans()
    
    # Bind the animation object firmly to the global scope variable
    anim = animation.FuncAnimation(
        fig, 
        update_line,
        fargs=(iterator, line), 
        interval=50,
        cache_frame_data=False
    )
    
    print("Opening radar plot window... (Press Ctrl+C in terminal or close window to exit)")
    try:
        plt.show()
    except KeyboardInterrupt:
        print("\nStopping via keyboard...")
    finally:
        print("Closing stream and stopping motor...")
        lidar.stop()
        lidar.disconnect()

if __name__ == '__main__':
    run()