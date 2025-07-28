import math
from globals import shared
from genericFunctions import evasion

def AiAlignment(class_name, errorPan, current_step, w):
    if class_name == 'blue_bucket' and abs(errorPan) > 50 and current_step % 2 != 0:
        errorPan = math.ceil(errorPan / 14)
        shared.steeringServoVal = shared.Pconstant * (95 - errorPan) - shared.Dconstant * ((shared.steeringServoVal - shared.pastSteeringServoVal) / 2)
        shared.myKit.servo[0].angle = shared.steeringServoVal
        shared.myKit.servo[1].angle = 143
        shared.pastSteeringServoVal = shared.steeringServoVal
        shared.looking = False
        shared.search_thread = None

    elif class_name == 'yellow_bucket' and abs(errorPan) > 50 and shared.target_conditions['yellow_bucket'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        shared.steeringServoVal = shared.Pconstant * (95 - errorPan) - shared.Dconstant * ((shared.steeringServoVal - shared.pastSteeringServoVal) / 2)
        shared.myKit.servo[0].angle = shared.steeringServoVal
        shared.myKit.servo[1].angle = 143
        shared.pastSteeringServoVal = shared.steeringServoVal
        shared.looking = False
        shared.search_thread = None

    elif class_name == 'red_bucketArch' and abs(errorPan) > 40 and shared.target_conditions['red_bucketArch'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        shared.steeringServoVal = shared.Pconstant * (95 - errorPan) - shared.Dconstant * ((shared.steeringServoVal - shared.pastSteeringServoVal) / 2)
        shared.myKit.servo[0].angle = shared.steeringServoVal
        shared.myKit.servo[1].angle = 143
        shared.pastSteeringServoVal = shared.steeringServoVal
        shared.looking = False
        shared.search_thread = None
        if abs(errorPan) < 100 and w > 1000:
                evasion(class_name)


    elif class_name == 'ramp' and abs(errorPan) > 40 and shared.target_conditions['ramp'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        shared.steeringServoVal = shared.Pconstant * (95 - errorPan) - shared.Dconstant * ((shared.steeringServoVal - shared.pastSteeringServoVal) / 2)
        shared.myKit.servo[0].angle = shared.steeringServoVal
        shared.myKit.servo[1].angle = 143
        shared.pastSteeringServoVal = shared.steeringServoVal
        shared.looking = False
        shared.search_thread = None
        if abs(errorPan) < 100 and w > 450:
                evasion(class_name)



def CVAlignment(errorPan):
        errorPan = math.ceil(errorPan / 14)
        shared.steeringServoVal = shared.Pconstant * (95 - errorPan) - shared.Dconstant * ((shared.steeringServoVal - shared.pastSteeringServoVal) / 2)
        shared.myKit.servo[0].angle = shared.steeringServoVal
        shared.myKit.servo[1].angle = 143
        shared.pastSteeringServoVal = shared.steeringServoVal
        shared.looking = False
        shared.search_thread = None



def AiCamTarget(class_name2, current_step, errorPan2, errorTilt2):
    if class_name2 == 'blue_bucket' and current_step % 2 != 0:
        shared.looking = False
        if abs(errorPan2) > 50:
            if errorPan2 > 0 and shared.xaxiscam < 180:
                shared.xaxiscam += 1
            elif errorPan2 < 0 and shared.xaxiscam > 0:
                shared.xaxiscam -= 1 
            shared.myKit.servo[3].angle = shared.xaxiscam

        if abs(errorTilt2) > 50:
            if errorTilt2 > 0 and shared.yaxiscam < 180:
                shared.yaxiscam += 1
            elif errorTilt2 < 0 and shared.yaxiscam > 0: 
                shared.yaxiscam -= 1 
            shared.myKit.servo[2].angle = shared.yaxiscam

    if class_name2 == 'yellow_bucket' and shared.target_conditions['yellow_bucket'] == shared.current_step:
        shared.looking = False
        if abs(errorPan2) > 50:
            if errorPan2 > 0 and shared.xaxiscam < 180:
                shared.xaxiscam += 1
            elif errorPan2 < 0 and shared.xaxiscam > 0:
                shared.xaxiscam -= 1 
            shared.myKit.servo[3].angle = shared.xaxiscam

        if abs(errorTilt2) > 50:
            if errorTilt2 > 0 and shared.yaxiscam < 180:
                shared.yaxiscam += 1
            elif errorTilt2 < 0 and shared.yaxiscam > 0: 
                shared.yaxiscam -= 1 
            #shared.myKit.servo[2].angle = shared.yaxiscam
            

def CVCamTarget(errorPan2, errorTilt2):
    if errorPan2 > 0 and shared.xaxiscam < 180:
        shared.xaxiscam += 1
    elif errorPan2 < 0 and shared.xaxiscam > 0:
        shared.xaxiscam -= 1
    shared.myKit.servo[3].angle = shared.xaxiscam

    if errorTilt2 > 0 and shared.yaxiscam < 180:
        shared.yaxiscam += 1
    elif errorTilt2 < 0 and shared.yaxiscam > 0:
        shared.yaxiscam -= 1
    #shared.myKit.servo[2].angle = shared.yaxiscam
    #print(f"CAM2CLR CAMVALPAN: {shared.xaxiscam}  CAM2CLR CAMVALTILT: {shared.yaxiscam}")

def AiTurnStopErly(item, current_step, errorPan):
    if abs(errorPan)<300:
        if item == 'blue_bucket' and current_step % 2 != 0:
            shared.myKit.servo[0].angle = 90
            shared.myKit.servo[1].angle = 90
            shared.evading = False

        elif item == 'yellow_bucket' and shared.target_conditions['yellow_bucket'] == current_step:
            shared.myKit.servo[0].angle = 90
            shared.myKit.servo[1].angle = 90
            shared.evading = False

        elif item == 'red_bucketArch' and shared.target_conditions['red_bucketArch'] == current_step:
            shared.myKit.servo[0].angle = 90
            shared.myKit.servo[1].angle = 90
            shared.evading = False

        elif item == 'ramp' and shared.target_conditions['ramp'] == current_step:
            shared.myKit.servo[0].angle = 90
            shared.myKit.servo[1].angle = 90
            shared.evading = False

def CVTurnStopErly(errorPan):
    if abs(errorPan)<200:
        shared.myKit.servo[0].angle = 90
        shared.myKit.servo[1].angle = 90
        shared.evading = False

#____________UNDERWORK______________________________________________________________________
def AisearchStopTrigger(class_name, current_step):
    if class_name in ['blue_bucket', 'yellow_bucket', 'ramp', 'red_buckerArch']:
        target_condition = shared.target_conditions.get(class_name, None)
        if (class_name == 'blue_bucket' and current_step % 2 != 0) or (target_condition == current_step):
            shared.looking = False
            shared.AiHUDkey =True




#hudsons idea align the car using the top cam
def AiHUDcamAlign(startingAngle, class_name2, shared, errorPan2, errorTilt2):
    target_condition = shared.target_conditions.get(class_name2, None)
    if startingAngle != 90 and (
        (class_name2 == 'blue_bucket' and shared.current_step % 2 != 0) or 
        (class_name2 in ['yellow_bucket', 'ramp', 'red_buckerArch'] and shared.current_step == target_condition)
    ):
        difference = startingAngle - 90
        if difference > 0:
            shared.myKit.servo[0].angle = 180
            shared.myKit.servo[1].angle = 127

        elif difference < 0:
            shared.myKit.servo[0].angle = 35
            shared.myKit.servo[1].angle = 127
        
        if errorPan2 > 0 and shared.xaxiscam < 180:
            shared.xaxiscam += 1
        elif errorPan2 < 0 and shared.xaxiscam > 0:
            shared.xaxiscam -= 1
        shared.myKit.servo[3].angle = shared.xaxiscam

        if errorTilt2 > 0 and shared.yaxiscam < 180:
            shared.yaxiscam += 1
        elif errorTilt2 < 0 and shared.yaxiscam > 0:
            shared.yaxiscam -= 1
        #shared.myKit.servo[2].angle = shared.yaxiscam



#____________ENDOFWORK______________________________________________________________________