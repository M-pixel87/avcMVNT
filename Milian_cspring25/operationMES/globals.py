class SharedState:
    def __init__(self):
        self.myKit = None
        self.evading = False
        self.orbiting = False
        self.looking = False
        self.search_thread = None
        self.steeringServoVal = 0
        self.pastSteeringServoVal = 0
        self.xaxiscam = 110
        self.yaxiscam = 90
        self.onbutton = 0
        self.pigsfly = 0
        self.current_step = 4
        self.Pconstant = 1.0
        self.Dconstant = 1.0
        self.lastItem = None
        self.evasionType = 0     
        self.detection = False   
        self.bigContours = False    
        self.bigContours2 = False    
        self.turningleft = False     
        self.turnright = False       
        self.angle = 0
        self.AiHUDkey =False
        self.target_conditions = {
            'blue_bucket_firstime': 1,
            'yellow_bucket': 2,
            'blue_bucket_secondtime': 3,
            'ramp': 4,
            'blue_bucket_thirdtime': 5,
            'red_bucketArch': 6,
            'blue_bucket_lasttime': 7
        }

shared = SharedState()