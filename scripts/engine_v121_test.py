"""Protocol §40 (D220): the grade's jump looked for on its latest sales (arm D) and D with fatter-tailed grade steps (arm E)
against the engine of the site (R = v1.20), all on the sales with the long history; then, for the adopted arm, the T3 of
§39 again (Y8): the sales with the title rules of D216 on must give R1 = 0 and no E2r item more than without them.

Usage: PYTHONPATH=. python scripts/engine_v121_test.py <work dir>      Writes results/v121/summary.json.
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



for tag, rules in (("hist", "0"), ("rules", "1")):
    sales = os.path.join(work, f"sales_{tag}.csv")
    if not os.path.exists(sales):
        run([os.path.join(ROOT, "scripts", "build_sales.py"), os.path.join(RAW, "sales_base.csv"), os.path.join(RAW, "alt"), sales,
             os.path.join(RAW, "tcgcharts")], {"SLABWISE_TC_HISTORY": "1", "SLABWISE_EN_RULES": rules})

SITE = {"SLABWISE_TC_HISTORY": "1", "SLABWISE_REVIEW_RECENT": "1", "SLABWISE_GRADE_JUMP": "1"}
RUNS = (("R", ["--v120"], dict(SITE)),
        ("D", ["--v121d"], dict(SITE, SLABWISE_GRADE_JUMP_RECENT="1")),
        ("E", ["--v121e"], dict(SITE, SLABWISE_GRADE_JUMP_RECENT="1", SLABWISE_STEP_T="2")))


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
for name in ("D", "E"):
    b = pd.read_csv(os.path.join(work, f"rows_{name}.csv"))
    m = ref_rows.merge(b, on="item_id", suffixes=("_n", "_h"))
    en, eh = np.abs(m["y_n"] - m["lvm_adj_n"]), np.abs(m["y_h"] - m["lvm_adj_h"])
    d = (eh - en).to_numpy()
    cards = m["card_n"].astype(str).to_numpy()
    uc = np.unique(cards)
    idx = {c: np.where(cards == c)[0] for c in uc}
    rng = np.random.default_rng(40)
    boots = [np.mean(np.concatenate([d[idx[c]] for c in rng.choice(uc, len(uc))])) for _ in range(2000)]
    r = res[name]
    r["n_common"] = int(len(m))
    r["Y3"] = dict(err_ref=float(en.mean()), err_arm=float(eh.mean()), diff_points=float(d.mean() * 100),
                   ci95_points=[float(np.percentile(boots, 2.5) * 100), float(np.percentile(boots, 97.5) * 100)])
    r["Y4"] = dict(cov_ref=cov(m["y_n"], m["lvm_adj_n"], m["s_pred_n"]), cov_arm=cov(m["y_h"], m["lvm_adj_h"], m["s_pred_h"]))
    r["site"] = s = site_stats(os.path.join(work, f"real_{name}.json"))
    r["passed"] = dict(
        Y1=r["R1"] == 0,
        Y2=r["E2r"] is not None and r["E2r"] <= 3 and r["E2r"] <= (res["R"]["E2r"] or 0),
        Y3=r["Y3"]["ci95_points"][1] <= 0.2,
        Y4=r["Y4"]["cov_arm"] >= r["Y4"]["cov_ref"] - 0.01 and r["Y4"]["cov_arm"] <= 0.85,
        Y5=s["Y5"] <= ref_site["Y5"],
        Y6=len(s["far"]) <= len(ref_site["far"]))
    r["all_passed"] = all(r["passed"].values())
ok = [n for n in ("D", "E") if res[n]["all_passed"]]
res["adopt"] = min(ok, key=lambda n: res[n]["Y3"]["err_arm"]) if ok else None
if res["adopt"]:                                         # Y8: the T3 of §39 again, with the adopted engine
    name = res["adopt"]
    flag, env = next((f, e) for n, f, e in RUNS if n == name)
    y8 = r1_of(os.path.join(work, "sales_rules.csv"), flag, dict(env, SLABWISE_EN_RULES="1"), name + "_rules")
    new_items = sorted(set(map(tuple, y8["E2r_keys"])) - set(map(tuple, res[name]["E2r_keys"])))
    res["Y8"] = dict(y8, new_E2r=new_items, passed=y8["R1"] == 0 and not new_items)
os.makedirs(os.path.join(ROOT, "results", "v121"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "v121", "summary.json"), "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
