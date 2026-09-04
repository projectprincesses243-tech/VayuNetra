# VayuNetra

**A decentralized coordination layer for autonomous drone swarms operating in GPS-denied disaster environments.**

Smart Horizon 2026 — 48-Hour International Hackathon
New Horizon College of Engineering, Bengaluru
Team ID `SHIH26-TID-504` · Problem Statement `SH-DST-05`

---

## What this project is

Drones are a solved commercial product. Getting a *fleet* of them to search a disaster zone as one coordinated team — without GPS, without a mobile network, and without any single controller — is not.

VayuNetra is the software layer that solves that second problem. We do not build drones or modify them. We build the intelligence that would run on a drone's companion computer, alongside its existing flight controller.

The system is developed as a **digital twin** — a complete software replica of the swarm, in which the coordination logic is written exactly as it would be for real flight hardware, and the communication layer is swappable. This allows the decision-making to be tested, broken deliberately, and measured before any hardware is risked.

---

## The three problems we address

**Coverage.** A single drone flies for roughly 25 minutes and observes one location at a time. A collapsed district is far too large. Multiple drones only help if they divide the area without duplicating effort.

**Position without GPS.** GPS requires a clear view of the sky. Under rubble, tree canopy, or between tall buildings, the signal is blocked or arrives after reflecting off surfaces, producing a confidently wrong position. A drone that does not know where it is cannot report where a survivor is.

**Decisions without a controller.** There is no functioning mobile network in a disaster zone. If one computer assigns every task, losing that computer stops the entire mission.

---

## System architecture

```
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
server/              FastAPI live-state server with WebSocket
Frontend/            React mission dashboard
Frontend/src/Backend/disaster_alerts/
                     pre-disaster alert ingestion (IMD, SACHET)
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

**Command-line options:**

```bash
python sim.py --no-ranging      # disable inter-drone ranging
python sim.py --kill-at 25      # remove a drone mid-mission
python sim.py --drones 3        # change fleet size
```

---

## Measured results

Reproduce with `python experiments.py`. Results are averaged across 8 random seeds.

Detection uses a small image set, so absolute rescue counts are limited by how many survivor frames the detector confirms rather than by swarm performance. The comparative results — with versus without ranging, and one drone versus several — are the meaningful measurements.

| Measurement | Result |
|---|---|
| Localization error, ranging active | ~8.8 m |
| Localization error, ranging denied | ~84.6 m |
| Improvement factor | **~9.6x** |
| Coverage, six drones | 100% |
| Coverage, single drone | ~43% |

---

## Hardware deployment

The same coordination code runs unmodified on a Raspberry Pi 4, which is the class of companion computer a real drone would carry.

```
  RASPBERRY PI 4          mission intelligence, perception, dashboard
        |
        | USB / UART
        |
  STM32F407G-DISC1        flight controller interface
        |
  ESP32                   swarm mesh radio (ESP-NOW)
```

**Verified:** Raspberry Pi hosts the full digital twin and runs missions independently of any laptop. STM32F407G-DISC1 detected over USB on `/dev/ttyACM0`. A terminal mission dashboard (`pi_dashboard.py`) displays live state directly on the Pi.

The STM32 represents the flight controller interface. It does not implement stabilization, motor mixing or sensor fusion — those are assumed to exist in a production flight controller such as a Pixhawk running ArduPilot or PX4.

---

## What is honestly not built

We would rather state these than have them discovered.

- **Terrain mapping.** We record which cells have been searched. We do not build a map of the environment. That is SLAM, and it solves a different problem.
- **Real thermal imaging.** The thermal channel is derived from visible-light imagery. We do not have a thermal camera.
- **Physical flight.** Nothing has flown. The flight controller interface is demonstrated, not the aircraft.
- **Distributed execution.** All drones currently run in one process, so bids do not yet cross a physical radio. The decision logic is decentralized; the deployment is not yet.
- **Secure communication.** No message authentication or encryption is implemented.
- **3D navigation.** The simulation operates on a 2D plane. Altitude, wind and aerodynamics are not modelled.

---

## Team

| Member | Contribution |
|---|---|
| Mantripragada Ramaa Gayatri | Integration, hardware architecture, Raspberry Pi deployment |
| Allu Uma Eashanvi | Environment, swarm behaviour, path planning, ESP32 |
| Vaishnavi H B | GPS-denied localization: dead reckoning, ranging, trilateration |
| Vandana H S | Mission dashboard, pre-disaster alert integration |
| Tejaswini Badami | Perception: YOLOv8 detection, multi-signal fusion |

---

## Acknowledgements

Reviewed against: Reynolds (1987) on flocking behaviour, Smith (1980) on the Contract Net Protocol, Ultralytics YOLOv8 documentation, Espressif ESP-NOW documentation, and published reviews of UAV deployment in disaster response including Nepal 2015, Hurricane Harvey 2017, and the Noto Peninsula earthquake 2024.