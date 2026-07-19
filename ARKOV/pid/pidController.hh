#pragma once

class pidController{

private:
    float k_p = 0.0f;
    float k_i = 0.0f;
    float k_d = 0.0f;

    float error = 0.0f;
    float setpoint = 0.0f;
    float prevError = 0.0f;

    float integral = 0.0f;
    float deriv = 0.0f;

    static constexpr float MAX_OUTPUT = 255.0f;
    static constexpr float MIN_OUTPUT = -255.0f;

public:
    pidController(float p, float i, float d);
    float calculate(float value, float deltaT);
    void setPoint(float newSetPoint);

};