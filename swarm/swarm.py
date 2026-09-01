import math
import config

from missions.manager import MissionManager
from swarm.boids import Boids
from planning.astar import AStarPlanner
from planning.path_follower import PathFollower


class Swarm:

    def __init__(self):

        self.drones = []

        self.boids = Boids()

        self.mission_manager = MissionManager(
            self.drones
        )

        self.path_planner = None

        self.path_follower = PathFollower(
            waypoint_radius=25
        )

    def add_drone(self, drone):

        self.drones.append(drone)

    def initialize_path_planner(self, environment):

        self.path_planner = AStarPlanner(
            environment,
            grid_size=20,
            drone_radius=10
        )

    def plan_drone_path(self, drone):

        if self.path_planner is None:
            return False

        if drone.zone is None:
            return False

        start = drone.position

        goal = drone.zone.center()

        path = self.path_planner.plan(
            start,
            goal
        )

        if not path:
            print(
                f"A* could not find a path for "
                f"Drone {drone.drone_id}"
            )
            return False

        self.path_follower.set_path(
            drone.drone_id,
            path
        )

        print(
            f"A* path planned for Drone "
            f"{drone.drone_id}: "
            f"{len(path)} waypoints"
        )

        return True

    def plan_all_paths(self):

        for drone in self.drones:

            if drone.zone is not None:

                self.plan_drone_path(
                    drone
                )

    def update(self, environment, dt):

        # -------------------------------------------------
        # Make sure A* planner exists
        # -------------------------------------------------

        if self.path_planner is None:

            self.initialize_path_planner(
                environment
            )

        for drone in self.drones:

            # -------------------------------------------------
            # Completed drones do not move
            # -------------------------------------------------

            if drone.state == "COMPLETED":
                continue

            # -------------------------------------------------
            # Get A* waypoint
            # -------------------------------------------------

            waypoint = (
                self.path_follower.update(
                    drone
                )
            )

            # -------------------------------------------------
            # If no waypoint exists, use mission zone
            # -------------------------------------------------

            if waypoint is None:

                if drone.zone is not None:

                    waypoint = (
                        drone.zone.center()
                    )

                else:

                    waypoint = None

            # -------------------------------------------------
            # Find Boids neighbours
            # -------------------------------------------------

            neighbors = self.boids.get_neighbors(
                drone,
                self.drones
            )

            # -------------------------------------------------
            # Calculate Boids behaviours
            # -------------------------------------------------

            separation = self.boids.separation(
                drone,
                neighbors
            )

            alignment = self.boids.alignment(
                drone,
                neighbors
            )

            cohesion = self.boids.cohesion(
                drone,
                neighbors
            )

            target_seeking = self.boids.target_seeking(
                drone,
                waypoint
            )

            obstacle_avoidance = (
                self.boids.obstacle_avoidance(
                    drone,
                    environment
                )
            )

            # -------------------------------------------------
            # Apply existing Phase 6 weights
            # -------------------------------------------------

            separation = [
                separation[0] *
                self.boids.separation_weight,

                separation[1] *
                self.boids.separation_weight
            ]

            alignment = [
                alignment[0] *
                self.boids.alignment_weight,

                alignment[1] *
                self.boids.alignment_weight
            ]

            cohesion = [
                cohesion[0] *
                self.boids.cohesion_weight,

                cohesion[1] *
                self.boids.cohesion_weight
            ]

            target_seeking = [
                target_seeking[0] *
                config.TARGET_SEEKING_WEIGHT,

                target_seeking[1] *
                config.TARGET_SEEKING_WEIGHT
            ]

            # -------------------------------------------------
            # Combine behaviours
            # -------------------------------------------------

            steering = [

                separation[0]
                + alignment[0]
                + cohesion[0]
                + target_seeking[0]
                + obstacle_avoidance[0],

                separation[1]
                + alignment[1]
                + cohesion[1]
                + target_seeking[1]
                + obstacle_avoidance[1]
            ]

            # -------------------------------------------------
            # Limit steering
            # -------------------------------------------------

            steering = self.boids.limit_steering(
                steering
            )

            # -------------------------------------------------
            # Apply steering
            # -------------------------------------------------

            drone.velocity[0] += (
                steering[0] * dt
            )

            drone.velocity[1] += (
                steering[1] * dt
            )

            # -------------------------------------------------
            # Limit speed
            # -------------------------------------------------

            drone.limit_speed()

            # -------------------------------------------------
            # Update heading
            # -------------------------------------------------

            if hasattr(
                drone,
                "update_heading"
            ):

                drone.update_heading()

            # -------------------------------------------------
            # Move
            # -------------------------------------------------

            drone.update_position(
                environment,
                dt
            )

            # -------------------------------------------------
            # Check mission completion
            # -------------------------------------------------

            if drone.zone is not None:

                target = drone.zone.center()

                dx = (
                    drone.position[0] -
                    target[0]
                )

                dy = (
                    drone.position[1] -
                    target[1]
                )

                distance_to_zone = math.sqrt(
                    dx ** 2 +
                    dy ** 2
                )

                if (
                    distance_to_zone <=
                    config.ZONE_ARRIVAL_RADIUS
                ):

                    drone.state = "COMPLETED"

                    drone.velocity = [
                        0.0,
                        0.0
                    ]

                    self.path_follower.clear_path(
                        drone.drone_id
                    )

        # -------------------------------------------------
        # Update Mission Manager
        # -------------------------------------------------

        self.mission_manager.update()

    def draw(self, screen):

        for drone in self.drones:

            drone.draw(screen)