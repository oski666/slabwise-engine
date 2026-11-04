"""Large simulated panel (protocol §18, D92): calibration + backtest of the adopted method on one seed.

Usage: PYTHONPATH=. python scripts/run_panel.py <seed> [base|alt] -> results/panel/v1.10/seed<seed>[_alt].json
Later versions rerun the same seeds with the parameters saved here (paired comparison seed by seed).
"""
import json
import os
import sys
from dataclasses import asdict

from slabwise.backtest import metrics, run, tier_metrics
from slabwise.calibrate import calibrate
from slabwise.sim import SimConfig, simulate

seed = int(sys.argv[1])
scenario = sys.argv[2] if len(sys.argv) > 2 else "base"
extra = dict(spike_share=0.30, sale_noise=0.13, era_mislabel=0.30) if scenario == "alt" else {}
m = simulate(SimConfig(seed=seed, contamination=0.15, **extra))
p, _, _ = calibrate(m, verbose=False)
res = run(m, "A", p)
out = metrics(res)
out["params"] = asdict(p)
out["seed"], out["contamination"], out["mode"], out["scenario"] = seed, 0.15, "A", scenario
out["TIERS"] = tier_metrics(res)
os.makedirs("results/panel/v1.10", exist_ok=True)
tag = "" if scenario == "base" else "_alt"
json.dump(out, open(f"results/panel/v1.10/seed{seed}{tag}.json", "w"), indent=1, ensure_ascii=False)
print(seed, scenario, "EV", round(out["EV"]["Slabwise LVM"], 4), "CA", round(out["CA"], 3), flush=True)
