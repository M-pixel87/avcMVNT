import math
from globals import shared

def AiAlignment(class_name, errorPan, current_step):
    if class_name == 'blue_bucket' and abs(errorPan) > 50 and current_step % 2 != 0:
        errorPan = math.ceil(errorPan / 14)
        shared.steeringServoVal = shared.Pconstant * (90 - errorPan) - shared.Dconstant * ((shared.steeringServoVal - shared.pastSteeringServoVal) / 2)
        shared.myKit.servo[0].angle = shared.steeringServoVal
        shared.myKit.servo[1].angle = 126
        shared.pastSteeringServoVal = shared.steeringServoVal
        shared.looking = False
        shared.search_thread = None

    elif class_name == 'yellow_bucket' and abs(errorPan) > 50 and shared.target_conditions['yellow_bucket'] == current_step:
        errorPan = math.ceil(errorPan / 14)
        shared.steeringServoVal = shared.Pconstant * (90 - errorPan) - shared.Dconstant * ((shared.steeringServoVal - shared.pastSteeringServoVal) / 2)
        shared.myKit.servo[0].angle = shared.steeringServoVal
        shared.myKit.servo[1].angle = 126
        shared.pastSteeringServoVal = shared.steeringServoVal
        shared.looking = False
        shared.search_thread = None


def CVAlignment(errorPan):
        errorPan = math.ceil(errorPan / 14)
        shared.steeringServoVal = shared.Pconstant * (90 - errorPan) - shared.Dconstant * ((shared.steeringServoVal - shared.pastSteeringServoVal) / 2)
        shared.myKit.servo[0].angle = shared.steeringServoVal
        shared.myKit.servo[1].angle = 126
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
    shared.myKit.servo[2].angle = shared.yaxiscam
    #print(f"CAM2CLR CAMVALPAN: {shared.xaxiscam}  CAM2CLR CAMVALTILT: {shared.yaxiscam}")

def AiTurnStopErly(item, current_step, errorPan):
    if abs(errorPan)<230:
        if item == 'blue_bucket' and current_step % 2 != 0:
            shared.myKit.servo[0].angle = 90
            shared.myKit.servo[1].angle = 90
            shared.evading = False

        elif item == 'yellow_bucket' and shared.target_conditions['yellow_bucket'] == current_step:
            shared.myKit.servo[0].angle = 90
            shared.myKit.servo[1].angle = 90
            shared.evading = False

        elif item == 'red_bucket_arch' and shared.target_conditions['red_bucket_arch'] == current_step:
            shared.myKit.servo[0].angle = 90
            shared.myKit.servo[1].angle = 90
            shared.evading = False

        elif item == 'ramp' and shared.target_conditions['ramp'] == current_step:
            shared.myKit.servo[0].angle = 90
            shared.myKit.servo[1].angle = 90
            shared.evading = False

def CVTurnStopErly():
    shared.myKit.servo[0].angle = 90
    shared.myKit.servo[1].angle = 90
    shared.evading = False