from rplidar import RPLidar
lidar = RPLidar('/dev/ttyUSB0')

def main():
    try:
        for scan in lidar.iter_scans():
            print(f"{scan} \n")
    except KeyboardInterrupt:
        lidar.stop()
        lidar.disconnect()


if __name__ == "__main__":
    main()