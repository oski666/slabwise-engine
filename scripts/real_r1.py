"""Protocol §10 R1 on real sales: card-grades with >= 2 sales all judged anomalous (p genuine < 0.5).

Usage: PYTHONPATH=. python scripts/real_r1.py <sales.csv> data/raw/era_map.json [--gap_start]
Same steps as prototype/build_real_data.py (identity layer, calibration of v1.2 parameters, weekly run).
"""
import json
import sys
from collections import defaultdict

import numpy as np

from slabwise.calibrate import calibrate_clean
from slabwise.identity import identity_layer
from slabwise.model import LatentValueModel
from slabwise.schema import GRADES
from slabwise.sources.csv_sales import era_of, load_sales_csv

path, era_path = sys.argv[1], sys.argv[2]
sales, cards = load_sales_csv(path)
era_map = json.load(open(era_path))
eras = sorted(set(era_map.values()) | {era_of(c, era_map) for c in cards})   # eras known only by prefix too (D117)
era = np.array([eras.index(era_of(c, era_map)) for c in cards])
clean, _ = identity_layer(sales, None, verify_certs=False)
W = int(clean["week"].max()) + 1
params, _, _ = calibrate_clean(clean, len(cards), era, len(eras), max(26, W // 3), trend=False, coverage="--coverage" in sys.argv)   # v1.11 test (§16)
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
    params.gap_start = "--gap_start" in sys.argv
    params.venue_gaps = "--venue_gaps" in sys.argv          # v1.9 test (protocol §14)
    params.grade_keep = 15 if "--grade_keep" in sys.argv else 0   # v1.10 test (protocol §15)
    params.vol_halflife = 13.0 if "--vol" in sys.argv else 0.0       # v1.12 test (protocol §17)
    params.variant_gaps = "--variant_gaps" in sys.argv            # v1.13 test (protocol §19)
    params.step_prior = "--steps" in sys.argv or "--pops" in sys.argv   # v1.14 test (protocol §20)
    params.pop_steps = "--pops" in sys.argv
    params.step_t, params.variant_pops = (4.0, True) if "--t_steps" in sys.argv else (0.0, False)   # v1.15 test (§22)
lvm = LatentValueModel(len(cards), era, len(eras), params)
lvm.set_parents([cards.index(c.split("/")[0]) if "/" in c and c.split("/")[0] in cards else -1 for c in cards])
if params.pop_steps:                                       # v1.14: PSA populations from tcgcharts (D76), base printings only
    _tc = json.load(open("data/raw/tcgcharts/cards.json"))
    lvm.set_pops([[float((_tc.get(c, {}).get("pop") or {}).get(str(g)) or np.nan) for g in (10, 9, 8, 7)] for c in cards])
groups = {w: g for w, g in clean.groupby("week")}
for w in range(W):
    lvm.ingest(w, groups.get(w, clean.iloc[:0]))
bad, n = [], 0
for i, c in enumerate(cards):
    if lvm.fit[i] is None:
        continue
    by = defaultdict(list)
    for o, p_ in zip(lvm.obs[i], lvm.fit[i]["pgen"]):
        by[GRADES[o["g"]]].append(p_)
    for g, v in by.items():
        n += 1
        if len(v) >= 2 and all(x < 0.5 for x in v):
            bad.append((c, g, len(v)))
est = lvm.estimates(W - 1)
# E2 (protocol §15): grades with >= 5 sales in the last 90 days whose value is > 0.5 log from their median
import pandas as pd
raw = pd.read_csv(path)
raw = raw[raw["excluded"].isna() | (raw["excluded"] == "")]
raw["d"] = pd.to_datetime(raw["date"], utc=True, format="mixed")
rec = raw[raw["d"] >= raw["d"].max() - pd.Timedelta(days=90)].groupby(["card", "grade"])["price_usd"].agg(["count", "median"])
far = []
for (cc, g), row in rec.iterrows():
    if row["count"] >= 5 and cc in cards:
        v = est[cards.index(cc), GRADES.index(int(g))]
        if np.isfinite(v) and abs(v - np.log(row["median"])) > 0.5:
            far.append((cc, int(g), int(row["count"]), round(float(row["median"])), round(float(np.exp(v)))))
print(f"E2: {len(far)} voci lontane dalle proprie vendite: {far}")
# E2r (protocol §23, D125): same rule against the recent sales (30 days if >= 5, else the last 5 of the grade)
last = raw[raw["d"] >= raw["d"].max() - pd.Timedelta(days=90)].sort_values("d")
far_r = []
for (cc, g), grp in last.groupby(["card", "grade"]):
    if len(grp) < 5 or cc not in cards:
        continue
    r30 = grp[grp["d"] >= raw["d"].max() - pd.Timedelta(days=30)]
    ref = float((r30 if len(r30) >= 5 else grp.tail(5))["price_usd"].median())
    v = est[cards.index(cc), GRADES.index(int(g))]
    if np.isfinite(v) and abs(v - np.log(ref)) > 0.5:
        far_r.append((cc, int(g), int(len(grp)), round(ref), round(float(np.exp(v)))))
print(f"E2r: {len(far_r)} voci lontane dalle vendite recenti: {far_r}")
print(f"auction offset {lvm.offs[1]:.3f}")
print(f"gap_start={params.gap_start} venue_gaps={params.venue_gaps} R1: {len(bad)} voci su {n}: {bad}")
