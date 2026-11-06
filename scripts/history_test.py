"""Protocol §35 (D188): the long tcgcharts history (from 1 July 2022, D85) in the prices, with the adopted engine v1.15.

Usage: PYTHONPATH=. python scripts/history_test.py <work dir>
1. Sales without and with the history (scripts/build_sales.py; SLABWISE_TC_HISTORY=1 for the second).
2. X1/X2: R1 and E2r on the sales with the history (scripts/real_r1.py).
3. X3/X4: phase R of the adopted engine on both (scripts/real_phase_r.py --adopted, one row per scored sale); compared
   on the sales scored in both runs (same item_id): mean |log error| with the venue offset, difference with a 95%
   interval by card bootstrap; coverage of the 80% band.
4. X5/X6: the site's build on both: grades with no value shown (no own sales, or in review), PSA 10 grades "Stimato";
   grades with >= 5 sales in 90 days and |log value - log median of those sales| > 0.5.
Writes results/history/summary.json.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
work = sys.argv[1]
os.makedirs(work, exist_ok=True)
RAW = os.path.join(ROOT, "data", "raw")
ERA = os.path.join(RAW, "era_map.json")


def run(args, env=None, out=None):
    print("$", " ".join(os.path.basename(a) for a in args[1:3]), flush=True)
    r = subprocess.run([sys.executable] + args, env=dict(os.environ, PYTHONPATH=ROOT, **(env or {})), capture_output=True, text=True)
    if out:
        open(out, "w").write(r.stdout + r.stderr)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f"errore in {args[0]}")
    return r.stdout


res = {}
for tag, env in (("now", {"SLABWISE_TC_HISTORY": "0"}), ("hist", {"SLABWISE_TC_HISTORY": "1"})):
    sales = os.path.join(work, f"sales_{tag}.csv")
    if not os.path.exists(sales):
        run([os.path.join(ROOT, "scripts", "build_sales.py"), os.path.join(RAW, "sales_base.csv"), os.path.join(RAW, "alt"), sales,
             os.path.join(RAW, "tcgcharts")], env)
    rows = os.path.join(work, f"rows_{tag}.csv")
    if not os.path.exists(rows):
        run([os.path.join(ROOT, "scripts", "real_phase_r.py"), sales, ERA, os.path.join(work, f"phase_r_{tag}.json"), "--adopted"],
            dict(env, PHASE_R_ROWS=rows))
    site = os.path.join(work, f"real_{tag}.json")
    if not os.path.exists(site):
        run([os.path.join(ROOT, "prototype", "build_real_data.py"), sales, ERA], dict(env, SLABWISE_OUT=site, SLABWISE_INDEX_FULL="0"))
    if tag == "hist":
        r1 = run([os.path.join(ROOT, "scripts", "real_r1.py"), sales, ERA, "--adopted"], env, os.path.join(work, "r1_hist.txt"))
        m1 = re.search(r"R1:\s*(\d+)", r1)
        m2 = re.search(r"E2r:\s*(\d+)", r1)
        res["X1_R1"] = int(m1.group(1)) if m1 else None
        res["X2_E2r"] = int(m2.group(1)) if m2 else None

# X3/X4 on the sales scored in both runs
a = pd.read_csv(os.path.join(work, "rows_now.csv"))
b = pd.read_csv(os.path.join(work, "rows_hist.csv"))
m = a.merge(b, on="item_id", suffixes=("_n", "_h"))
en, eh = np.abs(m["y_n"] - m["lvm_adj_n"]), np.abs(m["y_h"] - m["lvm_adj_h"])
d = (eh - en).to_numpy()
cards = m["card_n"].astype(str).to_numpy()
uc = np.unique(cards)
idx = {c: np.where(cards == c)[0] for c in uc}
rng = np.random.default_rng(35)
boots = [np.mean(np.concatenate([d[idx[c]] for c in rng.choice(uc, len(uc))])) for _ in range(2000)]
res["n_common"] = int(len(m))
res["X3"] = dict(err_now=float(en.mean()), err_hist=float(eh.mean()), diff_points=float(d.mean() * 100),
                 ci95_points=[float(np.percentile(boots, 2.5) * 100), float(np.percentile(boots, 97.5) * 100)])
cov = lambda y, e, s: float(np.mean(np.abs(y - e) <= 1.2816 * s))
res["X4"] = dict(cov_now=cov(m["y_n"], m["lvm_adj_n"], m["s_pred_n"]), cov_hist=cov(m["y_h"], m["lvm_adj_h"], m["s_pred_h"]))


def site_stats(path):
    D = json.load(open(path))
    hidden = sum(1 for c in D["cards"] for g in c["grades"] if not g.get("sales_all") or g.get("off"))
    est10 = sum(1 for c in D["cards"] for g in c["grades"] if g["grade"] == 10 and g.get("tier") == "Stimato")
    far = [(c["id"], g["grade"]) for c in D["cards"] for g in c["grades"]
           if (g.get("sales90") or 0) >= 5 and g.get("med90") and abs(np.log(g["value"] / g["med90"])) > 0.5]
    return dict(cards=len(D["cards"]), grades=sum(len(c["grades"]) for c in D["cards"]), hidden=hidden, psa10_stimato=est10, far=far)


res["X5"] = dict(now=site_stats(os.path.join(work, "real_now.json")), hist=site_stats(os.path.join(work, "real_hist.json")))
res["X6_far"] = res["X5"]["hist"]["far"]
x3, x4, x5 = res["X3"], res["X4"], res["X5"]
res["passed"] = dict(
    X1=res["X1_R1"] == 0,
    X2=res["X2_E2r"] is not None and res["X2_E2r"] <= 3,
    X3=x3["ci95_points"][1] <= 0.2,
    X4=x4["cov_hist"] >= x4["cov_now"] - 0.01 and x4["cov_hist"] <= 0.85,
    X5=x5["hist"]["hidden"] < x5["now"]["hidden"] and x5["hist"]["psa10_stimato"] < x5["now"]["psa10_stimato"],
    X6=len(res["X6_far"]) <= len(x5["now"]["far"]))
os.makedirs(os.path.join(ROOT, "results", "history"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "history", "summary.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
