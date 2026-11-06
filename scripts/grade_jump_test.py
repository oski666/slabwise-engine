"""Protocol §37 (D206): arm A of §36 (long tcgcharts history in the prices, review against the recent sales) and arm C
= A + jumps of a single grade (grade_jump, D155 thresholds), against the site of today (no history, v1.15, D98 on 13 weeks).
Only arm C can be adopted (A failed §36); A is run again for reference.

Usage: PYTHONPATH=. python scripts/grade_jump_test.py <work dir>
1. Sales without and with the history (scripts/build_sales.py; SLABWISE_TC_HISTORY=1 for the second).
2. Y1/Y2: R1 and E2r on the sales with the history, engine of each arm (scripts/real_r1.py; --v120 for arm C).
3. Y3/Y4: phase R (scripts/real_phase_r.py --adopted, one row per scored sale) for the reference and each arm; each arm
   is compared with the reference on the sales scored in both (same item_id): mean |log error| with the venue offset,
   difference with a 95% interval by card bootstrap; coverage of the 80% band.
4. Y5/Y6: the site's build for the reference and each arm (SLABWISE_REVIEW_RECENT=1 for the arms,
   SLABWISE_GRADE_JUMP=1 for arm C): grades with no value shown (no own sales, or in review) + PSA 10 "Stimato";
   grades with >= 5 sales in 90 days and |log value - log median of those sales| > 0.5.
Writes results/gradejump/summary.json.
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


for tag, hist in (("now", "0"), ("hist", "1")):
    sales = os.path.join(work, f"sales_{tag}.csv")
    if not os.path.exists(sales):
        run([os.path.join(ROOT, "scripts", "build_sales.py"), os.path.join(RAW, "sales_base.csv"), os.path.join(RAW, "alt"), sales,
             os.path.join(RAW, "tcgcharts")], {"SLABWISE_TC_HISTORY": hist})

# (name, sales, extra engine flag, site environment)
RUNS = (("ref", "now", [], {"SLABWISE_TC_HISTORY": "0", "SLABWISE_REVIEW_RECENT": "0", "SLABWISE_GRADE_JUMP": "0"}),
        ("A", "hist", [], {"SLABWISE_TC_HISTORY": "1", "SLABWISE_REVIEW_RECENT": "1", "SLABWISE_GRADE_JUMP": "0"}),
        ("C", "hist", ["--v120"], {"SLABWISE_TC_HISTORY": "1", "SLABWISE_REVIEW_RECENT": "1", "SLABWISE_GRADE_JUMP": "1"}))
res = {}
for name, tag, flag, env in RUNS:
    sales = os.path.join(work, f"sales_{tag}.csv")
    rows = os.path.join(work, f"rows_{name}.csv")
    if not os.path.exists(rows):
        run([os.path.join(ROOT, "scripts", "real_phase_r.py"), sales, ERA, os.path.join(work, f"phase_r_{name}.json"), "--adopted"] + flag,
            dict(env, PHASE_R_ROWS=rows), os.path.join(work, f"phase_r_{name}.txt"))
    site = os.path.join(work, f"real_{name}.json")
    if not os.path.exists(site):
        run([os.path.join(ROOT, "prototype", "build_real_data.py"), sales, ERA], dict(env, SLABWISE_OUT=site, SLABWISE_INDEX_FULL="0"))
    if name != "ref":
        r1 = run([os.path.join(ROOT, "scripts", "real_r1.py"), sales, ERA, "--adopted"] + flag, env, os.path.join(work, f"r1_{name}.txt"))
        m1, m2 = re.search(r"R1:\s*(\d+)", r1), re.search(r"E2r:\s*(\d+)", r1)
        e2 = re.search(r"E2r: \d+ voci lontane dalle vendite recenti: (.*)", r1)
        res[name] = dict(Y1_R1=int(m1.group(1)) if m1 else None, Y2_E2r=int(m2.group(1)) if m2 else None,
                         E2r_items=e2.group(1) if e2 else None)


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


ref_rows = pd.read_csv(os.path.join(work, "rows_ref.csv"))
cov = lambda y, e, s: float(np.mean(np.abs(y - e) <= 1.2816 * s))
ref_site = site_stats(os.path.join(work, "real_ref.json"))
res["ref_site"] = ref_site
for name in ("A", "C"):
    b = pd.read_csv(os.path.join(work, f"rows_{name}.csv"))
    m = ref_rows.merge(b, on="item_id", suffixes=("_n", "_h"))
    en, eh = np.abs(m["y_n"] - m["lvm_adj_n"]), np.abs(m["y_h"] - m["lvm_adj_h"])
    d = (eh - en).to_numpy()
    cards = m["card_n"].astype(str).to_numpy()
    uc = np.unique(cards)
    idx = {c: np.where(cards == c)[0] for c in uc}
    rng = np.random.default_rng(37)
    boots = [np.mean(np.concatenate([d[idx[c]] for c in rng.choice(uc, len(uc))])) for _ in range(2000)]
    r = res[name]
    r["n_common"] = int(len(m))
    r["Y3"] = dict(err_ref=float(en.mean()), err_arm=float(eh.mean()), diff_points=float(d.mean() * 100),
                   ci95_points=[float(np.percentile(boots, 2.5) * 100), float(np.percentile(boots, 97.5) * 100)])
    r["Y4"] = dict(cov_ref=cov(m["y_n"], m["lvm_adj_n"], m["s_pred_n"]), cov_arm=cov(m["y_h"], m["lvm_adj_h"], m["s_pred_h"]))
    r["site"] = s = site_stats(os.path.join(work, f"real_{name}.json"))
    r["passed"] = dict(
        Y1=r["Y1_R1"] == 0,
        Y2=r["Y2_E2r"] is not None and r["Y2_E2r"] <= 3,
        Y3=r["Y3"]["ci95_points"][1] <= 0.2,
        Y4=r["Y4"]["cov_arm"] >= r["Y4"]["cov_ref"] - 0.01 and r["Y4"]["cov_arm"] <= 0.85,
        Y5=s["Y5"] < ref_site["Y5"],
        Y6=len(s["far"]) <= len(ref_site["far"]))
    r["all_passed"] = all(r["passed"].values())
res["adopt"] = "C" if res["C"]["all_passed"] else None
os.makedirs(os.path.join(ROOT, "results", "gradejump"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "gradejump", "summary.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
