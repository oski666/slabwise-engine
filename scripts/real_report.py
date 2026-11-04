"""Real-sales report: every method replayed week by week on the real sales CSV.

Usage: PYTHONPATH=. python scripts/real_report.py data/raw/sales_all.csv data/raw/era_map.json results/real/report.json
Same protocol as scripts/run_real.py (parameters calibrated on the first third of the
weeks, then frozen; error on the next sale), plus the weekly estimates of each method
for the charts. Real data (P14): nothing here is simulated.
"""
import json
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

from slabwise.baselines import (CardLadderIndexed, LastSale, PriceChartingAgeWeighted, SlabwiseV0,
                                TCGChartsTiered)
from slabwise.calibrate import calibrate_clean
from slabwise.identity import identity_layer
from slabwise.model import LatentValueModel
from slabwise.schema import GRADE_INDEX, GRADES
from slabwise.sources.csv_sales import era_of, load_sales_csv

path, era_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
raw = pd.read_csv(path)
sales, cards = load_sales_csv(path)
t0 = pd.to_datetime(raw["date"], utc=True, format="mixed").min().normalize()
era_map = json.load(open(era_path))
eras = sorted(set(era_map.values()))
era = np.array([eras.index(era_of(c, era_map)) for c in cards])
clean, removed = identity_layer(sales, None, verify_certs=False)
single_venue = clean["venue"].nunique() == 1
if single_venue:
    clean["venue"] = "ebay"
W = int(clean["week"].max()) + 1
train = max(26, W // 3)
params, score, _ = calibrate_clean(clean, len(cards), era, len(eras), train)
models = [cls(len(cards), era, len(eras)) for cls in
          (LastSale, TCGChartsTiered, PriceChartingAgeWeighted, CardLadderIndexed, SlabwiseV0)]
lvm = LatentValueModel(len(cards), era, len(eras), params)
models.append(lvm)
names = [m.name for m in models]
groups = {wk: g for wk, g in clean.groupby("week")}
empty = clean.iloc[:0]
prev = {m.name: None for m in models}
errs = defaultdict(list)                         # (method, card) -> errors
hist = defaultdict(list)                         # (card, grade) -> weekly rows
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
            e = np.abs(prev[m.name][cc, gi] - lp)
            for j in np.where(ok)[0]:
                errs[(m.name, int(cc[j]))].append(float(e[j]))
    for m in models:
        m.ingest(w, g)
    for m in models:
        prev[m.name] = m.estimates(w)
    mean, sd = lvm.estimates_with_sd(w)
    for c in range(len(cards)):
        for k in range(4):
            if np.isfinite(mean[c, k]):
                hist[(c, k)].append([int(w)] + [None if not np.isfinite(prev[n][c, k]) else round(float(np.exp(prev[n][c, k])), 2)
                                                 for n in names[:-1]]
                                    + [round(float(np.exp(mean[c, k])), 2), round(float(np.exp(mean[c, k] - 1.2816 * sd[c, k])), 2),
                                       round(float(np.exp(mean[c, k] + 1.2816 * sd[c, k])), 2)])

day0 = t0.date()
wk_date = lambda w: str((t0 + pd.Timedelta(weeks=int(w) + 1)).date())          # noqa: E731
summary = {n: float(np.median(sum((errs[(n, c)] for c in range(len(cards))), []))) for n in names}
n_test = len(sum((errs[(names[0], c)] for c in range(len(cards))), []))
per_card = []
for c, cid in enumerate(cards):
    n = len(errs[(names[0], c)])
    if not n:
        continue
    per_card.append(dict(card=cid, n=n, err={nm: round(float(np.median(errs[(nm, c)])), 4) for nm in names}))
charts = []
for c, cid in enumerate(cards):
    s_all = clean[clean["card"] == c]
    if len(s_all) < 15:
        continue
    rem = removed[removed["card"] == c]
    grades = []
    for k, g in enumerate(GRADES):
        sg = s_all[s_all["grade"] == g]
        if len(sg) < 3 or not hist[(c, k)]:
            continue
        h = [[wk_date(r[0])] + r[1:] for r in hist[(c, k)]]
        pts = [[str((t0 + pd.Timedelta(days=float(d))).date()), round(float(p), 2), v]
               for d, p, v in zip(sg["day"], sg["price"], sg["venue"])]
        rp = rem[rem["grade"] == g]
        out_pts = [[str((t0 + pd.Timedelta(days=float(d))).date()), round(float(p), 2), r]
                   for d, p, r in zip(rp["day"], rp["price"], rp["reason"])]
        grades.append(dict(grade=g, history=h, sales=pts, removed=out_pts))
    if grades:
        charts.append(dict(card=cid, n=int(len(s_all)), grades=grades))
venues = clean.groupby("venue").size().to_dict()
res = dict(
    asof=str(pd.Timestamp.now(tz="UTC").date()), start=str(day0), weeks=W, train_weeks=train,
    train_end=wk_date(train), n_sales=int(len(sales)), n_clean=int(len(clean)), n_removed=int(len(removed)),
    removed_reasons=removed["reason"].value_counts().to_dict(), venues=venues,
    single_venue=bool(single_venue), venue_offset=round(float(lvm.venue_off), 4),
    params={k: v for k, v in params.__dict__.items()}, methods=names, n_test=n_test,
    error=summary, per_card=per_card, charts=charts,
    kappa={cards[c]: round(lvm.qc(c) / params.q_L, 2) for c in range(len(cards)) if lvm._qw[c] > 0},
    note="Dati reali: vendite concluse eBay (ultime settimane, 4 carte), Goldin e Fanatics Collect (2023-2026), "
         "raccolte con Apify. Campione piccolo.")
json.dump(res, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
print("test", n_test, {k: round(v, 4) for k, v in summary.items()}, "charts", len(charts))
