import matplotlib.pyplot as plt
import numpy as np
import math

# --- 1. Your Raw Data ---
# Load in pounds (lbs)
load_lbs = np.array([
    0, 2850, 5710, 8560, 11400, 17100, 20000, 20800, 23000,
    24200, 26800, 28800, 33650, 35750, 36000, 35850, 34050, 28000
])

# Gage length in inches (in.)
gage_length_in = np.array([
    2.000, 2.001, 2.002, 2.003, 2.004, 2.006, 2.008, 2.01, 2.015,
    2.02, 2.03, 2.04, 2.08, 2.12, 2.14, 2.16, 2.20, 2.23
])

# --- 2. Initial Specimen Parameters ---
# From problem 6-36 (which this data is for)
L0_initial_length = 2.000  # in.
d0_initial_diameter = 0.505  # in.

# Calculate the original cross-sectional area
A0_initial_area = math.pi * (d0_initial_diameter / 2)**2
# A0 ≈ 0.2003 in^2

# --- 3. Calculate Stress and Strain ---

# Engineering Strain (ε = delta_L / L0)
# (Gage Length - Initial Length) / Initial Length
engineering_strain = (gage_length_in - L0_initial_length) / L0_initial_length

# Engineering Stress (σ = F / A0)
# Load / Initial Area
# We will convert to ksi (kips per square inch) for cleaner numbers
# 1 ksi = 1000 psi
engineering_stress_psi = load_lbs / A0_initial_area
engineering_stress_ksi = engineering_stress_psi / 1000.0

# --- 4. Plot the Stress-Strain Curve ---

plt.figure