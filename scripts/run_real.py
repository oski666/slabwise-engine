"""Phase R: backtest on real sales (pillar P14). Only the next-sale metric exists here.

Usage: PYTHONPATH=. python scripts/run_real.py sales.csv [era_map.json]
era_map.json maps catalogue card ids to an era name (e.g. {"swsh7-215": "sm_swsh"}).
"""
import json
import sys

import numpy as np

from slabwise.baselines import (CardLadderIndexed, LastSale, PriceChartingAgeWeighted, SlabwiseV0,
                                TCGChartsTiered)
from slabwise.calibrate import calibrate_clean
from slabwise.identity import identity_layer
from slabwise.model import LatentValueModel
from slabwise.schema import GRADE_INDEX
from slabwise.sources.csv_sales import load_sales_csv

sales, cards = load_sales_csv(sys.argv[1])
era_map = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
eras = sorted(set(era_map.values())) or ["all"]
era = np.array([eras.index(era_map[c]) if c in era_map else 0 for c in cards])
clean, removed = identity_layer(sales, None, verify_certs=False)
if clean["venue"].nunique() == 1:
    # the venue offset o_v is "auction minus eBay": with a single venue it has no reference and
    # drifts into the card levels (D27). All sales are treated as the same venue.
    clean["venue"] = "ebay"
    print("una sola sede di vendita: scarto delle aste non stimabile, disattivato")
print(f"vendite {len(sales)}, pulite {len(clean)}, rimosse {len(removed)}")
W = int(clean["week"].max()) + 1
train = max(26, W // 3)
params, score, _ = calibrate_clean(clean, len(cards), era, len(eras), train)
print("parametri", params)
models = [cls(len(cards), era, len(eras)) for cls in
          (LastSale, TCGChartsTiered, PriceChartingAgeWeighted, CardLadderIndexed, SlabwiseV0)]
models.append(LatentValueModel(len(cards), era, len(eras), params))
groups = {wk: g for wk, g in clean.groupby("week")}
empty = clean.iloc[:0]
errs = {m.name: [] for m in models}
prev = {m.name: None for m in models}
for w in range(W):
    g = groups.get(w, empty)
    if w > train and len(g):
        cc = g["card"].to_numpy().astype(int)
        gi = np.array([GRADE_INDEX[int(x)] for x in g["grade"]])
        lp = np.log(g["price"].to_numpy())
        ok = np.ones(len(lp), bool)
        for m in models:
            ok &= np.isfinite(prev[m.name][cc, gi])
        for m in models:
            errs[m.name].extend(np.abs(prev[m.name][cc, gi] - lp)[ok])
    for m in models:
        m.ingest(w, g)
        prev[m.name] = m.estimates(w)
print("\nErrore mediano sulla vendita successiva (periodo di verifica):")
for n, e in errs.items():
    print(f"  {n:45s} {100 * np.median(e):5.1f}%  (n={len(e)})")
