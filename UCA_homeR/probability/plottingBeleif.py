import numpy as np
import matplotlib
matplotlib.use('TkAgg') # Force Tk to keep stable on the Pi
import matplotlib.pyplot as plt

class LocalizerVisualizer:
    def __init__(self, m):
        plt.ion()  
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.res = m.res
        self.xSize = m.xSize
        self.ySize = m.ySize
        
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
        
        # Flush the local window system GUI queue without introducing timing delays
        self.fig.canvas.flush_events()

    def close(self):
        plt.close(self.fig)