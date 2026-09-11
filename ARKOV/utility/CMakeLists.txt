cmake_minimum_required(VERSION 3.14)
project(ARKOV LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 1. Locate system OpenCV (pre-installed on Jetson)
find_package(OpenCV REQUIRED)

# 2. Build executable
# If you have a separate main.cpp testing cv_Webcam, add it here alongside cameras.cpp
add_executable(cameraTest 
    camerasTest.cpp
    cameras.cpp
)

# 3. Include headers
target_include_directories(cameraTest PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${OpenCV_INCLUDE_DIRS}
)

# 4. Link OpenCV libraries
target_link_libraries(cameraTest PRIVATE 
    ${OpenCV_LIBS}
)