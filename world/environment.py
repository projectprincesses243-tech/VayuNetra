import pygame
import config
from world.obstacle import Obstacle
from world.zone import Zone


class Environment:
    def __init__(
        self,
        width=config.WORLD_WIDTH,
        height=config.WORLD_HEIGHT
    ):
        self.width = width
        self.height = height

        self.obstacles = [
            Obstacle(
                250,
                150,
                500,
                300
            )
        ]

        self.zones = [
            Zone(1, 50, 50, 200, 150),
            Zone(2, 700, 50, 200, 150),
            Zone(3, 400, 500, 200, 150)
        ]

    def is_inside(self, position):
        x, y = position

        return (
            0 <= x <= self.width
            and
            0 <= y <= self.height
        )

    def keep_inside(self, position):
        x, y = position

        x = max(0, min(x, self.width))
        y = max(0, min(y, self.height))

        return [x, y]

    def draw(self, screen):
        for obstacle in self.obstacles:
            obstacle.draw(screen)

    def is_obstacle(self, position, radius=0):
        for obstacle in self.obstacles:
            if obstacle.contains_point(
                position,
                radius
            ):
                return True

        return False

    def get_avoidance_vector(
        self,
        position,
        radius=0
    ):
        total_x = 0.0
        total_y = 0.0

        for obstacle in self.obstacles:
            vector = obstacle.avoidance_vector(
                position,
                radius
            )

            total_x += vector[0]
            total_y += vector[1]

        return [
            total_x,
            total_y
        ]

    def obstacle_ahead(
        self,
        position,
        velocity,
        lookahead_distance=config.OBSTACLE_LOOKAHEAD,
        radius=0
    ):
        for obstacle in self.obstacles:
            if obstacle.is_ahead(
                position,
                velocity,
                lookahead_distance,
                radius
            ):
                return True

        return False

    def get_predictive_avoidance_vector(
        self,
        position,
        velocity,
        radius=0
    ):
        total_x = 0.0
        total_y = 0.0

        for obstacle in self.obstacles:
            vector = obstacle.get_avoidance_direction(
                position,
                velocity,
                radius
            )

            total_x += vector[0]
            total_y += vector[1]

        return [
            total_x,
            total_y
        ]