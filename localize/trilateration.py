
import numpy as np


# ==========================================================
# ROBUST TRILATERATION
# ==========================================================

def trilaterate(
    anchor_positions,
    distances,
    initial_guess
):
    """
    Estimate position using multiple anchors and
    nonlinear least-squares trilateration.

    Parameters
    ----------
    anchor_positions : array-like
        Known anchor coordinates, shape (N, 2).

    distances : array-like
        Measured distance from the drone to each anchor.

    initial_guess : array-like
        Initial position estimate, normally the
        dead-reckoning position.

    Returns
    -------
    numpy.ndarray or None
        Estimated [x, y] position.
        Returns None if the solver cannot produce
        a valid result.
    """

    anchors = np.asarray(
        anchor_positions,
        dtype=float
    )

    dists = np.asarray(
        distances,
        dtype=float
    )

    guess = np.asarray(
        initial_guess,
        dtype=float
    )

    # ------------------------------------------------------
    # Validate input
    # ------------------------------------------------------

    if anchors.ndim != 2:
        return None

    if anchors.shape[1] != 2:
        return None

    if dists.ndim != 1:
        return None

    if len(anchors) != len(dists):
        return None

    if len(anchors) < 3:
        return None

    if guess.shape != (2,):
        return None

    if not np.all(np.isfinite(anchors)):
        return None

    if not np.all(np.isfinite(dists)):
        return None

    if not np.all(np.isfinite(guess)):
        return None

    # ------------------------------------------------------
    # Try scipy least-squares
    # ------------------------------------------------------

    try:

        from scipy.optimize import least_squares

        def residuals(position):

            return (
                np.linalg.norm(
                    anchors - position,
                    axis=1
                )
                - dists
            )

        result = least_squares(
            residuals,
            guess
        )

        if result.success:

            estimated = np.asarray(
                result.x,
                dtype=float
            )

            if np.all(np.isfinite(estimated)):
                return estimated

    except (
        ImportError,
        ValueError,
        np.linalg.LinAlgError
    ):

        pass

    # ------------------------------------------------------
    # Fallback: linear least-squares solution
    # ------------------------------------------------------

    try:

        reference = anchors[0]

        reference_distance = dists[0]

        A = 2.0 * (
            anchors[1:] - reference
        )

        B = (
            reference_distance ** 2
            - dists[1:] ** 2
            + np.sum(
                anchors[1:] ** 2,
                axis=1
            )
            - np.sum(
                reference ** 2
            )
        )

        estimated, _, _, _ = np.linalg.lstsq(
            A,
            B,
            rcond=None
        )

        estimated = np.asarray(
            estimated,
            dtype=float
        )

        if np.all(np.isfinite(estimated)):
            return estimated

    except (
        ValueError,
        np.linalg.LinAlgError
    ):

        pass

    return None


# ==========================================================
# EXACT THREE-ANCHOR SOLVER
# ==========================================================

def trilaterate_exact_3(
    anchor_a,
    anchor_b,
    anchor_c,
    da,
    db,
    dc
):
    """
    Original direct linear trilateration solution
    for exactly three anchors.

    Kept as a reference implementation.

    This function is not the main solver used by
    the multi-drone simulation.
    """

    anchor_a = np.asarray(
        anchor_a,
        dtype=float
    )

    anchor_b = np.asarray(
        anchor_b,
        dtype=float
    )

    anchor_c = np.asarray(
        anchor_c,
        dtype=float
    )

    A = 2.0 * np.array([
        anchor_b - anchor_a,
        anchor_c - anchor_a
    ])

    B = np.array([
        da ** 2
        - db ** 2
        + np.dot(anchor_b, anchor_b)
        - np.dot(anchor_a, anchor_a),

        da ** 2
        - dc ** 2
        + np.dot(anchor_c, anchor_c)
        - np.dot(anchor_a, anchor_a)
    ])

    return np.linalg.solve(A, B)


# ==========================================================
# SIMPLE TEST
# ==========================================================

if __name__ == "__main__":

    anchors = np.array([
        [0.0, 0.0],
        [6.0, 0.0],
        [0.0, 6.0],
        [6.0, 6.0]
    ])

    actual_position = np.array([
        2.0,
        2.0
    ])

    distances = np.linalg.norm(
        anchors - actual_position,
        axis=1
    )

    estimated_position = trilaterate(
        anchors,
        distances,
        initial_guess=[1.5, 1.5]
    )

    print("TRILATERATION TEST")
    print("----------------------------------------")

    print(
        "Actual position:",
        actual_position
    )

    print(
        "Estimated position:",
        np.round(
            estimated_position,
            3
        )
    )

    error = np.linalg.norm(
        estimated_position
        - actual_position
    )

    print(
        "Position error:",
        round(
            float(error),
            3
        ),
        "m"
    )