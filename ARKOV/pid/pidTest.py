import time


k_p = 0.30
k_i = 0.05 # Larger approaches the target faster, underdamped if too high
k_d = 0.10 # Dampens
prev_error = 0.0
interval = 1.0

integral = 0.0
setpoint = 50

def pidLoop(sensorVal):
    global integral, prev_error

    val = sensorVal # Replace this with real sensor value or sim value

    error = setpoint - val
    integral += (error*interval)
    deriv = (error-prev_error) / interval
    output = (k_p * error) + (integral * k_i) + (deriv * k_d)
    prev_error = error
    print(f"OUTPUT: {output}") # DEBUG
    return output

accelleration = 0.0
velocity = 0.0

def sensorValUpdate(command):
    global accelleration,velocity 

    accelleration = command
    velocity += accelleration
    print(f"ACC: {accelleration}")# DEBUG
    print(f"VEL: {velocity} \n") # DEBUG



def main():
    while(True):
        time.sleep(interval)
        #Poll sensors
        command = pidLoop(velocity) # Returns new command value
        sensorValUpdate(command)


if __name__ == "__main__":
    main()