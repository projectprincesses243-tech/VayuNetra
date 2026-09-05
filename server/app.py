"""
VayuNetra Live State Server.

Runs the Digital Twin simulation in a background thread and publishes
the complete operational state over HTTP + WebSocket.

Run with:
    py -m server.app
"""

import sys
import asyncio
import threading
import time
import json
import uuid

sys.path.insert(0, ".")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sim import Mission
from core.bus import BUS


app = FastAPI(title="VayuNetra")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MissionConfigureRequest(BaseModel):
    name: str | None = None
    latitude: float
    longitude: float
    location_name: str | None = None
    mode: str = "SIMULATION"


class ReconCompleteRequest(BaseModel):
    candidate_viable: bool = True
    hazards: list[str] = []
    communication_quality: str = "UNKNOWN"
    accessibility: str = "UNKNOWN"


class StopMissionRequest(BaseModel):
    reason: str = "operator_stop"


class SimRunner:
    def __init__(self):
        self.lock = threading.Lock()
        self.mission = Mission()
        self.tick = 0
        self.running = False
        self.speed = 0.1
        self.kill_request = None

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running:
            with self.lock:
                if self.kill_request is not None:
                    self._do_kill(self.kill_request)
                    self.kill_request = None

                self.mission.step(self.tick)
                self.tick += 1

                if self.mission.complete:
                    self.running = False

            time.sleep(self.speed)

    def _do_kill(self, requested_id):
        m = self.mission

        if requested_id is not None and requested_id >= 0:
            target = next(
                (
                    d for d in m.drones
                    if d.drone_id == requested_id and d.alive
                ),
                None,
            )
        else:
            target = next(
                (
                    d for d in m.drones
                    if d.alive
                    and d.assigned_task
                    and d.state == "ENROUTE"
                ),
                None,
            )

            if target is None:
                target = next(
                    (d for d in m.drones if d.alive),
                    None,
                )

        if target is None:
            return None

        released = m.fsm.kill(target.drone_id)
        m.release_claims(target.drone_id)

        if released and released in m.tasks:
            m.tasks[released]["status"] = "OPEN"
            m.net.issue_cfp(m.tasks[released])

        return target.drone_id

    def snapshot(self):
        with self.lock:
            return self.mission.snapshot()

    def reset(self, ranging_on=True):
        with self.lock:
            self.running = False

        time.sleep(0.25)

        with self.lock:
            BUS.reset()
            self.mission = Mission(ranging_on=ranging_on)
            self.tick = 0

        self.start()

    def set_ranging(self, on):
        with self.lock:
            self.mission.bridge.set_ranging(on)

    def request_kill(self, drone_id=None):
        with self.lock:
            alive = [
                d.drone_id for d in self.mission.drones if d.alive
            ]

            if not alive:
                return {"killed": None, "reason": "no drones alive"}

            self.kill_request = -1 if drone_id is None else drone_id

            if not self.running:
                killed = self._do_kill(self.kill_request)
                self.kill_request = None
                return {"queued": False, "killed": killed}

        return {"queued": True}

    def configure_mission(
        self,
        name,
        latitude,
        longitude,
        location_name,
        mode,
    ):
        with self.lock:
            mission_id = f"OP-{uuid.uuid4().hex[:8].upper()}"

            result = self.mission.configure_mission(
                name=name,
                latitude=latitude,
                longitude=longitude,
                location_name=location_name,
                mode=mode,
            )

            if result["configured"]:
                self.mission.mission_config["id"] = mission_id
                self.mission.mission_config["status"] = "PLANNING"

                BUS.publish(
                    "MISSION_CONFIGURED",
                    {
                        "mission_id": mission_id,
                        "name": name,
                        "mode": mode,
                        "location": {
                            "latitude": latitude,
                            "longitude": longitude,
                            "name": location_name,
                        },
                    },
                )

            return {
                "mission_id": mission_id if result["configured"] else None,
                **result,
            }

    def start_mobile_zone(self):
        with self.lock:
            result = self.mission.start_mobile_zone()

            if result.get("started"):
                BUS.publish(
                    "MOBILE_ZONE_STARTED",
                    {
                        "speed_kmph": result.get("speed_kmph"),
                        "time_scale": result.get("time_scale"),
                    },
                )

            return result

    def launch_recon(self):
        with self.lock:
            result = self.mission.launch_recon()

            if result.get("launched"):
                BUS.publish(
                    "RECON_STARTED",
                    {
                        "launch_point": result.get("launch_point"),
                        "drones": self.mission.deployment["recon"].get(
                            "drones_deployed", []
                        ),
                    },
                )

            return result

    def complete_recon(
        self,
        candidate_viable,
        hazards,
        communication_quality,
        accessibility,
    ):
        with self.lock:
            result = self.mission.complete_recon(
                candidate_viable=candidate_viable,
                hazards=hazards,
                communication_quality=communication_quality,
                accessibility=accessibility,
            )

            if result.get("completed"):
                BUS.publish(
                    "RECON_COMPLETED",
                    {
                        "candidate_viable": candidate_viable,
                        "hazards": hazards,
                        "communication_quality": communication_quality,
                        "accessibility": accessibility,
                    },
                )

            return result

    def deploy_main_swarm(self):
        with self.lock:
            result = self.mission.deploy_main_swarm(
                deployment_method="MANUAL"
            )

            if result.get("deployed"):
                BUS.publish(
                    "SWARM_DEPLOYED",
                    {
                        "launch_point": result.get("launch_point"),
                        "count": result.get("count"),
                        "deployment_method": result.get(
                            "deployment_method"
                        ),
                    },
                )

            return result

    def stop_mission(self, reason="operator_stop"):
        with self.lock:
            result = self.mission.stop_mission(reason)

            if result.get("stopped"):
                BUS.publish(
                    "MISSION_STOPPED",
                    {"reason": reason},
                )

            return result


RUNNER = SimRunner()


@app.on_event("startup")
def startup():
    RUNNER.start()


@app.get("/api/state")
def state():
    return RUNNER.snapshot()


@app.post("/api/mission/configure")
def configure_mission(request: MissionConfigureRequest):
    return RUNNER.configure_mission(
        name=request.name,
        latitude=request.latitude,
        longitude=request.longitude,
        location_name=request.location_name,
        mode=request.mode,
    )


@app.post("/api/mission/mobile-zone/start")
def start_mobile_zone():
    return RUNNER.start_mobile_zone()


@app.post("/api/mission/recon/start")
def start_recon():
    return RUNNER.launch_recon()


@app.post("/api/mission/recon/complete")
def complete_recon(request: ReconCompleteRequest):
    return RUNNER.complete_recon(
        candidate_viable=request.candidate_viable,
        hazards=request.hazards,
        communication_quality=request.communication_quality,
        accessibility=request.accessibility,
    )


@app.post("/api/mission/deploy")
def deploy_main_swarm():
    return RUNNER.deploy_main_swarm()


@app.post("/api/mission/stop")
def stop_mission(request: StopMissionRequest | None = None):
    reason = request.reason if request else "operator_stop"
    return RUNNER.stop_mission(reason)


@app.post("/api/ranging/{on}")
def ranging(on: bool):
    RUNNER.set_ranging(on)
    return {"ranging_on": on}


@app.post("/api/kill")
def kill(drone_id: int = None):
    return RUNNER.request_kill(drone_id)


@app.post("/api/reset")
def reset(ranging_on: bool = True):
    RUNNER.reset(ranging_on)
    return {"reset": True, "ranging_on": ranging_on}


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()

    try:
        while True:
            await sock.send_text(json.dumps(RUNNER.snapshot()))
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
