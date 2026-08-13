from RoArmM3 import Arm
import time
import pygame
from pygame.locals import *

#initialize arm
arm = Arm(port="/dev/ttyUSB1",baudrate=115200)
arm.move_init()
arm.move_to_xyz(-0,12,-1,12) #phi,x,y,z
#note to self, init pygame, then init controller
pygame.init()
pygame.joystick.init()

joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
print(joysticks)
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            break

#controller buttons
        if event.type == pygame.JOYBUTTONDOWN:
            print(event)
#controller joysticks
        if event.type == pygame.JOYAXISMOTION:
            print(event)
#min/max the values, left stick for x and y axis movement, right stick for z axis movement (actually might not need get_axis(3))
#increment x and y values based on how long stick is help in x or y position, not exact mapping to x, y, and z values
    left_stick_x = round(pygame.joystick.Joystick(0).get_axis(0))
    left_stick_y = round(pygame.joystick.Joystick(0).get_axis(1))
    right_stick_x = round(pygame.joystick.Joystick(0).get_axis(2))
    right_stick_y = round(pygame.joystick.Joystick(0).get_axis(3))



















