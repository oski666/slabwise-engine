"""Protocol §61b (D294): the SlabRange as the real 8-in-10 of each card x grade, against the sample A.

Q:  half width = 80th percentile of |error| (sale minus the value of the week before, venue offset as in the sample)
    of the same card x grade in the 52 weeks before the sale's week; mixed with the same of the site era x grade band
    as (n q_card + 10 q_group) / (n + 10). The range is value +/- the half width.
Q2: the same for the 10th and the 90th percentile of the signed errors, separately: the range is value + lower to
    value + upper (it can be lopsided).
Values unchanged, so S4 and S6 hold by construction. S1 coverage 78-82%; S2 coverage in each tercile of the width
75-85%; S3 rank correlation of width and |error| >= A's + 0.10. Evaluation as §61: sales from 1 November 2025 with
genuine probability >= 0.5.

Usage: PYTHONPATH=. python scripts/slabrange_q_test.py <work dir>     Reuses rows_A.csv of slabrange_test.py if present.
Writes results/slabrange/summary_Q.json.
"""
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from slabwise.series import series_of  # noqa: E402

work = sys.argv[1]
os.makedirs(work, exist_ok=True)
RAW = os.path.join(ROOT, "data", "raw")
ERA = os.path.join(RAW, "era_map.json")
TIE, FROM = 10.0, "2025-11-01"


def run(args, env=None, out=None):
    print("$", " ".join(os.path.basename(a) for a in args[:3]), flush=True)
    r = subprocess.run([sys.executable] + args, env=dict(os.environ, PYTHONPATH=ROOT, **(env or {})), capture_output=True, text=True)
    if out:
        open(out, "w").write(r.stdout + r.stderr)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f"errore in {args[0]}")


sales = os.path.join(work, "sales_hist.csv")
if not os.path.exists(sales):
    run([os.path.join(ROOT, "scripts", "build_sales.py"), os.path.join(RAW, "sales_base.csv"), os.path.join(RAW, "alt"), sales,
         os.path.join(RAW, "tcgcharts")], {"SLABWISE_TC_HISTORY": "1"})
rows_p = os.path.join(work, "rows_A.csv")
if not os.path.exists(rows_p):
    run([os.path.join(ROOT, "scripts", "real_phase_r.py"), sales, ERA, os.path.join(work, "phase_r_A.json"), "--adopted", "--v120"],
        {"SLABWISE_TC_HISTORY": "1", "SLABWISE_REVIEW_RECENT": "1", "SLABWISE_GRADE_JUMP": "1", "PHASE_R_ROWS": rows_p},
        os.path.join(work, "phase_r_A.txt"))

raw = pd.read_csv(sales, usecols=["date", "excluded"], low_memory=False)
t0 = pd.to_datetime(raw.loc[raw["excluded"].isna() | (raw["excluded"] == ""), "date"], utc=True, format="mixed").min().normalize()
w_from = int((pd.Timestamp(FROM, tz="UTC") - t0).days // 7)

d = pd.read_csv(rows_p)
d["era"] = ["Giappone" if str(c).startswith("ja:") else series_of(str(c).split("/")[0]) for c in d["card"]]
d["band"] = np.where(d["grade"] >= 10, "PSA 10", np.where(d["grade"] >= 9, "PSA 9", "PSA 8 e sotto"))
d["e"] = d["y"] - d["lvm_adj"]
d = d.sort_values("week", kind="stable").reset_index(drop=True)
ev_mask = ((d["week"] >= w_from) & (d["pgen"] >= 0.5)).to_numpy()


def window_q(keys, vals, qs):
    """For each evaluated row: the quantiles qs of vals over the rows of the same key in the 52 weeks before its week,
    and how many rows that is. Computed once per (key, week)."""
    out = np.full((len(d), len(qs)), np.nan)
    n = np.zeros(len(d))
    wk_all = d["week"].to_numpy()
    for _, idx in d.groupby(keys).indices.items():
        wk = wk_all[idx]
        v = vals[idx]
        sel = idx[ev_mask[idx]]
        for w in np.unique(wk_all[sel]):
            lo, hi = np.searchsorted(wk, w - 52, side="left"), np.searchsorted(wk, w, side="left")
            rows = sel[wk_all[sel] == w]
            n[rows] = hi - lo
            if hi > lo:
                out[rows] = np.quantile(v[lo:hi], qs)
    return out, n


def mixed(qs, vals):
    qc, nc = window_q(["card", "grade"], vals, qs)
    qg, ng = window_q(["era", "band"], vals, qs)
    qc = np.where(np.isnan(qc), 0.0, qc)
    return (nc[:, None] * qc + TIE * qg) / (nc[:, None] + TIE), nc


e = d["e"].to_numpy()
hq, n_cg = mixed([0.8], np.abs(e))
d["q_half"] = hq[:, 0]
lh, _ = mixed([0.1, 0.9], e)
d["q2_lo"], d["q2_hi"] = lh[:, 0], lh[:, 1]

ev = d[ev_mask & d["q_half"].notna() & d["q2_lo"].notna()].copy()
ae = ev["e"].abs()


def judge(inside, width):
    terc = pd.qcut(width.rank(method="first"), 3, labels=["bassa", "media", "alta"])
    return dict(cov=round(float(inside.mean()), 4),
                cov_tercile={str(k): round(float(inside[terc == k].mean()), 4) for k in ["bassa", "media", "alta"]},
                rho=round(float(pd.Series(width.to_numpy()).corr(pd.Series(ae.to_numpy()), method="spearman")), 4),
                cov_era={k: round(float(inside[ev["era"] == k].mean()), 4) for k in sorted(ev["era"].unique())},
                cov_bucket={k: round(float(inside[ev["bucket"] == k].mean()), 4) for k in sorted(ev["bucket"].unique())},
                width_median=round(float(width.median()), 4))


A = judge(ae <= 1.2816 * ev["s_pred"], 2 * 1.2816 * ev["s_pred"])
Q = judge(ae <= ev["q_half"], 2 * ev["q_half"])
Q2 = judge((ev["e"] >= ev["q2_lo"]) & (ev["e"] <= ev["q2_hi"]), ev["q2_hi"] - ev["q2_lo"])


def passed(x):
    return dict(S1=0.78 <= x["cov"] <= 0.82, S2=all(0.75 <= v <= 0.85 for v in x["cov_tercile"].values()),
                S3=x["rho"] >= A["rho"] + 0.10, S4=True, S6=True)


pQ, pQ2 = passed(Q), passed(Q2)
ok = [k for k, p in (("Q", pQ), ("Q2", pQ2)) if all(p.values())]
res = dict(n_eval=int(len(ev)), from_=FROM, A=A, Q=Q, Q2=Q2, passed_Q=pQ, passed_Q2=pQ2,
           adopt=ok[0] if ok else None, n_cg_median=float(np.median(n_cg[ev.index])))
os.makedirs(os.path.join(ROOT, "results", "slabrange"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "slabrange", "summary_Q.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
