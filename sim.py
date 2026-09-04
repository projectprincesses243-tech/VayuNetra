"""
VayuNetra integrated simulation.

This module keeps the existing Digital Twin simulation and adds the
mission/deployment layer used by the Dashboard and Live Map.

Existing simulation:
    Drone movement
    -> perception
    -> survivor detection
    -> task creation
    -> auction/bidding
    -> rescue

New deployment layer:
    Admin Base
    -> incident location
    -> deployment feasibility
    -> direct deployment OR Mobile Zone
    -> reconnaissance
    -> Forward Base
    -> main swarm deployment

Run through:
    python -m server.app
"""

import sys
import math
import random
import argparse
import requests

sys.path.insert(0, ".")

from swarm.drone import Drone
from core.bus import BUS
from core.contracts import make_task
from mission.fsm import MissionFSM
from mission.auction import ContractNet
from integration.adapters import LocalizationBridge
from integration.perception_adapter import PerceptionAdapter


# ============================================================
# EXISTING DIGITAL TWIN CONFIGURATION
# ============================================================

ANCHORS = [
    [0.0, 0.0],
    [500.0, 0.0],
    [250.0, 500.0],
    [0.0, 500.0],
]

SIZE = 500.0
CELL = 50.0
DETECT_RADIUS = 40.0
RESCUE_RADIUS = 20.0


# ============================================================
# NEW DEPLOYMENT CONFIGURATION
# ============================================================

# Fixed administrative command base.
# This is persistent and does not need to be entered for every mission.
ADMIN_BASE = {
    "name": "New Horizon College of Engineering",
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India",
    "latitude": 13.0358,
    "longitude": 77.5647,
}

# Simulation assumption requested for the Mobile Zone.
MOBILE_ZONE_SPEED_KMPH = 45.0

# Demo acceleration: the UI still reports the physical speed as 45 km/h,
# while the Digital Twin advances simulated travel time faster so a judge
# can observe the complete workflow during a live demo.
MOBILE_ZONE_TIME_SCALE = 20.0

# Example drone endurance assumption.
# This is deliberately configurable rather than tied to a particular
# commercial drone model.
DRONE_MAX_ENDURANCE_MIN = 50.0

# Reserve kept for return/emergency handling.
DRONE_RESERVE_MIN = 15.0

# Approximate usable flight time.
DRONE_USABLE_FLIGHT_MIN = (
    DRONE_MAX_ENDURANCE_MIN - DRONE_RESERVE_MIN
)

# Assumed cruise speed for feasibility calculations.
# This is a simulation parameter and can later be replaced by
# actual platform-specific values.
DRONE_SPEED_KMPH = 45.0

# Initial drones are launched only when the Mobile Zone reaches
# this direct-fleet operating range from the incident.
# Initial assessment team. These IDs are reserved for assessment and are
# never reused as main-swarm allocation while the assessment is active.
INITIAL_ASSESSMENT_DRONE_COUNT = 4
INITIAL_ASSESSMENT_DRONE_IDS = [0, 1, 2, 3]

# Assessment time is part of the simulated mission envelope. It is not a
# geographic threshold. The resulting operational radius is calculated from
# endurance, reserve, speed and this assessment allowance.
INITIAL_ASSESSMENT_TIME_MIN = 8.0

# The disaster footprint is generated per simulation/mission. No fixed km
# radius is imposed; the displayed radius/area are outputs of the scenario.
DISASTER_RADIUS_DEG_MIN = 0.035
DISASTER_RADIUS_DEG_MAX = 0.105


