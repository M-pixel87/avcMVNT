#include <iostream>
#include <chrono>
#include <thread>

double k_p = 0.30;
double k_i = 0.05;
double k_d = 0.10;

double prev_error = 0.0;
double interval = 1.0;

double integral = 0.0;
uint8_t setpoint = 50;


double pidLoop(double sensorVal){
    error = setpoint - sensorVal;
    integral += (error * interval);
    deriv = (error-prev_error)/interval;
    prev_error = error;
    return((error*k_p)+(integral*k_i)+(deriv*k_d));
}


double accelleration = 0.0;
double velocity = 0.0;

double sensorValUpdate(double command){
    accelleration = command;
    velocity += accelleration;
}


int main(){
    while(1){
        this_thread::sleep_for(chrono::seconds(1));
        double command = pidLoop(velocity);
        sensorValUpdate(command);

    }

    return 0;
}