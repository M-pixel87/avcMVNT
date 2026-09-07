cmake_minimum_required(VERSION 3.14)
project(ARKOV LANGUAGES CXX)

# Use C++17 standard (required for std::clamp used in PID controller)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Export compile commands for VSCode LSP autocomplete and IntelliSense support
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Fetch dependency: serial communication library
include(FetchContent)
FetchContent_Declare(
    serial
    GIT_REPOSITORY https://github.com/wjwwood/serial.git
    GIT_TAG master
)
FetchContent_MakeAvailable(serial)

# Find OpenCV (for your vision and camera processing pipelines)
find_package(OpenCV REQUIRED)

# Include directories to allow neat clean #include paths in your codebase
target_include_directories(arkov_rover PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/types
    ${CMAKE_CURRENT_SOURCE_DIR}/localization
    ${CMAKE_CURRENT_SOURCE_DIR}/slam
    ${CMAKE_CURRENT_SOURCE_DIR}/pid
    ${CMAKE_CURRENT_SOURCE_DIR}/voxelVisulization
    ${CMAKE_CURRENT_SOURCE_DIR}/encoded
    ${CMAKE_CURRENT_SOURCE_DIR}/utility
    ${CMAKE_CURRENT_SOURCE_DIR}/communication/tests
)

# Specify all source files
set(SOURCES
    main.cpp
    localization/particleFilter.cpp
    slam/slamManager.cpp
    pid/pidController.cpp
    voxelVisulization/voxel_map.cpp
    encoded/driveOdometry.cpp
    utility/cameras.cpp
    utility/lidar.cpp
    communication/tests/microControllerCom.cpp
)

# Declare primary executable
add_executable(arkov_rover ${SOURCES})

# Link external libraries
target_link_libraries(arkov_rover PRIVATE
    serial
    ${OpenCV_LIBS}
)
