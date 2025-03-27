def AiAlignment(class_name, errorPan, current_step):  
    if class_name == 'blue_bucket' and abs(errorPan) > 50 and current_step % 2 != 0:
        errorPan = math.ceil(errorPan / 14)
        steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
        myKit.servo[0].angle = steeringServoVal
        myKit.servo[1].angle = 126
        pastSteeringServoVal = steeringServoVal
        looking = False
        search_thread = None

    elif class_name == 'yellow_bucket' and abs(errorPan) > 50 and target_conditions['yellow_bucket'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
        myKit.servo[0].angle = steeringServoVal
        myKit.servo[1].angle = 126
        pastSteeringServoVal = steeringServoVal
        looking = False
        search_thread = None

    elif class_name == 'red_buckerArch' and abs(errorPan) > 50 and target_conditions['red_buckerArch'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
        myKit.servo[0].angle = steeringServoVal
        myKit.servo[1].angle = 126
        pastSteeringServoVal = steeringServoVal
        looking = False
        search_thread = None

    elif class_name == 'ramp' and abs(errorPan) > 50 and target_conditions['ramp'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
        myKit.servo[0].angle = steeringServoVal
        myKit.servo[1].angle = 126
        pastSteeringServoVal = steeringServoVal
        looking = False
        search_thread = None


def CVAlignment():
    errorPan = math.ceil(errorPan / 14)
    steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
    myKit.servo[0].angle = steeringServoVal
    myKit.servo[1].angle = 126
    pastSteeringServoVal= steeringServoVal
    looking = False




#only applies to cam 2btw one with servos


def AiCamTarget(class_name2, current_step):
    global xaxiscam, yaxiscam, looking      
    if class_name2 == 'blue_bucket' and current_step % 2 != 0:
        looking = False
        
        if abs(errorPan2) > 50:
            if errorPan2 > 0 and xaxiscam < 180:
                xaxiscam += 1
            elif errorPan2 < 0 and xaxiscam > 0:
                xaxiscam -= 1 
            myKit.servo[3].angle = xaxiscam  

        if abs(errorTilt2) > 50:
            if errorTilt2 > 0 and yaxiscam < 180:
                yaxiscam += 1
            elif errorTilt2 < 0 and yaxiscam > 0: 
                yaxiscam -= 1 
            myKit.servo[2].angle = yaxiscam  

    elif class_name2 == 'yellow_bucket' and target_conditions['yellow_bucket'] == current_step:
        looking = False
        
        if abs(errorPan2) > 50:
            if errorPan2 > 0 and xaxiscam < 180:
                xaxiscam += 1
            elif errorPan2 < 0 and xaxiscam > 0:
                xaxiscam -= 1 
            myKit.servo[3].angle = xaxiscam

        if abs(errorTilt2) > 50:
            if errorTilt2 > 0 and yaxiscam < 180:
                yaxiscam += 1
            elif errorTilt2 < 0 and yaxiscam > 0: 
                yaxiscam -= 1 
            myKit.servo[2].angle = yaxiscam 



def CVCamTarget():
    global xaxiscam, yaxiscam     
    if errorPan2 > 0 and xaxiscam < 180:
        xaxiscam += 1
    elif errorPan2 < 0 and xaxiscam > 0:
        xaxiscam -= 1
    myKit.servo[3].angle = xaxiscam  
    if errorTilt2 > 0 and yaxiscam < 180:
        yaxiscam += 1
    elif errorTilt2 < 0 and yaxiscam > 0:
        yaxiscam -= 1
    myKit.servo[2].angle = yaxiscam  

    print(f"CAM2CLR CAMVALPAN: {xaxiscam}  CAM2CLR CAMVALTILT: {yaxiscam}")









#stop early function
def AiTurnStopErly(item, errorPan, current_step):  

    if item == 'blue_bucket' and current_step % 2 != 0:
        myKit.servo[0].angle = 90
        myKit.servo[1].angle = 90
        evading = False

    elif item == 'yellow_bucket' and target_conditions['yellow_bucket'] == current_step:
        myKit.servo[0].angle = 90
        myKit.servo[1].angle = 90
        evading = False

    elif item == 'red_buckerArch' and target_conditions['red_buckerArch'] == current_step:
        myKit.servo[0].angle = 90
        myKit.servo[1].angle = 90
        evading = False

    elif item == 'ramp' and target_conditions['ramp'] == current_step:
        myKit.servo[0].angle = 90
        myKit.servo[1].angle = 90
        evading = False


def CVTurnStopErly():
    myKit.servo[0].angle = 90
    myKit.servo[1].angle = 90
    evading = False




def SearchAiAlignment(item, errorPan, current_step):  
    if item == 'blue_bucket' and abs(errorPan) > 50 and current_step % 2 != 0:
        errorPan = math.ceil(errorPan / 14)
        steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
        myKit.servo[0].angle = steeringServoVal
        myKit.servo[1].angle = 126
        pastSteeringServoVal = steeringServoVal
        looking = False
        search_thread = None

    elif item == 'yellow_bucket' and abs(errorPan) > 50 and target_conditions['yellow_bucket'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
        myKit.servo[0].angle = steeringServoVal
        myKit.servo[1].angle = 126
        pastSteeringServoVal = steeringServoVal
        looking = False
        search_thread = None

    elif item == 'red_buckerArch' and abs(errorPan) > 50 and target_conditions['red_buckerArch'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
        myKit.servo[0].angle = steeringServoVal
        myKit.servo[1].angle = 126
        pastSteeringServoVal = steeringServoVal
        looking = False
        search_thread = None

    elif item == 'ramp' and abs(errorPan) > 50 and target_conditions['ramp'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
        myKit.servo[0].angle = steeringServoVal
        myKit.servo[1].angle = 126
        pastSteeringServoVal = steeringServoVal
        looking = False
        search_thread = None


def SearchCVAlignment():
    errorPan = math.ceil(errorPan / 14)
    steeringServoVal = Pconstant * (90 - errorPan) - Dconstant * ((steeringServoVal - pastSteeringServoVal) / 2)
    myKit.servo[0].angle = steeringServoVal
    myKit.servo[1].angle = 126
    pastSteeringServoVal= steeringServoVal
    looking = False