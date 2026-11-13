"""Protocol §61 (D274, D293), arms C and D against the sample A (the site's engine, v1.20).

C: the model's sale noise per card x grade from its own errors of the 52 weeks before, shrunk towards its site era x
grade band with weight n/(n+10) (LVMParams.card_noise); the SlabRange as in arm B, from C's own errors.
D: C, and the era factor split by grade band (only when written: LVMParams.band_factors).
S1-S3 on the band as in B; S4 median absolute error (total and per liquidity bucket) not above A's by more than 1%
relative; S5 mean over era x band cells with >= 200 sales of |median signed error| <= 75% of A's; S6 lag as in §57 not
worse than A. Evaluation: sales from 1 November 2025 with A's genuine probability >= 0.5, common to both arms.

Usage: PYTHONPATH=. python scripts/slabrange_cd_test.py <work dir> C|D      Writes results/slabrange/summary_<arm>.json.
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

work, ARM = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)
RAW = os.path.join(ROOT, "data", "raw")
ERA = os.path.join(RAW, "era_map.json")
Z, TIE, FROM = 1.2816, 10.0, "2025-11-01"
FLAGS = {"A": [], "C": ["--card_noise"], "D": ["--card_noise", "--band_factors"]}


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
SITE = {"SLABWISE_TC_HISTORY": "1", "SLABWISE_REVIEW_RECENT": "1", "SLABWISE_GRADE_JUMP": "1"}


def rows_of(name):
    p = os.path.join(work, f"rows_{name}.csv")
    if not os.path.exists(p):
        run([os.path.join(ROOT, "scripts", "real_phase_r.py"), sales, ERA, os.path.join(work, f"phase_r_{name}.json"), "--adopted",
             "--v120"] + FLAGS[name], dict(SITE, PHASE_R_ROWS=p), os.path.join(work, f"phase_r_{name}.txt"))
    d = pd.read_csv(p)
    d["era"] = ["Giappone" if str(c).startswith("ja:") else series_of(str(c).split("/")[0]) for c in d["card"]]
    d["band"] = np.where(d["grade"] >= 10, "PSA 10", np.where(d["grade"] >= 9, "PSA 9", "PSA 8 e sotto"))
    d["e"] = d["y"] - d["lvm_adj"]
    d = d.sort_values(["week"], kind="stable").reset_index(drop=True)

    def rms_before(keys):
        ss, n = np.zeros(len(d)), np.zeros(len(d))
        for _, idx in d.groupby(keys).indices.items():
            wk = d["week"].to_numpy()[idx]
            cs = np.concatenate([[0.0], np.cumsum(d["e"].to_numpy()[idx] ** 2)])
            lo, hi = np.searchsorted(wk, wk - 52, side="left"), np.searchsorted(wk, wk, side="left")
            ss[idx], n[idx] = cs[hi] - cs[lo], hi - lo
        return ss, n
    ss_cg, n_cg = rms_before(["card", "grade"])
    ss_eb, n_eb = rms_before(["era", "band"])
    s_eb2 = np.where(n_eb > 0, ss_eb / np.maximum(n_eb, 1), np.nan)
    d["s_band"] = np.sqrt((ss_cg + TIE * s_eb2) / (n_cg + TIE))
    return d.drop_duplicates("item_id").set_index("item_id")


raw = pd.read_csv(sales, usecols=["date", "excluded"], low_memory=False)
t0 = pd.to_datetime(raw.loc[raw["excluded"].isna() | (raw["excluded"] == ""), "date"], utc=True, format="mixed").min().normalize()
w_from = int((pd.Timestamp(FROM, tz="UTC") - t0).days // 7)

A, X = rows_of("A"), rows_of(ARM)
keep = A.index[(A["week"] >= w_from) & (A["pgen"] >= 0.5)].intersection(X.index[X["s_band"].notna()])
A, X = A.loc[keep], X.loc[keep]


def bands(d, s):
    ae = d["e"].abs()
    inside = ae <= Z * s
    terc = pd.qcut(s.rank(method="first"), 3, labels=["bassa", "media", "alta"])
    return dict(cov=round(float(inside.mean()), 4),
                cov_tercile={str(k): round(float(inside[terc == k].mean()), 4) for k in ["bassa", "media", "alta"]},
                rho=round(float(pd.Series(s.to_numpy()).corr(pd.Series(ae.to_numpy()), method="spearman")), 4),
                cov_era={k: round(float(inside[d["era"] == k].mean()), 4) for k in sorted(d["era"].unique())})


def err(d):
    ae = d["e"].abs()
    return dict(total=float(ae.median()), **{b: float(ae[d["bucket"] == b].median()) for b in sorted(d["bucket"].unique())})


def bias(d):
    g = d.groupby(["era", "band"])["e"].agg(["median", "size"])
    g = g[g["size"] >= 200]
    return float(g["median"].abs().mean()), {f"{a} · {b}": round(float(m), 4) for (a, b), m in g["median"].items()}


def lag(d):
    """As §57 Y7: per (site era, week) cell with >= 30 sales in the last 26 weeks, |median signed error|; mean."""
    x = d[d["week"] > d["week"].max() - 26]
    g = x.groupby(["era", "week"])["e"].agg(["median", "size"])
    g = g[g["size"] >= 30]
    return float(g["median"].abs().mean())


bA, bX = bands(A, A["s_pred"]), bands(X, X["s_band"])
eA, eX = err(A), err(X)
sA, cA = bias(A)
sX, cX = bias(X)
lA, lX = lag(A), lag(X)
passed = dict(S1=0.78 <= bX["cov"] <= 0.82, S2=all(0.75 <= v <= 0.85 for v in bX["cov_tercile"].values()),
              S3=bX["rho"] >= bA["rho"] + 0.10, S4=all(eX[k] <= eA[k] * 1.01 for k in eA), S5=sX <= 0.75 * sA, S6=lX <= lA)
res = dict(arm=ARM, n_eval=int(len(keep)), from_=FROM, band_A=bA, band=bX, err_A=eA, err=eX, S5_A=round(sA, 4), S5=round(sX, 4),
           cells_A=cA, cells=cX, lag_A=round(lA, 4), lag=round(lX, 4), passed=passed, all_passed=all(passed.values()))
os.makedirs(os.path.join(ROOT, "results", "slabrange"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "slabrange", f"summary_{ARM}.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
