

def ESCWaitFunction():
    global onbutton 
    
    while onbutton == 0:
        buttonstate_state = GPIO.input('GP48_SPI1_MISO')
        
        if buttonstate_state == GPIO.HIGH:
            print("Input pin is HIGH! MVMNT start")
            onbutton = 1
            myKit.servo[1].angle = 126  
        else:
            print("Input pin is LOW, don't move yet")
            myKit.servo[1].angle = 90
            time.sleep(5)


def searching():
    global looking, search_thread

    if search_thread and search_thread.is_alive():
        print("Search thread already running. Skipping new search.")
        return  

    def look_Around():
        global looking, search_thread
        looking = True
        angle = 0
        anglechng = 10
        myKit.servo[3].angle = 0 
        myKit.servo[2].angle = 90  
        print(":STARTING SEARCH:")

        while looking:
            if not looking:  
                print(":SEARCH STOPPED EARLY:")
                break

            print(f"Looking around at angle: {angle}")
            myKit.servo[3].angle = angle
            time.sleep(1)
            angle += anglechng

            if angle == 190 or angle == -10:
                anglechng *= -1


        #iwill need these two set to turn of the thread
        #looking = False
        #search_thread = None 
    
    search_thread = threading.Thread(target=look_Around)
    search_thread.start()




def turning(angle, speed, duration, angle2, speed2, duration2):
    def turn_and_stop():
        global evading
        myKit.servo[0].angle = angle
        myKit.servo[1].angle = speed
        myKit.servo[2].angle = 90
        myKit.servo[3].angle = 90
        time.sleep(duration)
        myKit.servo[0].angle = angle2
        myKit.servo[1].angle = speed2
        # In between the time of the second turn it will make evading false, meaning object detection can start
        time.sleep(duration2/2)
        time.sleep(duration2/2)
        myKit.servo[0].angle = 90
        myKit.servo[1].angle = 90
        evading = False
        print('')
        print('DONE EVADING')
        print('')
    threading.Thread(target=turn_and_stop).start()
