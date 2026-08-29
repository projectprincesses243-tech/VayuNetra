import numpy as np
import matplotlib.pyplot as plt

from .localizer import Localizer
from .dead_reckoning import DeadReckoner


# ==========================================================
# VAYUNETRA MULTI-DRONE LOCALIZATION BENCHMARK
# ==========================================================

ENVIRONMENT_SIZE = 500.0

NUM_DRONES = 8
NUM_STEPS = 200

DT = 1.0

# Complementary filter weight
# 0.0 = trust trilateration completely
# 1.0 = trust dead reckoning completely
ALPHA = 0.35


# ==========================================================
# SENSOR / SIMULATION SETTINGS
# ==========================================================

RANGE_NOISE_STD = 1.0

RANGE_FAILURE_PROBABILITY = 0.05

DEAD_RECKONING_BIAS = 0.02

RANDOM_SEED = 42


# ==========================================================
# ANCHOR POSITIONS
# ==========================================================

ANCHORS = np.array([
    [0.0, 0.0],
    [500.0, 0.0],
    [0.0, 500.0],
    [500.0, 500.0]
])


# ==========================================================
# INITIAL DRONE POSITIONS
# ==========================================================

INITIAL_POSITIONS = np.array([
    [50.0, 50.0],
    [100.0, 400.0],
    [200.0, 100.0],
    [300.0, 400.0],
    [400.0, 100.0],
    [450.0, 450.0],
    [150.0, 250.0],
    [350.0, 250.0]
])


# ==========================================================
# DRONE VELOCITIES
# ==========================================================

VELOCITIES = np.array([
    [1.0, 0.5],
    [0.8, -0.6],
    [-0.7, 0.9],
    [0.6, -0.8],
    [-0.5, 0.7],
    [-0.8, -0.5],
    [0.9, 0.3],
    [-0.6, 0.4]
])


# ==========================================================
# CREATE DRONES
# ==========================================================

def create_drones():

    drones = []

    for i in range(NUM_DRONES):

        initial_position = INITIAL_POSITIONS[i].copy()

        drone = {
            "id": i + 1,

            # Ground-truth position
            "position": initial_position.copy(),

            # True velocity
            "velocity": VELOCITIES[i].copy(),

            # Independent dead-reckoning estimate
            "dead_reckoning_position":
                initial_position.copy(),

            # Dead reckoner
            "dead_reckoner": DeadReckoner(
                initial_position=initial_position
            ),

            # Initial belief
            "belief_pos": initial_position.copy(),

            # Initial uncertainty
            "uncertainty": 0.0,

            # Simulated sensor ranges
            "simulated_ranges": None
        }

        drones.append(drone)

    return drones


# ==========================================================
# KEEP DRONE INSIDE ENVIRONMENT
# ==========================================================

def keep_inside_environment(drone):

    drone["position"] = np.clip(
        drone["position"],
        0.0,
        ENVIRONMENT_SIZE
    )


# ==========================================================
# SIMULATE NOISY RANGE MEASUREMENTS
# ==========================================================

def simulate_ranges(drone, anchors, rng):

    true_position = np.asarray(
        drone["position"],
        dtype=float
    )

    ranges = []

    for anchor in anchors:

        true_range = np.linalg.norm(
            true_position - anchor
        )

        # Individual range failure
        if rng.random() < RANGE_FAILURE_PROBABILITY:

            ranges.append(np.nan)

            continue

        noisy_range = (
            true_range
            + rng.normal(
                0.0,
                RANGE_NOISE_STD
            )
        )

        noisy_range = max(
            0.1,
            noisy_range
        )

        ranges.append(noisy_range)

    return ranges


# ==========================================================
# CLEAN FAILED RANGES
# ==========================================================

def clean_ranges(ranges, anchors):

    if ranges is None:
        return None

    valid_ranges = []
    valid_anchors = []

    for anchor, distance in zip(
        anchors,
        ranges
    ):

        if np.isfinite(distance):

            valid_anchors.append(anchor)
            valid_ranges.append(distance)

    if len(valid_ranges) < 3:
        return None

    return (
        np.asarray(valid_anchors, dtype=float),
        np.asarray(valid_ranges, dtype=float)
    )


# ==========================================================
# RUN ONE EXPERIMENT
# ==========================================================

