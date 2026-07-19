#include "pidController.hh"
#include <algorithm>

pidController::pidController(float p, float i, float d){
    k_p = p;
    k_i = i;
    k_d = d;
}

void pidController::setPoint(float newSetPoint){
    setpoint = newSetPoint;
}

float pidController::calculate(float value, float deltaT){
    if(deltaT <= 0.0f) { return 0.0f; }
    
    error = setpoint - value;
    
    integral += (error * deltaT);
    integral = std::clamp(integral, MIN_OUTPUT, MAX_OUTPUT);
    
    deriv = (error - prevError) / deltaT;
    prevError = error;
    
    float output = (error * k_p) + (integral * k_i) + (deriv * k_d);
    return std::clamp(output, MIN_OUTPUT, MAX_OUTPUT); // makes sure output is within the max boundaries
}