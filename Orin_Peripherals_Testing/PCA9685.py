from adafruit_servokit import ServoKit
myKit=ServoKit(channels=16)
import time
myKit.servo[0].angle=110
myKit.servo[1].angle=0
#for i in range(0,180,1):
 #   myKit.servo[0].angle=i
  #  time.sleep(.1)

#for i in range(180,0,-1):
 #   myKit.servo[0].angle=i
  #  time.sleep(.1)