def run_experiment(ranging_on):

    rng = np.random.default_rng(RANDOM_SEED)

    drones = create_drones()

    localizers = [
        Localizer(
            alpha=ALPHA,
            ranging_on=ranging_on
        )
        for _ in range(NUM_DRONES)
    ]

    error_history = []

    trajectory_actual = []

    trajectory_estimated = []

    for step in range(NUM_STEPS):

        step_errors = []

        actual_snapshot = []

        estimated_snapshot = []

        for i, drone in enumerate(drones):

            # ------------------------------------------------
            # 1. UPDATE TRUE POSITION
            # ------------------------------------------------

            drone["position"] = (
                drone["position"]
                + drone["velocity"] * DT
            )

            keep_inside_environment(drone)

            # ------------------------------------------------
            # 2. UPDATE DEAD RECKONING
            # ------------------------------------------------

            measured_velocity = (
                drone["velocity"]
                * (1.0 + DEAD_RECKONING_BIAS)
            )

            drone["dead_reckoning_position"] = (
                drone["dead_reckoning_position"]
                + measured_velocity * DT
            )

            drone["dead_reckoner"].position = (
                drone["dead_reckoning_position"].copy()
            )

            # ------------------------------------------------
            # 3. RANGE MEASUREMENTS
            # ------------------------------------------------

            if ranging_on:

                raw_ranges = simulate_ranges(
                    drone,
                    ANCHORS,
                    rng
                )

                cleaned = clean_ranges(
                    raw_ranges,
                    ANCHORS
                )

                if cleaned is None:

                    drone["simulated_ranges"] = None

                else:

                    valid_anchors, valid_ranges = cleaned

                    # Store the complete range set.
                    # NaN values represent failed measurements.
                    drone["simulated_ranges"] = raw_ranges

            else:

                drone["simulated_ranges"] = None

            # ------------------------------------------------
            # 4. LOCALIZATION
            # ------------------------------------------------

            estimated_position = localizers[i].update(
                drone,
                drones,
                ANCHORS
            )

            # ------------------------------------------------
            # 5. ERROR
            # ------------------------------------------------

            error = localizers[i].error(drone)

            if error is not None:

                step_errors.append(error)

            actual_snapshot.append(
                drone["position"].copy()
            )

            estimated_snapshot.append(
                estimated_position.copy()
            )

        # ----------------------------------------------------
        # SAVE HISTORY
        # ----------------------------------------------------

        if step_errors:

            error_history.append(
                np.asarray(step_errors)
            )

        trajectory_actual.append(
            np.asarray(actual_snapshot)
        )

        trajectory_estimated.append(
            np.asarray(estimated_snapshot)
        )

    return {
        "errors": np.asarray(error_history),
        "actual": np.asarray(trajectory_actual),
        "estimated": np.asarray(
            trajectory_estimated
        ),
        "drones": drones
    }


# ==========================================================
# PRINT EXPERIMENT RESULTS
# ==========================================================

def print_results(
    title,
    results
):

    errors = results["errors"]

    flat_errors = errors.flatten()

    print()
    print("----------------------------------------")
    print(title)
    print("----------------------------------------")

    print(
        "Average localization error:",
        round(
            float(np.mean(flat_errors)),
            3
        ),
        "m"
    )

    print(
        "Maximum localization error:",
        round(
            float(np.max(flat_errors)),
            3
        ),
        "m"
    )

    print(
        "Minimum localization error:",
        round(
            float(np.min(flat_errors)),
            3
        ),
        "m"
    )


# ==========================================================
# ERROR PLOT
# ==========================================================

def create_error_plot(
    off_results,
    on_results
):

    off_mean = np.mean(
        off_results["errors"],
        axis=1
    )

    on_mean = np.mean(
        on_results["errors"],
        axis=1
    )

    steps = np.arange(
        1,
        NUM_STEPS + 1
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.plot(
        steps,
        off_mean,
        label="Ranging OFF"
    )

    plt.plot(
        steps,
        on_mean,
        label="Ranging ON"
    )

    plt.xlabel(
        "Simulation Step"
    )

    plt.ylabel(
        "Average Localization Error (m)"
    )

    plt.title(
        "VayuNetra Localization Error Comparison"
    )

    plt.legend()

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        "localize/results_error_comparison.png",
        dpi=150
    )

    plt.close()


# ==========================================================
# TRAJECTORY PLOT
# ==========================================================

