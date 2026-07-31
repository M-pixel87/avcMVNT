import numpy as np
import time

curx = 0
cury = 0

index = 0

xsize = 10
ysize = 10

que = [(curx,cury)]
map = np.zeros((xsize,ysize))

# Add a set to track coordinates that are already in the queue
# This prevents adding duplicates and is actually faster because its hashed and unindexed
queued = set([(curx, cury)])

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
        
    # Check down
    if cury+1 < ysize and map[curx][cury+1] not in (1, 2) and (curx, cury+1) not in queued:
        que.append((curx,cury+1))
        queued.add((curx, cury+1))
        
    # Check left 
    if curx-1 >= 0 and map[curx-1][cury] not in (1, 2) and (curx-1, cury) not in queued:
        que.append((curx-1,cury))
        queued.add((curx-1, cury))
        
    # Check up 
    if cury-1 >= 0 and map[curx][cury-1] not in (1, 2) and (curx, cury-1) not in queued:
        que.append((curx,cury-1))
        queued.add((curx, cury-1))

def main():
    global curx,cury,index
    while map[curx][cury] != 3:
        # Print map for viewing
        print(map)
        print("\n")
        
        time.sleep(0.1) 

        # update map when traversed
        if map[curx][cury] == 0:
             map[curx][cury] = 1

        # add neighbors to que
        check_neihbors()
        
        index += 1
        
        # Safety check: if we run out of queue items, there is no path
        if index >= len(que):
            print("Queue empty: No path found!")
            break
            
        curVals = que[index]
        curx = curVals[0]
        cury = curVals[1]

if __name__ == "__main__":
    make_obstacles()
    main()