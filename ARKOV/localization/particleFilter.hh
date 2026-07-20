#pragma once
#include "types.hh"
#include <random>

class particleFilter{

public:
    particleFilter(int count, float start_x, float start_y, float start_theta);
    void predict(float delta_x, float delta_y, float delta_theta);
    void resample(); // resampling, particle generator

    Particle getBestPose();

private:
    std::vector<Particle> particles;

    std::mt19937 rng; // Hardware-optimized random number generator

    static constexpr float SIGMA = 0.15f;
    static constexpr float Z_RAND_WEIGHT = 0.05f;
    static constexpr float Z_HIT_WEIGHT = 0.95f;

};