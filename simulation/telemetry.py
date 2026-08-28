import csv
import time
import config


class Telemetry:
    def __init__(self):
        self.time = 0.0
        self.records = []

        # Obstacle avoidance telemetry
        self.obstacle_avoidance_events = 0
        self.previous_obstacle_state = {}

        # Collision telemetry
        self.drone_collision_events = 0
        self.obstacle_collision_events = 0

        # Mission / zone telemetry
        self.zone_arrival_events = 0
        self.previous_zone_state = {}

        # Run information
        self.run_id = int(time.time())
        self.experiment_name = config.EXPERIMENT_NAME

    def update_time(self, dt):
        self.time += dt

    def record_drone(self, drone):
        speed = (
            drone.velocity[0] ** 2 +
            drone.velocity[1] ** 2
        ) ** 0.5

        record = {
            "run_id": self.run_id,
            "experiment": self.experiment_name,
            "time": self.time,
            "drone_id": drone.drone_id,
            "x": drone.position[0],
            "y": drone.position[1],
            "vx": drone.velocity[0],
            "vy": drone.velocity[1],
            "speed": speed,
            "battery": drone.battery,
            "state": drone.state,
            "zone": drone.zone,
            "task": drone.current_task
        }

        self.records.append(record)

    def record_swarm(self, swarm, environment=None):

        # --------------------------------------------------
        # Record individual drone telemetry
        # --------------------------------------------------

        for drone in swarm.drones:

            self.record_drone(drone)

            if environment is not None:

                # --------------------------------------------------
                # Obstacle avoidance detection
                # --------------------------------------------------

                obstacle_active = environment.obstacle_ahead(
                    drone.position,
                    drone.velocity,
                    radius=drone.radius
                )

                previous_state = self.previous_obstacle_state.get(
                    drone.drone_id,
                    False
                )

                # Count only False -> True transitions
                if obstacle_active and not previous_state:
                    self.obstacle_avoidance_events += 1

                self.previous_obstacle_state[
                    drone.drone_id
                ] = obstacle_active

                # --------------------------------------------------
                # Obstacle collision detection
                # --------------------------------------------------

                if environment.is_obstacle(
                    drone.position,
                    drone.radius
                ):
                    self.obstacle_collision_events += 1

                # --------------------------------------------------
                # Zone arrival detection
                # --------------------------------------------------

                if drone.zone is not None:

                    target = drone.zone.center()

                    dx = drone.position[0] - target[0]
                    dy = drone.position[1] - target[1]

                    distance_to_zone = (
                        dx ** 2 +
                        dy ** 2
                    ) ** 0.5

                    # Drone is considered to have reached
                    # the zone when within 30 units
                    zone_reached = distance_to_zone <= 30

                    previous_zone_reached = (
                        self.previous_zone_state.get(
                            drone.drone_id,
                            False
                        )
                    )

                    # Count only False -> True transitions
                    if zone_reached and not previous_zone_reached:
                        self.zone_arrival_events += 1

                    self.previous_zone_state[
                        drone.drone_id
                    ] = zone_reached

                else:

                    # No assigned zone
                    self.previous_zone_state[
                        drone.drone_id
                    ] = False

        # --------------------------------------------------
        # Drone-to-drone collision detection
        # --------------------------------------------------

        for i in range(len(swarm.drones)):

            for j in range(i + 1, len(swarm.drones)):

                drone_a = swarm.drones[i]
                drone_b = swarm.drones[j]

                dx = (
                    drone_a.position[0] -
                    drone_b.position[0]
                )

                dy = (
                    drone_a.position[1] -
                    drone_b.position[1]
                )

                distance = (
                    dx ** 2 +
                    dy ** 2
                ) ** 0.5

                collision_distance = (
                    drone_a.radius +
                    drone_b.radius
                )

                if distance < collision_distance:
                    self.drone_collision_events += 1

    def save_csv(self, filename=None):

        if not self.records:
            return

        if filename is None:
            filename = f"telemetry_{self.run_id}.csv"

        fieldnames = self.records[0].keys()

        with open(
            filename,
            "w",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()
            writer.writerows(self.records)

    def average_speed(self):

        if not self.records:
            return 0.0

        total_speed = 0.0

        for record in self.records:
            total_speed += record["speed"]

        return total_speed / len(self.records)

    def minimum_inter_drone_distance(self):

        if not self.records:
            return 0.0

        minimum_distance = float("inf")

        times = {}

        for record in self.records:

            record_time = record["time"]

            if record_time not in times:
                times[record_time] = []

            times[record_time].append(record)

        for records in times.values():

            for i in range(len(records)):

                for j in range(i + 1, len(records)):

                    dx = (
                        records[i]["x"] -
                        records[j]["x"]
                    )

                    dy = (
                        records[i]["y"] -
                        records[j]["y"]
                    )

                    distance = (
                        dx ** 2 +
                        dy ** 2
                    ) ** 0.5

                    if distance < minimum_distance:
                        minimum_distance = distance

        return minimum_distance

    def average_swarm_spread(self):

        if not self.records:
            return 0.0

        times = {}

        for record in self.records:

            record_time = record["time"]

            if record_time not in times:
                times[record_time] = []

            times[record_time].append(record)

        total_spread = 0.0
        snapshot_count = 0

        for records in times.values():

            if not records:
                continue

            center_x = sum(
                record["x"]
                for record in records
            ) / len(records)

            center_y = sum(
                record["y"]
                for record in records
            ) / len(records)

            spread = 0.0

            for record in records:

                dx = record["x"] - center_x
                dy = record["y"] - center_y

                distance = (
                    dx ** 2 +
                    dy ** 2
                ) ** 0.5

                spread += distance

            spread /= len(records)

            total_spread += spread
            snapshot_count += 1

        if snapshot_count == 0:
            return 0.0

        return total_spread / snapshot_count

    def total_distance_travelled(self):

        if not self.records:
            return 0.0

        total_distance = 0.0

        drone_records = {}

        for record in self.records:

            drone_id = record["drone_id"]

            if drone_id not in drone_records:
                drone_records[drone_id] = []

            drone_records[drone_id].append(record)

        for records in drone_records.values():

            for i in range(1, len(records)):

                previous = records[i - 1]
                current = records[i]

                dx = (
                    current["x"] -
                    previous["x"]
                )

                dy = (
                    current["y"] -
                    previous["y"]
                )

                distance = (
                    dx ** 2 +
                    dy ** 2
                ) ** 0.5

                total_distance += distance

        return total_distance

    def summary(self):

        return {
            "run_id": self.run_id,
            "experiment": self.experiment_name,

            "average_speed": (
                self.average_speed()
            ),

            "minimum_inter_drone_distance": (
                self.minimum_inter_drone_distance()
            ),

            "average_swarm_spread": (
                self.average_swarm_spread()
            ),

            "total_distance_travelled": (
                self.total_distance_travelled()
            ),

            "obstacle_avoidance_events": (
                self.obstacle_avoidance_events
            ),

            "drone_collision_events": (
                self.drone_collision_events
            ),

            "obstacle_collision_events": (
                self.obstacle_collision_events
            ),

            "zone_arrival_events": (
                self.zone_arrival_events
            )
        }