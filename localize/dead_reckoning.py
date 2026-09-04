import numpy as np


class DeadReckoner:
    """
    2D dead-reckoning model with a fixed velocity bias
    and per-step random-walk noise.
    """

    def __init__(
        self,
        initial_position=(0.0, 0.0),
        bias=0.02,
        random_walk_std=0.005,
        rng=None
    ):
        self.position = np.asarray(
            initial_position,
            dtype=float
        )

        # Fixed velocity bias for this dead-reckoner.
        self.bias = float(bias)

        # Small random error added at every update.
        self.random_walk_std = float(
            random_walk_std
        )

        # Optional reproducible random generator.
        self.rng = rng

    def update(self, velocity=(0.0, 0.0), dt=1.0):
        velocity = np.asarray(
            velocity,
            dtype=float
        )

        # Fixed systematic error.
        measured_velocity = (
            velocity * (1.0 + self.bias)
        )

        # Per-step random walk.
        if self.rng is not None:
            random_error = self.rng.normal(
                0.0,
                self.random_walk_std,
                size=velocity.shape
            )
        else:
            random_error = np.zeros_like(
                velocity
            )

        measured_velocity = (
            measured_velocity + random_error
        )

        self.position = (
            self.position
            + measured_velocity * dt
        )

        return self.position.copy()


if __name__ == "__main__":

    rng = np.random.default_rng(42)

    reckoner = DeadReckoner(
        bias=0.02,
        random_walk_std=0.005,
        rng=rng
    )

    print("DEAD RECKONING TEST")
    print("----------------------------------------")

    for step in range(1, 11):

        position = reckoner.update(
            velocity=(1.0, 0.5)
        )

        actual_position = np.array([
            float(step),
            float(step) * 0.5
        ])

        error = np.linalg.norm(
            position - actual_position
        )

        print(
            f"Step: {step} | "
            f"Actual: {np.round(actual_position, 3)} | "
            f"Estimated: {np.round(position, 3)} | "
            f"Position error: {error:.3f} m"
        )