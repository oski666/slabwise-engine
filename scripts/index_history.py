"""Protocol §27 (D138): index history rebuilt with the long tcgcharts history, spliced at the published base week.

Usage: PYTHONPATH=. python scripts/index_history.py <work dir> [--skip-build]

1. Sales without and with the long history (scripts/build_sales.py, SLABWISE_TC_HISTORY=1), then the site's build on
   each (prototype/build_real_data.py with SLABWISE_OUT): prices and published indices come from the first, the
   rebuilt indices from the second.
2. H2-H3: consecutive sales of the same cert (auction archive, prototype/data/certs.json), same grade, both before the
   base and after the start of their era index's history: slope of dlog price on dlog index, bootstrap by card;
   mean squared error with and without the index.
3. H4: correlation of 4-week changes, rebuilt vs published, from the base to today, median over published indices.
H1 comes from the simulated market (results/index_history_H1.json). Writes results/index_history/summary.json and,
when H1-H4 pass, prototype/data/index_history.json (the rebuilt points before each base, scaled to 100 at the base).
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


def all_ix(d):
    out = {k: dict(v, kind="era") for k, v in (d.get("indexes") or {}).items()}
    if d.get("index_all"):
        out["tutto"] = dict(d["index_all"], kind="generale")
    out.update({"set:" + k: dict(v, kind="set") for k, v in (d.get("index_sets") or {}).items()})
    return out


P, H = all_ix(pub), all_ix(hist)


def level_at(points, day):
    ds = [p[0] for p in points]
    i = bisect_right(ds, day) - 1
    return points[i][1] if i >= 0 else None


spliced = {}
for k, p in P.items():
    h = H.get(k)
    if not h:
        continue
    base = p.get("base") or pub["index_base"]
    hb = level_at(h["points"], base)
    if not hb:
        continue
    start = next((d for d, n in (h.get("sizes") or []) if n >= MIN_BASKET[p["kind"]]), None)
    if not start or start >= base:
        continue
    spliced[k] = dict(start=start, base=base, points=[[d, round(v * 100 / hb, 2)] for d, v in h["points"] if start <= d < base],
                      scaled=[[d, v * 100 / hb] for d, v in h["points"]])

# H4: from the base to today, 4-week changes rebuilt vs published
h4 = {}
for k, s in spliced.items():
    pp = [x for x in P[k]["points"] if x[0] >= s["base"]]
    hh = dict((d, v) for d, v in s["scaled"])
    pairs = [(v, hh.get(d)) for d, v in pp if hh.get(d)]
    if len(pairs) < 10:
        continue
    a = np.log([x for x, _ in pairs])
    b = np.log([y for _, y in pairs])
    h4[k] = float(np.corrcoef(a[4:] - a[:-4], b[4:] - b[:-4])[0, 1])

# H2-H3: repeat sales of the same cert before the base of their era index
certs = json.load(open(os.path.join(ROOT, "prototype", "data", "certs.json")))["certs"]
series = {c["id"]: c["series"] for c in hist["cards"]}
pairs = []
for n, lst in certs.items():
    ok = sorted([s for s in lst if not (s[5] if len(s) > 5 else None)], key=lambda s: s[0])
    for a, b in zip(ok, ok[1:]):
        if a[2] != b[2] or a[1] != b[1] or a[0] == b[0]:
            continue
        k = series.get(a[1].split("/")[0])
        s = spliced.get(k)
        if not s or not (s["start"] <= a[0] and b[0] < s["base"]):
            continue
        ia, ib = level_at(s["scaled"], a[0]), level_at(s["scaled"], b[0])
        if ia and ib and a[3] > 0 and b[3] > 0:
            pairs.append((a[1].split("/")[0], float(np.log(ib / ia)), float(np.log(b[3] / a[3]))))
res = dict(asof=str(date.today()), indices=sorted(spliced), starts={k: v["start"] for k, v in spliced.items()}, pairs=len(pairs), H4=h4)
if len(pairs) >= 20:
    x = np.array([p[1] for p in pairs])
    y = np.array([p[2] for p in pairs])
    cards = np.array([p[0] for p in pairs])

    def slope(xx, yy):
        xm, ym = xx - xx.mean(), yy - yy.mean()
        return float(np.sum(xm * ym) / np.sum(xm ** 2)) if np.sum(xm ** 2) > 0 else float("nan")

    rng = np.random.default_rng(27)
    uc = np.unique(cards)
    boots = []
    for _ in range(2000):
        pick = rng.choice(uc, len(uc), replace=True)
        idx = np.concatenate([np.where(cards == c)[0] for c in pick])
        boots.append(slope(x[idx], y[idx]))
    mse_no = float(np.mean((y - y.mean()) ** 2))
    mse_ix = float(np.mean((y - x - np.mean(y - x)) ** 2))
    res.update(H2=dict(slope=slope(x, y), ci95=[float(np.nanpercentile(boots, 2.5)), float(np.nanpercentile(boots, 97.5))], cards=int(len(uc))),
               H3=dict(mse_without=mse_no, mse_with=mse_ix, reduction=1 - mse_ix / mse_no))
h1p = os.path.join(ROOT, "results", "index_history_H1.json")
h1 = json.load(open(h1p)) if os.path.exists(h1p) else None
res["H1"] = h1 and dict(slope=h1["slope_median"], corr=h1["corr_median"], n=h1["n"])
passed = dict(
    H1=bool(h1) and 0.70 <= h1["slope_median"] <= 1.30 and h1["corr_median"] >= 0.70,
    H2="H2" in res and 0.70 <= res["H2"]["slope"] <= 1.30 and res["H2"]["ci95"][0] > 0.30,
    H3="H3" in res and res["H3"]["reduction"] >= 0.10,
    H4=bool(h4) and float(np.median(list(h4.values()))) >= 0.80)
res["passed"] = passed
res["H4_median"] = float(np.median(list(h4.values()))) if h4 else None
os.makedirs(os.path.join(ROOT, "results", "index_history"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "index_history", "summary.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "starts"}, indent=1))
if all(passed.values()):
    json.dump({k: dict(start=v["start"], base=v["base"], points=v["points"]) for k, v in spliced.items()},
              open(os.path.join(ROOT, "prototype", "data", "index_history.json"), "w"), separators=(",", ":"))
    print("H1-H4 superati: prototype/data/index_history.json scritto")
else:
    print("non superato:", [k for k, v in passed.items() if not v])
