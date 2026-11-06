"""Protocol §32 (D173): the market band (pink) around the value band (blue).

Usage: PYTHONPATH=. python scripts/band_test.py <phase R rows csv> <sales csv> [after=2026-10-31]
The rows come from scripts/real_phase_r.py with PHASE_R_ROWS (one line per scored sale, estimate made before it).
For each era (and Japan), week by week, using only earlier weeks:
  z = (log price - estimate with venue offset) / s_pred
  v_e = exponential mean of z^2 (half-life 4 weeks); v0_e = mean of z^2 over the era's history; f_e = sqrt(max(1, v_e/v0_e))
  c (one for the whole market): c <- c * exp(0.5 * (share outside the pink band last week - 0.20)), within 0.8-3
  pink band = estimate +- 1.2816 * s_pred * f_e * c; "agitated market" when f_e >= 1.5.
Writes results/bands/summary.json and prints V1-V4.
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

from slabwise.series import series_of

HALF, GAMMA, CLO, CHI, ALARM, Z = 4.0, 0.5, 0.8, 3.0, 1.5, 1.2816
PER_ERA = "--per-era" in sys.argv                         # §33 (D175): one correction multiplier per era
rows = pd.read_csv(sys.argv[1])
raw = pd.read_csv(sys.argv[2], low_memory=False)
after = next((a for a in sys.argv[3:] if not a.startswith("--")), "2026-10-31")
t0 = pd.to_datetime(raw["date"], utc=True, format="mixed").min().normalize()
wk_after = int((pd.Timestamp(after, tz="UTC") - t0).days // 7)
rows["era"] = rows["card"].astype(str).map(lambda c: "Giappone" if c.startswith("ja:") else series_of(c.split("/")[0]))
rows["z"] = (rows["y"] - rows["lvm_adj"]) / rows["s_pred"]
lam = 0.5 ** (1 / HALF)

ewma, tot, cnt = {}, defaultdict(float), defaultdict(int)
c = 1.0
ce = defaultdict(lambda: 1.0)
out = []
for w, g in rows.sort_values("week").groupby("week"):
    f = {}
    for e in g["era"].unique():
        v0 = tot[e] / cnt[e] if cnt[e] else None
        f[e] = float(np.sqrt(max(1.0, ewma[e] / v0))) if v0 and e in ewma else 1.0
    fe = g["era"].map(f).to_numpy()
    cc = np.array([ce[e] for e in g["era"]]) if PER_ERA else np.full(len(g), c)
    inside_pink = np.abs(g["z"].to_numpy()) <= Z * fe * cc
    inside_now = np.abs(g["z"].to_numpy()) <= Z
    for k, e in enumerate(g["era"].to_numpy()):
        out.append((w, e, bool(inside_pink[k]), bool(inside_now[k]), f[e], float(cc[k])))
    miss = 1 - inside_pink.mean()                     # after scoring this week: update for the next one
    c = float(min(CHI, max(CLO, c * np.exp(GAMMA * (miss - 0.20)))))
    for e in g["era"].unique():
        m_e = 1 - inside_pink[(g["era"] == e).to_numpy()].mean()
        ce[e] = float(min(CHI, max(CLO, ce[e] * np.exp(GAMMA * (m_e - 0.20)))))
    for e, ge in g.groupby("era"):
        m = float(np.mean(ge["z"] ** 2))
        ewma[e] = lam * ewma[e] + (1 - lam) * m if e in ewma else m
        tot[e] += float(np.sum(ge["z"] ** 2)); cnt[e] += len(ge)

o = pd.DataFrame(out, columns=["week", "era", "pink", "now", "f", "c"])
late = o[o.week >= wk_after]
calm = o[o.f <= 1.1]
res = dict(n=len(o), n_after=len(late),
           V1=float(late.pink.mean()), V2=float(o.pink.mean()),
           V3={e: float(g.pink.mean()) for e, g in o.groupby("era")},
           V4=float(np.median(calm.f * calm.c)) if len(calm) else None,
           today_band=dict(all=float(o.now.mean()), after=float(late.now.mean())),
           alarm_share=float(o.groupby(["week", "era"]).f.first().ge(ALARM).mean()),
           alarm_share_after=float(late.groupby(["week", "era"]).f.first().ge(ALARM).mean()) if len(late) else None,
           c_last=float(o.c.iloc[-1]), f_last={e: float(g.f.iloc[-1]) for e, g in o.groupby("era")})
res["passed"] = dict(V1=0.75 <= res["V1"] <= 0.85, V2=0.75 <= res["V2"] <= 0.85,
                     V3=all(0.70 <= v <= 0.90 for v in res["V3"].values()), V4=res["V4"] is not None and res["V4"] <= 1.10)
res["c_last_era"] = {e: float(g.c.iloc[-1]) for e, g in o.groupby("era")}
os.makedirs("results/bands", exist_ok=True)
json.dump(res, open("results/bands/summary" + ("_per_era" if PER_ERA else "") + ".json", "w"), indent=1)
print(json.dumps(res, indent=1))
