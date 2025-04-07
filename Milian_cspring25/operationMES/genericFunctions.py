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
    

#DEPRECATED FUNCTION
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
#---------------------------------------------------


#ONE QUIRK: i moved all of the servo controlls into the turn_Stop function , because before the first turn was not threaded

#Direction dictates orbit direction. hopefully orbit will not be needed
def turning(angle, speed, duration, angle2, speed2, duration2, direction):
    shared.evading = True

    shared.AiHUDkey = True #turns on the lock 

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

        shared.AiHUDkey = False #disables the lock to continue normal operation of stoping early 

        shared.myKit.servo[0].angle = 90
        shared.myKit.servo[1].angle = 90
        shared.evading = False
        if(not shared.detection):
            orbit(direction)
        #print('\nDONE EVADING\n')
    threading.Thread(target=turn_and_stop).start()

#THIS IS ONLY FOR ORBIT, SHARED.EVADING IS REMOVED, 3 STEPS
def turningOrbit(angle, speed, duration, angle2, speed2, duration2, angle3, speed3, duration3):

    shared.AiHUDkey = True #turns on the lock this will allow for the screen to continue showing if wanted

    shared.myKit.servo[0].angle = angle
    shared.myKit.servo[1].angle = speed
    shared.myKit.servo[2].angle = 90
    shared.myKit.servo[3].angle = 90
    time.sleep(duration)
    shared.myKit.servo[0].angle = angle2#d
    shared.myKit.servo[1].angle = speed2#d
    time.sleep(duration2)#d
    def turn_and_stop():


        shared.AiHUDkey = False #disables the lock to continue normal operation of stoping early just and idea everyhing would need be moved inside tho
        shared.myKit.servo[0].angle = angle3
        shared.myKit.servo[1].angle = speed3
        time.sleep(duration3/2)
        if(shared.detection == True):
            return
        time.sleep(duration3/2)
        shared.myKit.servo[0].angle = 90
        shared.myKit.servo[1].angle = 90
    threading.Thread(target=turn_and_stop).start()

#what i changed here is that i moved the d part into that a 
#spce where its locked and cant do anything idea is that this will filterbad reading





#beautifull loop
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



#addition meant to do the blue evading with tweeks on the postion of the blue bucket

    if(localItem == 'blue_bucket' and shared.current_step == 1):
        print("Evading BlueBucket")
        shared.current_step += 1
        #shared.evasionType = 1
        turning(180, 130, 2, 27, 132, 10, "right") #remeber to fix values before real run

    if(localItem == 'blue_bucket' and shared.current_step == 3):
        print("Evading BlueBucket")
        shared.current_step += 1
        #shared.evasionType = 3
        turning(180, 130, 2, 27, 132, 8, "right") #remeber to fix values before real run

    if(localItem == 'blue_bucket' and shared.current_step == 5):
        print("Evading BlueBucket")
        shared.current_step += 1
        #shared.evasionType = 4
        turning(180, 130, 2, 27, 132, 8, "right") #remeber to fix values before real run

    if(localItem == 'blue_bucket' and shared.current_step == 7):
        print("Evading BlueBucket")
        shared.current_step += 1
        #shared.evasionType = 7
        turning(180, 130, 2, 27, 132, 8, "right") #remeber to fix values before real run

#end of additions meant to do the blue evading with tweeks on the postion of the blue bucket



    elif(localItem == 'yellow_bucket' and shared.current_step== 2):
        print("Evading YellowBucket")
        shared.current_step += 1
        shared.evasionType = 2
        turning(27, 130, 3, 170, 132, 8, "left")



    elif(localItem == 'ramp' and shared.current_step==4):
        print("Evading ramp")
        # This holds same function as using a turning method but not threaded , therefore no outside interference
        shared.myKit.servo[0].angle = 160
        shared.myKit.servo[1].angle = 142
        time.sleep(5)
        shared.myKit.servo[0].angle = 35
        shared.myKit.servo[1].angle = 142
        time.sleep(5)
        shared.current_step += 1
        #shared.evasionType = 4



    elif(localItem == 'red_bucketArch' and shared.current_step==6):
        print("Evading RedBucket")
        # drives forward like a madman, no outside distractions
        shared.myKit.servo[0].angle = 92
        shared.myKit.servo[1].angle = 142
        time.sleep(5)
        shared.current_step += 1
        #shared.evasionType = 6 i  * EVASION TYPE IS A DEPRECIATED VARIABLE (NO USE) * 

    else:
        print("This action and level shouldnt happend")
 