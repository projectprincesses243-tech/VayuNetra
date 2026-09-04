import math
import config


class Boids:
    def __init__(
        self,
        neighbor_radius=config.NEIGHBOR_RADIUS,
        separation_strength=config.SEPARATION_STRENGTH,
        max_steering_force=config.MAX_STEERING_FORCE,
        separation_weight=config.SEPARATION_WEIGHT,
        alignment_weight=config.ALIGNMENT_WEIGHT,
        cohesion_weight=config.COHESION_WEIGHT

    ):
        self.neighbor_radius = neighbor_radius
        self.separation_strength = separation_strength
        self.max_steering_force = max_steering_force

        self.separation_weight = separation_weight
        self.alignment_weight = alignment_weight
        self.cohesion_weight = cohesion_weight
        self.obstacle_avoidance_weight = config.OBSTACLE_AVOIDANCE_WEIGHT

    def get_neighbors(self, drone, drones):
        neighbors = []

        for other in drones:
            if other is drone:
                continue

            dx = other.position[0] - drone.position[0]
            dy = other.position[1] - drone.position[1]

            distance = math.sqrt(dx**2 + dy**2)

            if distance <= self.neighbor_radius:
                neighbors.append(other)

        return neighbors

    def separation(self, drone, neighbors):
        separation_vector = [0.0, 0.0]

        for neighbor in neighbors:
            dx = drone.position[0] - neighbor.position[0]
            dy = drone.position[1] - neighbor.position[1]

            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                separation_vector[0] += dx / distance
                separation_vector[1] += dy / distance

        return [
            separation_vector[0] * self.separation_strength,
            separation_vector[1] * self.separation_strength
        ]


    def alignment(self, drone, neighbors):
        if not neighbors:
            return [0.0, 0.0]

        average_velocity = [0.0, 0.0]

        for neighbor in neighbors:
            average_velocity[0] += neighbor.velocity[0]
            average_velocity[1] += neighbor.velocity[1]

        average_velocity[0] /= len(neighbors)
        average_velocity[1] /= len(neighbors)

        return [
            average_velocity[0] - drone.velocity[0],
            average_velocity[1] - drone.velocity[1]
        ]

    def cohesion(self, drone, neighbors):
        if not neighbors:
            return [0.0, 0.0]

        center = [0.0, 0.0]

        for neighbor in neighbors:
            center[0] += neighbor.position[0]
            center[1] += neighbor.position[1]

        center[0] /= len(neighbors)
        center[1] /= len(neighbors)

        return [
            center[0] - drone.position[0],
            center[1] - drone.position[1]
        ]


    def target_seeking(self, drone, target):
        if target is None:
            return [0.0, 0.0]

        dx = target[0] - drone.position[0]
        dy = target[1] - drone.position[1]

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return [0.0, 0.0]

        direction_x = dx / distance
        direction_y = dy / distance

        return [
            direction_x * drone.max_speed,
            direction_y * drone.max_speed
        ]

    def obstacle_avoidance(self, drone, environment):
        avoidance = environment.get_predictive_avoidance_vector(
            drone.position,
            drone.velocity,
            drone.radius
        )

        return [
            avoidance[0] * self.obstacle_avoidance_weight,
            avoidance[1] * self.obstacle_avoidance_weight
        ]

    def limit_steering(self, steering):
        magnitude = math.sqrt(
            steering[0] ** 2 +
            steering[1] ** 2
        )

        if magnitude > self.max_steering_force:
            scale = self.max_steering_force / magnitude

            steering[0] *= scale
            steering[1] *= scale

        return steering