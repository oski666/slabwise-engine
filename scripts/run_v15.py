"""Protocol section 8 (D47): rerun one v1.2 job with the roll-forward bound on, using the v1.2 calibrated
parameters of the same job, and add the confidence-tier metrics (T1/T2).

Usage: PYTHONPATH=. python scripts/run_v15.py <v1.2 result json> [bound]   -> results/<same name>
"""
import json
import os
import sys

from slabwise.backtest import metrics, run, tier_metrics
from slabwise.model import LVMParams
from slabwise.sim import SimConfig, simulate

src = sys.argv[1]
bound = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
old = json.load(open(src))
extra = dict(spike_share=0.30, sale_noise=0.13, era_mislabel=0.30) if old["scenario"] == "alt" else {}
m = simulate(SimConfig(seed=old["seed"], contamination=old["contamination"], **extra))
p = LVMParams(**{**old["params"], "roll_bound": bound})
res = run(m, old["mode"], p)
out = metrics(res)
out["params"] = {**old["params"], "roll_bound": bound}
out["seed"], out["contamination"], out["mode"], out["scenario"] = old["seed"], old["contamination"], old["mode"], old["scenario"]
out["bounded"] = res.model.n_bounded
out["TIERS"] = tier_metrics(res)
json.dump(out, open(os.path.join("results", os.path.basename(src)), "w"), indent=1, ensure_ascii=False)
print(os.path.basename(src), "EV", round(out["EV"]["Slabwise LVM"], 4), "bounded", out["bounded"], json.dumps(out["TIERS"]))
