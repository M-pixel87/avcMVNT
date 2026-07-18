import ctypes
import os
import numpy as np

# 1. Define C-compatible structures inside Python
class Pose(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("theta", ctypes.c_float)
    ]

class LidarRay(ctypes.Structure):
    _fields_ = [
        ("quality", ctypes.c_int),
        ("angle", ctypes.c_float),
        ("distance", ctypes.c_float)
    ]

class Map(ctypes.Structure):
    _fields_ = [
        ("xSize", ctypes.c_int),
        ("ySize", ctypes.c_int),
        ("res", ctypes.c_float),
        ("grid", ctypes.POINTER(ctypes.c_int)) # Pointer to the flattened int array
    ]

# 2. Load the compiled shared object library
lib_path = os.path.abspath("./clibrary.so")
c_lib = ctypes.CDLL(lib_path)

# 3. Define input and output data types for the C function
c_lib.beam_range_finder_likelihood.argtypes = [
    ctypes.POINTER(LidarRay),  # const lidarRay* scan
    ctypes.c_int,              # int scanSize
    Pose,                      # pose p (Passed by value)
    Map                        # map m  (Passed by value)
]
c_lib.beam_range_finder_likelihood.restype = ctypes.c_float


def run_c_likelihood(scan_data, current_pose, python_map):
    """
    Exposes the fast C ray-casting backend to Python routine.
    
    scan_data: List or array of rays, where each ray is [quality, angle, distance_mm]
    current_pose: Tuple or list of (x, y, theta)
    python_map: existing Python map instance
    """
  
    num_rays = len(scan_data)
    c_ray_array = (LidarRay * num_rays)()
    
    for i, ray in enumerate(scan_data):
        c_ray_array[i].quality = int(ray[0])
        c_ray_array[i].angle = float(ray[1])
        c_ray_array[i].distance = float(ray[2])
        
    # Pack the evaluation pose
    c_pose = Pose(current_pose[0], current_pose[1], current_pose[2])
    
    # Flatten map's grid data into a contiguous 1D numpy array of C ints
    # Assumes python_map.grid is a 2D matrix or have access to its raw data layout
    flat_grid = np.array(python_map.mapAr, dtype=ctypes.c_int).flatten()
    grid_ptr = flat_grid.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    
    # Pack the structural Map object
    c_map = Map(
        xSize=int(python_map.xSize),
        ySize=int(python_map.ySize),
        res=float(python_map.res),
        grid=grid_ptr
    )
    
    # Execute the C loop at native speed
    likelihood_score = c_lib.beam_range_finder_likelihood(
        c_ray_array, 
        num_rays, 
        c_pose, 
        c_map
    )
    
    return likelihood_score

# --- Test execution check ---
if __name__ == "__main__":
    # Mocking class configurations for confirmation
    class MockMap:
        xSize = 100
        ySize = 60
        res = 0.05
        grid = np.zeros((60, 100), dtype=np.int32) # Clean map layout
        grid[20, :] = 1 # Place a sample wall across row 20
        
    m1 = MockMap()
    
    # Mock Scan: [quality, angle, distance_mm]
    mock_scan = [
        [15, 0.0, 1200.0],
        [15, 90.0, 800.0],
        [15, 180.0, 2500.0]
    ]
    
    test_pose = (1.5, 0.5, 0.0)
    
    score = run_c_likelihood(mock_scan, test_pose, m1)
    print(f"C Backend execution successful. Returned Log-Likelihood: {score:.4f}")