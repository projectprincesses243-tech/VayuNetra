# VayuNetra — Measured Results

Generated 2026-09-04 08:23  

Seeds per condition: 8  |  Reproduce with `python experiments.py`


## A — Swarm vs single drone

| Drones | Survivors rescued (of 5) | Coverage % | Ticks |
|---|---|---|---|
| 1 | 0.12 ± 0.35 | 17.75 ± 11.68 | 499 |
| 3 | 0.25 ± 0.46 | 33.0 ± 12.19 | 499 |
| 6 | 0.5 ± 0.76 | 49.88 ± 10.59 | 499 |

## B — GPS-denied localization

| Condition | Mean position error (m) | Range |
|---|---|---|
| Ranging ON | 8.82 ± 0.0 | 8.82 – 8.82 |
| Ranging OFF | 85.18 ± 3.62 | 79.56 – 88.18 |

**Improvement: 9.7x**


## C — GPS denial causes mission failure

| Condition | Survivors rescued (of 5) |
|---|---|
| With ranging | 0.5 ± 0.76 |
| Without ranging | 0.38 ± 0.74 |

Same detections in both cases. Without ranging, drones accept tasks but navigate on a drifted belief and fail to arrive.


## D — Failure recovery

| Condition | Rescued | Auctions run |
|---|---|---|
| No failure | 0.5 | 0.5 |
| One drone lost mid-task | 0.5 | 0.75 |

Kill timed to catch a drone carrying a task. Extra auctions are re-auctions of the released task. Recovery requires no central coordinator.


## E — Graceful degradation

| Fleet size | Rescued (of 5) | Coverage % |
|---|---|---|
| 6 | 0.5 ± 0.76 | 49.88 |
| 5 | 0.75 ± 1.04 | 45.12 |
| 4 | 0.38 ± 0.52 | 41.5 |
| 3 | 0.25 ± 0.46 | 33.0 |
| 2 | 0.25 ± 0.46 | 25.5 |

## What these numbers are, and are not

- All figures are means over 8 random seeds, with standard deviation.
- Range measurements use Gaussian noise calibrated to published UWB accuracy (~10 cm). They are modelled, not measured from hardware.
- Dead-reckoning drift is modelled as fixed per-drone bias plus a random walk. Magnitudes are tuned, not taken from a specific IMU.
- Perception in these runs is a proximity model, not YOLO inference. Detection accuracy is reported separately from the perception module.
- All drones run in one process, so bids do not yet cross a physical radio.