class Mission:

    def __init__(
        self,
        n_drones=128,
        n_survivors=5,
        seed=42,
        ranging_on=True,
    ):
        random.seed(seed)

        # ====================================================
        # EXISTING DRONE SIMULATION
        # ====================================================

        self.drones = []

        for i in range(n_drones):
            d = Drone(
                drone_id=i,
                position=(
                    random.uniform(50, 450),
                    random.uniform(50, 450),
                ),
            )

            d.belief_pos = list(d.position)
            d.velocity = [0.0, 0.0]
            d.alive = True
            d.state = "STANDBY"
            d.assigned_task = None
            d.uncertainty = 0.0
            d.search_target = None
            d.gps_denied = False

            self.drones.append(d)

        # ====================================================
        # EXISTING SURVIVOR SIMULATION
        # ====================================================

        self.survivors = [
            {
                "id": i,
                "pos": [
                    random.uniform(50, 450),
                    random.uniform(50, 450),
                ],
                "found": False,
                "rescued": False,
            }
            for i in range(n_survivors)
        ]

        # ====================================================
        # EXISTING SYSTEM COMPONENTS
        # ====================================================

        self.bridge = LocalizationBridge(
            self.drones,
            ANCHORS,
            ranging_on=ranging_on,
        )

        self.fsm = MissionFSM(self.drones)

        self.net = ContractNet(
            settle_ticks=4
        )

        self.perception = PerceptionAdapter(
            use_real=False,
            seed=seed,
        )

        self.tasks = {}
        self.complete = False

        # ====================================================
        # NEW MISSION CONFIGURATION
        # ====================================================

        self.mission_config = {
            "id": None,
            "name": None,

            # PLANNING / REAL / SIMULATION
            "mode": "SIMULATION",

            # User supplied incident location.
            # This starts empty because the frontend will provide it.
            "incident_location": None,

            # Fixed command centre.
            "admin_base": dict(ADMIN_BASE),

            "status": "PLANNING",
        }

        # ====================================================
        # NEW DEPLOYMENT STATE
        # ====================================================

        self.deployment = {
            "status": "WAITING_FOR_LOCATION",

            "fleet": {
                "registered_count": n_drones,
                "available_count": max(
                    0,
                    n_drones - len(
                        INITIAL_ASSESSMENT_DRONE_IDS[
                            :min(INITIAL_ASSESSMENT_DRONE_COUNT, n_drones)
                        ]
                    ),
                ),
                "initial_assessment_drone_ids": list(INITIAL_ASSESSMENT_DRONE_IDS[:min(INITIAL_ASSESSMENT_DRONE_COUNT, n_drones)]),
                "main_swarm_drone_ids": [],
                "reserve_drone_ids": [],
                "disabled_drone_ids": [],
            },

            # Direct-fleet decision.
            "direct_feasible": None,
            "distance_km": None,
            "drone_endurance_min": DRONE_MAX_ENDURANCE_MIN,
            "reserve_min": DRONE_RESERVE_MIN,
            "usable_flight_time_min": DRONE_USABLE_FLIGHT_MIN,
            "drone_speed_kmph": DRONE_SPEED_KMPH,
            "maximum_operational_range_km": round(
                DRONE_USABLE_FLIGHT_MIN * DRONE_SPEED_KMPH / 60.0, 2
            ),
            "required_flight_time_min": None,
            "decision_reason": None,
            "assessment_time_min": INITIAL_ASSESSMENT_TIME_MIN,

            "estimated_drone_flight_min": None,
            "estimated_mobile_zone_travel_min": None,

            "mobile_zone": {
                "status": "STANDBY",
                "speed_kmph": MOBILE_ZONE_SPEED_KMPH,
                "position": None,
                "distance_from_admin_km": None,
                "distance_to_incident_km": None,
                "progress_percent": 0.0,
                "target_position": None,
                "started": False,
                "time_scale": MOBILE_ZONE_TIME_SCALE,
            },

            "recon": {
                "status": "NOT_STARTED",
                "launched": False,
                "launch_point": None,
                "assessment": None,
                "hazards": [],
                "survivors_detected": 0,
                "communication_quality": None,
                "accessibility": None,
                "drones_deployed": [],
                "imagery_status": "NOT_REQUESTED",
                "imagery_source": None,
                "imagery_timestamp": None,
                "imagery_source_url": None,
                "supporting_information_status": "NOT_CHECKED",
                "supporting_information_note": None,
                "perception_status": "NOT_STARTED",
                "disaster_region": None,
                "priority_zones": [],
                "priority_status": "NOT_STARTED",
                "safety_status": "NOT_STARTED",
                "safety_score": None,
            },

            "forward_base": {
                "status": "NOT_SELECTED",
                "position": None,
                "source": None,
                "confidence": None,
                "recon_required": True,
                "safety_score": None,
                "reason": None,
            },

            "main_swarm": {
                "status": "NOT_DEPLOYED",
                "launch_point": None,
                "deployed_count": 0,
                "deployment_method": None,
                "manual_override_available": False,
            },
        }

        # ====================================================
        # EXISTING DISTRIBUTED SEARCH STATE
        # ====================================================

        n_cells = int(SIZE // CELL)

        self.unsearched = {
            (cx, cy)
            for cx in range(n_cells)
            for cy in range(n_cells)
        }

        self.total_cells = len(self.unsearched)

        self.claimed = {}

        # ====================================================
        # EVENT SUBSCRIPTION
        # ====================================================

        BUS.subscribe(
            "SURVIVOR_DETECTED",
            self.on_detection,
        )

    # ========================================================
    # MISSION CONFIGURATION API
    # ========================================================

    def configure_mission(
        self,
        name=None,
        latitude=None,
        longitude=None,
        location_name=None,
        mode="SIMULATION",
    ):
        """
        Configure the mission from the frontend.

        The frontend can eventually provide geocoded coordinates.
        No city/location list is hardcoded here.
        """
        # Reset the simulation state for every new mission.
        # This prevents tasks, survivors, auctions, metrics and
        # Digital Twin state from leaking from the previous mission.
        self.__init__(
            n_drones=128,
            n_survivors=5,
            seed=42,
            ranging_on=True,
        )
        self.mission_config["name"] = name

        mode = str(mode).upper()

        if mode not in {"REAL", "SIMULATION"}:
            mode = "SIMULATION"

        self.mission_config["mode"] = mode

        if latitude is None or longitude is None:
            self.mission_config["incident_location"] = None

            self.deployment["status"] = "WAITING_FOR_LOCATION"

            return {
                "configured": False,
                "reason": "incident location required",
            }

        self.mission_config["incident_location"] = {
            "name": location_name,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "precision": "coordinates",
            "source": "frontend",
        }

        self.mission_config["status"] = "PLANNING"

        self._calculate_deployment_feasibility()

        return {
            "configured": True,
            "mode": mode,
            "location": self.mission_config["incident_location"],
            "deployment": self.deployment,
        }

    # ========================================================
    # LOCATION / DISTANCE CALCULATION
    # ========================================================

    @staticmethod
    def haversine_km(
        lat1,
        lon1,
        lat2,
        lon2,
    ):
        
        """
        Calculate great-circle distance between two coordinates.
        """

        earth_radius_km = 6371.0

        p1 = math.radians(lat1)
        p2 = math.radians(lat2)

        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)

        a = (
            math.sin(dp / 2) ** 2
            + math.cos(p1)
            * math.cos(p2)
            * math.sin(dl / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )

        return earth_radius_km * c

    def _incident_coordinates(self):
        location = self.mission_config.get(
            "incident_location"
        )

        if not location:
            return None

        return (
            location["latitude"],
            location["longitude"],
        )

    def _calculate_deployment_feasibility(self):
        """
        First-stage direct fleet feasibility.

        If direct deployment is not feasible, the Mobile Zone becomes
        required. Initial assessment drones are NOT launched here.
        They launch later, only when the Mobile Zone reaches the
        configured direct-fleet operating range.
        """
        incident = self._incident_coordinates()

        if incident is None:
            self.deployment["status"] = "WAITING_FOR_LOCATION"
            return

        admin = self.mission_config["admin_base"]

        distance = self.haversine_km(
            admin["latitude"],
            admin["longitude"],
            incident[0],
            incident[1],
        )

        self.deployment["distance_km"] = round(distance, 2)

        one_way_minutes = (
            distance / DRONE_SPEED_KMPH * 60.0
            if DRONE_SPEED_KMPH > 0
            else float("inf")
        )

        # Direct deployment must leave time for outbound travel, initial
        # search/assessment and return, while preserving the reserve.
        required_round_trip_min = (2.0 * one_way_minutes) + INITIAL_ASSESSMENT_TIME_MIN
        practical_one_way_range_km = max(
            0.0,
            ((DRONE_USABLE_FLIGHT_MIN - INITIAL_ASSESSMENT_TIME_MIN) / 2.0)
            * DRONE_SPEED_KMPH / 60.0,
        )

        self.deployment["estimated_drone_flight_min"] = round(
            one_way_minutes, 1
        )
        self.deployment["required_flight_time_min"] = round(
            required_round_trip_min, 1
        )
        self.deployment["maximum_operational_range_km"] = round(
            practical_one_way_range_km, 2
        )
        self.deployment["assessment_time_min"] = INITIAL_ASSESSMENT_TIME_MIN

        direct_feasible = required_round_trip_min <= DRONE_USABLE_FLIGHT_MIN
        self.deployment["direct_feasible"] = direct_feasible

        if direct_feasible:
            self.deployment["status"] = "DIRECT_DEPLOYMENT_FEASIBLE"
            self.deployment["decision_reason"] = (
                "Required one-way flight time is within the "
                "usable drone flight envelope."
            )
            self.deployment["mobile_zone"]["status"] = "NOT_REQUIRED"
            self.deployment["mobile_zone"]["position"] = {
                "latitude": admin["latitude"],
                "longitude": admin["longitude"],
            }
            # Direct deployment still starts with the four-drone
            # initial assessment. The complete swarm is NOT launched yet.
            self.deployment["recon"]["status"] = "WAITING_FOR_DIRECT_LAUNCH"
            self.deployment["recon"]["launch_point"] = {
                "latitude": admin["latitude"],
                "longitude": admin["longitude"],
            }
            self.deployment["forward_base"]["status"] = "NOT_REQUIRED"
            self.deployment["main_swarm"]["manual_override_available"] = False
        else:
            self.deployment["status"] = "MOBILE_ZONE_REQUIRED"
            self.deployment["decision_reason"] = (
                "Required flight time exceeds the usable drone flight "
                "time after reserve; Mobile Zone deployment is required."
            )
            self._prepare_mobile_zone()

    # ========================================================
    # MOBILE ZONE
    # ========================================================

    def _prepare_mobile_zone(self):
        """
        Prepare the Mobile Zone at the Admin Base.

        IMPORTANT:
        The Mobile Zone moves continuously toward the incident.
        Initial assessment drones are launched only after the Mobile
        Zone reaches the configured direct-fleet operating range.
        """
        incident = self._incident_coordinates()
        if incident is None:
            return

        admin = self.mission_config["admin_base"]

        mobile = self.deployment["mobile_zone"]
        mobile["status"] = "STANDBY"
        mobile["speed_kmph"] = MOBILE_ZONE_SPEED_KMPH
        mobile["started"] = False
        mobile["time_scale"] = MOBILE_ZONE_TIME_SCALE
        mobile["position"] = {
            "latitude": admin["latitude"],
            "longitude": admin["longitude"],
        }
        mobile["target_position"] = {
            "latitude": incident[0],
            "longitude": incident[1],
        }
        mobile["distance_from_admin_km"] = 0.0
        mobile["distance_to_incident_km"] = round(
            self.deployment["distance_km"], 2
        )
        mobile["progress_percent"] = 0.0

        # Travel time until the Mobile Zone reaches the direct-fleet
        # operating range, not until it reaches the incident.
        operational_range_km = self.deployment.get(
            "maximum_operational_range_km", 0.0
        )
        launch_travel_km = max(
            0.0,
            self.deployment["distance_km"] - operational_range_km,
        )

        self.deployment["estimated_mobile_zone_travel_min"] = round(
            launch_travel_km / MOBILE_ZONE_SPEED_KMPH * 60.0,
            1,
        )

        self.deployment["recon"]["status"] = "WAITING_FOR_RANGE"
        self.deployment["recon"]["launch_point"] = None
        self.deployment["recon"]["launched"] = False

    def start_mobile_zone(self):
        """Operator command to start the Mobile Zone from Admin Base."""
        if self.deployment["direct_feasible"]:
            return {
                "started": False,
                "reason": "Direct deployment is feasible; Mobile Zone is not required.",
            }

        mobile = self.deployment["mobile_zone"]

        if mobile.get("status") == "AT_ASSESSMENT_RANGE":
            return {
                "started": False,
                "reason": "Mobile Zone is already inside direct-fleet assessment range.",
                "status": mobile["status"],
            }

        if mobile.get("status") == "MOVING_TO_FORWARD_BASE":
            return {
                "started": False,
                "reason": "Mobile Zone is already moving toward the selected Forward Base.",
                "status": mobile["status"],
            }

        if mobile.get("status") == "AT_FORWARD_BASE":
            return {
                "started": False,
                "reason": "Mobile Zone has already reached the Forward Base.",
                "status": mobile["status"],
            }

        mobile["status"] = "MOVING"
        mobile["started"] = True
        self.deployment["status"] = "MOBILE_ZONE_MOVING"

        return {
            "started": True,
            "status": mobile["status"],
            "speed_kmph": MOBILE_ZONE_SPEED_KMPH,
            "time_scale": MOBILE_ZONE_TIME_SCALE,
            "distance_to_incident_km": mobile.get("distance_to_incident_km"),
            "progress_percent": mobile.get("progress_percent", 0.0),
        }

    # ========================================================
    # RECONNAISSANCE
    # ========================================================

    def _interpolate_position(self, fraction):
        """Interpolate between Admin Base and incident coordinates."""
        incident = self._incident_coordinates()
        if incident is None:
            return None

        admin = self.mission_config["admin_base"]
        f = max(0.0, min(1.0, fraction))

        return {
            "latitude": round(
                admin["latitude"] +
                (incident[0] - admin["latitude"]) * f,
                6,
            ),
            "longitude": round(
                admin["longitude"] +
                (incident[1] - admin["longitude"]) * f,
                6,
            ),
        }

    def _mobile_zone_step(self, dt_seconds=1.0):
        """
        Move the Mobile Zone.

        Phase 1:
            Admin Base -> direct-fleet operational range.
            Reaching this range makes initial drone deployment available to the operator.

        Phase 2:
            Assessment range -> selected Forward Base.
            Reaching the Forward Base automatically deploys the swarm.
        """
        if self.deployment["direct_feasible"]:
            return

        mobile = self.deployment["mobile_zone"]
        status = mobile.get("status")

        if status not in {
            "MOVING",
            "AT_ASSESSMENT_RANGE",
            "MOVING_TO_FORWARD_BASE",
        }:
            return

        movement_km = MOBILE_ZONE_SPEED_KMPH * dt_seconds * MOBILE_ZONE_TIME_SCALE / 3600.0

        if status == "MOVING":
            total_distance = self.deployment["distance_km"]
            current_distance = mobile.get("distance_to_incident_km")

            if total_distance is None or current_distance is None:
                return

            new_distance = max(0.0, current_distance - movement_km)
            travelled = total_distance - new_distance
            fraction = travelled / total_distance if total_distance else 1.0

            mobile["position"] = self._interpolate_position(fraction)
            mobile["distance_from_admin_km"] = round(travelled, 2)
            mobile["distance_to_incident_km"] = round(new_distance, 2)
            mobile["progress_percent"] = round(
                100.0 * travelled / total_distance, 1
            )

            if new_distance <= self.deployment.get("maximum_operational_range_km", 0.0):
                mobile["status"] = "AT_ASSESSMENT_RANGE"
                mobile["started"] = False
                self.deployment["status"] = "INITIAL_ASSESSMENT_READY"
            return

        # Phase 2: travel from assessment point to Forward Base.
        forward = self.deployment["forward_base"]
        target = forward.get("position")

        if not target or not mobile.get("position"):
            return

        current = mobile["position"]
        distance_to_base = self.haversine_km(
            current["latitude"],
            current["longitude"],
            target["latitude"],
            target["longitude"],
        )

        if distance_to_base <= max(movement_km, 0.05):
            mobile["position"] = dict(target)
            mobile["status"] = "AT_FORWARD_BASE"
            mobile["progress_percent"] = 100.0
            mobile["started"] = False
            mobile["distance_to_incident_km"] = round(
                self.haversine_km(
                    target["latitude"],
                    target["longitude"],
                    self._incident_coordinates()[0],
                    self._incident_coordinates()[1],
                ),
                2,
            )
            self._establish_forward_base()
            return

        # Move toward Forward Base by the available movement distance.
        fraction = min(1.0, movement_km / distance_to_base)
        mobile["position"] = {
            "latitude": round(
                current["latitude"]
                + (target["latitude"] - current["latitude"]) * fraction,
                6,
            ),
            "longitude": round(
                current["longitude"]
                + (target["longitude"] - current["longitude"]) * fraction,
                6,
            ),
        }

        mobile["distance_to_incident_km"] = round(
            self.haversine_km(
                mobile["position"]["latitude"],
                mobile["position"]["longitude"],
                self._incident_coordinates()[0],
                self._incident_coordinates()[1],
            ),
            2,
        )

        forward_distance = self.haversine_km(
            self.deployment["forward_base"]["position"]["latitude"],
            self.deployment["forward_base"]["position"]["longitude"],
            self._incident_coordinates()[0],
            self._incident_coordinates()[1],
        )
        total_distance = self.deployment["distance_km"]
        phase_span = max(
            total_distance - forward_distance,
            0.001,
        )
        mobile["progress_percent"] = round(
            100.0
            * (total_distance - mobile["distance_to_incident_km"])
            / phase_span,
            1,
        )

    def _launch_initial_assessment_automatically(self):
        recon = self.deployment["recon"]

        if recon["launched"]:
            return

        recon["launched"] = True
        recon["status"] = "IN_PROGRESS"
        recon["launch_point"] = dict(
            self.deployment["mobile_zone"]["position"]
        )

        preferred_ids = set(
            self.deployment.get("fleet", {}).get(
                "initial_assessment_drone_ids", INITIAL_ASSESSMENT_DRONE_IDS
            )
        )
        recon_drones = [
            d for d in self.drones
            if d.alive and d.drone_id in preferred_ids
        ][:INITIAL_ASSESSMENT_DRONE_COUNT]

        recon["drones_deployed"] = [
            d.drone_id for d in recon_drones
        ]

        for d in recon_drones:
            d.state = "RECON_ASSESSMENT"

        self.deployment["fleet"]["initial_assessment_drone_ids"] = [d.drone_id for d in recon_drones]
        self.deployment["recon"]["travel_progress_percent"] = 0.0
        self.deployment["recon"]["assessment_progress_percent"] = 0.0
        self.deployment["recon"]["started_tick"] = BUS.tick
        self.deployment["recon"]["assessment_complete_tick"] = BUS.tick + max(20, int(INITIAL_ASSESSMENT_TIME_MIN * 6))
        # Assessment completes asynchronously in _mobile_zone_step/step.
        self.deployment["recon"]["status"] = "DRONES_DEPLOYED"

    def _launch_direct_initial_assessment(self):
        """Launch exactly four assessment drones from the Admin Base."""
        recon = self.deployment["recon"]

        if recon.get("launched"):
            return False

        preferred_ids = self.deployment["fleet"].get(
            "initial_assessment_drone_ids",
            INITIAL_ASSESSMENT_DRONE_IDS,
        )

        recon_drones = [
            d for d in self.drones
            if d.alive and d.drone_id in set(preferred_ids)
        ][:INITIAL_ASSESSMENT_DRONE_COUNT]

        if len(recon_drones) < min(
            INITIAL_ASSESSMENT_DRONE_COUNT,
            len(self.drones),
        ):
            return False

        recon["launched"] = True
        recon["status"] = "DRONES_DEPLOYED"
        recon["launch_point"] = {
            "latitude": self.mission_config["admin_base"]["latitude"],
            "longitude": self.mission_config["admin_base"]["longitude"],
        }
        recon["drones_deployed"] = [d.drone_id for d in recon_drones]
        recon["travel_progress_percent"] = 0.0
        recon["assessment_progress_percent"] = 0.0
        recon["started_tick"] = BUS.tick
        recon["assessment_complete_tick"] = (
            BUS.tick + max(20, int(INITIAL_ASSESSMENT_TIME_MIN * 6))
        )

        for d in recon_drones:
            d.state = "RECON_ASSESSMENT"

        return True

    def launch_recon(self):
        """
        Launch the four-drone initial assessment.

        Direct missions launch from Admin Base.
        Mobile-Zone missions launch only after the Mobile Zone reaches
        the dynamically calculated assessment range.
        """
        incident = self._incident_coordinates()

        if incident is None:
            return {
                "launched": False,
                "reason": "incident location required",
            }

        recon = self.deployment["recon"]

        if recon.get("launched"):
            return {
                "launched": False,
                "reason": "initial assessment already launched",
                "status": recon.get("status"),
            }

        if self.deployment.get("direct_feasible"):
            launched = self._launch_direct_initial_assessment()
            return {
                "launched": launched,
                "status": recon.get("status"),
                "launch_point": recon.get("launch_point"),
                "assessment_drone_ids": recon.get("drones_deployed", []),
            }

        mobile = self.deployment["mobile_zone"]

        if mobile.get("distance_to_incident_km") is not None and (
            mobile["distance_to_incident_km"]
            > self.deployment.get("maximum_operational_range_km", 0.0)
        ):
            return {
                "launched": False,
                "reason": (
                    "Mobile Zone has not reached direct-fleet "
                    "operational range yet."
                ),
            }

        self._launch_initial_assessment_automatically()

        return {
            "launched": True,
            "status": recon["status"],
            "launch_point": recon["launch_point"],
            "assessment_drone_ids": recon.get("drones_deployed", []),
        }

    def _run_initial_assessment(self):
        """
        Simulation perception pipeline.

        The generated observations are deliberately structured as
        perception outputs: disaster region, hazards, survivor
        indications and priority zones. In REAL mode, this method is
        the integration point for externally obtained imagery/source
        observations; it must not fabricate real-world evidence.
        """
        recon = self.deployment["recon"]
        mode = self.mission_config["mode"]

        recon["perception_status"] = "PROCESSING"

        if mode == "REAL":
            recon["imagery_status"] = "AWAITING_EXTERNAL_SOURCE"
            recon["imagery_source"] = "MOSDAC LIVE / Bhuvan (external supporting imagery)"
            recon["imagery_timestamp"] = None
            recon["imagery_source_url"] = "https://www.mosdac.gov.in/mosdac-live"
            recon["supporting_information_status"] = "EXTERNAL_SOURCE_REQUIRED"
            recon["supporting_information_note"] = (
                "Real mode requires an obtained external satellite/supporting "
                "image before perception can report disaster evidence. "
                "No real-world detections are fabricated by the simulation."
            )
            recon["perception_status"] = "AWAITING_REAL_INPUT"
            recon["status"] = "AWAITING_REAL_ASSESSMENT"
            recon["assessment"] = (
                "Initial drones are ready for real imagery/perception input."
            )
            return

        # SIMULATION: deterministic-looking but varied assessment.
        rng = random.Random(
            (self.mission_config.get("id") or "SIMULATION") .__hash__()
            if self.mission_config.get("id")
            else 42
        )

        # Disaster region represented as an irregular polygon around
        # the incident. This is map-ready geographic data.
        center_lat, center_lon = self._incident_coordinates()
        radii = [0.030, 0.045, 0.050, 0.035, 0.025, 0.040, 0.055, 0.038]
        points = []
        for i, radius in enumerate(radii):
            angle = 2 * math.pi * i / len(radii)
            jitter = 0.85 + rng.random() * 0.30
            lat = center_lat + math.sin(angle) * radius * jitter
            lon = center_lon + math.cos(angle) * radius * jitter
            points.append({
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
            })

        priority_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        priority_zones = []

        # Partition the complete simulated disaster footprint into four
        # non-overlapping angular sectors. The outer boundary is the
        # irregular disaster polygon above; these sectors provide a
        # presentation-friendly priority zoning layer for the Live Map.
        # Convert a simulation-generated angular footprint into a displayed
        # geographic radius. The radius is generated per mission; it is not
        # a fixed VayuNetra rule.
        mean_deg = sum(
            math.hypot(
                p["latitude"] - center_lat,
                (p["longitude"] - center_lon) * math.cos(math.radians(center_lat)),
            )
            for p in points
        ) / max(len(points), 1)
        radius_deg = max(0.001, mean_deg * (1.15 + rng.random() * 0.55))
        radius_km = radius_deg * 111.32
        km_per_degree_lat = 111.32
        km_per_degree_lon = max(1.0, 111.32 * math.cos(math.radians(center_lat)))

        # Keep at least four zones; a larger simulated footprint may create
        # additional zones so swarm demand can scale with the scenario.
        zone_count = max(4, min(8, 4 + int(radius_km // 6)))
        priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        priority_zones = []
        total_area = math.pi * radius_km * radius_km

        for i in range(zone_count):
            priority = priority_order[min(i, len(priority_order) - 1)]
            start_angle = (2 * math.pi * i / zone_count) - (math.pi / zone_count)
            end_angle = (2 * math.pi * (i + 1) / zone_count) - (math.pi / zone_count)
            zone_points = [{"latitude": round(center_lat, 6), "longitude": round(center_lon, 6)}]
            for j in range(7):
                angle = start_angle + (end_angle - start_angle) * j / 6.0
                radial_km = radius_km * (0.86 + 0.11 * rng.random())
                zone_points.append({
                    "latitude": round(center_lat + math.sin(angle) * radial_km / km_per_degree_lat, 6),
                    "longitude": round(center_lon + math.cos(angle) * radial_km / km_per_degree_lon, 6),
                })
            priority_zones.append({
                "id": f"Z-{i + 1:02d}",
                "priority": priority,
                "score": round(max(0.35, 0.96 - i * (0.48 / max(zone_count - 1, 1))), 2),
                "polygon": zone_points,
                "area_km2": round(total_area / zone_count, 2),
                "reason": "Priority derived from simulated hazard, survivor indication, accessibility and coverage demand.",
            })

        # Allocate only the non-assessment fleet. At least one main-swarm
        # drone is assigned to every zone whenever enough drones remain.
        assessment_ids = set(self.deployment["fleet"].get("initial_assessment_drone_ids", []))
        available_main = [d.drone_id for d in self.drones if d.alive and d.drone_id not in assessment_ids]

        # Demand is weighted by priority and area. The resulting required
        # count is scenario-derived and capped by available mission fleet.
        priority_weight = {"CRITICAL": 4.0, "HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}
        demand_scores = [
            max(0.5, z["area_km2"]) * priority_weight.get(z["priority"], 1.0)
            for z in priority_zones
        ]
        # Scale demand from zone count and relative area rather than a fixed
        # kilometer-to-drone rule. Ensure every zone can receive one drone.
        requested_main_count = min(
            len(available_main),
            max(len(priority_zones), int(round(len(priority_zones) * (1.5 + rng.random() * 1.5)))),
        )
        allocation_counts = [0] * len(priority_zones)
        for i in range(min(requested_main_count, len(priority_zones))):
            allocation_counts[i] = 1
        for _ in range(max(0, requested_main_count - len(priority_zones))):
            target = max(
                range(len(priority_zones)),
                key=lambda idx: demand_scores[idx] / (allocation_counts[idx] + 1),
            )
            allocation_counts[target] += 1

        assigned_by_zone = {z["id"]: [] for z in priority_zones}
        cursor = 0
        for zone_index, count in enumerate(allocation_counts):
            zone_id = priority_zones[zone_index]["id"]
            assigned_by_zone[zone_id] = available_main[cursor:cursor + count]
            cursor += count

        for z in priority_zones:
            assigned = assigned_by_zone[z["id"]]
            z["allocated_drone_ids"] = assigned
            z["allocated_drone_count"] = len(assigned)
            z["active_drone_count"] = len(assigned)

        allocated_main_ids = [drone_id for ids in assigned_by_zone.values() for drone_id in ids]
        recon["allocated_drone_ids"] = allocated_main_ids
        recon["allocated_drone_count"] = len(allocated_main_ids)
        recon["required_main_swarm_count"] = requested_main_count
        recon["allocation_status"] = "COMPLETE"

        survivor_count = min(
            len(self.survivors),
            2 + rng.randint(0, 2),
        )

        recon["hazards"] = [
            "Flooded/access-restricted area",
            "Potential structural/environmental hazard",
        ]
        recon["survivors_detected"] = survivor_count
        recon["communication_quality"] = "GOOD"
        recon["accessibility"] = "LIMITED"
        recon["disaster_region"] = {
            "type": "Polygon",
            "polygon": points,
            "estimated": True,
            "source": "simulated_initial_assessment",
            "radius_km": round(radius_km, 2),
            "estimated_area_km2": round(math.pi * radius_km ** 2, 2),
        }
        recon["priority_zones"] = priority_zones
        recon["priority_status"] = "COMPLETE"

        # Safety assessment is deliberately produced at the same time.
        recon["safety_status"] = "COMPLETE"
        safety_score = round(
            0.72 + rng.random() * 0.20,
            2,
        )
        recon["safety_score"] = safety_score

        self._complete_simulated_recon(safety_score)

    def _complete_simulated_recon(self, safety_score):
        recon = self.deployment["recon"]
        recon["perception_status"] = "COMPLETE"
        recon["imagery_status"] = "SIMULATED_INPUT"
        recon["imagery_source"] = "SIMULATED_DISASTER_IMAGERY"
        recon["supporting_information_status"] = "NOT_APPLICABLE"
        recon["assessment"] = (
            "Initial assessment complete: disaster footprint, priority zoning "
            "and Forward Base safety candidates generated."
        )

        # Dynamic Forward Base candidates. The first candidate is deliberately
        # not final: a later safety re-evaluation may select a nearer/better site.
        incident = self._incident_coordinates()
        mobile_position = self.deployment["mobile_zone"]["position"]
        rng = random.Random(f"{self.mission_config.get('id')}-forward")
        candidates = []
        if incident and mobile_position:
            current_to_incident = self.haversine_km(
                mobile_position["latitude"], mobile_position["longitude"],
                incident[0], incident[1]
            )
            candidate_count = 3 + rng.randint(0, 2)
            for i in range(candidate_count):
                # Candidate placement is scenario-generated as a fraction of
                # the remaining route, not a fixed kilometre offset.
                fraction = 0.15 + (0.70 * (i + 1) / (candidate_count + 1))
                jitter = (rng.random() - 0.5) * 0.08
                f = max(0.05, min(0.92, fraction + jitter))
                pos = {
                    "latitude": round(mobile_position["latitude"] + (incident[0] - mobile_position["latitude"]) * f, 6),
                    "longitude": round(mobile_position["longitude"] + (incident[1] - mobile_position["longitude"]) * f, 6),
                }
                safety = round(max(0.0, min(1.0, safety_score + (rng.random() - 0.5) * 0.25)), 2)
                accessibility = round(0.55 + rng.random() * 0.40, 2)
                communication = round(0.60 + rng.random() * 0.35, 2)
                suitability = round(0.45 * safety + 0.30 * accessibility + 0.25 * communication, 2)
                candidates.append({
                    "id": f"FBS-{i + 1:02d}",
                    "position": pos,
                    "safety_score": safety,
                    "accessibility_score": accessibility,
                    "communication_score": communication,
                    "suitability_score": suitability,
                    "distance_to_incident_km": round(self.haversine_km(pos["latitude"], pos["longitude"], incident[0], incident[1]), 2),
                    "status": "SAFE" if safety >= 0.65 else "UNSAFE",
                })
            safe_candidates = [c for c in candidates if c["status"] == "SAFE"]
            safe_candidates.sort(key=lambda c: (-c["suitability_score"], c["distance_to_incident_km"]))
            selected = safe_candidates[0] if safe_candidates else max(candidates, key=lambda c: c["safety_score"])

            # Explicit dynamic re-evaluation: if another safe candidate is
            # nearer and sufficiently suitable, it replaces the first pick.
            reevaluated = min(
                safe_candidates,
                key=lambda c: c["distance_to_incident_km"],
                default=selected,
            )
            if reevaluated["id"] != selected["id"] and reevaluated["suitability_score"] >= selected["suitability_score"] - 0.08:
                previous_id = selected["id"]
                selected = reevaluated
                recon["forward_base_reallocated"] = True
                recon["forward_base_reallocation_reason"] = (
                    f"Re-evaluation replaced {previous_id} with {selected['id']} "
                    "because a nearer safe and sufficiently suitable site was found."
                )
            else:
                recon["forward_base_reallocated"] = False
                recon["forward_base_reallocation_reason"] = "Initial safe candidate remained the best evaluated site."

            self.deployment["forward_base"]["candidates"] = candidates
            self.deployment["forward_base"]["re_evaluation_status"] = "COMPLETE"
            self.deployment["forward_base"]["selected_candidate_id"] = selected["id"]
            self.deployment["forward_base"]["previous_candidate_id"] = None
            self.deployment["forward_base"].update({
                "status": "SELECTED",
                "position": selected["position"],
                "source": "initial_assessment_and_safety_re_evaluation",
                "confidence": selected["suitability_score"],
                "recon_required": False,
                "safety_score": selected["safety_score"],
                "reason": "Final Forward Base selected from dynamically evaluated safe candidates.",
            })
        else:
            self.deployment["forward_base"]["status"] = "NOT_SELECTED"

        if self.deployment.get("direct_feasible"):
            self.deployment["status"] = "DIRECT_ZONING_COMPLETE"
            self.deployment["main_swarm"]["manual_override_available"] = True
            self.deployment["mobile_zone"]["status"] = "NOT_REQUIRED"
        else:
            self.deployment["status"] = "FORWARD_BASE_SELECTED"
            self.deployment["main_swarm"]["manual_override_available"] = True
            self.deployment["mobile_zone"]["status"] = "MOVING_TO_FORWARD_BASE"

    def _establish_forward_base(self):
        mobile = self.deployment["mobile_zone"]
        forward = self.deployment["forward_base"]

        if forward["status"] != "SELECTED":
            return

        mobile["status"] = "AT_FORWARD_BASE"
        mobile["position"] = dict(forward["position"])

        incident = self._incident_coordinates()
        if incident:
            mobile["distance_to_incident_km"] = round(
                self.haversine_km(
                    mobile["position"]["latitude"],
                    mobile["position"]["longitude"],
                    incident[0],
                    incident[1],
                ),
                2,
            )

        self.deployment["status"] = "FORWARD_BASE_ESTABLISHED"

        # Automatic swarm deployment once Forward Base is physically reached.
        self.deploy_main_swarm(deployment_method="AUTOMATIC")

    def complete_recon(
        self,
        candidate_viable=True,
        hazards=None,
        communication_quality="UNKNOWN",
        accessibility="UNKNOWN",
    ):
        """
        Compatibility endpoint for externally supplied recon results.

        Priority and safety can later be populated from the perception
        model. This method never declares a site safe without assessment.
        """
        recon = self.deployment["recon"]

        if not recon["launched"]:
            return {
                "completed": False,
                "reason": "recon not launched",
            }

        if hazards is None:
            hazards = []

        recon["status"] = "COMPLETED"
        recon["hazards"] = list(hazards)
        recon["communication_quality"] = communication_quality
        recon["accessibility"] = accessibility
        recon["candidate_viable"] = bool(candidate_viable)
        recon["priority_status"] = (
            recon["priority_status"]
            if recon["priority_status"] != "NOT_STARTED"
            else "PENDING"
        )
        recon["safety_status"] = "COMPLETE"

        if candidate_viable:
            if self.mission_config["mode"] == "REAL":
                recon["perception_status"] = "AWAITING_REAL_INPUT"
                recon["imagery_status"] = "AWAITING_EXTERNAL_SOURCE"
                recon["supporting_information_status"] = "NOT_CHECKED"
                recon["assessment"] = (
                    "Real-mode recon result received, but no real imagery "
                    "or perception evidence is fabricated by the simulation."
                )
                return {
                    "completed": True,
                    "candidate_viable": True,
                    "assessment": recon["assessment"],
                }

            self._complete_simulated_recon(0.80)
        else:
            recon["assessment"] = (
                "Forward Base site rejected; Mobile Zone must reposition."
            )
            self.deployment["forward_base"] = {
                "status": "NOT_SELECTED",
                "position": None,
                "source": None,
                "confidence": None,
                "recon_required": True,
                "safety_score": None,
                "reason": "Site rejected during safety assessment.",
            }
            self.deployment["status"] = "REPOSITION_REQUIRED"

        return {
            "completed": True,
            "candidate_viable": bool(candidate_viable),
            "assessment": recon["assessment"],
        }

    # ========================================================
    # MAIN SWARM DEPLOYMENT
    # ========================================================

    def deploy_main_swarm(self, deployment_method="MANUAL"):
        """
        Deploy the main swarm.

        Normal operation:
            - Direct mission: automatically deploys after four-drone
              assessment/zoning completes, from the Admin Base.
            - Non-direct mission: automatically deploys when the Mobile
              Zone reaches the selected Forward Base.

        Manual operator override remains available for a selected
        Forward Base in non-direct missions.
        """
        if self.deployment["main_swarm"]["status"] == "DEPLOYED":
            return {
                "deployed": True,
                "reason": "main swarm already deployed",
                "mode": self.deployment["main_swarm"]["deployment_method"],
            }

        deployment_method = str(deployment_method).upper()

        if self.deployment["direct_feasible"]:
            # Direct deployments originate at the fixed Admin Base.
            # AUTOMATIC is the normal path after assessment/zoning.
            if deployment_method not in {"AUTOMATIC", "MANUAL"}:
                deployment_method = "AUTOMATIC"
            launch_point = {
                "latitude": self.mission_config["admin_base"]["latitude"],
                "longitude": self.mission_config["admin_base"]["longitude"],
            }
            deployment_status = "DIRECT"

            recon = self.deployment["recon"]
            if recon.get("status") == "WAITING_FOR_DIRECT_LAUNCH":
                self._launch_direct_initial_assessment()
                self.deployment["status"] = "DIRECT_INITIAL_ASSESSMENT"
                return {
                    "deployed": False,
                    "phase": "INITIAL_ASSESSMENT",
                    "reason": "Direct deployment starts with four assessment drones.",
                    "assessment_drone_ids": recon.get("drones_deployed", []),
                }

            if recon.get("status") != "DIRECT_ZONING_COMPLETE":
                return {
                    "deployed": False,
                    "phase": "INITIAL_ASSESSMENT",
                    "reason": "Four-drone zoning must complete before the main swarm deploys.",
                    "assessment_progress_percent": recon.get(
                        "assessment_progress_percent", 0.0
                    ),
                }

        else:
            forward = self.deployment["forward_base"]

            if forward["status"] != "SELECTED":
                return {
                    "deployed": False,
                    "reason": (
                        "Forward Base has not been selected by "
                        "the initial safety assessment."
                    ),
                }

            launch_point = forward["position"]
            deployment_status = "FORWARD_BASE"

            if deployment_method == "MANUAL":
                mobile = self.deployment["mobile_zone"]
                if mobile["status"] != "AT_FORWARD_BASE":
                    deployment_method = "MANUAL_OVERRIDE"

        allocated_ids = list(self.deployment["recon"].get("allocated_drone_ids", []))
        if not allocated_ids:
            # Direct deployment still allocates dynamically from the non-assessment fleet.
            assessment_ids = set(self.deployment["fleet"].get("initial_assessment_drone_ids", []))
            available_ids = [d.drone_id for d in self.drones if d.alive and d.drone_id not in assessment_ids]
            zone_count = len(self.deployment["recon"].get("priority_zones", []))
            allocated_ids = available_ids[:max(zone_count, min(len(available_ids), 8))]

        for d in self.drones:
            if d.drone_id in allocated_ids:
                d.state = "DEPLOYING_TO_ZONE"

        self.deployment["fleet"]["main_swarm_drone_ids"] = allocated_ids
        self.deployment["fleet"]["reserve_drone_ids"] = [
            d.drone_id for d in self.drones
            if d.alive and d.drone_id not in set(allocated_ids)
            and d.drone_id not in set(
                self.deployment["fleet"].get(
                    "initial_assessment_drone_ids", []
                )
            )
        ]
        self.deployment["fleet"]["available_count"] = len(
            self.deployment["fleet"]["reserve_drone_ids"]
        )

        alive_count = len(allocated_ids)
        zone_allocations = self.deployment["recon"].get(
            "priority_zones", []
        )
        drone_zone_map = {}
        for zone in zone_allocations:
            for drone_id in zone.get("allocated_drone_ids", []):
                drone_zone_map[str(drone_id)] = zone["id"]

        self.deployment["main_swarm"] = {
            "status": "DEPLOYING_TO_ZONES",
            "launch_point": launch_point,
            "deployed_count": alive_count,
            "deployment_method": deployment_method,
            "manual_override_available": False,
            "assigned_drone_ids": allocated_ids,
            "active_drone_count": alive_count,
            "zone_allocations": zone_allocations,
            "drone_zone_map": drone_zone_map,
            "required_drone_count": self.deployment["recon"].get(
                "required_main_swarm_count", alive_count
            ),
            "zoning_phase": "COMPLETE",
            "zone_arrival_progress_percent": 0.0,
        }

        self.deployment["status"] = "MAIN_SWARM_DEPLOYING_TO_ZONES"
        self.mission_config["status"] = "ACTIVE"

        return {
            "deployed": True,
            "mode": deployment_status,
            "launch_point": launch_point,
            "count": alive_count,
            "deployment_method": deployment_method,
        }

    # ========================================================
    # EXISTING SURVIVOR DETECTION
    # ========================================================

    def on_detection(self, p):

        tid = f"T{p['survivor_id']:03d}"

        if tid in self.tasks:
            return

        task = make_task(
            tid,
            p["location"][0],
            p["location"][1],
            p["confidence"],
        )

        self.tasks[tid] = task

        self.net.issue_cfp(task)

    # ========================================================
    # EXISTING SEARCH
    # ========================================================

    def cell_centre(self, cell):
        return [
            cell[0] * CELL + CELL / 2,
            cell[1] * CELL + CELL / 2,
        ]

    def claim_cell(self, drone):
        """
        Each drone picks its own next search cell.
        """

        available = [
            c
            for c in self.unsearched
            if c not in self.claimed
        ]

        if not available:

            self.claimed = {
                k: v
                for k, v in self.claimed.items()
                if v == drone.drone_id
            }

            available = [
                c
                for c in self.unsearched
                if c not in self.claimed
            ]

            if not available:
                return None

        bx, by = drone.belief_pos

        best = min(
            available,
            key=lambda c: math.dist(
                self.cell_centre(c),
                (bx, by),
            ),
        )

        self.claimed[best] = drone.drone_id

        return best

    def release_claims(self, drone_id):

        self.claimed = {
            k: v
            for k, v in self.claimed.items()
            if v != drone_id
        }

    # ========================================================
    # EXISTING DRONE MOVEMENT
    # ========================================================

    def move(self, d):
        """
        Fly to an assigned survivor,
        otherwise sweep the next search cell.
        """

        if (
            d.assigned_task
            and d.assigned_task in self.tasks
        ):
            target = self.tasks[
                d.assigned_task
            ]["location"]

        else:

            if (
                d.search_target is None
                or d.search_target
                not in self.unsearched
            ):
                d.search_target = (
                    self.claim_cell(d)
                )

            target = (
                self.cell_centre(
                    d.search_target
                )
                if d.search_target
                else None
            )

        if target is None:
            d.velocity = [0.0, 0.0]
            return

        # Navigate using BELIEF, not truth.
        bx, by = d.belief_pos

        dx = target[0] - bx
        dy = target[1] - by

        dist = math.hypot(dx, dy) or 1.0

        speed = min(
            3.0,
            dist,
        )

        d.velocity = [
            dx / dist * speed,
            dy / dist * speed,
        ]

        d.position = [
            max(
                0,
                min(
                    SIZE,
                    d.position[0]
                    + d.velocity[0],
                ),
            ),
            max(
                0,
                min(
                    SIZE,
                    d.position[1]
                    + d.velocity[1],
                ),
            ),
        ]

        d.battery -= 0.08

        # A cell counts as searched when the drone
        # believes it has arrived.
        if (
            d.search_target
            and math.dist(
                (bx, by),
                target,
            )
            < CELL / 2
        ):
            self.unsearched.discard(
                d.search_target
            )

            self.claimed.pop(
                d.search_target,
                None,
            )

            d.search_target = None

    # ========================================================
    # EXISTING PERCEPTION
    # ========================================================

    def perceive(self, d):

        hit = self.perception.scan(
            d,
            self.survivors,
        )

        if hit is None:
            return

        self.survivors[
            hit["survivor_id"]
        ]["found"] = True

        BUS.publish(
            "SURVIVOR_DETECTED",
            {
                "drone_id": d.drone_id,
                "survivor_id": hit[
                    "survivor_id"
                ],
                "location": hit[
                    "location"
                ],
                "confidence": hit[
                    "confidence"
                ],
                "frame": hit["frame"],
                "boxes": hit["boxes"],
            },
        )

    # ========================================================
    # EXISTING COVERAGE
    # ========================================================

    def coverage(self):

        return (
            100.0
            * (
                self.total_cells
                - len(self.unsearched)
            )
            / self.total_cells
        )

    # ========================================================
    # EXISTING SIMULATION STEP
    # ========================================================

    def step(
        self,
        tick,
        kill_at=None,
        kill_id=None,
    ):

        BUS.tick = tick

        # Complete the simulated initial assessment after the drones have
        # had time to travel/assess; never generate the report instantly.
        recon = self.deployment.get("recon", {})
        if (
            recon.get("launched")
            and recon.get("status") in {"DRONES_DEPLOYED", "IN_PROGRESS"}
            and recon.get("assessment_complete_tick") is not None
            and tick >= recon["assessment_complete_tick"]
        ):
            recon["assessment_progress_percent"] = 100.0
            self._run_initial_assessment()

            if (
                recon.get("perception_status") == "COMPLETE"
                and recon.get("priority_status") == "COMPLETE"
                and recon.get("safety_status") == "COMPLETE"
            ):
                # Direct missions must transition immediately from
                # assessment/zoning into automatic main-swarm deployment.
                # Do NOT overwrite DIRECT_ZONING_COMPLETE before the
                # deployment routine consumes it.
                if self.deployment.get("direct_feasible"):
                    recon["status"] = "DIRECT_ZONING_COMPLETE"
                    if self.deployment.get("main_swarm", {}).get("status") == "NOT_DEPLOYED":
                        self.deploy_main_swarm(deployment_method="AUTOMATIC")
                else:
                    recon["status"] = "COMPLETED"

        # -----------------------------------------------
        # Optional demo drone kill
        # -----------------------------------------------

        if (
            kill_at
            and tick == kill_at
        ):

            if kill_id is None:

                busy = [
                    d
                    for d in self.drones
                    if (
                        d.alive
                        and d.assigned_task
                        and d.state == "ENROUTE"
                    )
                ]

                if busy:
                    kill_id = (
                        busy[0].drone_id
                    )

            if kill_id is not None:

                released = self.fsm.kill(
                    kill_id
                )

                self.release_claims(
                    kill_id
                )

                print(
                    f"  [t{tick}] "
                    f"drone {kill_id} lost, "
                    f"released {released}"
                )

                if released:
                    self.net.issue_cfp(
                        self.tasks[released]
                    )

        # -----------------------------------------------
        # Mission/deployment progression
        # -----------------------------------------------

        self._mobile_zone_step(dt_seconds=1.0)

        # -----------------------------------------------
        # Existing drone loop
        # -----------------------------------------------
        # -----------------------------------------------
        # Gate existing Digital Twin until main swarm
        # deployment is active.
        # -----------------------------------------------

        main_swarm = self.deployment.get("main_swarm", {})
        main_swarm_status = main_swarm.get("status")
        main_swarm_active = (
            self.mission_config.get("status") == "ACTIVE"
            and main_swarm_status in {
                "DEPLOYING_TO_ZONES",
                "DEPLOYED",
            }
        )

        if not main_swarm_active:
            self.bridge.update()
            return

        if main_swarm_status == "DEPLOYING_TO_ZONES":
            progress = min(
                100.0,
                float(main_swarm.get("zone_arrival_progress_percent", 0.0))
                + 5.0,
            )
            main_swarm["zone_arrival_progress_percent"] = round(progress, 1)
            if progress >= 100.0:
                main_swarm["status"] = "DEPLOYED"
                self.deployment["status"] = "MAIN_SWARM_DEPLOYED"
                for d in self.drones:
                    if d.drone_id in set(
                        main_swarm.get("assigned_drone_ids", [])
                    ) and d.alive:
                        d.state = "SEARCHING"

        for d in self.drones:

            if not d.alive:
                continue

            # Recon drones return to normal Digital Twin behavior after
            # the initial assessment has completed. The actual perception
            # pipeline remains the same interface for future real inputs.
            if d.state == "RECON_ASSESSMENT":
                continue

            self.move(d)

            self.perceive(d)

            self.fsm.check_battery(d)

        # -----------------------------------------------
        # Localization
        # -----------------------------------------------

        self.bridge.update()

        # -----------------------------------------------
        # Existing auction system
        # -----------------------------------------------

        alive = [
            d
            for d in self.drones
            if d.alive
        ]

        self.net.collect_bids(alive)

        for (
            task_id,
            winner,
            cost,
        ) in self.net.resolve():

            w = next(
                d
                for d in self.drones
                if d.drone_id == winner
            )

            w.assigned_task = task_id

            self.tasks[
                task_id
            ]["status"] = "ASSIGNED"

            self.fsm.transition(
                w,
                "ENROUTE",
                "won auction",
            )

            print(
                f"  [t{tick}] "
                f"{task_id} -> "
                f"drone {winner} "
                f"(cost {cost:.0f})"
            )

        # -----------------------------------------------
        # Existing rescue completion
        # -----------------------------------------------

        for d in self.drones:

            if (
                d.state == "ENROUTE"
                and d.assigned_task
            ):

                if (
                    math.dist(
                        d.position,
                        self.tasks[
                            d.assigned_task
                        ]["location"],
                    )
                    < RESCUE_RADIUS
                ):

                    sid = int(
                        d.assigned_task[1:]
                    )

                    self.survivors[
                        sid
                    ]["rescued"] = True

                    self.tasks[
                        d.assigned_task
                    ]["status"] = "DONE"

                    BUS.publish(
                        "TASK_COMPLETED",
                        {
                            "task_id":
                            d.assigned_task
                        },
                    )

                    print(
                        f"  [t{tick}] "
                        f"{d.assigned_task} "
                        f"rescued by "
                        f"drone {d.drone_id}"
                    )

                    d.assigned_task = None

                    self.fsm.transition(
                        d,
                        "SEARCHING",
                        "rescue complete",
                    )

        # -----------------------------------------------
        # Mission completion
        # -----------------------------------------------

        if (
            self.mission_config["status"] == "ACTIVE"
            and all(s["rescued"] for s in self.survivors)
        ):
            self.complete = True

            self.mission_config[
                "status"
            ] = "COMPLETED"

            self.deployment[
                "status"
            ] = "MISSION_COMPLETE"

        return kill_id

    # ========================================================
    # MISSION CONTROL
    # ========================================================

    def stop_mission(self, reason="operator_stop"):
        """Stop the active mission without deleting its history/state."""
        self.mission_config["status"] = "STOPPED"
        self.deployment["status"] = "MISSION_STOPPED"

        if self.deployment["mobile_zone"]["status"] in {
            "MOVING",
            "AT_ASSESSMENT_RANGE",
        }:
            self.deployment["mobile_zone"]["status"] = "STOPPED"

        for d in self.drones:
            if d.alive:
                d.velocity = [0.0, 0.0]

        return {
            "stopped": True,
            "reason": reason,
        }

    # ========================================================
    # EXISTING RUN
    # ========================================================

    def run(
        self,
        ticks=400,
        kill_at=None,
        kill_id=None,
    ):

        BUS.publish(
            "MISSION_STARTED",
            {},
        )

        if self.mission_config["status"] == "PLANNING":
            self.mission_config["status"] = "ACTIVE"

        for tick in range(ticks):

            kill_id = self.step(
                tick,
                kill_at,
                kill_id,
            )

            if (
                kill_at
                and tick == kill_at
            ):
                kill_at = None

            if self.complete:

                BUS.publish(
                    "MISSION_COMPLETE",
                    {"tick": tick},
                )

                print(
                    f"\n  MISSION COMPLETE "
                    f"at tick {tick}"
                )

                break

        return self.results()

    # ========================================================
    # EXISTING RESULTS
    # ========================================================

    def results(self):

        return {
            "ticks": BUS.tick,

            "coverage": round(
                self.coverage(),
                1,
            ),

            "rescued": sum(
                s["rescued"]
                for s in self.survivors
            ),

            "detected": sum(
                s["found"]
                for s in self.survivors
            ),

            "total": len(
                self.survivors
            ),

            "mean_error": round(
                self.bridge.mean_error(),
                2,
            ),

            "auctions": BUS.count(
                "TASK_AWARDED"
            ),

            "bids": BUS.count(
                "BID_PLACED"
            ),

            "lost": BUS.count(
                "DRONE_DIED"
            ),
        }

    # ========================================================
    # SNAPSHOT FOR DASHBOARD + LIVE MAP
    # ========================================================

    def snapshot(self):
        """
        Complete read-only system state.

        Existing frontend fields are preserved.

        New fields:
            mission
            deployment

        The frontend can consume these through the
        existing WebSocket without a separate refresh.
        """

        fleet = self.deployment.setdefault("fleet", {})
        assessment_ids = set(
            fleet.get("initial_assessment_drone_ids", [])
        )
        main_ids = set(
            fleet.get("main_swarm_drone_ids", [])
        )
        disabled_ids = {
            d.drone_id for d in self.drones if not d.alive
        }
        reserve_ids = [
            d.drone_id for d in self.drones
            if d.alive
            and d.drone_id not in assessment_ids
            and d.drone_id not in main_ids
        ]
        fleet["registered_count"] = len(self.drones)
        fleet["disabled_drone_ids"] = sorted(disabled_ids)
        fleet["reserve_drone_ids"] = sorted(reserve_ids)
        fleet["available_count"] = len(reserve_ids)

        return {

            # ------------------------------------------------
            # Existing state
            # ------------------------------------------------

            "tick": BUS.tick,

            "complete": self.complete,

            "world": {
                "size": SIZE,
                "anchors": ANCHORS,
                "cell": CELL,
            },

            "ranging_on": (
                self.bridge
                .localizers[
                    self.drones[0].drone_id
                ]
                .ranging_on
            ),

            "searched_cells": [
                self.cell_centre(c)
                for c in (
                    {
                        (x, y)
                        for x in range(
                            int(SIZE // CELL)
                        )
                        for y in range(
                            int(SIZE // CELL)
                        )
                    }
                    - self.unsearched
                )
            ],

            "drones": [

                {
                    "id": d.drone_id,

                    "true_pos": [
                        round(
                            d.position[0],
                            1,
                        ),
                        round(
                            d.position[1],
                            1,
                        ),
                    ],

                    "belief_pos": [
                        round(
                            d.belief_pos[0],
                            1,
                        ),
                        round(
                            d.belief_pos[1],
                            1,
                        ),
                    ],

                    "error": round(
                        self.bridge.error(d),
                        2,
                    ),

                    "uncertainty": round(
                        d.uncertainty,
                        2,
                    ),

                    "battery": round(
                        d.battery,
                        1,
                    ),

                    "state": d.state,

                    "alive": d.alive,

                    "gps_status": "DENIED" if getattr(d, "gps_denied", False) else "AVAILABLE",

                    "mission_role": (
                        "DISABLED"
                        if not d.alive
                        else "INITIAL_ASSESSMENT"
                        if d.drone_id in set(
                            self.deployment.get("fleet", {}).get(
                                "initial_assessment_drone_ids", []
                            )
                        )
                        else "MAIN_SWARM"
                        if d.drone_id in set(
                            self.deployment.get("fleet", {}).get(
                                "main_swarm_drone_ids", []
                            )
                        )
                        else "RESERVE"
                    ),

                    "zone_id": self.deployment.get(
                        "main_swarm", {}
                    ).get("drone_zone_map", {}).get(str(d.drone_id)),

                    "assigned_task":
                        d.assigned_task,

                    "search_target": (
                        self.cell_centre(
                            d.search_target
                        )
                        if d.search_target
                        else None
                    ),

                }

                for d in self.drones

            ],

            "survivors": [

                {
                    "id": s["id"],

                    "pos": [
                        round(
                            s["pos"][0],
                            1,
                        ),
                        round(
                            s["pos"][1],
                            1,
                        ),
                    ],

                    "found": s["found"],

                    "rescued":
                        s["rescued"],
                }

                for s in self.survivors

            ],

            "tasks": list(
                self.tasks.values()
            ),

            "open_auctions": [

                {
                    "task_id": tid,

                    "age": c["age"],

                    "bids": [
                        {
                            "drone_id": k,
                            "cost": round(
                                v,
                                1,
                            ),
                        }

                        for k, v in sorted(
                            c["bids"].items(),
                            key=lambda kv: kv[1],
                        )

                        if v != float("inf")
                    ],

                }

                for (
                    tid,
                    c
                ) in self.net.open_calls.items()

            ],

            "metrics": self.results(),

            "events": BUS.recent(25),

            # ------------------------------------------------
            # NEW MISSION STATE
            # ------------------------------------------------

            "mission": {

                "id":
                    self.mission_config["id"],

                "name":
                    self.mission_config["name"],

                "mode":
                    self.mission_config["mode"],

                "status":
                    self.mission_config["status"],

                "incident_location":
                    self.mission_config[
                        "incident_location"
                    ],

                "admin_base":
                    self.mission_config[
                        "admin_base"
                    ],

            },

            # ------------------------------------------------
            # NEW DEPLOYMENT STATE
            # ------------------------------------------------

            "fleet": self.deployment.get("fleet", {}),
            "deployment": self.deployment,

        }


# ============================================================
# COMMAND-LINE SIMULATION
# ============================================================

if __name__ == "__main__":

    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--kill-at",
        type=int,
        default=None,
    )

    ap.add_argument(
        "--kill-id",
        type=int,
        default=None,
    )

    ap.add_argument(
        "--no-ranging",
        action="store_true",
    )

    ap.add_argument(
        "--drones",
        type=int,
        default=128,
    )

    ap.add_argument(
        "--ticks",
        type=int,
        default=400,
    )

    a = ap.parse_args()

    m = Mission(
        n_drones=a.drones,
        ranging_on=not a.no_ranging,
    )

    r = m.run(
        ticks=a.ticks,
        kill_at=a.kill_at,
        kill_id=a.kill_id,
    )

    print(
        "\n  " + "-" * 40
    )

    for k, v in r.items():
        print(
            f"  {k:12} {v}"
        )
