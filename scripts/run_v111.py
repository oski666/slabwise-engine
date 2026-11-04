"""Protocol §16 (D87): rerun one v1.10 job with v1.11, the same calibrated parameters plus the coverage factor on the
noises, chosen on the first 52 weeks of the same simulated market (the calibration weeks of the simulated protocol).

Usage: PYTHONPATH=. python scripts/run_v111.py results/v1.10/<job>.json -> results/v1.11/<job>.json
"""
import json
import os
import sys

from slabwise.backtest import metrics, run, tier_metrics
from slabwise.calibrate import coverage_fit
from slabwise.identity import identity_layer, sim_cert_lookup
from slabwise.model import LVMParams
from slabwise.sim import ERAS, SimConfig, simulate

src = sys.argv[1]
old = json.load(open(src))
extra = dict(spike_share=0.30, sale_noise=0.13, era_mislabel=0.30) if old["scenario"] == "alt" else {}
m = simulate(SimConfig(seed=old["seed"], contamination=old["contamination"], **extra))
p0 = LVMParams(**{**old["params"], "grade_keep": 15})
clean, _ = identity_layer(m.sales, sim_cert_lookup(m.sales))
p, k, cov = coverage_fit(clean, m.cfg.n_cards, m.era_obs, len(ERAS), p0, 52, 26)
res = run(m, old["mode"], p)
out = metrics(res)
out["params"] = dict(p.__dict__)
out["coverage_k"], out["coverage_calib"] = k, cov
out["seed"], out["contamination"], out["mode"], out["scenario"] = old["seed"], old["contamination"], old["mode"], old["scenario"]
out["bounded"] = res.model.n_bounded
out["TIERS"] = tier_metrics(res)
json.dump(out, open(os.path.join("results", "v1.11", os.path.basename(src)), "w"), indent=1, ensure_ascii=False)
print(os.path.basename(src), "k", k, "EV", round(out["EV"]["Slabwise LVM"], 4), "CA", round(out["CA"], 3), flush=True)