def create_trajectory_plot(
    off_results,
    on_results
):

    actual = off_results["actual"]

    off_estimated = (
        off_results["estimated"]
    )

    on_estimated = (
        on_results["estimated"]
    )

    plt.figure(
        figsize=(10, 8)
    )

    # Plot actual trajectory of Drone 1
    plt.plot(
        actual[:, 0, 0],
        actual[:, 0, 1],
        marker="o",
        markersize=2,
        label="Actual Drone 1"
    )

    # Ranging OFF
    plt.plot(
        off_estimated[:, 0, 0],
        off_estimated[:, 0, 1],
        label="Estimated - Ranging OFF"
    )

    # Ranging ON
    plt.plot(
        on_estimated[:, 0, 0],
        on_estimated[:, 0, 1],
        label="Estimated - Ranging ON"
    )

    # Anchors
    plt.scatter(
        ANCHORS[:, 0],
        ANCHORS[:, 1],
        marker="^",
        s=80,
        label="Anchors"
    )

    plt.xlabel(
        "X Position (m)"
    )

    plt.ylabel(
        "Y Position (m)"
    )

    plt.title(
        "VayuNetra Drone Localization Trajectory"
    )

    plt.xlim(
        0,
        ENVIRONMENT_SIZE
    )

    plt.ylim(
        0,
        ENVIRONMENT_SIZE
    )

    plt.legend()

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        "localize/results_trajectory_comparison.png",
        dpi=150
    )

    plt.close()


# ==========================================================
# MAIN BENCHMARK
# ==========================================================

def run_simulation():

    print()
    print("VAYUNETRA LOCALIZATION BENCHMARK")
    print("----------------------------------------")

    print(
        f"Environment: "
        f"{ENVIRONMENT_SIZE} x "
        f"{ENVIRONMENT_SIZE} m"
    )

    print(
        f"Drones: {NUM_DRONES}"
    )

    print(
        f"Simulation steps: {NUM_STEPS}"
    )

    print(
        f"Alpha: {ALPHA}"
    )

    print(
        f"Range noise STD: "
        f"{RANGE_NOISE_STD} m"
    )

    print(
        f"Range failure probability: "
        f"{RANGE_FAILURE_PROBABILITY * 100:.1f}%"
    )

    # ======================================================
    # RANGING OFF
    # ======================================================

    print()
    print("Running RANGING OFF experiment...")

    off_results = run_experiment(
        ranging_on=False
    )

    # ======================================================
    # RANGING ON
    # ======================================================

    print(
        "Running RANGING ON experiment..."
    )

    on_results = run_experiment(
        ranging_on=True
    )

    # ======================================================
    # RESULTS
    # ======================================================

    print_results(
        "RANGING OFF",
        off_results
    )

    print_results(
        "RANGING ON",
        on_results
    )

    # ======================================================
    # COMPARISON
    # ======================================================

    off_average = float(
        np.mean(
            off_results["errors"]
        )
    )

    on_average = float(
        np.mean(
            on_results["errors"]
        )
    )

    improvement = (
        (off_average - on_average)
        / off_average
        * 100.0
    )

    print()
    print("----------------------------------------")
    print("FINAL COMPARISON")
    print("----------------------------------------")

    print(
        f"Ranging OFF average error: "
        f"{off_average:.3f} m"
    )

    print(
        f"Ranging ON average error:  "
        f"{on_average:.3f} m"
    )

    print(
        f"Error improvement: "
        f"{improvement:.1f}%"
    )

    # ======================================================
    # CREATE PLOTS
    # ======================================================

    create_error_plot(
        off_results,
        on_results
    )

    create_trajectory_plot(
        off_results,
        on_results
    )

    print()
    print("----------------------------------------")
    print("PLOTS SAVED")
    print("----------------------------------------")

    print(
        "localize/results_error_comparison.png"
    )

    print(
        "localize/results_trajectory_comparison.png"
    )

    # ======================================================
    # FINAL DRONE POSITIONS — RANGING ON
    # ======================================================

    print()
    print("----------------------------------------")
    print("FINAL RANGING-ON DRONE POSITIONS")
    print("----------------------------------------")

    for drone in on_results["drones"]:

        print(
            f"Drone {drone['id']}: "
            f"Actual="
            f"{np.round(drone['position'], 2)} | "
            f"Estimated="
            f"{np.round(drone['belief_pos'], 2)} | "
            f"Uncertainty="
            f"{drone['uncertainty']:.3f} m"
        )


# ==========================================================
# PROGRAM ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    run_simulation()