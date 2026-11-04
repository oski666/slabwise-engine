"""Protocol section 9b (D53): rerun one v1.5 job with the hierarchical venue gaps (v1.6b), using the calibrated
parameters stored in the v1.5 result of the same job. Adds V4: the auction gap learnt vs the simulator's.

Usage: PYTHONPATH=. python scripts/run_v16.py <v1.5 result json>   -> results/<same name>
"""
import json
import os
import sys

import numpy as np

from slabwise.backtest import metrics, run, tier_metrics
from slabwise.model import LVMParams
from slabwise.sim import SimConfig, simulate

src = sys.argv[1]
old = json.load(open(src))
extra = dict(spike_share=0.30, sale_noise=0.13, era_mislabel=0.30) if old["scenario"] == "alt" else {}
cfg = SimConfig(seed=old["seed"], contamination=old["contamination"], **extra)
m = simulate(cfg)
p = LVMParams(**old["params"])
res = run(m, old["mode"], p)
out = metrics(res)
out["params"] = old["params"]
out["seed"], out["contamination"], out["mode"], out["scenario"] = old["seed"], old["contamination"], old["mode"], old["scenario"]
out["TIERS"] = tier_metrics(res)
out["V4"] = {"auction_gap": float(res.model.offs[1]), "auction_spread": float(res.model.s_venue[1]),
             "sim_auction_gap": float(cfg.auction_premium + cfg.copy_quality * np.sqrt(2 / np.pi))}
json.dump(out, open(os.path.join("results", os.path.basename(src)), "w"), indent=1, ensure_ascii=False)
print(os.path.basename(src), "EV", round(out["EV"]["Slabwise LVM"], 4), "CA", round(out["CA"], 3), json.dumps(out["V4"]))
