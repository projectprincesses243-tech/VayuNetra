"""
VayuNetra evidence pack.

Runs five controlled experiments across multiple random seeds and writes
both a JSON file and a readable report.

Every number in the pitch must come from this file. Run it with:
    python experiments.py
"""

import sys, json, statistics, importlib
from datetime import datetime
sys.path.insert(0, ".")

SEEDS = [1, 7, 13, 21, 42, 99, 123, 256]


def fresh_mission(**kwargs):
    """
    Build a Mission with a clean event bus.

    BUS.reset() mutates the shared object in place, so every module that
    imported it stays pointed at the same live bus. Reloading modules
    instead would give sim.py a new bus while mission/ kept the old one -
    events would publish to one and be counted from the other.
    """
    from core.bus import BUS
    from sim import Mission
    BUS.reset()
    return Mission(**kwargs)


def run_once(seed, ranging_on=True, n_drones=6, kill_at=None, ticks=500):
    m = fresh_mission(n_drones=n_drones, n_survivors=5,
                      seed=seed, ranging_on=ranging_on)
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):     # silence per-tick prints
        result = m.run(ticks=ticks, kill_at=kill_at)
    return result


def summarise(runs, key):
    vals = [r[key] for r in runs]
    return {
        "mean": round(statistics.mean(vals), 2),
        "stdev": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0,
        "min": round(min(vals), 2),
        "max": round(max(vals), 2),
        "n": len(vals),
    }


def experiment_A():
    """Does the swarm beat a single drone?"""
    print("  A - swarm size ...", end="", flush=True)
    out = {}
    for n in (1, 3, 6):
        runs = [run_once(s, n_drones=n) for s in SEEDS]
        out[f"{n}_drones"] = {
            "rescued": summarise(runs, "rescued"),
            "coverage": summarise(runs, "coverage"),
            "ticks": summarise(runs, "ticks"),
        }
        print(f" {n}", end="", flush=True)
    print(" done")
    return out


def experiment_B():
    """Does inter-drone ranging fix GPS-denied localization?"""
    print("  B - localization ...", end="", flush=True)
    on = [run_once(s, ranging_on=True) for s in SEEDS]
    off = [run_once(s, ranging_on=False) for s in SEEDS]
    e_on = summarise(on, "mean_error")
    e_off = summarise(off, "mean_error")
    print(" done")
    return {
        "ranging_on": e_on,
        "ranging_off": e_off,
        "improvement_factor": round(e_off["mean"] / e_on["mean"], 1) if e_on["mean"] else None,
    }


def experiment_C():
    """Does GPS denial cause mission failure, not just position error?"""
    print("  C - mission impact ...", end="", flush=True)
    on = [run_once(s, ranging_on=True) for s in SEEDS]
    off = [run_once(s, ranging_on=False) for s in SEEDS]
    print(" done")
    return {
        "rescued_with_ranging": summarise(on, "rescued"),
        "rescued_without_ranging": summarise(off, "rescued"),
        "note": "Same detections in both cases. Without ranging, drones accept "
                "tasks but navigate on a drifted belief and fail to arrive.",
    }

def experiment_D():
    """Does the swarm recover when a drone carrying a task is lost?"""
    print("  D - failure recovery ...", end="", flush=True)
    baseline = [run_once(s) for s in SEEDS]

    # Try several kill times per seed and keep the first that actually
    # catches a drone en route. Killing an idle drone releases no task,
    # so it does not exercise re-auction at all.
    killed = []
    for s in SEEDS:
        for t in (5, 8, 12, 20, 30):
            r = run_once(s, kill_at=t)
            if r["lost"] > 0:
                killed.append(r)
                break
        else:
            killed.append(run_once(s, kill_at=5))

    print(" done")
    return {
        "no_failure": {"rescued": summarise(baseline, "rescued"),
                       "auctions": summarise(baseline, "auctions")},
        "one_drone_lost": {"rescued": summarise(killed, "rescued"),
                           "auctions": summarise(killed, "auctions"),
                           "drones_lost": summarise(killed, "lost")},
        "note": "Kill timed to catch a drone carrying a task. Extra auctions "
                "are re-auctions of the released task. Recovery requires no "
                "central coordinator.",
    }


def experiment_E():
    """How much of the fleet can be lost before the mission degrades?"""
    print("  E - degradation ...", end="", flush=True)
    out = {}
    for n in (6, 5, 4, 3, 2):
        runs = [run_once(s, n_drones=n) for s in SEEDS]
        out[f"{n}_drones"] = {
            "rescued": summarise(runs, "rescued"),
            "coverage": summarise(runs, "coverage"),
        }
        print(f" {n}", end="", flush=True)
    print(" done")
    return out


