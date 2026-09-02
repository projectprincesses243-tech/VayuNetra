"""
Live state server. Runs the simulation in a background thread and publishes
state over HTTP and WebSocket for the dashboard.

Run with:  python -m server.app
Then open: http://127.0.0.1:8000/api/state
"""

import sys, asyncio, threading, time, json
sys.path.insert(0, ".")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from sim import Mission
from core.bus import BUS

app = FastAPI(title="VayuNetra")

# React dev server runs on a different port, so the browser needs permission
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimRunner:
    """Runs the mission in a background thread at a fixed rate."""

    def __init__(self):
        self.lock = threading.Lock()
        self.mission = Mission()
        self.tick = 0
        self.running = False
        self.speed = 0.1          # seconds per tick
        self.kill_request = None  # None = nothing pending, -1 = auto, int = specific id

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running and self.tick < 5000:
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
        """
        Kill a drone. Called from inside the loop, holding the lock.

        Preference order:
          1. the specific drone asked for
          2. a drone carrying a task  (best demo - triggers a re-auction)
          3. any living drone         (still a valid failure demo)

        Falling through to 3 matters: by the time a judge presses the button
        the mission is often finished and nobody is en route. Returning 200
        while killing nothing is worse than killing an idle drone.
        """
        m = self.mission

        if requested_id is not None and requested_id >= 0:
            target = next((d for d in m.drones
                           if d.drone_id == requested_id and d.alive), None)
        else:
            target = next((d for d in m.drones
                           if d.alive and d.assigned_task and d.state == "ENROUTE"), None)
            if target is None:
                target = next((d for d in m.drones if d.alive), None)

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
            alive = [d.drone_id for d in self.mission.drones if d.alive]
            if not alive:
                return {"killed": None, "reason": "no drones alive"}
            self.kill_request = -1 if drone_id is None else drone_id
            if not self.running:      # mission finished - apply immediately
                self._do_kill(self.kill_request)
                self.kill_request = None
        return {"queued": True}


RUNNER = SimRunner()


@app.on_event("startup")
def startup():
    RUNNER.start()


@app.get("/api/state")
def state():
    """Complete system state. Poll this, or use the WebSocket below."""
    return RUNNER.snapshot()


@app.post("/api/ranging/{on}")
def ranging(on: bool):
    """The R key. /api/ranging/false denies ranging corrections."""
    RUNNER.set_ranging(on)
    return {"ranging_on": on}


@app.post("/api/kill")
def kill(drone_id: int = None):
    """
    The K key. Omit drone_id to auto-target.
    Takes effect on the next tick, so poll /api/state or watch the socket.
    """
    return RUNNER.request_kill(drone_id)


@app.post("/api/reset")
def reset(ranging_on: bool = True):
    RUNNER.reset(ranging_on)
    return {"reset": True, "ranging_on": ranging_on}


@app.websocket("/ws")
async def ws(sock: WebSocket):
    """Streams state at 10 Hz. Preferred over polling."""
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