# VayuNetra

**A decentralized coordination layer for autonomous drone swarms operating in GPS-denied disaster environments.**

Smart Horizon 2026 — 48-Hour International Hackathon
New Horizon College of Engineering, Bengaluru
Team ID `SHIH26-TID-504` · Problem Statement `SH-DST-05`

![Complete hardware setup integrated with the digital twin](Docs/Images/Complete%20Hardware%20Setup%20integrated%20with%20digital%20twin.jpeg)

*The full bench during the hackathon. Left: the digital twin running its mission console. Right: Mission Planner with ArduPilot. Foreground: Raspberry Pi 4, STM32F407G-DISC1, and three ESP32 mesh nodes with an I²C status display.*

---

## What this project is

Drones are a solved commercial product. Getting a *fleet* of them to search a disaster zone as one coordinated team — without GPS, without a mobile network, and without any single controller — is not.

VayuNetra is the software layer that solves that second problem. We do not build drones or modify them. We build the intelligence that would run on a drone's companion computer, alongside its existing flight controller.

The system is developed as a **digital twin** — a complete software replica of the swarm, in which the coordination logic is written exactly as it would be for real flight hardware, and the communication layer is swappable. This allows the decision-making to be tested, broken deliberately, and measured before any hardware is risked.

The twin is not confined to a laptop. It runs on a Raspberry Pi 4 acting as the edge gateway, receiving MAVLink telemetry from an STM32F407G-DISC1 over serial, and ingesting live government disaster alerts from the NDMA SACHET feed. Real data enters from both ends.

---

## The three problems we address

**Coverage.** A single drone flies for roughly 25 minutes and observes one location at a time. A collapsed district is far too large. Multiple drones only help if they divide the area without duplicating effort.

**Position without GPS.** GPS requires a clear view of the sky. Under rubble, tree canopy, or between tall buildings, the signal is blocked or arrives after reflecting off surfaces, producing a confidently wrong position. A drone that does not know where it is cannot report where a survivor is.

**Decisions without a controller.** There is no functioning mobile network in a disaster zone. If one computer assigns every task, losing that computer stops the entire mission.

---

## System architecture

```
   PRE-DISASTER INTELLIGENCE          HARDWARE TELEMETRY
   NDMA SACHET / IMD alerts           Mission Planner + ArduPilot
            |                                  |
   normalize, dedupe, store           STM32F407G-DISC1 (MAVLink)
            |                                  |
   disaster scenario                   serial link
            \                                  /
             \                                /
              RASPBERRY PI 4 — EDGE GATEWAY
                          |
   MISSION INTERFACE      observer only; issues no commands
          ^
   COORDINATION LAYER     auction, task lifecycle, sector claiming
          ^
   AGENT LAYER            belief position, perception, motion, battery
          ^
   MESSAGE LAYER          packet contract, independent of transport
          ^
   +------+------+
 simulated     ESP-NOW
 transport     transport
```

Every module publishes events to a shared bus rather than calling other modules directly. This is what allows the transport layer to be replaced — from in-process messages to physical radio — without any layer above it changing.

---

## Core design decisions

**Every drone holds two positions.** `position` is ground truth, known only to the simulator. `belief_pos` is what the drone itself estimates. All navigation, bidding and coverage decisions use the belief. When localization degrades, the mission degrades — exactly as it would in the field.

**No allocator exists in the codebase.** Task allocation runs as a Contract Net auction. Each drone computes its own bid from distance, battery and current commitment. Bids propagate by gossip. Ties break deterministically on drone ID, so every drone independently reaches the same winner without a coordinating step.

**Sector claiming is local.** Each drone selects the nearest unclaimed cell using its own position estimate. No sectors are assigned. When a drone is lost, its claims are released automatically and other drones absorb them through the same ordinary rules — there is no recovery procedure.

**Detection requires corroboration.** A single camera mistakes rubble and debris for people. An alert is raised only when at least two of three independent signals agree, and the trained model must be one of them. A false positive is not a wasted trip — it sends a rescue team into an unstable structure for nothing.

**Pre-disaster intelligence runs isolated.** The alert service is a separate process on its own port. If the government feed is slow, unreachable, or malformed, the twin continues to run. External dependencies are never allowed to sit in the mission loop.

---

## Repository structure

