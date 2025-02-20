from adafruit_servokit import ServoKit
myKit=ServoKit(channels=16)
import time
myKit.servo[0].angle=110 #mycenter to look straight from left to right numbers higher than 110 turn camera to right from perpectic of the camera
myKit.servo[1].angle=0 #my center up and down wise higher numbers look down more
