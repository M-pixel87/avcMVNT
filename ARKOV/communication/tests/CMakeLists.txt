cmake_minimum_required(VERSION 3.14)
project(ARKOV)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)

FetchContent_Declare(
    serial
    GIT_REPOSITORY https://github.com/wjwwood/serial.git
    GIT_TAG        master
)

FetchContent_MakeAvailable(serial)
add_executable(CCommunication microControllerCom.cpp)

target_link_libraries(CCommunication PRIVATE serial)