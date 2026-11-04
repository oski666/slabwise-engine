"""The public scorecard (D105): what the site claims, checked against the sales that came after.

Usage: PYTHONPATH=. python scripts/pagella.py data/raw/sales_all.csv prototype/data/pagella.json

(1) Phase R of the adopted engine on the real sales (results/real/pagella_base.json, written when a version is
adopted): next-sale error against every competitor with the 95% interval, coverage, quarter by quarter.
(2) Every sealed snapshot (data/seals) against the eBay sales of the following 4 weeks for the same card and grade:
share inside the published 80% next-sale range and median error. Only sales after the snapshot count.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sales_p, out = sys.argv[1], sys.argv[2]
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
base = json.load(open(os.path.join(root, "results", "real", "pagella_base.json")))
d = pd.read_csv(sales_p)
d = d[d["excluded"].isna() | (d["excluded"] == "")]
d = d[d["venue"] == "ebay"]
d["t"] = pd.to_datetime(d["date"], utc=True, format="mixed")
checks = []
seal_dir = os.path.join(root, "data", "seals")
for f in sorted(os.listdir(seal_dir)) if os.path.isdir(seal_dir) else []:
    if not f.endswith(".json"):
        continue
    s = json.load(open(os.path.join(seal_dir, f)))
    t0 = pd.Timestamp(s["asof"][:10], tz="UTC") + pd.Timedelta(days=1)
    win = d[(d["t"] >= t0) & (d["t"] < t0 + pd.Timedelta(days=28))]
    if not len(win):
        checks.append({"seal": f, "asof": s["asof"][:10], "engine": s.get("engine"), "sales": 0, "stamped": os.path.exists(os.path.join(seal_dir, f + ".ots"))})
        continue
    rows = {(r["card"], r["grade"]): r for r in s["rows"] if "sale_lo" in r}
    inside, errs = [], []
    for _, x in win.iterrows():
        r = rows.get((x["card"], int(x["grade"])))
        if not r:
            continue
        inside.append(r["sale_lo"] <= x["price_usd"] <= r["sale_hi"])
        errs.append(abs(np.log(x["price_usd"] / r["value"])))
    checks.append({"seal": f, "asof": s["asof"][:10], "engine": s.get("engine"), "sales": len(inside),
                   "coverage": float(np.mean(inside)) if inside else None, "error": float(np.median(errs)) if errs else None,
                   "complete": bool(pd.Timestamp.now(tz="UTC") >= t0 + pd.Timedelta(days=28)),
                   "stamped": os.path.exists(os.path.join(seal_dir, f + ".ots"))})
json.dump({"base": base, "seals": checks}, open(out, "w"), ensure_ascii=False, indent=1)
print(len(checks), "istantanee controllate ->", out)
