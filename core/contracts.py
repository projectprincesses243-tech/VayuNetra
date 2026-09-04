"""
The shapes every VayuNetra module agrees on.

Changing anything here breaks other people's code.
Tell the team in the group before you edit this file.
"""


def make_drone(drone_id, x, y):
    """
    Create one drone in the standard shape.

    position   = GROUND TRUTH. Where the drone actually is.
                 The simulation knows this. The drone does NOT.
                 Only world/ and localize/ranging may read it.

    belief_pos = Where the drone THINKS it is.
                 This is what navigation and bidding must use.
                 In a GPS-denied environment this is all a real drone has.
    """
    return {
        "id":            drone_id,
        "position":      [float(x), float(y)],
        "belief_pos":    [float(x), float(y)],
        "velocity":      [0.0, 0.0],
        "battery":       100.0,
        "state":         "SEARCHING",
        "assigned_task": None,
        "uncertainty":   0.0,
        "alive":         True,
    }


def make_task(task_id, x, y, confidence=1.0):
    """A survivor that needs a drone sent to it."""
    return {
        "id":         task_id,
        "location":   [float(x), float(y)],
        "confidence": confidence,
        "status":     "OPEN",        # OPEN -> ASSIGNED -> DONE
        "assignee":   None,
    }


# Drone states. A drone is always in exactly one of these.
DRONE_STATES = ["SEARCHING", "ENROUTE", "RESCUING", "RETURNING", "DEAD"]

# Every event name used in the system. Publishing a name not on this
# list is almost always a typo, so keep it as the single source of truth.
EVENTS = [
    "TICK",
    "MISSION_STARTED",
    "SURVIVOR_DETECTED",
    "TASK_CREATED",
    "CFP_ISSUED",
    "BID_PLACED",
    "TASK_AWARDED",
    "TASK_COMPLETED",
    "STATE_CHANGED",
    "DRONE_LOW_BATTERY",
    "DRONE_DIED",
    "MISSION_COMPLETE",
]