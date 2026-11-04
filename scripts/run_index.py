"""v1.4 (D38, protocol section 7): published era index on one simulated seed.

Usage: PYTHONPATH=. python scripts/run_index.py SEED
Uses the v1.2 parameters already calibrated for that seed (results/v1.2/seedN_c15_A.json),
runs the LVM week by week with the index and writes results/index_seedN.json.
"""
import json
import sys

import numpy as np

from slabwise.identity import identity_layer, sim_cert_lookup
from slabwise.index import EraIndex
from slabwise.model import LatentValueModel, LVMParams
from slabwise.sim import ERAS, SimConfig, simulate

seed = int(sys.argv[1])
p = LVMParams(**json.load(open(f"results/v1.2/seed{seed}_c15_A.json"))["params"])
m = simulate(SimConfig(seed=seed, contamination=0.15))
clean, _ = identity_layer(m.sales, sim_cert_lookup(m.sales))
W = m.cfg.weeks
lvm = LatentValueModel(m.cfg.n_cards, m.era_obs, len(ERAS), p)
ONE = "--one" in sys.argv                              # D130 (protocol section 26): one grade per card
STR = "--strata" in sys.argv                           # D143 (protocol section 28): reserved seats per grade
idx = EraIndex(m.era_obs, len(ERAS), one_per_card=ONE, strata=2 if STR else 0)
groups = {w: g for w, g in clean.groupby("week")}
for w in range(W):
    lvm.ingest(w, groups.get(w, clean.iloc[:0]))
    idx.update(w, lvm, lvm.estimates(w))
res = {"seed": seed, "eras": {}}
for e, name in enumerate(ERAS):
    s = idx.series(e, W)
    ws = np.array([w for w in range(64, W) if np.isfinite(s[w]) and np.isfinite(s[w - 12])])
    if len(ws) < 10:
        res["eras"][name] = None
        continue
    est_d = s[ws] - s[ws - 12]
    tru_d = m.factor[e, ws] - m.factor[e, ws - 12]
    fac = np.array([lvm.F[e][w + 1] - lvm.F[e][w + 1 - 12] for w in ws])
    res["eras"][name] = dict(
        slope=float(np.sum(est_d * tru_d) / np.sum(tru_d ** 2)), corr=float(np.corrcoef(est_d, tru_d)[0, 1]),
        factor_slope=float(np.sum(fac * tru_d) / np.sum(tru_d ** 2)), factor_corr=float(np.corrcoef(fac, tru_d)[0, 1]),
        basket=len(idx.basket[e]), weeks=int(len(ws)),
        index=[round(float(x), 4) if np.isfinite(x) else None for x in s], truth=[round(float(x), 4) for x in m.factor[e]])
json.dump(res, open(f"results/index_seed{seed}{'_one' if ONE else ''}{'_strata' if STR else ''}.json", "w"))
print(seed, {k: (None if v is None else {kk: round(vv, 2) for kk, vv in v.items() if kk in ("slope", "corr", "factor_slope", "factor_corr", "basket")})
             for k, v in res["eras"].items()})
