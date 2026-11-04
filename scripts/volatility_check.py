"""Protocol §24 (D127): does past movement of the engine's weekly estimates say anything about later movement?

Usage: PYTHONPATH=. python scripts/volatility_check.py data/raw/sales_all.csv data/raw/era_map.json
"""
import json
import sys

import numpy as np
from scipy.stats import spearmanr

from slabwise.calibrate import calibrate_clean
from slabwise.identity import identity_layer
from slabwise.model import LatentValueModel
from slabwise.sources.csv_sales import era_of, load_sales_csv
from slabwise.volatility import moves, vol

path, era_path = sys.argv[1], sys.argv[2]
sales, cards = load_sales_csv(path)
era_map = json.load(open(era_path))
eras = sorted(set(era_map.values()) | {era_of(c, era_map) for c in cards})
era = np.array([eras.index(era_of(c, era_map)) for c in cards])
clean, _ = identity_layer(sales, None, verify_certs=False)
W = int(clean["week"].max()) + 1
params, _, _ = calibrate_clean(clean, len(cards), era, len(eras), max(26, W // 3), trend=False)
lvm = LatentValueModel(len(cards), era, len(eras), params)
lvm.set_parents([cards.index(c.split("/")[0]) if "/" in c and c.split("/")[0] in cards else -1 for c in cards])
_tc = json.load(open("data/raw/tcgcharts/cards.json"))
lvm.set_pops([[float((_tc.get(c, {}).get("pop") or {}).get(str(g)) or np.nan) for g in (10, 9, 8, 7)] for c in cards])
groups = {w: g for w, g in clean.groupby("week")}
est = np.full((W, len(cards), 4), np.nan)
sd = np.full((W, len(cards), 4), np.nan)
for w in range(W):
    lvm.ingest(w, groups.get(w, clean.iloc[:0]))
    est[w], sd[w] = lvm.estimates_with_sd(w)
LONG = "--long" in sys.argv                            # §24b: 13-week moves, 104 weeks of past
past, later, width, past_all = [], [], [], []
for c in range(len(cards)):
    for g in range(4):
        if LONG:
            a = est[max(0, W - 130):W - 26, c, g]
            pts = est[[W - 26, W - 13, W - 1], c, g]
            if np.isfinite(a).sum() >= 52 and np.isfinite(pts).all():
                past.append(vol(a, 13)); later.append(float(np.mean(np.abs(np.diff(pts)))))
            continue
        a, b = est[W - 78:W - 26, c, g], est[W - 26:, c, g]
        if np.isfinite(a).sum() >= 26 and np.isfinite(b).sum() >= 26:
            past.append(vol(a)); later.append(float(np.mean(np.abs(moves(b)))))
        cur = est[W - 52:, c, g]
        if np.isfinite(cur).sum() >= 26 and np.isfinite(sd[-1, c, g]):
            past_all.append(vol(cur)); width.append(float(sd[-1, c, g]))
past, later = np.array(past), np.array(later)
rho = spearmanr(past, later).statistic
lo, hi = np.quantile(past, [1 / 3, 2 / 3])
ratio = float(np.median(later[past >= hi]) / np.median(later[past <= lo]))
out = dict(n=len(past), V1_spearman=round(float(rho), 3), V1=bool(rho >= 0.30), V2_ratio=round(ratio, 2), V2=bool(ratio >= 1.5),
           V3_spearman_vol_width=round(float(spearmanr(past_all, width).statistic), 3) if width else None, n_V3=len(width))
print(json.dumps(out, indent=1))
