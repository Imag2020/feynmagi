# Conway's Game of Life in Python

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Define the size of the grid
grid_size = (10, 10)

# Initialize the grid with zeros
grid = np.zeros(grid_size, dtype=int)

def update(frame):
    # Apply the rules of Conway's Game of Life to the grid
    new_grid = grid.copy()
    
    for i in range(1, grid_size[0] - 1):
        for j in range(1, grid_size[1] - 1):
            # Count the number of living neighbors
            living_neighbors = np.sum(grid[i-1:i+2, j-1:j+2]) - grid[i, j]
            
            # Apply the rules to determine if the cell should be alive or dead in the next generation
            if grid[i, j] == 1 and (living_neighbors < 2 or living_neighbors > 3):
                new_grid[i, j] = 0
            elif grid[i, j] == 0 and living_neighbors == 3:
                new_grid[i, j] = 1
    
    # Update the grid for the next frame
    grid = new_grid.copy()

# Create a figure and axis object to display the grid
fig, ax = plt.subplots(figsize=(8, 8))
im = ax.imshow(grid, cmap='gray', animated=True)

# Set up the animation
ani = animation.FuncAnimation(fig, update, frames=np.arange(100), interval=200, blit=True)

plt.show()