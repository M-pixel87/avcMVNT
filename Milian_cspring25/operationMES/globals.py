class SharedState:
    def __init__(self):
        self.myKit = None
        self.evading = False
        self.looking = False
        self.search_thread = None
        self.steeringServoVal = 0
        self.pastSteeringServoVal = 0
        self.xaxiscam = 110
        self.yaxiscam = 90
        self.onbutton = 0
        self.pigsfly = 0
        self.current_step = 1
        self.Pconstant = 1.0
        self.Dconstant = 1.0
        self.lastItem = None
        self.evasionType = 0        # Added
        self.bigContours = False     # Added
        self.bigContours2 = False    # Added
        self.turningleft = False     # Added
        self.turnright = False       # Added
        self.searching = False       # Added
        self.target_conditions = {
            'blue_bucket_firstime': 1,
            'yellow_bucket': 2,
            'blue_bucket_secondtime': 3,
            'ramp': 4,
            'blue_bucket_thirdtime': 5,
            'red_bucket_arch': 6,
            'blue_bucket_lasttime': 7
        }

shared = SharedState()