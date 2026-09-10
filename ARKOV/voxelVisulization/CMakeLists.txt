cmake_minimum_required(VERSION 3.14)
project(ARKOV LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Fetch dependency: Polyscope 3D Visualizer only
include(FetchContent)
FetchContent_Declare(
    polyscope
    GIT_REPOSITORY https://github.com/nmwsharp/polyscope.git
    GIT_TAG master
)
FetchContent_MakeAvailable(polyscope)

# Specify global include directories for your headers
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/types
    ${CMAKE_CURRENT_SOURCE_DIR}/voxelVisulization
)

# Build the standalone Polyscope visualization demo
add_executable(voxel_vis_demo 
    voxel_vis_demo.cpp 
    voxelVisulization/voxel_map.cpp
)

# Link Polyscope
target_link_libraries(voxel_vis_demo PRIVATE polyscope)