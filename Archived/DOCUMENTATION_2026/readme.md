# AVC 2026 Documentation (1st place)

## General Overview : Hudson Reeves 6/8/2026

**WARNING:** This code is very unpolished in certain areas such as universalMain and inputSystem.  
Some of the code may be hard to follow or not even used. You are warned.
  
First, this documentation will be going over the code presented under the following location.  
-> **avcMVNT/Archived/ARU_afall25/WD_HUD** , this is at the top of the Archived folder
  
The "main" code, meaning : the file that we run to start the program is universalMain.py  

universalMain.py is the glue which holds the entire system together. It calls all the other  
systems. What do I mean? It creates an object of the classes defined in the _____system.py files.  
If you are uncomfortable with this idea please consult some videos about object oriented programming.  
universalMain.py handles all of connecting of all the systems while attempting to maintain a freq run speed.

displaySystem.py handles displaying the video feed, sensor data, and bounding boxes on ai detection.  

inputSystem.py handles all kinds of inputs, most notably: Bluetooth controller, Ai_controls, intelCamera,  
webcam feed.  

motorSystem.py handles sending the speed commands to the microcontroller over serial.

sensorSystem.py handles receiving the sensor data from the microcontroller over serial packets.

## In-Depth Systems 

### DisplaySystem.py 
#### Class DisplaySystem
The class display system acts as a delegator, it takes in a camera, name, and a mode. Based upon the mode string  
it will make the display system a gpu , tkinter, or yolo based display system.

Dislay System yolo is the main one used in the program. It offers these functionalities
- update display is a function all types of display systems share. It takes on a frame (picture) detection list  
from the AI, motor output, sensor data, and more.
- loop through ai detections and place bounding boxes.
```
if detections:
            for det in detections:
```
- loop through sensor data 
```
if data is not None:
            for key, value in data.items():
```
There are also more things it loops through but it is less important

### InputSystem.py
#### Class AI

