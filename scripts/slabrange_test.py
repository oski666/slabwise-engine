"""Protocol §61 (D274), arm B against the sample A: the SlabRange of each card x grade from its own recent errors.

A = the engine of the site (v1.20) with its band (s_pred, as on the site). B = the same values; the band of a sale is
1.2816 x s, where s^2 = (n s_cg^2 + 10 s_eb^2) / (n + 10): s_cg is the root mean square of the errors (sale minus the
value of the week before) of the same card x grade over the 52 weeks before the sale's week, n how many, and s_eb the
same over the sale's site era x grade band (PSA 10, PSA 9, PSA 8 and below). Only sales before the sale's week (P11).
B leaves the values unchanged, so S4 and S6 hold by construction; S5 is for C and D only.
Evaluation: sales from 1 November 2025 with genuine probability >= 0.5.

Usage: PYTHONPATH=. python scripts/slabrange_test.py <work dir>       Writes results/slabrange/summary.json.
"""
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from slabwise.series import series_of  # noqa: E402
from slabwise.suspects import flag  # noqa: E402

work = sys.argv[1]
os.makedirs(work, exist_ok=True)
RAW = os.path.join(ROOT, "data", "raw")
ERA = os.path.join(RAW, "era_map.json")
Z = 1.2816
TIE = 10.0                     # fixed in §61 before the results
FROM = "2025-11-01"


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
rows_p = os.path.join(work, "rows_A.csv")
if not os.path.exists(rows_p):
    run([os.path.join(ROOT, "scripts", "real_phase_r.py"), sales, ERA, os.path.join(work, "phase_r_A.json"), "--adopted", "--v120"],
        dict(SITE, PHASE_R_ROWS=rows_p), os.path.join(work, "phase_r_A.txt"))

raw = pd.read_csv(sales, usecols=["item_id", "date", "card", "grade", "price_usd", "excluded"], low_memory=False)
t0 = pd.to_datetime(raw.loc[raw["excluded"].isna() | (raw["excluded"] == ""), "date"], utc=True, format="mixed").min().normalize()
w_from = int((pd.Timestamp(FROM, tz="UTC") - t0).days // 7)

d = pd.read_csv(rows_p)
d["era"] = ["Giappone" if str(c).startswith("ja:") else series_of(str(c).split("/")[0]) for c in d["card"]]
d["band"] = np.where(d["grade"] >= 10, "PSA 10", np.where(d["grade"] >= 9, "PSA 9", "PSA 8 e sotto"))
d["e"] = d["y"] - d["lvm_adj"]
d = d.sort_values(["week"]).reset_index(drop=True)

# arm B: running sums of squared errors per key over the 52 weeks before the sale's week
def rms_before(keys):
    out_ss, out_n = np.zeros(len(d)), np.zeros(len(d))
    for _, idx in d.groupby(keys).indices.items():
        wk = d["week"].to_numpy()[idx]
        e2 = d["e"].to_numpy()[idx] ** 2
        cs = np.concatenate([[0.0], np.cumsum(e2)])
        lo = np.searchsorted(wk, wk - 52, side="left")
        hi = np.searchsorted(wk, wk, side="left")      # strictly before the sale's week
        out_ss[idx] = cs[hi] - cs[lo]
        out_n[idx] = hi - lo
    return out_ss, out_n


ss_cg, n_cg = rms_before(["card", "grade"])
ss_eb, n_eb = rms_before(["era", "band"])
s_eb2 = np.where(n_eb > 0, ss_eb / np.maximum(n_eb, 1), np.nan)
s_cg2 = np.where(n_cg > 0, ss_cg / np.maximum(n_cg, 1), 0.0)
d["s_B"] = np.sqrt((n_cg * s_cg2 + TIE * s_eb2) / (n_cg + TIE))
d["s_A"] = d["s_pred"]

ev = d[(d["week"] >= w_from) & (d["pgen"] >= 0.5) & d["s_B"].notna()].copy()
ae = ev["e"].abs()


def arm(s):
    s = ev[s]
    inside = ae <= Z * s
    terc = pd.qcut(s.rank(method="first"), 3, labels=["bassa", "media", "alta"])
    by_t = {str(k): round(float(inside[terc == k].mean()), 4) for k in ["bassa", "media", "alta"]}
    rho = float(pd.Series(s.to_numpy()).corr(pd.Series(ae.to_numpy()), method="spearman"))
    return dict(cov=round(float(inside.mean()), 4), cov_tercile=by_t, rho=round(rho, 4),
                cov_era={k: round(float(inside[ev["era"] == k].mean()), 4) for k in sorted(ev["era"].unique())},
                cov_bucket={k: round(float(inside[ev["bucket"] == k].mean()), 4) for k in sorted(ev["bucket"].unique())})


A, B = arm("s_A"), arm("s_B")
passed = dict(S1=0.78 <= B["cov"] <= 0.82, S2=all(0.75 <= v <= 0.85 for v in B["cov_tercile"].values()),
              S3=B["rho"] >= A["rho"] + 0.10, S4=True, S6=True)

# exceptions of the data (§61): flagged by the rule and confirmed by Oscar, per era
s_all = raw.copy()
s_all["excluded"] = s_all["excluded"].fillna("")
susp = flag(s_all.to_dict("records"))
s_all["era"] = ["Giappone" if str(c).startswith("ja:") else series_of(str(c).split("/")[0]) for c in s_all["card"]]
conf = s_all["excluded"].fillna("").astype(str).str.startswith("esclusa da Oscar")
exc = dict(flagged=dict(Counter(s_all.loc[s_all["item_id"].isin(susp), "era"])), confirmed=dict(Counter(s_all.loc[conf, "era"])),
           flagged_total=len(susp), confirmed_total=int(conf.sum()),
           note="con e senza eccezioni il campione è lo stesso finché le confermate sono zero")

res = dict(n_eval=int(len(ev)), from_=FROM, weeks_from=w_from, A=A, B=B, passed_B=passed, B_adopted_round1=all(passed.values()),
           exceptions=exc, n_cg_median=float(np.median(n_cg[ev.index])))
os.makedirs(os.path.join(ROOT, "results", "slabrange"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "slabrange", "summary.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
