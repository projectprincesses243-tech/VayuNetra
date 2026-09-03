import numpy as np
import matplotlib.pyplot as plt

from .localizer import Localizer
from .dead_reckoning import DeadReckoner


# ==========================================================
# VAYUNETRA MULTI-DRONE LOCALIZATION
# TURNING / CURVED TRAJECTORY BENCHMARK
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
# SENSOR SETTINGS
# ==========================================================

RANGE_NOISE_STD = 1.0

RANGE_FAILURE_PROBABILITY = 0.05

# Dead-reckoning systematic bias.
# The actual error model is implemented inside DeadReckoner.
DEAD_RECKONING_BIAS = 0.02

# Random-walk noise used by DeadReckoner.
DEAD_RECKONING_RANDOM_WALK_STD = 0.005

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
# BASE VELOCITIES
# ==========================================================

BASE_VELOCITIES = np.array([
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

def create_drones(rng):

    drones = []

    for i in range(NUM_DRONES):

        initial_position = INITIAL_POSITIONS[i].copy()

        drone = {
            "id": i + 1,

            # Ground truth position
            "position": initial_position.copy(),

            # Current true velocity
            "velocity": BASE_VELOCITIES[i].copy(),

            # Dead-reckoning estimate
            "dead_reckoning_position":
                initial_position.copy(),

            # Dead reckoner object
            "dead_reckoner": DeadReckoner(
                initial_position=initial_position,
                bias=DEAD_RECKONING_BIAS,
                random_walk_std=DEAD_RECKONING_RANDOM_WALK_STD,
                rng=rng
            ),

            # Localization result
            "belief_pos": initial_position.copy(),

            # Uncertainty
            "uncertainty": 0.0,

            # Simulated ranges
            "simulated_ranges": None
        }

        drones.append(drone)

    return drones


# ==========================================================
# TURNING / CURVED MOTION
# ==========================================================

def update_velocity(drone_index, step):

    base_velocity = BASE_VELOCITIES[drone_index]

    # Different turning rates for different drones.
    turn_rate = 0.015 + (
        drone_index * 0.002
    )

    # Slowly change heading as simulation progresses.
    angle = turn_rate * step

    rotation = np.array([
        [np.cos(angle), -np.sin(angle)],
        [np.sin(angle),  np.cos(angle)]
    ])

    velocity = rotation @ base_velocity

    return velocity


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

        # Random range failure
        if rng.random() < RANGE_FAILURE_PROBABILITY:

            ranges.append(np.nan)

            continue

        # Gaussian range noise
        noisy_range = (
            true_range
            + rng.normal(
                0.0,
                RANGE_NOISE_STD
            )
        )

        # Distance cannot be negative
        noisy_range = max(
            0.1,
            noisy_range
        )

        ranges.append(noisy_range)

    return ranges


# ==========================================================
# CLEAN RANGE MEASUREMENTS
# ==========================================================

def clean_ranges(ranges):

    if ranges is None:
        return None

    valid_ranges = [
        value
        for value in ranges
        if np.isfinite(value)
    ]

    if len(valid_ranges) < 3:
        return None

    return valid_ranges


# ==========================================================
# RUN ONE EXPERIMENT
# ==========================================================

def run_experiment(ranging_on):

    rng = np.random.default_rng(RANDOM_SEED)

    drones = create_drones(rng)

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

    for step in range(1, NUM_STEPS + 1):

        step_errors = []

        actual_snapshot = []

        estimated_snapshot = []

        for i, drone in enumerate(drones):

            # ------------------------------------------------
            # 1. UPDATE TRUE VELOCITY
            # ------------------------------------------------

            drone["velocity"] = update_velocity(
                i,
                step
            )

            # ------------------------------------------------
            # 2. UPDATE TRUE POSITION
            # ------------------------------------------------

            drone["position"] = (
                drone["position"]
                + drone["velocity"] * DT
            )

            keep_inside_environment(drone)

            # ------------------------------------------------
            # 3. UPDATE DEAD RECKONING
            # ------------------------------------------------

            drone["dead_reckoning_position"] = (
                drone["dead_reckoner"].update(
                    velocity=drone["velocity"],
                    dt=DT
                )
            )

            # ------------------------------------------------
            # 4. RANGE MEASUREMENTS
            # ------------------------------------------------

            if ranging_on:

                ranges = simulate_ranges(
                    drone,
                    ANCHORS,
                    rng
                )

                cleaned_ranges = clean_ranges(
                    ranges
                )

                if cleaned_ranges is None:

                    drone["simulated_ranges"] = None

                else:

                    drone["simulated_ranges"] = ranges

            else:

                drone["simulated_ranges"] = None

            # ------------------------------------------------
            # 5. LOCALIZATION
            # ------------------------------------------------

            estimated_position = localizers[i].update(
                drone,
                drones,
                ANCHORS
            )

            # ------------------------------------------------
            # 6. ERROR
            # ------------------------------------------------

            error = localizers[i].error(
                drone
            )

            if error is not None:

                step_errors.append(error)

            actual_snapshot.append(
                drone["position"].copy()
            )

            estimated_snapshot.append(
                estimated_position.copy()
            )

        # ----------------------------------------------------
        # SAVE STEP DATA
        # ----------------------------------------------------

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
        "VayuNetra Turning-Trajectory Error Comparison"
    )

    plt.legend()

    plt.grid(True)

    plt.tight_layout()

    plt.savefig(
        "localize/results_turning_error_comparison.png",
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

    # Drone 1 actual path
    plt.plot(
        actual[:, 0, 0],
        actual[:, 0, 1],
        marker="o",
        markersize=2,
        label="Actual Drone 1"
    )

    # Dead-reckoning path
    plt.plot(
        off_estimated[:, 0, 0],
        off_estimated[:, 0, 1],
        label="Estimated - Ranging OFF"
    )

    # Localization path
    plt.plot(
        on_estimated[:, 0, 0],
        on_estimated[:, 0, 1],
        label="Estimated - Ranging ON"
    )

    # Anchor locations
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
        "VayuNetra Turning Drone Trajectory"
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
        "localize/results_turning_trajectory_comparison.png",
        dpi=150
    )

    plt.close()


# ==========================================================
# MAIN SIMULATION
# ==========================================================

def run_simulation():

    print()

    print(
        "VAYUNETRA TURNING-TRAJECTORY "
        "LOCALIZATION BENCHMARK"
    )

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

    print(
        f"Dead-reckoning bias: "
        f"{DEAD_RECKONING_BIAS}"
    )

    print(
        f"Dead-reckoning random-walk STD: "
        f"{DEAD_RECKONING_RANDOM_WALK_STD}"
    )

    print()

    # ======================================================
    # RANGING OFF
    # ======================================================

    print(
        "Running RANGING OFF "
        "turning experiment..."
    )

    off_results = run_experiment(
        ranging_on=False
    )

    # ======================================================
    # RANGING ON
    # ======================================================

    print(
        "Running RANGING ON "
        "turning experiment..."
    )

    on_results = run_experiment(
        ranging_on=True
    )

    # ======================================================
    # RESULTS
    # ======================================================

    off_errors = (
        off_results["errors"].flatten()
    )

    on_errors = (
        on_results["errors"].flatten()
    )

    off_average = float(
        np.mean(off_errors)
    )

    on_average = float(
        np.mean(on_errors)
    )

    off_maximum = float(
        np.max(off_errors)
    )

    on_maximum = float(
        np.max(on_errors)
    )

    improvement = (
        (off_average - on_average)
        / off_average
        * 100.0
    )

    # ======================================================
    # PRINT RESULTS
    # ======================================================

    print()

    print("----------------------------------------")
    print("RANGING OFF")
    print("----------------------------------------")

    print(
        f"Average localization error: "
        f"{off_average:.3f} m"
    )

    print(
        f"Maximum localization error: "
        f"{off_maximum:.3f} m"
    )

    print()

    print("----------------------------------------")
    print("RANGING ON")
    print("----------------------------------------")

    print(
        f"Average localization error: "
        f"{on_average:.3f} m"
    )

    print(
        f"Maximum localization error: "
        f"{on_maximum:.3f} m"
    )

    print()

    print("----------------------------------------")
    print("TURNING-TRAJECTORY COMPARISON")
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
    print("TURNING-TRAJECTORY PLOTS SAVED")
    print("----------------------------------------")

    print(
        "localize/"
        "results_turning_error_comparison.png"
    )

    print(
        "localize/"
        "results_turning_trajectory_comparison.png"
    )

    # ======================================================
    # FINAL POSITIONS
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