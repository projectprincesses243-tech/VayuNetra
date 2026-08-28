class IntegrationBridge:

    def __init__(self, swarm):

        self.swarm = swarm

    def get_drone(
        self,
        drone_id
    ):

        for drone in self.swarm.drones:

            if drone.drone_id == drone_id:
                return drone

        return None

    def get_drone_state(
        self,
        drone_id
    ):

        drone = self.get_drone(
            drone_id
        )

        if drone is None:
            return None

        return {
            "drone_id": drone.drone_id,

            "position": {
                "x": drone.position[0],
                "y": drone.position[1]
            },

            "velocity": {
                "vx": drone.velocity[0],
                "vy": drone.velocity[1]
            },

            "heading": drone.heading,

            "battery": drone.battery,

            "state": drone.state,

            "zone": (
                drone.zone.zone_id
                if drone.zone is not None
                else None
            ),

            "task": drone.current_task
        }

    def get_swarm_state(self):

        return [
            self.get_drone_state(
                drone.drone_id
            )
            for drone in self.swarm.drones
        ]

    def assign_mission(
        self,
        drone_id,
        zone
    ):

        drone = self.get_drone(
            drone_id
        )

        if drone is None:
            return False

        self.swarm.mission_manager.assign_zone(
            drone,
            zone
        )

        return True

    def get_mission_summary(self):

        return (
            self.swarm
            .mission_manager
            .summary()
        )