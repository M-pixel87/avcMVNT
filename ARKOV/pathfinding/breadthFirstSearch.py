import numpy as np
import time

curx = 0
cury = 0

index = 0

xsize = 10
ysize = 10

que = [(curx,cury)]
map = np.zeros((xsize,ysize))

queued = set([(curx, cury)])

# Format is { (target_x, target_y) : (source_x, source_y) }
came_from = {(curx, cury): None}

'''
0 = not checked
1 = checked
2 = obstacle
3 = endpoint
4 = path 
'''

def make_obstacles():
    map[0][0] = 1 # place start
    map[9][9] = 3 # place end

    map[4][0] = 2 # obstacles 
    map[4][1] = 2
    map[4][2] = 2
    map[4][3] = 2
    map[4][4] = 2

def check_neihbors():
    global curx,cury,xsize,ysize
    
    # Check right
    if curx+1 < xsize and map[curx+1][cury] not in (1, 2) and (curx+1, cury) not in queued:
        que.append((curx+1,cury))
        queued.add((curx+1,cury))
        came_from[(curx+1, cury)] = (curx, cury) # Record where we came from
        
    # Check down
    if cury+1 < ysize and map[curx][cury+1] not in (1, 2) and (curx, cury+1) not in queued:
        que.append((curx,cury+1))
        queued.add((curx, cury+1))
        came_from[(curx, cury+1)] = (curx, cury)
        
    # Check left 
    if curx-1 >= 0 and map[curx-1][cury] not in (1, 2) and (curx-1, cury) not in queued:
        que.append((curx-1,cury))
        queued.add((curx-1, cury))
        came_from[(curx-1, cury)] = (curx, cury)
        
    # Check up 
    if cury-1 >= 0 and map[curx][cury-1] not in (1, 2) and (curx, cury-1) not in queued:
        que.append((curx,cury-1))
        queued.add((curx, cury-1))
        came_from[(curx, cury-1)] = (curx, cury)

def main():
    global curx,cury,index
    
    target_found = False
    
    while map[curx][cury] != 3:
        # Print map for viewing
        print(map)
        print("\n")
        
        #time.sleep(0.25) # Artificial Latency for viewing updates

        # update map when traversed
        if map[curx][cury] == 0:
             map[curx][cury] = 1

        # add neighbors to que
        check_neihbors()
        
        index += 1
        
        if index >= len(que):
            print("Queue empty: No path found!")
            break
            
        curVals = que[index]
        curx = curVals[0]
        cury = curVals[1]
        
        if map[curx][cury] == 3:
            target_found = True

    # --- NEW: PATH RECONSTRUCTION ---
    if target_found:
        print("Target Found! Reconstructing path...\n")
        path = []
        current = (curx, cury) # Start backtracking from the end
        
        # Loop backwards through our dictionary until we hit 'None' (the start)
        while current is not None:
            path.append(current)
            current = came_from[current]
            
        # Reverse the list so it goes from Start -> End
        path.reverse()
        
        print("Final Path Coordinates:")
        for step in path:
            map[step[0]][step[1]] = 4
            print(step)
        print(map)

if __name__ == "__main__":
    make_obstacles()
    main()