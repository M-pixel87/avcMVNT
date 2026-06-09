import importlib
import sys

def check_dependencies():
    print("==================================================")
    print("🤖 JETSON ORIN DEPENDENCY CHECKER")
    print("==================================================\n")

    # Dictionary of module names to test, mapped to their installation instructions/notes
    dependencies = {
        "pygame": {
            "install": "pip3 install pygame",
            "notes": "Standard pip install should work."
        },
        "serial": {
            "install": "pip3 install pyserial",
            "notes": "Module is 'serial', but the package is 'pyserial'."
        },
        "numpy": {
            "install": "pip3 install numpy",
            "notes": "Standard pip install. (Ensure it doesn't conflict with PyTorch's numpy requirements)."
        },
        "cv2": {
            "install": "sudo apt-get install python3-opencv",
            "notes": "Usually included with NVIDIA JetPack. Do NOT 'pip install opencv-python' as it removes hardware acceleration."
        },
        "torch": {
            "install": "Download wheel from NVIDIA forums.",
            "notes": "CRITICAL: Do NOT use standard pip. You must install the specific PyTorch wheel for JetPack: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048"
        },
        "ultralytics": {
            "install": "pip3 install ultralytics",
            "notes": "Installs YOLOv8. Warning: this might try to downgrade/upgrade your Jetson PyTorch. Run with '--no-deps' if it breaks torch."
        },
        "jetson_inference": {
            "install": "Build from source (dusty-nv/jetson-inference)",
            "notes": "Must be cloned and built from source: https://github.com/dusty-nv/jetson-inference"
        },
        "jetson_utils": {
            "install": "Build from source (dusty-nv/jetson-inference)",
            "notes": "Included and installed automatically when building jetson_inference."
        },
        "pyrealsense2": {
            "install": "Build librealsense from source",
            "notes": "Difficult to install on ARM. See Intel's official guide for Jetson: https://github.com/IntelRealSense/librealsense/tree/master/doc/installation_jetson.md"
        },
        "roarm_sdk": {
            "install": "pip3 install roarm-sdk",
            "notes": "Alternatively, clone the Waveshare github repository and run setup.py."
        }
    }

    missing_packages = []
    installed_packages = []

    for module, info in dependencies.items():
        try:
            importlib.import_module(module)
            installed_packages.append(module)
            print(f"✅ {module:<16} - Found")
        except ImportError:
            missing_packages.append((module, info))
            print(f"❌ {module:<16} - MISSING")

    print("\n==================================================")
    print("📊 SUMMARY")
    print("==================================================")
    
    if not missing_packages:
        print("\n🎉 All dependencies are installed! Your script is ready to run.")
        sys.exit(0)
    else:
        print(f"\n⚠️ You are missing {len(missing_packages)} dependencies.\n")
        print("🛠️  HOW TO FIX:\n")
        for module, info in missing_packages:
            print(f"--- {module} ---")
            print(f"    Command/Fix : {info['install']}")
            print(f"    Jetson Note : {info['notes']}\n")
        sys.exit(1)

if __name__ == "__main__":
    check_dependencies()