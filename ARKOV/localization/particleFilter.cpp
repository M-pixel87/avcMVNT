#include "particlefilter.hh"
#include <cmath>
#include <algorithm>
#include <limits>

/*!
    \addtogroup SLAM
*/

particleFilter::particleFilter(int count, float start_x, float start_y, float start_theta) {
    num_particles = count;
    std::random_device rd;
    rng.seed(rd());
    
    //This creates an initial equal probability for all particles
    float initial_weight = 1.0f / static_cast<float>(num_particles);

    //LOOP THROUGH PARTICLE NUM: assign positions, theta, weight, add to list
    for (int i = 0; i < num_particles; i++) {
        Particle p;
        p.x = start_x;
        p.y = start_y;
        p.theta = start_theta;
        p.weight = initial_weight;
        particles.push_back(p);
    }
}

void particleFilter::predict(float delta_x, float delta_y, float delta_theta) {
    // Magnitude of the translation
    float trans_mag = std::sqrt((delta_x * delta_x) + (delta_y * delta_y));
    
    // Apply noise to the pose components using tunable header constants
    float noise_x_y = (trans_mag * ODOM_TRANS_NOISE) + ODOM_TRANS_BASE_NOISE;
    float noise_th = (std::abs(delta_theta) * ODOM_ROT_NOISE) + ODOM_ROT_BASE_NOISE; 

    // Bell Curve Distribution
    std::normal_distribution<float> dist_x(0.0f, noise_x_y);
    std::normal_distribution<float> dist_y(0.0f, noise_x_y);
    std::normal_distribution<float> dist_theta(0.0f, noise_th);

    // Add noise & odometry to particles on a curve
    for (auto& p : particles) {
        p.x += delta_x + dist_x(rng);
        p.y += delta_y + dist_y(rng);
        p.theta += delta_theta + dist_theta(rng);

        // fmod makes sure rotation wraps 360->0 0->360
        p.theta = std::fmod(p.theta, 6.28318530718f);
        if (p.theta < 0.0f) {
            p.theta += 6.28318530718f;
        }
    }
}

void particleFilter::updateWeights(const VoxelMap& map, const std::vector<LiDARPoint>& scan) {
    // Convert header pitch degrees to radians and precompute trig
    constexpr float PITCH_RAD = SENSOR_PITCH_DEG * (3.14159265359f / 180.0f);
    static const float cos_pitch = std::cos(PITCH_RAD);
    static const float sin_pitch = std::sin(PITCH_RAD);

    float max_log_weight = -std::numeric_limits<float>::infinity();

    for (auto& p : particles) {
        float log_weight = 0.0f;
        
        const float cos_yaw = std::cos(p.theta);
        const float sin_yaw = std::sin(p.theta);

        for (size_t i = 0; i < scan.size(); i += SUBSAMPLE_STRIDE) {
            const auto& pt = scan[i];
            
            // Static LiDAR pitch offset
            float pitched_x = (pt.x * cos_pitch) + (pt.z * sin_pitch);
            float pitched_y = pt.y; 
            float pitched_z = (-pt.x * sin_pitch) + (pt.z * cos_pitch);
            
            // Dynamic particle yaw rotation
            float rotated_x = (pitched_x * cos_yaw) - (pitched_y * sin_yaw);
            float rotated_y = (pitched_x * sin_yaw) + (pitched_y * cos_yaw);
            float rotated_z = pitched_z; 
            
            // Map coordinates lookup
            float map_x = p.x + rotated_x;
            float map_y = p.y + rotated_y;
            float map_z = SENSOR_Z_OFFSET + rotated_z; 
            
            int voxel_state = map.getVoxelState(map_x, map_y, map_z);
            
            if (voxel_state == 1) { // 1 = OCCUPIED
                log_weight += HIT_SCORE;
            } else if (voxel_state == 0) { // 0 = EMPTY
                log_weight += EMPTY_SCORE;
            }
        }
        
        p.weight = log_weight;
        
        if (log_weight > max_log_weight) {
            max_log_weight = log_weight;
        }
    }

    // Normalize weights by shifting max to 0 to prevent float overflow
    float weight_sum = 0.0f;
    for (auto& p : particles) {
        p.weight = std::exp(p.weight - max_log_weight);
        weight_sum += p.weight;
    }

    // Convert weights back to standard probability curve
    for (auto& p : particles) {
        p.weight /= weight_sum;
    }
}


// loops through and just finds best pose, maybe can be optimized idk
Particle particleFilter::getBestPose() {
    Particle best_particle = particles[0];
    for (const auto& p : particles) {
        if (p.weight > best_particle.weight) {
            best_particle = p;
        }
    }
    return best_particle;
}

void particleFilter::resample() {
    std::vector<float> weights;
    weights.reserve(num_particles);
    for (const auto& p : particles) {
        weights.push_back(p.weight);
    }

    std::discrete_distribution<int> dist(weights.begin(), weights.end());
    std::vector<Particle> resampled_particles;
    resampled_particles.reserve(num_particles);

    // loops through and copies particles with a chance based on weight. Then resets its likelihood to equally probable
    for (int i = 0; i < num_particles; i++) {
        resampled_particles.push_back(particles[dist(rng)]);
        resampled_particles.back().weight = 1.0f / static_cast<float>(num_particles);
    }

    particles = resampled_particles;
}

//! @}