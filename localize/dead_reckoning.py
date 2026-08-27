import numpy as np

# 2D dead reckoning with drift

actual_x = 0.0
actual_y = 0.0

estimated_x = 0.0
estimated_y = 0.0

# Simulate 10 movements
for step in range(1, 11):

    # Actual drone movement
    actual_x = actual_x + 1.0
    actual_y = actual_y + 0.5

    # Estimated movement has a small error
    estimated_x = estimated_x + 1.05
    estimated_y = estimated_y + 0.52

    # Calculate position error
    error_x = estimated_x - actual_x
    error_y = estimated_y - actual_y

    # Calculate total distance error
    position_error = np.sqrt(error_x**2 + error_y**2)

    print(
        "Step:", step,
        "| Actual:", (round(actual_x, 2), round(actual_y, 2)),
        "| Estimated:", (round(estimated_x, 2), round(estimated_y, 2)),
        "| Position error:", round(position_error, 3), "m"
    )