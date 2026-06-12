#define _USE_MATH_DEFINES  

#include <stdio.h>
#include <math.h>

typedef struct {
    float x;
    float y;
    float theta;
} pose;

typedef struct {
    int quality;
    float angle;
    float distance;
} lidarRay;

typedef struct {
    int xSize;
    int ySize;
    float res;
    int* grid;
} map;

float ray_cast(map m, float x, float y, float robot_theta, float ray_angle_deg) {
    float globalRot = robot_theta + (ray_angle_deg * (M_PI / 180.0));
    
    float dx = cosf(globalRot);
    float dy = sinf(globalRot);
    
    float current_dist = 0.0f;
    float step_size = m.res * 0.5f; 
    float max_cast_range = 4.0f;    
    
    while (current_dist < max_cast_range) {
        float wx = x + dx * current_dist;
        float wy = y + dy * current_dist;
     
        int gx = (int)(wx / m.res);
        int gy = (int)(wy / m.res);
        
        if (gx < 0 || gx >= m.xSize || gy < 0 || gy >= m.ySize) {
            return max_cast_range;
        }
        
        if (m.grid[gy * m.xSize + gx] > 0) {
            return current_dist; 
        }
        
        current_dist += step_size;
    }
    return max_cast_range;
}

# THIS IS REPLACED BY CWRAPPER.py c code. This is old and slow
float beam_range_finder_likelihood(const lidarRay* scan, int scanSize, pose p, map m) {
    float q = 0.0f; // Cumulative log-likelihood score
    
    float sigma = 0.15f;
    float z_rand_weight = 0.05f;  
    float z_hit_weight = 0.95f;   
    float max_range = 4.0f;

    float gaussian_constant = 1.0f / (sqrtf(2.0f * M_PI) * sigma);
    
    for (int i = 0; i < scanSize; i++) {
        lidarRay ray = scan[i];
        float actualDist = ray.distance / 1000.0f; 

        // Filter out extreme noise or out-of-bounds readings
        if (actualDist >= max_range || actualDist <= 0.1f) {
            continue;
        }

        float expectedDist = ray_cast(m, p.x, p.y, p.theta, ray.angle);
        

        float delta = actualDist - expectedDist;
        float p_hit = gaussian_constant * expf(-(delta * delta) / (2.0f * sigma * sigma));
        float p_rand = 1.0f / max_range;
        
        float p_total = (z_hit_weight * p_hit) + (z_rand_weight * p_rand);
        
        q += logf(p_total);
    }
    #--------------------------------------------------------------------------------
    
    return q;
}