import pygame
import config


class Obstacle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            (120, 120, 120),
            (
                self.x,
                self.y,
                self.width,
                self.height
            )
        )

    def contains_point(self, position, radius=0):
        x, y = position

        return (
            self.x - radius <= x <= self.x + self.width + radius
            and
            self.y - radius <= y <= self.y + self.height + radius
        )

    def avoidance_vector(self, position, radius=0):
        x, y = position

        left = self.x - radius
        right = self.x + self.width + radius
        top = self.y - radius
        bottom = self.y + self.height + radius

        if not (
            left <= x <= right
            and
            top <= y <= bottom
        ):
            return [0.0, 0.0]

        distances = {
            "left": abs(x - left),
            "right": abs(right - x),
            "top": abs(y - top),
            "bottom": abs(bottom - y)
        }

        nearest_side = min(
            distances,
            key=distances.get
        )

        if nearest_side == "left":
            return [-1.0, 0.0]

        if nearest_side == "right":
            return [1.0, 0.0]

        if nearest_side == "top":
            return [0.0, -1.0]

        return [0.0, 1.0]

    def is_ahead(
        self,
        position,
        velocity,
        lookahead_distance,
        radius=0
    ):
        speed = (
            velocity[0] ** 2 +
            velocity[1] ** 2
        ) ** 0.5

        if speed == 0:
            return False

        direction_x = velocity[0] / speed
        direction_y = velocity[1] / speed

        steps = 20

        for i in range(1, steps + 1):
            distance = (
                lookahead_distance * i / steps
            )

            test_position = [
                position[0] + direction_x * distance,
                position[1] + direction_y * distance
            ]

            if self.contains_point(
                test_position,
                radius
            ):
                return True

        return False

    def get_avoidance_direction(
        self,
        position,
        velocity,
        radius=0
    ):
        x, y = position

        speed = (
            velocity[0] ** 2 +
            velocity[1] ** 2
        ) ** 0.5

        if speed == 0:
            return [0.0, 0.0]

        # If the obstacle is not ahead,
        # it should not influence the drone.
        if not self.is_ahead(
            position,
            velocity,
            config.OBSTACLE_LOOKAHEAD,
            radius
        ):
            return [0.0, 0.0]

        left = self.x - radius
        right = self.x + self.width + radius
        top = self.y - radius
        bottom = self.y + self.height + radius

        # Find the center of the obstacle.
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2

        # Determine whether the drone is approaching
        # from the left or right.
        if x < center_x:
            horizontal_direction = -1.0
        else:
            horizontal_direction = 1.0

        # Compare top and bottom escape distances.
        distance_to_top = abs(y - top)
        distance_to_bottom = abs(bottom - y)

        if distance_to_top <= distance_to_bottom:
            vertical_direction = -1.0
        else:
            vertical_direction = 1.0

        # If approaching mostly horizontally,
        # prioritize going around the obstacle vertically.
        if abs(velocity[0]) >= abs(velocity[1]):
            return [
                0.0,
                vertical_direction
            ]

        # If approaching mostly vertically,
        # prioritize horizontal escape.
        return [
            horizontal_direction,
            0.0
        ]