"""Drone state machine. Every state change in the system goes through here."""

from core.bus import BUS


# What each state is allowed to become. Anything not listed is impossible.
VALID_TRANSITIONS = {
    "SEARCHING": {"ENROUTE", "RETURNING", "DEAD"},
    "ENROUTE":   {"RESCUING", "SEARCHING", "RETURNING", "DEAD"},
    "RESCUING":  {"SEARCHING", "RETURNING", "DEAD"},
    "RETURNING": {"SEARCHING", "DEAD"},
    "DEAD":      set(),          # nothing comes back from here
}


class MissionFSM:
    def __init__(self, drones):
        self.drones = drones

    def transition(self, drone, new_state, reason=""):
        old = drone.state
        if new_state not in VALID_TRANSITIONS.get(old, set()):
            print(f"  [fsm] blocked {old} -> {new_state} on drone {drone.drone_id}")
            return False

        drone.state = new_state
        BUS.publish("STATE_CHANGED", {
            "drone_id": drone.drone_id,
            "from": old,
            "to": new_state,
            "reason": reason,
        })
        return True

    def kill(self, drone_id, reason="manual"):
        """
        Kill a drone mid-mission. Returns the task it was holding, if any,
        so the auction can re-open it. This is demo beat 4.
        """
        drone = next((d for d in self.drones if d.drone_id == drone_id), None)
        if drone is None or drone.state == "DEAD":
            return None

        released = getattr(drone, "assigned_task", None)
        drone.alive = False
        drone.state = "DEAD"
        drone.assigned_task = None
        drone.velocity = [0.0, 0.0]

        BUS.publish("DRONE_DIED", {"drone_id": drone_id,
                                   "released_task": released,
                                   "reason": reason})
        return released

    def check_battery(self, drone, threshold=20.0):
        if drone.battery < threshold and drone.state not in ("RETURNING", "DEAD"):
            BUS.publish("DRONE_LOW_BATTERY", {"drone_id": drone.drone_id,
                                              "battery": drone.battery})
            return self.transition(drone, "RETURNING", "low battery")
        return False