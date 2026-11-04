"""Protocol §20 (D101): rerun one v1.10 job with v1.14, the same calibrated parameters plus the step prior informed by PSA populations.

Usage: PYTHONPATH=. python scripts/run_v114.py results/v1.10/<job>.json -> results/v1.14/<job>.json
"""
import json
import os
import sys

from slabwise.backtest import metrics, run, tier_metrics
from slabwise.model import LVMParams
from slabwise.sim import SimConfig, simulate

src = sys.argv[1]
old = json.load(open(src))
extra = dict(spike_share=0.30, sale_noise=0.13, era_mislabel=0.30) if old["scenario"] == "alt" else {}
m = simulate(SimConfig(seed=old["seed"], contamination=old["contamination"], **extra))
p = LVMParams(**{**old["params"], "grade_keep": 15, "step_prior": True, "pop_steps": True})
res = run(m, old["mode"], p)
out = metrics(res)
out["params"] = dict(p.__dict__)
out["steps"] = res.model._step_cache
out["seed"], out["contamination"], out["mode"], out["scenario"] = old["seed"], old["contamination"], old["mode"], old["scenario"]
out["bounded"] = res.model.n_bounded
out["TIERS"] = tier_metrics(res)
json.dump(out, open(os.path.join("results", "v1.14", os.path.basename(src)), "w"), indent=1, ensure_ascii=False)
print(os.path.basename(src), "EV", round(out["EV"]["Slabwise LVM"], 4), "CA", round(out["CA"], 3), flush=True)
