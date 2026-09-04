"""
Translates between Eashanvi's Drone objects and Vaishnavi's Localizer dicts.

Neither of their modules is modified. All translation happens here, so if
either of them changes a name, this is the only file that needs fixing.

Drift now comes from Vaishnavi's real DeadReckoner class rather than a
temporary shim. Her model is bias-plus-random-walk, correctly structured -
we tune the magnitude here (bias/walk_std) so the drift stays visible on
a projector, without touching her actual implementation.
"""

import numpy as np

from core.bus import BUS
from localize.localizer import Localizer
from localize.dead_reckoning import DeadReckoner


class LocalizationBridge:
    MAX_UNCERTAINTY = 60.0      # metres - keeps the dashboard circle sane

    def __init__(self, drones, anchors, ranging_on=True,
                 bias_std=0.15, walk_std=0.75,
                 alpha=0.10, seed=42):
        self.drones = drones
        self.rng = np.random.default_rng(seed)

        # Vaishnavi's get_ranges expects plain coordinates, not dicts.
        # Accept either format and normalise here.
        self.anchors = np.array(
            [a["position"] if isinstance(a, dict) else a for a in anchors],
            dtype=float,
        )

        self.localizers = {}
        self.reckoners = {}

        for d in drones:
            d.belief_pos = list(d.position)      # new field on her object
            d.uncertainty = 0.0
            self.localizers[d.drone_id] = Localizer(alpha=alpha, ranging_on=ranging_on)

            # One DeadReckoner per drone, each with its own random seed so
            # every drone drifts differently - same as a real IMU, where
            # each physical sensor has its own fixed error.
            self.reckoners[d.drone_id] = DeadReckoner(
                initial_position=d.position,
                bias=bias_std,
                random_walk_std=walk_std,
                rng=np.random.default_rng(seed + d.drone_id),
            )

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

        # Real dead reckoning - her class, not a manual injection.
        dr_pos = self.reckoners[drone.drone_id].update(velocity=drone.velocity)
        view["dead_reckoning_position"] = np.asarray(dr_pos, dtype=float)

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