"""Phase R (protocol section 12, D55): next-sale error on the real sales, LVM against the competitors' rules.

Usage: PYTHONPATH=. python scripts/real_phase_r.py data/raw/sales_all.csv data/raw/era_map.json results/real/phase_r.json

Same calibration as the site (first max(26, W/3) weeks). For every clean sale in a week after calibration,
each method's estimate for that card and grade at the end of the previous week is compared with the price
(log). Only sales every method can estimate are used. Liquidity bucket of a sale: sales of its card in the
previous 52 weeks (>= 26, 6-25, <= 5).
"""
import json
import os
import sys

import numpy as np

from slabwise.baselines import (CardLadderIndexed, LastSale, PriceChartingAgeWeighted, SlabwiseV0,
                                TCGChartsTiered)
from slabwise.calibrate import calibrate_clean
from slabwise.identity import identity_layer
from slabwise.model import VENUES, LatentValueModel
from slabwise.schema import GRADE_INDEX
from slabwise.sources.csv_sales import era_of, load_sales_csv

path, era_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
sales, cards = load_sales_csv(path)
era_map = json.load(open(era_path))
eras = sorted(set(era_map.values()))
era = np.array([eras.index(era_of(c, era_map)) for c in cards])
clean, removed = identity_layer(sales, None, verify_certs=False)
C, E = len(cards), len(eras)
W = int(clean["week"].max()) + 1
train = max(26, W // 3)
params, _, _log = calibrate_clean(clean, C, era, E, train, trend=False, coverage="--coverage" in sys.argv)   # v1.11 test (§16)
print("coverage fit", [x[0] for x in _log if "coverage_k" in x[0]], flush=True)
ADOPTED = "--adopted" in sys.argv                     # D110: the engine the site uses (LVMParams defaults)
if "--v116" in sys.argv:                              # v1.16 test (protocol §25, D128)
    params.cov_halflife = 13.0
if "--v118" in sys.argv:                              # v1.18 test (protocol §34, D177)
    params.era_noise = True
if "--v117" in sys.argv:                              # v1.17 test (protocol §30, D155)
    params.jump = True
if "--v114" in sys.argv:                              # the engine before v1.15 (protocol §22, D124)
    params.step_t, params.variant_pops = 0.0, False
if not ADOPTED:
    params.gap_start = "--gap_start" in sys.argv          # v1.8 (D67, protocol §13 C4)
    params.venue_gaps = "--venue_gaps" in sys.argv        # v1.9 test (protocol §14)
    params.grade_keep = 15 if "--grade_keep" in sys.argv else 0   # v1.10 test (protocol §15)
    params.vol_halflife = 13.0 if "--vol" in sys.argv else 0.0       # v1.12 test (protocol §17)
    params.variant_gaps = "--variant_gaps" in sys.argv            # v1.13 test (protocol §19)
    params.step_prior = "--steps" in sys.argv or "--pops" in sys.argv   # v1.14 test (protocol §20)
    params.pop_steps = "--pops" in sys.argv
    params.step_t, params.variant_pops = (4.0, True) if "--t_steps" in sys.argv else (0.0, False)   # v1.15 test (§22)
for a_ in sys.argv[4:]:                               # diagnostics only: force calibrated parameters (D69)
    if a_.startswith("--set="):
        for kv in a_[6:].split(","):
            k, v = kv.split(":")
            setattr(params, k, float(v))
print("params", {k: (round(v, 5) if isinstance(v, float) else v) for k, v in params.__dict__.items()}, "W", W, "train", train, flush=True)
lvm = LatentValueModel(C, era, E, params)
lvm.set_parents([cards.index(c.split("/")[0]) if "/" in c and c.split("/")[0] in cards else -1 for c in cards])
if params.pop_steps:                                       # v1.14: PSA populations from tcgcharts (D76), base printings only
    _tc = json.load(open("data/raw/tcgcharts/cards.json"))
    lvm.set_pops([[float((_tc.get(c, {}).get("pop") or {}).get(str(g)) or np.nan) for g in (10, 9, 8, 7)] for c in cards])
models = [cls(C, era, E) for cls in (LastSale, TCGChartsTiered, PriceChartingAgeWeighted, CardLadderIndexed, SlabwiseV0)] + [lvm]
names = [m.name for m in models]
groups = {w: g for w, g in clean.groupby("week")}
empty = clean.iloc[:0]
weekly_card = np.zeros((W, C))
for (w, c), n in clean.groupby(["week", "card"]).size().items():
    weekly_card[int(w), int(c)] = n
row_keys = []
rows = []                     # (bucket, price log, {name: estimate}, lvm sd, venue)
prev, prev_off, prev_kappa = {}, np.zeros(len(VENUES)), 1.0
prev_ke = np.ones(E)                                  # v1.18: the per-era noise factors known at that time
for w in range(W):
    g = groups.get(w, empty)
    if w > train and len(g) and prev:
        for _, s in g.iterrows():
            c, gi = int(s["card"]), GRADE_INDEX[int(s["grade"])]
            ests = {n: prev[n][0][c, gi] for n in names}
            if all(np.isfinite(v) for v in ests.values()):
                n52 = weekly_card[max(0, w - 52):w, c].sum()
                bucket = "alta (≥26)" if n52 >= 26 else "media (6-25)" if n52 >= 6 else "bassa (≤5)"
                row_keys.append((cards[c], int(s["grade"]), s.get("item_id", "")))
                rows.append((bucket, float(np.log(s["price"])), ests, float(prev[lvm.name][1][c, gi]), s["venue"],
                             float(prev_off[VENUES.index(s["venue"])] if s["venue"] in VENUES else 0.0),
                             prev_kappa * (float(prev_ke[era[c]]) if params.era_noise else 1.0), w))
    for m in models:
        m.ingest(w, g)
    prev = {}
    for m in models:
        if m is lvm:
            mean, sd = lvm.estimates_with_sd(w)
            prev[m.name] = (mean, sd)
            prev_off = lvm.offs.copy()                # the model's venue offsets known at that time (D69)
            prev_kappa = lvm.kappa                    # v1.12: the noise factor known at that time
            prev_ke = lvm.kappa_e.copy()
        else:
            prev[m.name] = (m.estimates(w), None)

y = np.array([r[1] for r in rows])
err = {n: np.abs(np.array([r[2][n] for r in rows]) - y) for n in names}
buckets = sorted({r[0] for r in rows})
res = {"n_sales": len(rows), "train_weeks": train, "weeks": W, "methods": names,
       "ES": {n: float(np.median(err[n])) for n in names},
       "ES_bucket": {b: {"n": int(sum(r[0] == b for r in rows)),
                         **{n: float(np.median(err[n][[r[0] == b for r in rows]])) for n in names}} for b in buckets}}
venues_ = sorted({r[4] for r in rows})                 # reported only: error by venue of the sale
res["ES_venue"] = {v: {"n": int(sum(r[4] == v for r in rows)),
                       **{n: float(np.median(err[n][[r[4] == v for r in rows]])) for n in names}} for v in venues_}
print("offs", [round(float(x), 4) for x in lvm.offs], flush=True)
# reported only (D69): the LVM value is an eBay copy; its own forecast of a sale in another venue adds that venue's offset
adj = np.abs(np.array([r[2][lvm.name] + r[5] for r in rows]) - y)
res["ES_lvm_venue_adjusted"] = float(np.median(adj))
res["ES_venue_adjusted"] = {v: float(np.median(adj[[r[4] == v for r in rows]])) for v in venues_}
comp = [n for n in names if n != lvm.name]
L = lvm.name
res["R2"] = {"passed": bool(all(res["ES"][L] < res["ES"][n] for n in comp)),
             "best_competitor": min(comp, key=lambda n: res["ES"][n])}
res["R3"] = {b: {"lvm": res["ES_bucket"][b][L], "best": min(res["ES_bucket"][b][n] for n in comp),
                 "passed": bool(res["ES_bucket"][b][L] <= 1.05 * min(res["ES_bucket"][b][n] for n in comp))} for b in buckets}
res["R3_passed"] = bool(all(v["passed"] for v in res["R3"].values()))
noise = np.array([params.sigma_a if r[4] == "auction" else params.sigma_e for r in rows])
kap = np.array([r[6] for r in rows])
band = 1.2816 * np.sqrt(np.array([r[3] for r in rows]) ** 2 + (noise ** 2 + params.sigma_q ** 2) * kap)
res["R4_coverage"] = float(np.mean(err[L] <= band))
if os.environ.get("PHASE_R_AFTER"):                    # protocol §25 K6: coverage on a held-out recent period only
    import pandas as _pd
    _raw = _pd.read_csv(path)
    _t0 = _pd.to_datetime(_raw["date"], utc=True, format="mixed").min().normalize()
    _wk = int((_pd.Timestamp(os.environ["PHASE_R_AFTER"], tz="UTC") - _t0).days // 7)
    _sel = np.array([r[7] for r in rows]) >= _wk
    res["R4_after"] = {"from": os.environ["PHASE_R_AFTER"], "n": int(_sel.sum()), "coverage": float(np.mean((err[L] <= band)[_sel]))}
# reported only (protocol §17): quarter by quarter (13-week blocks), LVM vs best competitor, and coverage
wk = np.array([r[7] for r in rows])
res["quarters"] = []
for q0 in range(int(wk.min()), int(wk.max()) + 1, 13):
    sel = (wk >= q0) & (wk < q0 + 13)
    if sel.sum() >= 100:
        res["quarters"].append({"week": q0, "n": int(sel.sum()), "lvm": float(np.median(err[L][sel])),
                                "best": float(min(np.median(err[n][sel]) for n in comp)), "coverage": float(np.mean((err[L] <= band)[sel])),
                                "kappa": float(np.mean(kap[sel]))})
if os.environ.get("PHASE_R_ROWS"):                     # diagnostics only: one line per scored sale
    import csv as _csv
    with open(os.environ["PHASE_R_ROWS"], "w", newline="") as fh:
        wr = _csv.writer(fh)
        wr.writerow(["bucket", "card", "grade", "item_id", "week", "venue", "y", "lvm", "lvm_adj", "sd", "s_pred"] + comp)
        for r, (cc, gg, ii), b_ in zip(rows, row_keys, band):     # s_pred: the R4 band / 1.2816 (protocol §32)
            wr.writerow([r[0], cc, gg, ii, r[7], r[4], round(r[1], 4), round(r[2][L], 4), round(r[2][L] + r[5], 4), round(r[3], 4),
                         round(float(b_) / 1.2816, 5)] + [round(r[2][n], 4) for n in comp])
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: res[k] for k in ("n_sales", "ES", "R2", "R3", "R3_passed", "R4_coverage", "R4_after") if k in res}, indent=1, ensure_ascii=False))
