"""Protocol §31 (D167): how many items in an index basket. Same algorithm as §29, only the basket size K changes.

Usage: PYTHONPATH=. python scripts/index_k_test.py <work dir>
1. Sales with the long history (scripts/build_sales.py, SLABWISE_TC_HISTORY=1), once.
2. The site's build in history mode for each variant: era/Japan K = 10, 15, 20 with general 30, plus general 60.
3. Q1 error reduction and Q2 slope on repeat sales of the same cert (as J2-J3 of §29), per variant, pooled over the
   era indices (pairs in their own group's index) and separately for the general index (English pairs);
   Q3 noise: median |weekly log change| of the index, mean over the era indices.
Writes results/index_k/summary.json.
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
MIN_BASKET = {"era": 5, "generale": 15}
VARIANTS = [("K10", 10, 30), ("K15", 15, 30), ("K20", 20, 30), ("G60", 10, 60)]
# §58 (D263): VARIANTS=K20:20:60,K30:30:60,K40:40:60 (first one is the reference), results in results/index_k58/
if os.environ.get("VARIANTS"):
    VARIANTS = [(t, int(k), int(g)) for t, k, g in (v.split(":") for v in os.environ["VARIANTS"].split(","))]
OUTDIR = os.environ.get("OUTDIR", "index_k")

sales = os.path.join(work, "sales_hist.csv")
env0 = dict(os.environ, PYTHONPATH=ROOT, SLABWISE_TC_HISTORY="1", SLABWISE_INDEX_FULL="0")
if not os.path.exists(sales):
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_sales.py"), os.path.join(ROOT, "data", "raw", "sales_base.csv"),
                    os.path.join(ROOT, "data", "raw", "alt"), sales, os.path.join(ROOT, "data", "raw", "tcgcharts")], check=True, env=env0)
runs = {}
for tag, k, kall in VARIANTS:
    out = os.path.join(work, f"real_{tag}.json")
    if not os.path.exists(out):
        env = dict(env0, SLABWISE_OUT=out, SLABWISE_IX_K=str(k), SLABWISE_IX_KALL=str(kall))
        subprocess.run([sys.executable, os.path.join(ROOT, "prototype", "build_real_data.py"), sales, os.path.join(ROOT, "data", "raw", "era_map.json")],
                       check=True, env=env)
    runs[tag] = json.load(open(out))
    print(tag, "costruito", flush=True)


def level_at(points, day):
    ds = [p[0] for p in points]
    i = bisect_right(ds, day) - 1
    return points[i][1] if i >= 0 else None


def trim(ix, kind):
    if not ix:
        return None
    start = next((d for d, n in (ix.get("sizes") or []) if n >= MIN_BASKET[kind]), None)
    if not start:
        return None
    pts = [p for p in ix["points"] if p[0] >= start]
    return dict(ix, start=start, points=pts) if len(pts) > 26 else None


def slope(xx, yy):
    xm = xx - xx.mean()
    return float(np.sum(xm * (yy - yy.mean())) / np.sum(xm ** 2)) if np.sum(xm ** 2) > 0 else float("nan")


certs = json.load(open(os.path.join(ROOT, "prototype", "data", "certs.json")))["certs"]


def pairs_for(run, general):
    group = {c["id"]: ("Giappone" if c["lang"] == "ja" else c["series"]) for c in run["cards"]}
    lang = {c["id"]: c["lang"] for c in run["cards"]}
    H = {"tutto": trim(run.get("index_all"), "generale")} if general else \
        {k: v for k, v in ((k, trim(v, "era")) for k, v in (run.get("indexes") or {}).items()) if v}
    out = []
    for lst in certs.values():
        ok = sorted([s for s in lst if not (s[5] if len(s) > 5 else None)], key=lambda s: s[0])
        for a, b in zip(ok, ok[1:]):
            if a[2] != b[2] or a[1] != b[1] or a[0] == b[0] or not (a[3] > 0 and b[3] > 0):
                continue
            cid = a[1].split("/")[0]
            if general:
                if lang.get(a[1], lang.get(cid)) == "ja":
                    continue
                h = H["tutto"]
            else:
                h = H.get(group.get(a[1]) or group.get(cid))
            if not h or a[0] < h["start"]:
                continue
            ia, ib = level_at(h["points"], a[0]), level_at(h["points"], b[0])
            if ia and ib:
                out.append((cid, float(np.log(ib / ia)), float(np.log(b[3] / a[3]))))
    return out, H


def measure(run, general):
    pr, H = pairs_for(run, general)
    res = dict(pairs=len(pr))
    if len(pr) >= 20:
        x = np.array([p[1] for p in pr]); y = np.array([p[2] for p in pr]); cards = np.array([p[0] for p in pr])
        rng = np.random.default_rng(31)
        uc = np.unique(cards)
        boots = []
        for _ in range(2000):
            pick = rng.choice(uc, len(uc), replace=True)
            idx = np.concatenate([np.where(cards == c)[0] for c in pick])
            boots.append(slope(x[idx], y[idx]))
        no, wi = float(np.mean((y - y.mean()) ** 2)), float(np.mean((y - x - np.mean(y - x)) ** 2))
        res.update(Q1=1 - wi / no, Q2=dict(slope=slope(x, y), ci95=[float(np.nanpercentile(boots, 2.5)), float(np.nanpercentile(boots, 97.5))]))
    noise = []
    for v in H.values():
        if v:
            lv = np.log([p[1] for p in v["points"]])
            noise.append(float(np.median(np.abs(np.diff(lv)))))
    res["Q3"] = float(np.mean(noise)) if noise else None
    res["sizes"] = {k: (v["sizes"][-1][1] if v and v.get("sizes") else None) for k, v in H.items()}
    return res


def margin(run):
    """§58 Q4: per era, the median over the last 52 weeks of the 95% margin of the basket's 4-week change; the max over eras."""
    m = {k: float(np.median([x[1] for x in v])) for k, v in (run.get("index_margin") or {}).items() if v}
    return dict(per_era={k: round(v, 4) for k, v in m.items()}, max=round(max(m.values()), 4) if m else None)