```
core/                shared data contract and event bus
world/               environment, obstacles, survivors
swarm/               drone agents, Boids flocking, movement
planning/            A* pathfinding and waypoint following
localize/            dead reckoning, ranging, trilateration, filtering
perception/          YOLOv8 detection and multi-signal fusion
mission/             state machine and Contract Net auction
integration/         adapters connecting independently written modules
pre_disaster/        NDMA SACHET alert service (standalone, port 8001)
server/              FastAPI live-state server with WebSocket
firmware/            ESP32 ESP-NOW mesh nodes and STM32 MAVLink sketch
Frontend/            React mission dashboard
Docs/Images/         hardware and deployment photographs
tools/               frame mapping, detector tests, demo scripts
console.html         standalone mission console, no build step
sim.py               integrated mission loop
experiments.py       controlled experiment suite
```

---

## Running it

Requires Python 3.12.

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
source .venv/bin/activate         # Linux / Raspberry Pi

pip install numpy scipy fastapi "uvicorn[standard]" pygame
pip install opencv-python ultralytics    # perception (optional)
pip install feedparser requests          # pre-disaster alerts (optional)
```

**Run a mission:**

```bash
python sim.py
```

**Run with the live dashboard:**

```bash
python -m server.app
```

Then open `console.html` in a browser, or run the React dashboard:

```bash
cd Frontend
npm install
npm run dev
```

**Run the pre-disaster alert service** (separate terminal, separate port):

```bash
cd pre_disaster
python -m uvicorn app:app --port 8001
```

Trigger a fetch with `POST /api/alerts/check`, then read `GET /api/alerts`.

**Command-line options:**

```bash
python sim.py --no-ranging      # disable inter-drone ranging
python sim.py --kill-at 25      # remove a drone mid-mission
python sim.py --drones 3        # change fleet size
```

---

## Measured results

Reproduce with `python experiments.py`. All figures are means over 8 random seeds (1, 7, 13, 21, 42, 99, 123, 256), reported with standard deviation.

### GPS-denied localization

| Condition | Mean position error |
|---|---|
| Ranging active | 2.61 m ± 0.67 |
| Ranging denied | 23.74 m ± 5.62 |
| **Improvement factor** | **9.1x** |

### Swarm size versus single drone

| Drones | Survivors rescued (of 5) | Coverage |
|---|---|---|
| 1 | 0.88 ± 0.83 | 16.25% ± 14.08 |
| 3 | 2.00 ± 1.20 | 30.75% ± 11.42 |
| 6 | 2.62 ± 1.69 | 49.00% ± 10.54 |

### Failure recovery

| Condition | Rescued | Auctions run |
|---|---|---|
| No failure | 2.62 | 2.88 |
| One drone lost mid-task | 2.12 | 3.38 |

The kill is timed to catch a drone actively carrying a task. The extra auctions are re-auctions of the released task. Recovery requires no central coordinator and no recovery procedure — the ordinary rules absorb the loss.

### Graceful degradation

| Fleet size | Rescued (of 5) | Coverage |
|---|---|---|
| 6 | 2.62 ± 1.69 | 49.00% |
| 5 | 3.12 ± 1.36 | 46.12% |
| 4 | 2.88 ± 1.36 | 39.12% |
| 3 | 2.00 ± 1.20 | 30.75% |
| 2 | 1.25 ± 1.04 | 23.25% |

### Perception fusion

Evaluated across 1,417 real disaster-scene images spanning six categories (collapsed building, fire, flood, landslide, traffic incident, normal). In 646 cases, partial single-sensor agreement was correctly suppressed because the trained model did not corroborate it. This is a false-alert suppression rate, not a precision/recall figure — the image set has no survivor ground truth.

### What these numbers are, and are not

- Range measurements use Gaussian noise calibrated to published UWB accuracy (~10 cm). They are modelled, not measured from hardware.
- Dead-reckoning drift is modelled as fixed per-drone bias plus a random walk. Magnitudes are tuned, not taken from a specific IMU.
- Perception in the swarm experiment runs a proximity model, not YOLO inference. Detector accuracy is measured separately, above.
- All drones in the twin run in one process, so bids do not yet cross a physical radio.

---

## Hardware deployment

The same coordination code runs unmodified on a Raspberry Pi 4, which is the class of companion computer a real drone would carry.

```
  MISSION PLANNER + ARDUPILOT     simulated flight telemetry source
        |
        | MAVLink
        |
  STM32F407G-DISC1                flight controller interface
        |
        | serial
        |
  RASPBERRY PI 4                  digital twin host, perception, dashboard
        |
  ESP32 x3                        swarm mesh radio (ESP-NOW)
