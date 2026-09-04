# VayuNetra — Measured Results

Generated 2026-09-01 10:58  

Seeds per condition: 8  |  Reproduce with `python experiments.py`


## A — Swarm vs single drone

| Drones | Survivors rescued (of 5) | Coverage % | Ticks |
|---|---|---|---|
| 1 | 2.12 ± 1.13 | 43.5 ± 0.76 | 499 |
| 3 | 4.88 ± 0.35 | 80.25 ± 15.07 | 346 |
| 6 | 5 ± 0.0 | 77.5 ± 19.64 | 175 |

## B — GPS-denied localization

| Condition | Mean position error (m) | Range |
|---|---|---|
| Ranging ON | 3.29 ± 1.06 | 1.67 – 4.7 |
| Ranging OFF | 67.03 ± 28.26 | 16.31 – 86.18 |

**Improvement: 20.4x**


## C — GPS denial causes mission failure

| Condition | Survivors rescued (of 5) |
|---|---|
| With ranging | 5 ± 0.0 |
| Without ranging | 3.75 ± 1.04 |

Same detections in both cases. Without ranging, drones accept tasks but navigate on a drifted belief and fail to arrive.


## D — Failure recovery

| Condition | Rescued | Auctions run |
|---|---|---|
| No failure | 5 | 5 |
| One drone lost mid-task | 4.75 | 5.75 |

Kill timed to catch a drone carrying a task. Extra auctions are re-auctions of the released task. Recovery requires no central coordinator.


## E — Graceful degradation

| Fleet size | Rescued (of 5) | Coverage % |
|---|---|---|
| 6 | 5 ± 0.0 | 77.5 |
| 5 | 5 ± 0.0 | 82.62 |
| 4 | 5 ± 0.0 | 92.75 |
| 3 | 4.88 ± 0.35 | 80.25 |
| 2 | 3.75 ± 1.16 | 80.38 |

## What these numbers are, and are not

- All figures are means over 8 random seeds, with standard deviation.
- Range measurements use Gaussian noise calibrated to published UWB accuracy (~10 cm). They are modelled, not measured from hardware.
- Dead-reckoning drift is modelled as fixed per-drone bias plus a random walk. Magnitudes are tuned, not taken from a specific IMU.
- Perception in these runs is a proximity model, not YOLO inference. Detection accuracy is reported separately from the perception module.
- All drones run in one process, so bids do not yet cross a physical radio.