# Conway's Game of Life is a cellular automaton devised by John Horton Conway in 1970.
# The intention was simply to provide a set of rules which, given any initial condition,
# would produce a seemingly random but deterministic pattern of zeros and ones.

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Define the size of the grid
rows = 100
cols = 100

# Initialize the grid with zeros (dead cells)
grid = np.zeros((rows, cols))

def update(frameNum):
    global grid
    
    # Create a copy of the current grid to avoid modifying it while iterating over it
    new_grid = grid.copy()
    
    # Iterate over each cell in the grid
    for r in range(rows):
        for c in range(cols):
            # Calculate the number of living neighbors
            living_neighbors = np.sum(grid[r-1:r+2, c-1:c+2]) - grid[r, c]
            
            # Apply the rules of Conway's Game of Life to update the cell state
            if grid[r, c] == 1 and (living_neighbors < 2 or living_neighbors > 3):
                new_grid[r, c] = 0
            elif grid[r, c] == 0 and living_neighbors == 3:
                new_grid[r, c] = 1
            
            # Update the cell state in the new grid
            grid[r, c] = new_grid[r, c]
    
    return new_grid

# Create a figure and an animation object
fig, ax = plt.subplots()
ani = animation.FuncAnimation(fig, update, frames=100, interval=200, blit=True)

# Show the animation
plt.show()