def write_report(data, path="EVIDENCE.md"):
    L = []
    L.append("# VayuNetra — Measured Results\n")
    L.append(f"Generated {data['generated']}  \n")
    L.append(f"Seeds per condition: {len(SEEDS)}  |  Reproduce with `python experiments.py`\n")

    a = data["A_swarm_size"]
    L.append("\n## A — Swarm vs single drone\n")
    L.append("| Drones | Survivors rescued (of 5) | Coverage % | Ticks |")
    L.append("|---|---|---|---|")
    for k in ("1_drones", "3_drones", "6_drones"):
        r = a[k]
        L.append(f"| {k.split('_')[0]} | {r['rescued']['mean']} ± {r['rescued']['stdev']} "
                 f"| {r['coverage']['mean']} ± {r['coverage']['stdev']} | {r['ticks']['mean']:.0f} |")

    b = data["B_localization"]
    L.append("\n## B — GPS-denied localization\n")
    L.append("| Condition | Mean position error (m) | Range |")
    L.append("|---|---|---|")
    L.append(f"| Ranging ON | {b['ranging_on']['mean']} ± {b['ranging_on']['stdev']} "
             f"| {b['ranging_on']['min']} – {b['ranging_on']['max']} |")
    L.append(f"| Ranging OFF | {b['ranging_off']['mean']} ± {b['ranging_off']['stdev']} "
             f"| {b['ranging_off']['min']} – {b['ranging_off']['max']} |")
    L.append(f"\n**Improvement: {b['improvement_factor']}x**\n")

    c = data["C_mission_impact"]
    L.append("\n## C — GPS denial causes mission failure\n")
    L.append("| Condition | Survivors rescued (of 5) |")
    L.append("|---|---|")
    L.append(f"| With ranging | {c['rescued_with_ranging']['mean']} ± {c['rescued_with_ranging']['stdev']} |")
    L.append(f"| Without ranging | {c['rescued_without_ranging']['mean']} ± {c['rescued_without_ranging']['stdev']} |")
    L.append(f"\n{c['note']}\n")

    d = data["D_failure_recovery"]
    L.append("\n## D — Failure recovery\n")
    L.append("| Condition | Rescued | Auctions run |")
    L.append("|---|---|---|")
    L.append(f"| No failure | {d['no_failure']['rescued']['mean']} | {d['no_failure']['auctions']['mean']} |")
    L.append(f"| One drone lost mid-task | {d['one_drone_lost']['rescued']['mean']} "
             f"| {d['one_drone_lost']['auctions']['mean']} |")
    L.append(f"\n{d['note']}\n")

    e = data["E_degradation"]
    L.append("\n## E — Graceful degradation\n")
    L.append("| Fleet size | Rescued (of 5) | Coverage % |")
    L.append("|---|---|---|")
    for k in ("6_drones", "5_drones", "4_drones", "3_drones", "2_drones"):
        r = e[k]
        L.append(f"| {k.split('_')[0]} | {r['rescued']['mean']} ± {r['rescued']['stdev']} "
                 f"| {r['coverage']['mean']} |")

    L.append("\n## What these numbers are, and are not\n")
    L.append("- All figures are means over 8 random seeds, with standard deviation.")
    L.append("- Range measurements use Gaussian noise calibrated to published UWB "
             "accuracy (~10 cm). They are modelled, not measured from hardware.")
    L.append("- Dead-reckoning drift is modelled as fixed per-drone bias plus a "
             "random walk. Magnitudes are tuned, not taken from a specific IMU.")
    L.append("- Perception in these runs is a proximity model, not YOLO inference. "
             "Detection accuracy is reported separately from the perception module.")
    L.append("- All drones run in one process, so bids do not yet cross a physical radio.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    print("\nRunning experiments. This takes a few minutes.\n")
    data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "seeds": SEEDS,
        "A_swarm_size": experiment_A(),
        "B_localization": experiment_B(),
        "C_mission_impact": experiment_C(),
        "D_failure_recovery": experiment_D(),
        "E_degradation": experiment_E(),
    }

    with open("evidence.json", "w") as f:
        json.dump(data, f, indent=2)
    write_report(data)

    b = data["B_localization"]
    c = data["C_mission_impact"]
    print("\n  " + "-" * 46)
    print(f"  Localization improvement : {b['improvement_factor']}x")
    print(f"  Rescued with ranging     : {c['rescued_with_ranging']['mean']} / 5")
    print(f"  Rescued without          : {c['rescued_without_ranging']['mean']} / 5")
    print("  " + "-" * 46)
    print("\n  Written: evidence.json, EVIDENCE.md\n")