import map

def main():
    m1 = map.map(5, 3, 0.2)
    m1.preCompile()
    
    
    test_heading = 0
    test_ray = 90
    
    print(f"\n--- INSPECTING PRE-COMPILED DISTANCES ---")
    print(f"Robot Heading Layer: {m1.thetaArray[test_heading]}°")
    print(f"LiDAR Ray Beam Angle: {test_ray}°")
    print(f"Matrix Dimension Spatial View (Rows = Y meters, Cols = X meters):\n")
    
    # Loop backwards through Y (rows) so that the top of the terminal represents 
    # the top of the physical map room layout
    for j in reversed(range(m1.ySize)):
        row_strings = []
        for i in range(m1.xSize):
            # Pull the precompiled float value from your 4D lookup table
            dist = m1.preCompiledMap[i, j, test_heading, test_ray]
            
            # Format to 2 decimal places for tight structural spacing
            row_strings.append(f"{dist:4.2f}")
            
        # Join the row items with spaces to look like a clean grid matrix layout
        print("  ".join(row_strings))

if __name__ == "__main__":
    main()