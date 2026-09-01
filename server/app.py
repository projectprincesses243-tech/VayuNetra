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
        self.pending_kill = None

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running and self.tick < 2000:
            with self.lock:
                kill_at = self.tick if self.pending_kill is not None else None
                kill_id = self.pending_kill if self.pending_kill != -1 else None
                self.mission.step(self.tick, kill_at, kill_id)
                self.pending_kill = None
                self.tick += 1
                if self.mission.complete:
                    self.running = False
            time.sleep(self.speed)

    def snapshot(self):
        with self.lock:
            return self.mission.snapshot()

    def reset(self, ranging_on=True):
        with self.lock:
            self.running = False
            self.mission = Mission(ranging_on=ranging_on)
            self.tick = 0
        time.sleep(0.2)
        self.start()

    def set_ranging(self, on):
        with self.lock:
            self.mission.bridge.set_ranging(on)

    def kill(self, drone_id=None):
        with self.lock:
            self.pending_kill = -1 if drone_id is None else drone_id


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
    """The K key. Omit drone_id to auto-target a drone that is en route."""
    RUNNER.kill(drone_id)
    return {"killed": drone_id if drone_id is not None else "auto"}


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