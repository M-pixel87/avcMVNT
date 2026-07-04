import numpy as np
import matplotlib
matplotlib.use('TkAgg') # Force Tk to keep stable on the Pi
import matplotlib.pyplot as plt
import time

class LocalizerVisualizer:
    def __init__(self, m):
        plt.ion()  
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.res = m.res
        self.xSize = m.xSize
        self.ySize = m.ySize
        
        # Add a frame counter to track when to redraw
        self.frame_counter = 0
        
        blank_matrix = np.zeros((self.ySize, self.xSize))
        
        self.heatmap = self.ax.imshow(
            blank_matrix, 
            cmap='viridis', 
            origin='lower',
            extent=[0, self.xSize * self.res, 0, self.ySize * self.res]
        )
        
        self.ax.set_title("Markov Localization Belief Heatmap")
        self.ax.set_xlabel("X Position (meters)")
        self.ax.set_ylabel("Y Position (meters)")
        self.fig.colorbar(self.heatmap, ax=self.ax, label="Probability Density")
        
        # Render the initial frame completely once
        self.fig.canvas.draw()
        plt.show(block=False)
        
        # Cache the static background layout pixels (labels, colorbar, axes)
        self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)

    def update(self, belief_grid):
        # 1. FRAME THROTTLE: Only process the visual update every 3rd frame
        self.frame_counter += 1
        if self.frame_counter % 3 != 0:
            return

        belief_2d = np.sum(belief_grid, axis=2).T
        
        # Update just the raw image array reference structure 
        self.heatmap.set_data(belief_2d)
        
        max_val = np.max(belief_2d)
        self.heatmap.set_clim(vmin=0, vmax=max_val if max_val > 0 else 1.0)
        
        # Restore the cached static background layout over the old frame
        self.fig.canvas.restore_region(self.bg)
        
        # Re-draw ONLY the changing pixel data region
        self.ax.draw_artist(self.heatmap)
        
        # Push the updated pixels directly onto the active hardware screen buffer
        self.fig.canvas.blit(self.fig.bbox)
        
        # Flush the local window system GUI queue
        self.fig.canvas.flush_events()
        
        # 2. CPU YIELD: Give the OS 1 millisecond to acknowledge the window is still alive
        time.sleep(0.001)

    def close(self):
        plt.close(self.fig)


class ParticleVisualizer:
    def __init__(self, m):
        plt.ion()  
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.res = m.res
        self.xSize = m.xSize
        self.ySize = m.ySize
        
        self.frame_counter = 0
        
        # Set static map limits
        self.ax.set_xlim(0, self.xSize * self.res)
        self.ax.set_ylim(0, self.ySize * self.res)
        
        # Initialize scatter plots for particles and the best estimate
        self.particles_scatter = self.ax.scatter([], [], c='red', s=5, alpha=0.5)
        self.best_pose_scatter = self.ax.scatter([], [], c='blue', s=40, marker='*')
        
        self.ax.set_title("Monte Carlo Particle Filter Localization")
        self.ax.set_xlabel("X Position (meters)")
        self.ax.set_ylabel("Y Position (meters)")
        
        # Render the initial frame completely once
        self.fig.canvas.draw()
        plt.show(block=False)
        
        # Cache the static background
        self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)

    def update_particles(self, particles, best_pose=None):
        # 1. FRAME THROTTLE
        self.frame_counter += 1
        if self.frame_counter % 3 != 0:
            return

        # Update X and Y coordinates (ignoring Theta for the scatter plot)
        self.particles_scatter.set_offsets(particles[:, :2])
        
        if best_pose is not None:
            self.best_pose_scatter.set_offsets([[best_pose[0], best_pose[1]]])
        
        # Restore background
        self.fig.canvas.restore_region(self.bg)
        
        # Draw artists
        self.ax.draw_artist(self.particles_scatter)
        if best_pose is not None:
            self.ax.draw_artist(self.best_pose_scatter)
            
        # Blit and flush
        self.fig.canvas.blit(self.fig.bbox)
        self.fig.canvas.flush_events()
        
        # 2. CPU YIELD
        time.sleep(0.001)

    def close(self):
        plt.close(self.fig)