def passes(v, ref):
    return bool("Q1" in v and "Q1" in ref and v["Q1"] >= ref["Q1"] - 0.01
                and 0.70 <= v["Q2"]["slope"] <= 1.30 and v["Q2"]["ci95"][0] > 0.30
                and v["Q3"] is not None and ref["Q3"] is not None and v["Q3"] <= ref["Q3"] * 1.10)


summary = dict(asof=str(date.today()), era={}, generale={})
if os.environ.get("VARIANTS"):                     # §58
    ref = VARIANTS[0][0]
    for tag, _, _ in VARIANTS:
        summary["era"][tag] = dict(measure(runs[tag], False), Q4=margin(runs[tag]),
                                   distinct_cards={k: len({b.split(" PSA ")[0] for b in v.get("basket", [])}) for k, v in (runs[tag].get("indexes") or {}).items()})
    R = summary["era"][ref]
    summary["passed"] = {t: passes(summary["era"][t], R) and summary["era"][t]["Q4"]["max"] is not None
                         and R["Q4"]["max"] is not None and summary["era"][t]["Q4"]["max"] < R["Q4"]["max"] for t, _, _ in VARIANTS[1:]}
    ok = [k for t, k, _ in VARIANTS[1:] if summary["passed"][t]]
    summary["adopt"] = dict(era=max(ok) if ok else VARIANTS[0][1])
else:
    for tag in ("K10", "K15", "K20"):
        summary["era"][tag] = measure(runs[tag], False)
    for tag in ("K10", "G60"):
        summary["generale"][tag] = measure(runs[tag], True)
    E, G = summary["era"], summary["generale"]
    summary["passed"] = dict(K15=passes(E["K15"], E["K10"]), K20=passes(E["K20"], E["K10"]), G60=passes(G["G60"], G["K10"]))
    summary["adopt"] = dict(era=20 if summary["passed"]["K20"] else 15 if summary["passed"]["K15"] else 10,
                            generale=60 if summary["passed"]["G60"] else 30)
os.makedirs(os.path.join(ROOT, "results", OUTDIR), exist_ok=True)
json.dump(summary, open(os.path.join(ROOT, "results", OUTDIR, "summary.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
