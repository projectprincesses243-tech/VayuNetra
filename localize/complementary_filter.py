import numpy as np


def complementary_filter(dead_reckoning, trilateration, alpha=0.35):
    """
    Combine dead-reckoning and trilateration.

    alpha = 0.0 -> trust trilateration completely
    alpha = 1.0 -> trust dead reckoning completely

    If trilateration is unavailable, dead reckoning is returned.
    """

    dead_reckoning = np.asarray(dead_reckoning, dtype=float)

    if trilateration is None:
        return dead_reckoning.copy()

    trilateration = np.asarray(trilateration, dtype=float)

    filtered_position = (
        alpha * dead_reckoning
        + (1.0 - alpha) * trilateration
    )

    return filtered_position


if __name__ == "__main__":

    actual_positions = np.array([
        [1.0, 0.5],
        [2.0, 1.0],
        [3.0, 1.5],
        [4.0, 2.0],
        [5.0, 2.5],
        [6.0, 3.0],
        [7.0, 3.5],
        [8.0, 4.0],
        [9.0, 4.5],
        [10.0, 5.0]
    ])

    dead_reckoning_positions = actual_positions * 1.05

    trilateration_positions = actual_positions + np.array([
        [0.05, -0.02],
        [0.10, -0.04],
        [0.15, -0.06],
        [0.20, -0.08],
        [0.25, -0.10],
        [0.30, -0.12],
        [0.35, -0.14],
        [0.40, -0.16],
        [0.45, -0.18],
        [0.50, -0.20]
    ])

    alpha = 0.5

    filtered_positions = []

    for step in range(len(actual_positions)):

        filtered = complementary_filter(
            dead_reckoning_positions[step],
            trilateration_positions[step],
            alpha
        )

        filtered_positions.append(filtered)

    filtered_positions = np.array(filtered_positions)

    dead_reckoning_errors = np.linalg.norm(
        dead_reckoning_positions - actual_positions,
        axis=1
    )

    trilateration_errors = np.linalg.norm(
        trilateration_positions - actual_positions,
        axis=1
    )

    filtered_errors = np.linalg.norm(
        filtered_positions - actual_positions,
        axis=1
    )

    print("MULTI-STEP LOCALIZATION")
    print("----------------------------------------")

    for i in range(len(actual_positions)):

        print(
            f"Step {i + 1}: "
            f"Actual={np.round(actual_positions[i], 3)} | "
            f"DR={np.round(dead_reckoning_positions[i], 3)} | "
            f"Trilat={np.round(trilateration_positions[i], 3)} | "
            f"Filtered={np.round(filtered_positions[i], 3)}"
        )

        print(
            f"         "
            f"DR Error={dead_reckoning_errors[i]:.3f} m | "
            f"Trilat Error={trilateration_errors[i]:.3f} m | "
            f"Filtered Error={filtered_errors[i]:.3f} m"
        )

    print()
    print("----------------------------------------")
    print("AVERAGE ERRORS")
    print("----------------------------------------")

    print(
        "Dead Reckoning:",
        round(np.mean(dead_reckoning_errors), 3),
        "m"
    )

    print(
        "Trilateration:",
        round(np.mean(trilateration_errors), 3),
        "m"
    )

    print(
        "Complementary Filter:",
        round(np.mean(filtered_errors), 3),
        "m"
    )
