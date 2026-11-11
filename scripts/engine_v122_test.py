"""Protocol §57 (D260): the model's market groups = the site's six eras (arm F), or the six eras plus two Japanese groups
(arm G), against the engine of the site (R = v1.20, three groups), on the sales with the long history.
Y1-Y6 as in §40; Y7 is the lag: median signed error by (site era, week) over the last 26 weeks.

Usage: PYTHONPATH=. python scripts/engine_v122_test.py <work dir>      Writes results/v122/summary.json.
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
    print("$", " ".join(os.path.basename(a) for a in args[:3]), env or "", flush=True)
    r = subprocess.run([sys.executable] + args, env=dict(os.environ, PYTHONPATH=ROOT, **(env or {})), capture_output=True, text=True)
    if out:
        open(out, "w").write(r.stdout + r.stderr)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f"errore in {args[0]}")
    return r.stdout



sales = os.path.join(work, "sales_hist.csv")
if not os.path.exists(sales):
    run([os.path.join(ROOT, "scripts", "build_sales.py"), os.path.join(RAW, "sales_base.csv"), os.path.join(RAW, "alt"), sales,
         os.path.join(RAW, "tcgcharts")], {"SLABWISE_TC_HISTORY": "1"})

SITE = {"SLABWISE_TC_HISTORY": "1", "SLABWISE_REVIEW_RECENT": "1", "SLABWISE_GRADE_JUMP": "1"}
RUNS = (("R", ["--v120"], dict(SITE)),
        ("F", ["--v120"], dict(SITE, SLABWISE_MODEL_ERAS="site")),
        ("G", ["--v120"], dict(SITE, SLABWISE_MODEL_ERAS="site_ja")))


def r1_of(sales, flag, env, tag):
    out = run([os.path.join(ROOT, "scripts", "real_r1.py"), sales, ERA, "--adopted"] + flag, env, os.path.join(work, f"r1_{tag}.txt"))
    m1, m2 = re.search(r"R1:\s*(\d+)", out), re.search(r"E2r:\s*(\d+)", out)
    e2 = re.search(r"E2r: \d+ voci lontane dalle vendite recenti: (.*)", out)
    items = e2.group(1) if e2 else "[]"
    return dict(R1=int(m1.group(1)) if m1 else None, E2r=int(m2.group(1)) if m2 else None, E2r_items=items,
                E2r_keys=sorted({tuple(x[:2]) for x in eval(items)}) if items.startswith("[") else [])


res = {}
sales = os.path.join(work, "sales_hist.csv")
for name, flag, env in RUNS:
    rows = os.path.join(work, f"rows_{name}.csv")
    if not os.path.exists(rows):
        run([os.path.join(ROOT, "scripts", "real_phase_r.py"), sales, ERA, os.path.join(work, f"phase_r_{name}.json"), "--adopted"] + flag,
            dict(env, PHASE_R_ROWS=rows), os.path.join(work, f"phase_r_{name}.txt"))
    site = os.path.join(work, f"real_{name}.json")
    if not os.path.exists(site):
        run([os.path.join(ROOT, "prototype", "build_real_data.py"), sales, ERA], dict(env, SLABWISE_OUT=site, SLABWISE_INDEX_FULL="0"))
    res[name] = r1_of(sales, flag, env, name)


def site_stats(path):
    D = json.load(open(path))
    gr = [(c, g) for c in D["cards"] for g in c["grades"]]
    nosale = sum(1 for c, g in gr if not g.get("sales_all"))
    review = sum(1 for c, g in gr if g.get("sales_all") and g.get("off"))
    est10 = sum(1 for c, g in gr if g["grade"] == 10 and g.get("tier") == "Stimato" and g.get("sales_all") and not g.get("off"))
    far = [(c["id"], g["grade"]) for c, g in gr
           if (g.get("sales90") or 0) >= 5 and g.get("med90") and abs(np.log(g["value"] / g["med90"])) > 0.5]
    return dict(cards=len(D["cards"]), grades=len(gr), no_sales=nosale, in_review=review, hidden=nosale + review,
                psa10_stimato=est10, Y5=nosale + review + est10, far=far)


ref_rows = pd.read_csv(os.path.join(work, "rows_R.csv"))
cov = lambda y, e, s: float(np.mean(np.abs(y - e) <= 1.2816 * s))  # noqa: E731
res["R"]["site"] = ref_site = site_stats(os.path.join(work, "real_R.json"))
sys.path.insert(0, ROOT)
from slabwise.series import series_of  # noqa: E402


def lag(m, col_y, col_p):
    """Y7: per (site era, week) cell with >= 30 sales in the last 26 weeks, |median signed log error|; mean over cells."""
    d = m[m["week_n"] > m["week_n"].max() - 26].copy()
    d["site_era"] = ["Giappone" if str(c).startswith("ja:") else series_of(str(c).split("/")[0]) for c in d["card_n"]]
    d["err"] = d[col_y] - d[col_p]
    g = d.groupby(["site_era", "week_n"])["err"].agg(["median", "size"])
    g = g[g["size"] >= 30]
    by = g["median"].abs().groupby(level=0).mean()
    return float(g["median"].abs().mean()), {k: round(float(v), 4) for k, v in by.items()}, int(len(g))


for name in ("F", "G"):
    b = pd.read_csv(os.path.join(work, f"rows_{name}.csv"))
    m = ref_rows.merge(b, on="item_id", suffixes=("_n", "_h"))
    en, eh = np.abs(m["y_n"] - m["lvm_adj_n"]), np.abs(m["y_h"] - m["lvm_adj_h"])
    d = (eh - en).to_numpy()
    cards = m["card_n"].astype(str).to_numpy()
    uc = np.unique(cards)
    idx = {c: np.where(cards == c)[0] for c in uc}
    rng = np.random.default_rng(57)
    boots = [np.mean(np.concatenate([d[idx[c]] for c in rng.choice(uc, len(uc))])) for _ in range(2000)]
    r = res[name]
    r["n_common"] = int(len(m))
    r["Y3"] = dict(err_ref=float(en.mean()), err_arm=float(eh.mean()), diff_points=float(d.mean() * 100),
                   ci95_points=[float(np.percentile(boots, 2.5) * 100), float(np.percentile(boots, 97.5) * 100)])
    r["Y4"] = dict(cov_ref=cov(m["y_n"], m["lvm_adj_n"], m["s_pred_n"]), cov_arm=cov(m["y_h"], m["lvm_adj_h"], m["s_pred_h"]))
    L_ref, by_ref, cells = lag(m, "y_n", "lvm_adj_n")
    L_arm, by_arm, _ = lag(m, "y_h", "lvm_adj_h")
    worst = sorted(by_ref, key=lambda k: -by_ref[k])[:2]
    r["Y7"] = dict(L_ref=round(L_ref, 4), L_arm=round(L_arm, 4), cells=cells, by_era_ref=by_ref, by_era_arm=by_arm, worst=worst)
    r["site"] = s = site_stats(os.path.join(work, f"real_{name}.json"))
    r["passed"] = dict(
        Y1=r["R1"] == 0,
        Y2=r["E2r"] is not None and r["E2r"] <= 3 and r["E2r"] <= (res["R"]["E2r"] or 0),
        Y3=r["Y3"]["ci95_points"][1] <= 0.2,
        Y4=r["Y4"]["cov_arm"] >= r["Y4"]["cov_ref"] - 0.01 and r["Y4"]["cov_arm"] <= max(0.85, r["Y4"]["cov_ref"]),
        Y5=s["Y5"] <= ref_site["Y5"],
        Y6=len(s["far"]) <= len(ref_site["far"]),
        Y7=L_arm <= 0.8 * L_ref and all(by_arm.get(k, 9) < by_ref[k] for k in worst))
    r["all_passed"] = all(r["passed"].values())
ok = [n for n in ("F", "G") if res[n]["all_passed"]]
res["adopt"] = min(ok, key=lambda n: res[n]["Y7"]["L_arm"]) if ok else None
os.makedirs(os.path.join(ROOT, "results", "v122"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "v122", "summary.json"), "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
