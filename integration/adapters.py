"""
Translates between Eashanvi's Drone objects and Vaishnavi's Localizer dicts.

Neither of their modules is modified. All translation happens here, so if
either of them changes a name, this is the only file that needs fixing.
"""

import numpy as np

from core.bus import BUS
from localize.localizer import Localizer


class LocalizationBridge:
    """
    Gives every Drone object a belief_pos and keeps it updated.

    drift_shim: temporary. Vaishnavi's DeadReckoner currently has no error
    model, so belief would track truth perfectly and the ghost would never
    separate. We inject IMU-style error through her own supported
    'dead_reckoning_position' hook. Set to False once her fix lands.
    """

    MAX_UNCERTAINTY = 60.0      # metres - keeps the dashboard circle sane

    def __init__(self, drones, anchors, ranging_on=True,
                 drift_shim=True, bias_std=0.15, walk_std=0.75,
                 alpha=0.10, seed=42):
        self.drones = drones
        self.drift_shim = drift_shim
        self.rng = np.random.default_rng(seed)

        # Vaishnavi's get_ranges expects plain coordinates, not dicts.
        # Accept either format and normalise here.
        self.anchors = np.array(
            [a["position"] if isinstance(a, dict) else a for a in anchors],
            dtype=float,
        )

        self.localizers = {}
        self.dr_positions = {}
        self.biases = {}

        for d in drones:
            d.belief_pos = list(d.position)      # new field on her object
            d.uncertainty = 0.0
            self.localizers[d.drone_id] = Localizer(alpha=alpha, ranging_on=ranging_on)
            self.dr_positions[d.drone_id] = np.array(d.position, dtype=float)
            self.biases[d.drone_id] = self.rng.normal(0, bias_std, size=2)

        self.walk_std = walk_std

    def set_ranging(self, on):
        """The R key in the demo flips this."""
        for loc in self.localizers.values():
            loc.ranging_on = on

    def _as_dict(self, drone):
        """Object -> dict, in the shape Vaishnavi's Localizer expects."""
        view = {
            "id":          drone.drone_id,
            "position":    list(drone.position),
            "velocity":    list(drone.velocity),
            "belief_pos":  list(drone.belief_pos),
            "uncertainty": drone.uncertainty,
        }

        if self.drift_shim:
            dr = self.dr_positions[drone.drone_id]
            noise = self.biases[drone.drone_id] + self.rng.normal(0, self.walk_std, size=2)
            dr = dr + np.array(drone.velocity, dtype=float) + noise
            self.dr_positions[drone.drone_id] = dr
            view["dead_reckoning_position"] = dr.copy()

        return view

    def update(self):
        """Run localization for every drone. Call once per simulation tick."""
        views = [self._as_dict(d) for d in self.drones]

        for drone, view in zip(self.drones, views):
            self.localizers[drone.drone_id].update(view, views, self.anchors)
            drone.belief_pos = list(np.asarray(view["belief_pos"], dtype=float))

            # Cap uncertainty. Without this it grows without bound and the
            # dashboard circle eventually covers the whole map.
            drone.uncertainty = min(
                float(view.get("uncertainty", 0.0)),
                self.MAX_UNCERTAINTY,
            )

    def error(self, drone):
        """True position error in metres. Analytics only - drones never see this."""
        return float(np.linalg.norm(
            np.array(drone.position, dtype=float) -
            np.array(drone.belief_pos, dtype=float)))

    def mean_error(self):
        alive = [d for d in self.drones if getattr(d, "alive", True)]
        if not alive:
            return 0.0
        return float(np.mean([self.error(d) for d in alive]))