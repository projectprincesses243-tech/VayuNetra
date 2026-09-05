# VayuNetra — Measured Results

Generated 2026-09-05 08:14  

Seeds per condition: 8  |  Reproduce with `python experiments.py`


## A — Swarm vs single drone

| Drones | Survivors rescued (of 5) | Coverage % | Ticks |
|---|---|---|---|
| 1 | 0.88 ± 0.83 | 16.25 ± 14.08 | 499 |
| 3 | 2 ± 1.2 | 30.75 ± 11.42 | 499 |
| 6 | 2.62 ± 1.69 | 49.0 ± 10.54 | 426 |

## B — GPS-denied localization

| Condition | Mean position error (m) | Range |
|---|---|---|
| Ranging ON | 2.61 ± 0.67 | 1.39 – 3.33 |
| Ranging OFF | 23.74 ± 5.62 | 13.97 – 30.82 |

**Improvement: 9.1x**


## C — GPS denial causes mission failure

| Condition | Survivors rescued (of 5) |
|---|---|
| With ranging | 2.62 ± 1.69 |
| Without ranging | 2.25 ± 1.39 |

Same detections in both cases. Without ranging, drones accept tasks but navigate on a drifted belief and fail to arrive.


## D — Failure recovery

| Condition | Rescued | Auctions run |
|---|---|---|
| No failure | 2.62 | 2.88 |
| One drone lost mid-task | 2.12 | 3.38 |

Kill timed to catch a drone carrying a task. Extra auctions are re-auctions of the released task. Recovery requires no central coordinator.


## E — Graceful degradation

| Fleet size | Rescued (of 5) | Coverage % |
|---|---|---|
| 6 | 2.62 ± 1.69 | 49.0 |
| 5 | 3.12 ± 1.36 | 46.12 |
| 4 | 2.88 ± 1.36 | 39.12 |
| 3 | 2 ± 1.2 | 30.75 |
| 2 | 1.25 ± 1.04 | 23.25 |

## What these numbers are, and are not

- All figures are means over 8 random seeds, with standard deviation.
- Range measurements use Gaussian noise calibrated to published UWB accuracy (~10 cm). They are modelled, not measured from hardware.
- Dead-reckoning drift is modelled as fixed per-drone bias plus a random walk. Magnitudes are tuned, not taken from a specific IMU.
- Perception in these runs is a proximity model, not YOLO inference. Detection accuracy is reported separately from the perception module.
- All drones run in one process, so bids do not yet cross a physical radio.