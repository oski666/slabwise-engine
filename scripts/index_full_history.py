"""Protocol §29 (D148): indices computed entirely with the long tcgcharts history, no splicing.

Usage: PYTHONPATH=. python scripts/index_full_history.py <work dir> [--skip-build]

1. Sales without and with the long history (scripts/build_sales.py, SLABWISE_TC_HISTORY=1), then the site's build on each
   (prototype/build_real_data.py with SLABWISE_OUT): published indices from the first, history indices from the second.
2. J2-J3: consecutive sales of the same cert (prototype/data/certs.json), same grade, both inside the history index of
   the card's group (era, or "Giappone"): slope of dlog price on dlog index (bootstrap by card), squared error with and
   without the index.
3. J4: pairs whose first sale is after the published index's base: squared error with the history index against the
   published one (at least 30 pairs).
J1 is the simulated-market result of §7 and §27 H1, reported. Writes results/index_full_history/summary.json and, when
J1-J4 pass, prototype/data/index_full.json (indexes, index_all, index_sets of the history run, from each first basket
of at least 5 items, 15 for the general index), which the site build uses for the indices.
"""
import json
import os
import subprocess
import sys
from bisect import bisect_right
from datetime import date

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
work = sys.argv[1]
os.makedirs(work, exist_ok=True)
MIN_BASKET = {"era": 5, "set": 5, "generale": 15}


def build(tag, history):
    env = dict(os.environ, PYTHONPATH=ROOT, SLABWISE_OUT=os.path.join(work, f"real_{tag}.json"))
    env["SLABWISE_INDEX_FULL"] = "0"                         # published indices from this run, not from index_full.json
    if history:
        env["SLABWISE_TC_HISTORY"] = "1"
    else:
        env.pop("SLABWISE_TC_HISTORY", None)
    csv = os.path.join(work, f"sales_{tag}.csv")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_sales.py"), os.path.join(ROOT, "data", "raw", "sales_base.csv"),
                    os.path.join(ROOT, "data", "raw", "alt"), csv, os.path.join(ROOT, "data", "raw", "tcgcharts")], check=True, env=env)
    subprocess.run([sys.executable, os.path.join(ROOT, "prototype", "build_real_data.py"), csv, os.path.join(ROOT, "data", "raw", "era_map.json")],
                   check=True, env=env)


if "--skip-build" not in sys.argv:
    build("pub", False)
    build("hist", True)
pub = json.load(open(os.path.join(work, "real_pub.json")))
hist = json.load(open(os.path.join(work, "real_hist.json")))


def level_at(points, day):
    ds = [p[0] for p in points]
    i = bisect_right(ds, day) - 1
    return points[i][1] if i >= 0 else None


def trim(ix, kind):
    """The series from its first basket of MIN_BASKET items, rescaled to 100 at that point's base week if it has one."""
    if not ix:
        return None
    start = next((d for d, n in (ix.get("sizes") or []) if n >= MIN_BASKET[kind]), None)
    if not start:
        return None
    pts = [p for p in ix["points"] if p[0] >= start]
    return dict(ix, start=start, points=pts) if len(pts) > 26 else None


H = {k: trim(v, "era") for k, v in (hist.get("indexes") or {}).items()}
H = {k: v for k, v in H.items() if v}
P = pub.get("indexes") or {}
group = {c["id"]: ("Giappone" if c["lang"] == "ja" else c["series"]) for c in hist["cards"]}

certs = json.load(open(os.path.join(ROOT, "prototype", "data", "certs.json")))["certs"]
pairs = []
for n, lst in certs.items():
    ok = sorted([s for s in lst if not (s[5] if len(s) > 5 else None)], key=lambda s: s[0])
    for a, b in zip(ok, ok[1:]):
        if a[2] != b[2] or a[1] != b[1] or a[0] == b[0] or not (a[3] > 0 and b[3] > 0):
            continue
        k = group.get(a[1]) or group.get(a[1].split("/")[0])
        h = H.get(k)
        if not h or a[0] < h["start"]:
            continue
        ia, ib = level_at(h["points"], a[0]), level_at(h["points"], b[0])
        if not (ia and ib):
            continue
        pa = pb = None
        if k in P and a[0] >= (P[k].get("base") or pub["index_base"]):
            pa, pb = level_at(P[k]["points"], a[0]), level_at(P[k]["points"], b[0])
        pairs.append(dict(card=a[1].split("/")[0], x=float(np.log(ib / ia)), y=float(np.log(b[3] / a[3])),
                          xp=float(np.log(pb / pa)) if pa and pb else None))
res = dict(asof=str(date.today()), indices=sorted(H), starts={k: v["start"] for k, v in H.items()}, pairs=len(pairs),
           J1=dict(par7=dict(slope=1.02, corr=0.807), h1_27=dict(slope=0.945, corr=0.747), passed=True))


def slope(xx, yy):
    xm, ym = xx - xx.mean(), yy - yy.mean()
    return float(np.sum(xm * ym) / np.sum(xm ** 2)) if np.sum(xm ** 2) > 0 else float("nan")


if len(pairs) >= 20:
    x = np.array([p["x"] for p in pairs])
    y = np.array([p["y"] for p in pairs])
    cards = np.array([p["card"] for p in pairs])
    rng = np.random.default_rng(29)
    uc = np.unique(cards)
    boots = []
    for _ in range(2000):
        pick = rng.choice(uc, len(uc), replace=True)
        idx = np.concatenate([np.where(cards == c)[0] for c in pick])
        boots.append(slope(x[idx], y[idx]))
    res["J2"] = dict(slope=slope(x, y), ci95=[float(np.nanpercentile(boots, 2.5)), float(np.nanpercentile(boots, 97.5))], cards=int(len(uc)))
    no, wi = float(np.mean((y - y.mean()) ** 2)), float(np.mean((y - x - np.mean(y - x)) ** 2))
    res["J3"] = dict(mse_without=no, mse_with=wi, reduction=1 - wi / no)
late = [p for p in pairs if p["xp"] is not None]
if late:
    y = np.array([p["y"] for p in late])
    xh = np.array([p["x"] for p in late])
    xp = np.array([p["xp"] for p in late])
    res["J4"] = dict(pairs=len(late), mse_history=float(np.mean((y - xh - np.mean(y - xh)) ** 2)),
                     mse_published=float(np.mean((y - xp - np.mean(y - xp)) ** 2)))
    res["J4"]["ratio"] = res["J4"]["mse_history"] / res["J4"]["mse_published"]
passed = dict(J1=True,
              J2="J2" in res and 0.70 <= res["J2"]["slope"] <= 1.30 and res["J2"]["ci95"][0] > 0.30,
              J3="J3" in res and res["J3"]["reduction"] >= 0.10,
              J4="J4" in res and res["J4"]["pairs"] >= 30 and res["J4"]["ratio"] <= 1.05)
res["passed"] = passed
os.makedirs(os.path.join(ROOT, "results", "index_full_history"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "index_full_history", "summary.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
if all(passed.values()):
    out = dict(indexes=H, index_all=trim(hist.get("index_all"), "generale"),
               index_sets={k: v for k, v in ((k, trim(v, "set")) for k, v in (hist.get("index_sets") or {}).items()) if v},
               index_base=hist.get("index_base"), asof=res["asof"])
    json.dump(out, open(os.path.join(ROOT, "prototype", "data", "index_full.json"), "w"), separators=(",", ":"))
    print("J1-J4 superati: prototype/data/index_full.json scritto")
else:
    print("non superato:", [k for k, v in passed.items() if not v])
