cmake_minimum_required(VERSION 3.14)
project(ARKOV LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)
FetchContent_Declare(
    opencv
    GIT_REPOSITORY https://github.com/opencv/opencv.git
    GIT_TAG 5.x
)
FetchContent_MakeAvailable(opencv)

# Specify global include directories for your headers
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Build the standalone Polyscope visualization demo
add_executable(cameraTest 
    cameras.cpp 
)

# Link Polyscope
target_link_libraries(cameraTest PRIVATE opencv)