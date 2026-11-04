"""Protocol §21 (D106): are the 80% forecast ranges at 4, 13 and 26 weeks honest on the real sales?

Usage: PYTHONPATH=. python scripts/forecast_check.py data/raw/sales_tc.csv data/raw/era_map.json results/real/forecast.json

Same set-up as phase R with the adopted engine. Each week w after calibration, every method's estimate is kept. A
sale in week t is compared with the forecast made d weeks earlier (w = t - d) for every d within h-2..h+2: the LVM's
80% range for horizon h (value of week w, variance grown by h weeks of drift plus sale and copy noise), and the
errors of the LVM, of the last sale and of the tcgcharts median made at w. Cluster bootstrap by card (§18).
"""
import json
import sys

import numpy as np

from slabwise.baselines import LastSale, TCGChartsTiered
from slabwise.calibrate import calibrate_clean
from slabwise.identity import identity_layer
from slabwise.model import LatentValueModel
from slabwise.schema import GRADE_INDEX
from slabwise.sources.csv_sales import era_of, load_sales_csv
from slabwise.stats import cluster_bootstrap_diff

path, era_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
H = (4, 13, 26)
sales, cards = load_sales_csv(path)
era_map = json.load(open(era_path))
eras = sorted(set(era_map.values()))
era = np.array([eras.index(era_of(c, era_map)) for c in cards])
clean, _ = identity_layer(sales, None, verify_certs=False)
C, E = len(cards), len(eras)
W = int(clean["week"].max()) + 1
train = max(26, W // 3)
params, _, _ = calibrate_clean(clean, C, era, E, train, trend=False)
lvm = LatentValueModel(C, era, E, params)
lvm.set_parents([cards.index(c.split("/")[0]) if "/" in c and c.split("/")[0] in cards else -1 for c in cards])
_tc = json.load(open("data/raw/tcgcharts/cards.json"))
lvm.set_pops([[float((_tc.get(c, {}).get("pop") or {}).get(str(g)) or np.nan) for g in (10, 9, 8, 7)] for c in cards])
comp = [LastSale(C, era, E), TCGChartsTiered(C, era, E)]
M = np.full((W, C, 4), np.nan); SD = M.copy(); FV = M.copy(); K = np.ones(W)
CM = {m.name: np.full((W, C, 4), np.nan) for m in comp}
groups = {w: g for w, g in clean.groupby("week")}
empty = clean.iloc[:0]
for w in range(W):
    g = groups.get(w, empty)
    lvm.ingest(w, g)
    for m in comp:
        m.ingest(w, g)
    if w >= train:
        M[w], SD[w] = lvm.estimates_with_sd(w)
        FV[w] = lvm.forecast_var_week()
        K[w] = getattr(lvm, "kappa", 1.0)
        for m in comp:
            CM[m.name][w] = m.estimates(w)
res = {"n_weeks": W, "train": train, "horizons": {}}
cl_all = np.array([c.split("/")[0] for c in cards])
for h in H:
    rows = []
    for t, g in groups.items():
        for _, s in g.iterrows():
            c, gi = int(s["card"]), GRADE_INDEX[int(s["grade"])]
            y = float(np.log(s["price"]))
            for d in range(h - 2, h + 3):
                w = t - d
                if w < train or not np.isfinite(M[w, c, gi]) or not all(np.isfinite(CM[n][w, c, gi]) for n in CM):
                    continue
                noise = (params.sigma_a if s["venue"] == "auction" else params.sigma_e) ** 2 + params.sigma_q ** 2
                band = 1.2816 * np.sqrt(SD[w, c, gi] ** 2 + h * FV[w, c, gi] + noise * K[w])
                rows.append((c, y, M[w, c, gi], band, *[CM[n][w, c, gi] for n in CM]))
    if not rows:
        continue
    a = np.array(rows, dtype=float)
    cl = cl_all[a[:, 0].astype(int)]
    e_l = np.abs(a[:, 2] - a[:, 1])
    r = {"pairs": len(a), "coverage": float(np.mean(e_l <= a[:, 3])), "width_median_pct": float(np.median(np.exp(a[:, 3]) - 1)),
         "error_lvm": float(np.median(e_l)), "vs": {}}
    for i, n in enumerate(CM):
        e_c = np.abs(a[:, 4 + i] - a[:, 1])
        d_, lo, hi, _ = cluster_bootstrap_diff(e_l, e_c, cl)
        r["vs"][n] = {"error": float(np.median(e_c)), "diff": d_, "ci": [lo, hi]}
    res["horizons"][str(h)] = r
    print(h, json.dumps(r, ensure_ascii=False), flush=True)
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
