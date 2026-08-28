import math


class PathFollower:

    def __init__(
        self,
        waypoint_radius=25
    ):

        self.waypoint_radius = (
            waypoint_radius
        )

        self.paths = {}

        self.current_waypoints = {}

    def set_path(
        self,
        drone_id,
        path
    ):

        self.paths[drone_id] = path

        self.current_waypoints[
            drone_id
        ] = 0

    def clear_path(
        self,
        drone_id
    ):

        if drone_id in self.paths:

            del self.paths[
                drone_id
            ]

        if drone_id in self.current_waypoints:

            del self.current_waypoints[
                drone_id
            ]

    def get_current_waypoint(
        self,
        drone_id
    ):

        if drone_id not in self.paths:

            return None

        path = self.paths[
            drone_id
        ]

        if not path:

            return None

        index = self.current_waypoints.get(
            drone_id,
            0
        )

        if index >= len(path):

            return None

        return path[index]

    def update(
        self,
        drone
    ):

        waypoint = self.get_current_waypoint(
            drone.drone_id
        )

        if waypoint is None:

            return None

        dx = (
            waypoint[0] -
            drone.position[0]
        )

        dy = (
            waypoint[1] -
            drone.position[1]
        )

        distance = math.sqrt(
            dx ** 2 +
            dy ** 2
        )

        if distance <= self.waypoint_radius:

            self.current_waypoints[
                drone.drone_id
            ] += 1

            waypoint = (
                self.get_current_waypoint(
                    drone.drone_id
                )
            )

        return waypoint

    def is_complete(
        self,
        drone_id
    ):

        if drone_id not in self.paths:

            return True

        path = self.paths[
            drone_id
        ]

        if not path:

            return True

        index = self.current_waypoints.get(
            drone_id,
            0
        )

        return index >= len(path)