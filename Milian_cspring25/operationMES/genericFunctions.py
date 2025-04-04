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
        #this angles needed for the seaching second part hudalign
        #shared.angle = 0 already set before in the globals file
        anglechng = 10
        shared.myKit.servo[3].angle = 0 
        shared.myKit.servo[2].angle = 90  
        #print(":STARTING SEARCH:")

        while shared.looking:
            if not shared.looking:  
                #print(":SEARCH STOPPED EARLY:")
                break

            #print(f"Looking around at angle: {angle}")
            shared.myKit.servo[3].angle = shared.angle
            time.sleep(1)
            shared.angle += anglechng

            if shared.angle >= 181 or shared.angle <= -9:
                anglechng *= -1
    
    shared.search_thread = threading.Thread(target=look_Around)
    shared.search_thread.start()

    

def turning(angle, speed, duration, angle2, speed2, duration2, direction):
    shared.evading = True
    shared.myKit.servo[0].angle = angle
    shared.myKit.servo[1].angle = speed
    shared.myKit.servo[2].angle = 90
    shared.myKit.servo[3].angle = 90
    time.sleep(duration)
    def turn_and_stop():
        shared.myKit.servo[0].angle = angle2
        shared.myKit.servo[1].angle = speed2
        time.sleep(duration2/2)
        time.sleep(duration2/2)
        shared.myKit.servo[0].angle = 90
        shared.myKit.servo[1].angle = 90
        shared.evading = False
        if(not shared.detection):
            orbit(direction)
        #print('\nDONE EVADING\n')
    threading.Thread(target=turn_and_stop).start()

#THIS IS ONLY FOR ORBIT, SHARED.EVADING IS REMOVED 3 STEPS
def turningOrbit(angle, speed, duration, angle2, speed2, duration2, angle3, speed3, duration3):
    shared.myKit.servo[0].angle = angle
    shared.myKit.servo[1].angle = speed
    shared.myKit.servo[2].angle = 90
    shared.myKit.servo[3].angle = 90
    time.sleep(duration)
    def turn_and_stop():
        shared.myKit.servo[0].angle = angle2
        shared.myKit.servo[1].angle = speed2
        time.sleep(duration2/2)
        if(shared.detection == True):
            return
        time.sleep(duration2/2)
        shared.myKit.servo[0].angle = angle3
        shared.myKit.servo[1].angle = speed3
        time.sleep(duration3/2)
        if(shared.detection == True):
            return
        time.sleep(duration3/2)
        shared.myKit.servo[0].angle = 90
        shared.myKit.servo[1].angle = 90
    threading.Thread(target=turn_and_stop).start()


def orbit(dir):
    shared.orbiting = True
    while(shared.orbiting == True):
        if not shared.orbiting:
            break
        #Turning numbers are to be adjusted
        if(dir == 'left'):
            turningOrbit(85, 130, 5, 153, 132, 4, 90, 132, 5)
        elif(dir == 'right'):
            turningOrbit(95, 132, 5, 27, 132, 4, 85, 132, 5)
        

def evasion(localItem):
    shared.evading = True
    if(localItem == 'blue_bucket' and shared.current_step % 2 != 0):
        print("Evading BlueBucket")
        shared.current_step += 1
        shared.evasionType = 1
        turning(180, 130, 2, 27, 132, 8, "right")
    elif(localItem == 'yellow_bucket' and shared.current_step== 2):
        print("Evading YellowBucket")
        shared.current_step += 1
        shared.evasionType = 2
        turning(27, 130, 3, 170, 132, 8, "left")
    elif(localItem == 'ramp' and shared.current_step==4):
        print("mama im scared i dont want to jump")
        shared.current_step += 1
        shared.evasionType = 3
        turning(27, 140, 4, 160, 140, 4)
    elif(localItem == 'red_bucketArch' and shared.current_step==6):
        print("Evading RedBucket")
        # drives forward like a madman, no outside distractions
        shared.myKit.servo[0].angle = 90
        shared.myKit.servo[1].angle = 142
        time.sleep(5)
        shared.current_step += 1
        shared.evasionType = 4
    else:
        print("NOTBUILTYET")
        #shared.evasionType = 0
        #defaultEvade()