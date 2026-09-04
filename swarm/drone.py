import math
import pygame
import config


class Drone:
    def __init__(self, drone_id, position):
        self.drone_id = drone_id
        self.position = list(position)
        self.velocity = [0.0, 0.0]

        self.max_speed = config.MAX_SPEED

        self.radius = 10

        self.heading = 0.0

        self.battery = 100.0
        self.state = "IDLE"
        self.zone = None
        self.current_task = None

    def update_position(self, environment, dt):
        new_position = [
            self.position[0] + self.velocity[0] * dt,
            self.position[1] + self.velocity[1] * dt
        ]

        new_position = environment.keep_inside(
            new_position
        )

        # Normal movement.
        if not environment.is_obstacle(
            new_position,
            self.radius
        ):
            self.position = new_position
            return

        # If the full movement would enter an obstacle,
        # try moving horizontally only.
        horizontal_position = [
            new_position[0],
            self.position[1]
        ]

        if not environment.is_obstacle(
            horizontal_position,
            self.radius
        ):
            self.position = horizontal_position
            self.velocity[1] = 0.0
            return

        # If horizontal movement is blocked,
        # try moving vertically only.
        vertical_position = [
            self.position[0],
            new_position[1]
        ]

        if not environment.is_obstacle(
            vertical_position,
            self.radius
        ):
            self.position = vertical_position
            self.velocity[0] = 0.0
            return

        # If both directions are blocked,
        # stop the velocity so the drone does not
        # continue pushing into the obstacle.
        self.velocity[0] = 0.0
        self.velocity[1] = 0.0

    def limit_speed(self):
        speed = math.sqrt(
            self.velocity[0] ** 2 +
            self.velocity[1] ** 2
        )

        if speed > self.max_speed:
            scale = self.max_speed / speed

            self.velocity[0] *= scale
            self.velocity[1] *= scale

    def draw(self, screen):
        x = int(self.position[0])
        y = int(self.position[1])

        pygame.draw.circle(
            screen,
            (0, 200, 255),
            (x, y),
            8
        )

        font = pygame.font.Font(
            None,
            18
        )

        label = font.render(
            f"D{self.drone_id}",
            True,
            (255, 255, 255)
        )

        screen.blit(
            label,
            (x + 10, y - 8)
        )