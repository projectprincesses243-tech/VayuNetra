import numpy as np

# Positions of three drones
drone_a = np.array([0.0, 0.0])
drone_b = np.array([3.0, 4.0])
drone_c = np.array([6.0, 0.0])

# Calculate distances between drones
distance_ab = np.linalg.norm(drone_b - drone_a)
distance_ac = np.linalg.norm(drone_c - drone_a)
distance_bc = np.linalg.norm(drone_c - drone_b)

print("Drone A position:", drone_a)
print("Drone B position:", drone_b)
print("Drone C position:", drone_c)

print("Distance A-B:", round(distance_ab, 2), "metres")
print("Distance A-C:", round(distance_ac, 2), "metres")
print("Distance B-C:", round(distance_bc, 2), "metres")