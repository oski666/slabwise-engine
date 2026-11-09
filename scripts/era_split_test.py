"""Protocol §54 (D253): Contemporanea (C) against Sword & Shield (SS) and Scarlet & Violet with Mega (SV).

Usage: python scripts/era_split_test.py results/era_split/series.json [base week, default 2024-01-05]
  E1 correlation of the weekly log changes of SS and SV below 0.8
  E2 at the last rebalance SS and SV have at least 20 eligible items each
  E3 volatility of SS and of SV (last 26 weeks, x sqrt 52) at most 1.5 x that of C
  E4 no weekly change of SS or SV beyond +-15%
"""
import json
import os
import sys

import numpy as np

S = json.load(open(sys.argv[1]))
base = sys.argv[2] if len(sys.argv) > 2 else "2024-01-05"
wk = S["weeks"]
arr = lambda v: np.array([np.nan if x is None else x for x in v], float)   # noqa: E731
C, SS, SV = arr(S["C"]), arr(S["SS"]), arr(S["SV"])
ok = lambda w, *xs: all(np.isfinite(x[w]) and np.isfinite(x[w - 1]) for x in xs)   # noqa: E731
use = [w for w in range(1, len(wk)) if wk[w] >= base and ok(w, C, SS, SV)]
d = lambda x, ws: np.array([x[w] - x[w - 1] for w in ws])   # noqa: E731
corr = float(np.corrcoef(d(SS, use), d(SV, use))[0, 1])
last = [w for w in use if w >= len(wk) - 26]
vol = lambda x: float(np.std(d(x, last), ddof=1) * np.sqrt(52))   # noqa: E731
el = {}
for w_, dd in S["seats"]:
    for g, (e, st) in dd.items():
        el[g] = e
jump = max(float(np.max(np.abs(np.exp(d(x, use)) - 1))) for x in (SS, SV))
res = dict(weeks=len(use),
           E1=dict(passed=bool(corr < 0.8), corr=round(corr, 3)),
           E2=dict(passed=bool(min(el.values()) >= 20), eligible_last=el),
           E3=dict(passed=bool(max(vol(SS), vol(SV)) <= 1.5 * vol(C)), vol_C=round(vol(C), 4), vol_SS=round(vol(SS), 4), vol_SV=round(vol(SV), 4)),
           E4=dict(passed=bool(jump <= 0.15), max_weekly_change=round(jump, 4)),
           returns_13w_last=dict(C=round(float(C[-1] - C[-14]), 4), SS=round(float(SS[-1] - SS[-14]), 4), SV=round(float(SV[-1] - SV[-14]), 4)))
res["adopt"] = bool(all(res[k]["passed"] for k in ("E1", "E2", "E3", "E4")))
json.dump(res, open(os.path.join(os.path.dirname(sys.argv[1]), "summary.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
