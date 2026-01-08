import time
import Jetson.GPIO as GPIO
import threading
from globals import shared

def ESCWaitFunction():
    global onbutton
    while shared.onbutton == 0:
        buttonstate_state = GPIO.input('GP48_SPI1_MISO')
        if buttonstate_state == GPIO.HIGH:
            #print("Input pin is HIGH! MVMNT start")
            shared.onbutton = 1
            shared.myKit.servo[1].angle = 126  
        else:
            #print("Input pin is LOW, don't move yet")
            shared.myKit.servo[1].angle = 90
            time.sleep(1)

def searching():
    if shared.search_thread and shared.search_thread.is_alive():
        #print("Search thread already running. Skipping new search.")
        return  

    def look_Around():
        shared.looking = True
        angle = 0
        anglechng = 10
        shared.myKit.servo[3].angle = 0 
        shared.myKit.servo[2].angle = 90  
        #print(":STARTING SEARCH:")

        while shared.looking:
            if not shared.looking:  
                #print(":SEARCH STOPPED EARLY:")
                break

            #print(f"Looking around at angle: {angle}")
            shared.myKit.servo[3].angle = angle
            time.sleep(1)
            angle += anglechng

            if angle == 190 or angle == -10:
                anglechng *= -1
    
    shared.search_thread = threading.Thread(target=look_Around)
    shared.search_thread.start()

def turning(angle, speed, duration, angle2, speed2, duration2):
    def turn_and_stop():
        shared.myKit.servo[0].angle = angle
        shared.myKit.servo[1].angle = speed
        shared.myKit.servo[2].angle = 90
        shared.myKit.servo[3].angle = 90
        time.sleep(duration)
        shared.myKit.servo[0].angle = angle2
        shared.myKit.servo[1].angle = speed2
        time.sleep(duration2/2)
        time.sleep(duration2/2)
        shared.myKit.servo[0].angle = 90
        shared.myKit.servo[1].angle = 90
        shared.evading = False
        #print('\nDONE EVADING\n')
    threading.Thread(target=turn_and_stop).start()





def evasion(localItem):
    shared.evading = True
    if(localItem == 'blue_bucket'):
        print("Evading BlueBucket")
        shared.current_step += 1
        shared.evasionType = 1
        turning(180, 126, 3, 30, 126, 11)
    elif(localItem == 'yellow_bucket'):
        print("Evading YellowBucket")
        shared.current_step += 1
        shared.evasionType = 2
        turning(33, 126, 4, 180, 126, 4)
    elif(localItem == 'red_bucketArch'):
        print("Evading RedBucket")
        shared.current_step += 1
        shared.evasionType = 3
        turning(90, 130, 4, 99, 126, 3)
    else:
        print("NOTBUILTYET")
        #shared.evasionType = 0
        #defaultEvade()