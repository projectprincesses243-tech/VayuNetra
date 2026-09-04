import numpy as np


class DeadReckoner:
    """
    Simple 2D dead-reckoning model.

    The position is updated using the supplied velocity
    and time step.
    """

    def __init__(self, initial_position=(0.0, 0.0)):
        self.position = np.asarray(initial_position, dtype=float)

    def update(self, velocity=(0.0, 0.0), dt=1.0):
        velocity = np.asarray(velocity, dtype=float)

        self.position = self.position + velocity * dt

        return self.position.copy()


if __name__ == "__main__":

    reckoner = DeadReckoner()

    print("DEAD RECKONING TEST")
    print("----------------------------------------")

    for step in range(1, 11):

        position = reckoner.update(
            velocity=(1.05, 0.52)
        )

        actual_position = np.array([
            float(step),
            float(step) * 0.5
        ])

        error = np.linalg.norm(position - actual_position)

        print(
            f"Step: {step} | "
            f"Actual: {np.round(actual_position, 3)} | "
            f"Estimated: {np.round(position, 3)} | "
            f"Position error: {error:.3f} m"
        )