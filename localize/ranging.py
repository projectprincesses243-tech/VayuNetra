
import numpy as np


# ==========================================================
# RANGE MEASUREMENT SETTINGS
# ==========================================================

DEFAULT_NOISE_STD = 1.0


# ==========================================================
# CALCULATE DISTANCE
# ==========================================================

def calculate_distance(position_a, position_b):
    """
    Calculate Euclidean distance between two 2D positions.
    """

    position_a = np.asarray(position_a, dtype=float)
    position_b = np.asarray(position_b, dtype=float)

    return float(
        np.linalg.norm(position_a - position_b)
    )


# ==========================================================
# GET RANGES
# ==========================================================

def get_ranges(
    drone,
    all_drones,
    anchors,
    noise_std=DEFAULT_NOISE_STD,
    rng=None
):
    """
    Generate range measurements from the target drone
    to the known anchors.

    If the drone contains 'simulated_ranges', those
    measurements are used directly.

    Parameters
    ----------
    drone : dict
        Drone whose position is being estimated.

    all_drones : list
        Other drones in the simulation.

    anchors : array-like
        Known anchor positions.

    noise_std : float
        Standard deviation of range noise.

    rng : numpy random generator
        Random generator used for reproducible noise.

    Returns
    -------
    list or None
        Range measurements.
    """

    # ------------------------------------------------------
    # USE SIMULATED MEASUREMENTS WHEN AVAILABLE
    # ------------------------------------------------------

    if "simulated_ranges" in drone:

        simulated_ranges = drone["simulated_ranges"]

        if simulated_ranges is None:
            return None

        return list(simulated_ranges)

    # ------------------------------------------------------
    # OTHERWISE CALCULATE RANGES FROM POSITION
    # ------------------------------------------------------

    if "position" not in drone:
        return None

    position = np.asarray(
        drone["position"],
        dtype=float
    )

    ranges = []

    for anchor in anchors:

        anchor = np.asarray(
            anchor,
            dtype=float
        )

        true_distance = calculate_distance(
            position,
            anchor
        )

        # Add measurement noise
        if rng is not None:
            noise = rng.normal(
                0.0,
                noise_std
            )
        else:
            noise = 0.0

        measured_distance = (
            true_distance + noise
        )

        # Distance cannot be negative
        measured_distance = max(
            0.1,
            measured_distance
        )

        ranges.append(
            measured_distance
        )

    return ranges