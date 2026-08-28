class MissionManager:

    def __init__(self, drones):
        self.drones = drones
        self.missions = []

    def assign_zone(self, drone, zone):

        drone.zone = zone
        drone.state = "ACTIVE"
        drone.current_task = "SURVEILLANCE"

        mission = {
            "drone_id": drone.drone_id,
            "zone_id": zone.zone_id,
            "task": "SURVEILLANCE",
            "status": "ACTIVE"
        }

        self.missions.append(mission)

    def update(self):

        for mission in self.missions:

            if mission["status"] != "ACTIVE":
                continue

            drone = self._find_drone(
                mission["drone_id"]
            )

            if drone is None:
                continue

            if drone.state == "COMPLETED":
                mission["status"] = "COMPLETED"

    def _find_drone(self, drone_id):

        for drone in self.drones:

            if drone.drone_id == drone_id:
                return drone

        return None

    def summary(self):

        return self.missions