
import numpy as np

total_area = 30*30  # 30x30 ft
rows = 10
cols = 10
sqft_per_cell = total_area / (rows*cols)

ar = np.zeros((rows, cols), dtype=np.uint8)


def main():
    print(ar)
    print("2D Mapping Test")

if __name__ == "__main__":
    main()
