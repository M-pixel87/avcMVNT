#pragma once
#include "types.hh"
#include <random>
#include <vector>

class particleFilter{

public:
    particleFilter(int count, float start_x, float start_y, float start_theta);
    void predict(float delta_x, float delta_y, float delta_theta);
    void updateWeights(const VoxelMap& map, const std::vector<LiDARPoint>& scan);
    void resample(); // resampling, particle generator

    Particle getBestPose();

private:
    std::vector<Particle> particles;
    int num_particles; 

    std::mt19937 rng; // Hardware-optimized random number generator

    static constexpr float SIGMA = 0.15f;
    static constexpr float Z_RAND_WEIGHT = 0.05f;
    static constexpr float Z_HIT_WEIGHT = 0.95f;

    // Odometry Noise (Bell Curve) Parameters
    static constexpr float ODOM_TRANS_NOISE = 0.10f;        // 10% translation scaling
    static constexpr float ODOM_TRANS_BASE_NOISE = 0.01f;   // Base translation noise (meters)
    static constexpr float ODOM_ROT_NOISE = 0.05f;          // 5% rotation scaling
    static constexpr float ODOM_ROT_BASE_NOISE = 0.0087266f;// Base rotation noise (radians)

    // LiDAR Hardware Mounting Parameters
    static constexpr float SENSOR_PITCH_DEG = 90.0f; 
    static constexpr float SENSOR_Z_OFFSET = 0.5f;   

    // Endpoint Scoring Parameters
    static constexpr size_t SUBSAMPLE_STRIDE = 20; // optimization , only check nth point
    static constexpr float HIT_SCORE = 2.0f;       
    static constexpr float EMPTY_SCORE = -0.1f;

};