```

### Live telemetry on the Raspberry Pi

![VayuNetra mission console running on the Raspberry Pi](Docs/Images/Dashboard%20Console.jpeg)

*The mission console with a live MAVLink link. 18,407 messages received and forwarded, STM32F407 reported connected on the hardware bus, and navigation, attitude, motion, power and link-health panels populated from real telemetry rather than placeholder values.*

![Raspberry Pi 4 alongside the running console](Docs/Images/Dashboard%20Console%20with%20Raspberry%20Pi.jpeg)

*The same console with the Pi 4 in frame. The twin runs on the Pi itself, reached over a Wi-Fi hotspot and SSH — no laptop is required for the mission to continue.*

### Flight controller interface

![Mission Planner connected to the STM32F407G-DISC1](Docs/Images/Mission%20Planner%20with%20STM32.jpeg)

*ArduPilot Mission Planner tracking the vehicle over a live MAVLink connection, with the STM32F407G-DISC1 wired in at the front of the bench.*

![Mission Planner telemetry view](Docs/Images/Mission%20Planner%20Integrated%20with%20STM32.png)

*Mission Planner receiving heartbeat and position messages from the STM32 sketch in `firmware/stmsketch/`.*

### Swarm mesh radio

![ESP32 nodes running the ESP-NOW mesh protocol](Docs/Images/ESP32%20Communication%20Protocol.jpeg)

*Three ESP32 nodes exchanging ESP-NOW packets peer-to-peer, with an I²C display reporting node state. Each node carries a survivor-trigger input and a defined message contract (`MSG_SURVIVOR`, `MSG_EVENT_ACK`). Firmware in `firmware/`.*

### Verified

- Raspberry Pi 4 hosts the full digital twin and runs missions independently of any laptop, accessed over Wi-Fi hotspot and SSH.
- STM32F407G-DISC1 enumerates over USB as an ST-LINK device and is detected on the hardware bus.
- MAVLink heartbeat and position packets stream from the STM32 into a `pymavlink` receiver on the Pi, with message counts confirmed on the console.
- A terminal mission dashboard displays live fleet state, navigation, attitude, power and link health directly on the Pi.
- Three ESP32 nodes exchange ESP-NOW packets peer-to-peer with a defined message contract, survivor-trigger input and I²C status output.

The STM32 represents the flight controller interface. It does not implement stabilization, motor mixing or sensor fusion — those are assumed to exist in a production flight controller such as a Pixhawk running ArduPilot or PX4. Telemetry in the current setup originates from Mission Planner, not from a flying airframe. This is hardware-in-the-loop validation of the interface, not a flight test.

---

## What is honestly not built

We would rather state these than have them discovered.

- **Terrain mapping.** We record which cells have been searched. We do not build a map of the environment. That is SLAM, and it solves a different problem.
- **Real thermal imaging.** The thermal channel is derived from visible-light imagery. We do not have a thermal camera.
- **Physical flight.** Nothing has flown. The flight controller interface is demonstrated, not the aircraft.
- **Distributed execution.** All drones in the twin currently run in one process, so bids do not yet cross a physical radio. The ESP-NOW mesh is proven separately; the two are not yet joined.
- **Severity-driven task priority.** Live disaster alerts reach the mission and appear in mission state, but `hazard`, `severity` and `priority` are not yet read by the auction cost function. The intelligence is displayed, not yet acted upon.
- **Secure communication.** No message authentication or encryption is implemented.
- **3D navigation.** The simulation operates on a 2D plane. Altitude, wind and aerodynamics are not modelled.

---

## Team

| Member | Contribution |
|---|---|
| Mantripragada Ramaa Gayatri | Integration, hardware architecture, Raspberry Pi deployment |
| Allu Uma Eashanvi | Environment, swarm behaviour, path planning, ESP32 |
| Vaishnavi H B | GPS-denied localization: dead reckoning, ranging, trilateration; pre-disaster alert service |
| Vandana H S | Mission dashboard, pre-disaster alert integration |
| Tejaswini Badami | Perception: YOLOv8 detection, multi-signal fusion |

---

## Acknowledgements

Reviewed against: Reynolds (1987) on flocking behaviour, Smith (1980) on the Contract Net Protocol, Grieves (2014) on digital twin architecture, Ultralytics YOLOv8 documentation, Espressif ESP-NOW documentation, the MAVLink and ArduPilot reference documentation, the NDMA SACHET Common Alerting Protocol schema, and published reviews of UAV deployment in disaster response including Nepal 2015, Hurricane Harvey 2017, and the Noto Peninsula earthquake 2024.