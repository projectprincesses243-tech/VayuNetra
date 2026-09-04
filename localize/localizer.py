import numpy as np

from .dead_reckoning import DeadReckoner
from .ranging import get_ranges
from .trilateration import trilaterate
from .complementary_filter import complementary_filter


class Localizer:

    def __init__(self, alpha=0.35, ranging_on=True):
        self.alpha = alpha
        self.ranging_on = ranging_on

    # ======================================================
    # UPDATE LOCALIZATION
    # ======================================================

    def update(self, drone, all_drones, anchors):
        """
        Update the drone's estimated position.

        Pipeline:

        Dead Reckoning
              |
              +------+
                     |
        Trilateration|
              |      |
              +------+
                     |
                     v
          Complementary Filter
                     |
                     v
                 belief_pos
        """

        # --------------------------------------------------
        # 1. DEAD RECKONING
        # --------------------------------------------------

        if "dead_reckoner" not in drone:

            drone["dead_reckoner"] = DeadReckoner(
                initial_position=drone.get(
                    "position",
                    [0.0, 0.0]
                )
            )

        # Use the simulation's independent DR estimate
        # when it is available.

        if "dead_reckoning_position" in drone:

            dr_position = np.asarray(
                drone["dead_reckoning_position"],
                dtype=float
            )

            drone["dead_reckoner"].position = (
                dr_position.copy()
            )

        else:

            dr_position = np.asarray(
                drone["dead_reckoner"].update(
                    drone.get(
                        "velocity",
                        [0.0, 0.0]
                    )
                ),
                dtype=float
            )

        # --------------------------------------------------
        # 2. TRILATERATION
        # --------------------------------------------------

        trilat_position = None

        if self.ranging_on:

            try:

                ranges = get_ranges(
                    drone,
                    all_drones,
                    anchors
                )

                if (
                    ranges is not None
                    and len(ranges) >= 3
                ):

                    # The trilateration solver expects:
                    #
                    #   anchors
                    #   distances
                    #   initial guess
                    #
                    trilat_position = trilaterate(
                        anchors,
                        ranges,
                        dr_position
                    )

            except (
                TypeError,
                ValueError,
                np.linalg.LinAlgError
            ):

                trilat_position = None

        # --------------------------------------------------
        # 3. COMPLEMENTARY FILTER
        # --------------------------------------------------

        filtered_position = complementary_filter(
            dr_position,
            trilat_position,
            alpha=self.alpha
        )

        # --------------------------------------------------
        # 4. STORE BELIEF
        # --------------------------------------------------

        drone["belief_pos"] = np.asarray(
            filtered_position,
            dtype=float
        )

        # --------------------------------------------------
        # 5. UNCERTAINTY
        # --------------------------------------------------

        if trilat_position is None:

            drone["uncertainty"] = 1.0

        else:

            drone["uncertainty"] = float(
                np.linalg.norm(
                    dr_position
                    - np.asarray(
                        trilat_position,
                        dtype=float
                    )
                )
            )

        return drone["belief_pos"]

    # ======================================================
    # LOCALIZATION ERROR
    # ======================================================

    def error(self, drone):
        """
        Calculate localization error using the
        ground-truth position available in simulation.
        """

        if (
            "position" not in drone
            or "belief_pos" not in drone
        ):
            return None

        actual = np.asarray(
            drone["position"],
            dtype=float
        )

        estimated = np.asarray(
            drone["belief_pos"],
            dtype=float
        )

        return float(
            np.linalg.norm(
                actual - estimated
            )
        )