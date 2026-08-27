import numpy as np

# Known positions of three anchor drones
anchor_a = np.array([0.0, 0.0])
anchor_b = np.array([6.0, 0.0])
anchor_c = np.array([3.0, 5.0])

# Actual position - used ONLY to create test measurements
actual_position = np.array([2.0, 2.0])

# Simulated distance measurements
# Perfect distances
true_distance_a = np.linalg.norm(actual_position - anchor_a)
true_distance_b = np.linalg.norm(actual_position - anchor_b)
true_distance_c = np.linalg.norm(actual_position - anchor_c)

# Add small measurement errors
distance_a = true_distance_a + 0.10
distance_b = true_distance_b - 0.08
distance_c = true_distance_c + 0.05

# Build the trilateration equations
A = 2 * np.array([
    anchor_b - anchor_a,
    anchor_c - anchor_a
])

B = np.array([
    distance_a**2 - distance_b**2
    + np.dot(anchor_b, anchor_b)
    - np.dot(anchor_a, anchor_a),

    distance_a**2 - distance_c**2
    + np.dot(anchor_c, anchor_c)
    - np.dot(anchor_a, anchor_a)
])

# Solve for the estimated position
estimated_position = np.linalg.solve(A, B)

print("Actual position:", actual_position)
print("Estimated position:", np.round(estimated_position, 3))
# Calculate position error
position_error = np.linalg.norm(
    estimated_position - actual_position
)

print("Position error:", round(position_error, 3), "m")