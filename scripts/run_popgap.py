"""Protocol §20 L7 (D101): "useful populations" market (pop_gap 0.3) for one panel seed, v1.10 or v1.14 with the
parameters calibrated for that seed in the v1.10 panel.

Usage: PYTHONPATH=. python scripts/run_popgap.py <seed> <v1.10|v1.14> -> results/v1.14/popgap/seed<seed>_<version>.json
"""
import json
import os
import sys

from slabwise.backtest import metrics, run
from slabwise.model import LVMParams
from slabwise.sim import SimConfig, simulate

seed, ver = int(sys.argv[1]), sys.argv[2]
base = json.load(open(f"results/panel/v1.10/seed{seed}.json"))
m = simulate(SimConfig(seed=seed, contamination=0.15, pop_gap=0.3))
p = LVMParams(**{**base["params"], "step_prior": ver == "v1.14", "pop_steps": ver == "v1.14"})
res = run(m, "A", p)
out = metrics(res)
out["seed"], out["version"] = seed, ver
os.makedirs("results/v1.14/popgap", exist_ok=True)
json.dump(out, open(f"results/v1.14/popgap/seed{seed}_{ver}.json", "w"), indent=1, ensure_ascii=False)
print(seed, ver, "EV", round(out["EV"]["Slabwise LVM"], 4), "CA", round(out["CA"], 3), flush=True)
