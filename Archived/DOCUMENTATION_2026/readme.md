# **AVC 2026 Documentation (1st place)**

## **General Overview : Hudson Reeves 6/8/2026**

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

## **In-Depth Systems** 

### **DisplaySystem.py** 
#### **Class DisplaySystem**
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

### **InputSystem.py**
#### **Class AI**
The AI class is for the jetson-inference AI model we used to run. You need to specify the path to the AI model  
that we trained aswell as its label file. The label file is a txt file with the annotations we have for the model  
ex: red_ball , blue_bucket
```
def __init__(self): 
        self.net = jetson_inference.detectNet( 
            model="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_jone/ssd-mobilenet.onnx", 
            labels="/home/uafs/Downloads/jetson-inference/python/training/detection/ssd/models/test_jone/labels.txt", 
```

#### **Class AI_YOLO**
This handles (of course) the new implementation of our yolo AI model utelizing the python library ultralytics.  
It features a single function "detect", where it will return the detections from the ai model on a specific frame.
```
def __init__(self, model_path='/home/uafs/Downloads/weights(4).engine', conf_threshold=0.5): 
```

#### **Class IntelCamera**
Handles the realsense-435i camera. Deals with a depth 2d array for each detection pixel aswell as a rgb 3d array  
for a regular video feed.  

#### **Class cvWebcam**
Used primarily for regular webcam videofeeds. Returns a frame,

#### **Class XboxController**
Poll is the primary function called, it gathers the joystick data and button data returned in a list.  
Utelizes the pygame library for the controller connection functionality.

#### **Class AI_Inputs**
AI_Inputs is a complex class. It features every single bit of logic for the autonomous logic that drives the vehicle,  
the arm, and any other system associated with it.  

This class has a large number of variables, infact large is a understatement. This could prob be optimized.  

get_fast_media_depth will get the avg value for a group of depth pixels from the intel cam.  

The update_target is called alot. It is an important function as it updates the autonomous driving based  
upon detection target objects.  

update_arm_logic is a complex state machine for various different states of the ro-arm-m3.  
This may for example control : Arm center with ball, arm reach out, arm close grip, ect.  

move_command is the actual commands getting sent with the correct speed commands.  

### **motorSystem.py**

#### **Class CytronMotor**
This class inherits from a motorSystem class that doesnt have any functionality by itself. The class only has  
one function itself (the set power function).  

The one function it has simply sends a command which is understood by the microcontroller uno and updates  
the speed of the motors via the motor driver.

### **sensorSystem.py**
This system handles the sensor input from the microcontroller which has gathered and sent a packet containing  
multiple different sensor data values.

#### **Class sensorSystem**
All you really need to know is that read_loop is the most important. Its a multithreaded loop to read the serial  
buffer whenever there is a new packet. You can read the source code to see the format of the packet.
