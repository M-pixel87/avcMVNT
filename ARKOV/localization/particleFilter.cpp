#include "particlefilter.hh"
#include <cmath>
#include <algorithm>

particleFilter::particleFilter(int count, float start_x, float start_y, float start_theta) {
    num_particles = count;
    std::random_device rd;
    rng.seed(rd());
    
    float initial_weight = 1.0f / static_cast<float>(num_particles);

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
    float trans_mag = std::sqrt((delta_x * delta_x) + (delta_y * delta_y));
    
    float noise_x_y = (trans_mag * 0.10f) + 0.01f;
    float noise_th = (std::abs(delta_theta) * 0.05f) + 0.0087266f; 

    std::normal_distribution<float> dist_x(0.0f, noise_x_y);
    std::normal_distribution<float> dist_y(0.0f, noise_x_y);
    std::normal_distribution<float> dist_theta(0.0f, noise_th);

    for (auto& p : particles) {
        p.x += delta_x + dist_x(rng);
        p.y += delta_y + dist_y(rng);
        p.theta += delta_theta + dist_theta(rng);

        p.theta = std::fmod(p.theta, 6.28318530718f);
        if (p.theta < 0.0f) {
            p.theta += 6.28318530718f;
        }
    }
}

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

    for (int i = 0; i < num_particles; i++) {
        resampled_particles.push_back(particles[dist(rng)]);
        resampled_particles.back().weight = 1.0f / static_cast<float>(num_particles);
    }

    particles = resampled_particles;
}