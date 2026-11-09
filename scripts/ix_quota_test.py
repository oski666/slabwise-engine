"""Protocol §51 (D245): a general index with 12 seats per era (Q) against today's general index (A).

Usage: python scripts/ix_quota_test.py results/ix_quota/series.json [base week, default 2024-01-05]
Reads the series written by prototype/build_real_data.py with SLABWISE_IX_QUOTA_TEST=1 and writes
results/ix_quota/summary.json with Q1-Q4 and the adoption verdict.
  Q1 every era with >= 12 eligible items has at least 12 seats at every rebalance (amended before the test, see §51)
  Q2 median |13-week return of Q - of M| < the same for A (M: the five era indices, equal weights)
  Q3 volatility of Q (weekly log changes, last 26 weeks, x sqrt 52) <= 1.5 x that of A
  Q4 no weekly change of Q beyond +-15%
Protocol §53 (D251), the Japanese index: SEATS=5 Q3VS=M (volatility against the mean of the Japanese eras).
"""
import json
import os
import sys

import numpy as np

S = json.load(open(sys.argv[1]))
base = sys.argv[2] if len(sys.argv) > 2 else "2024-01-05"
SEATS = int(os.environ.get("SEATS", "12"))
Q3VS = os.environ.get("Q3VS", "A")
weeks = S["weeks"]
arr = lambda v: np.array([np.nan if x is None else x for x in v], float)   # noqa: E731
A, Q = arr(S["A"]), arr(S["Q"])
E = {k: arr(v) for k, v in S["eras"].items()}
# M: each week the mean of the eras' log changes (eras with a level both weeks), chained
M = np.full(len(weeks), np.nan)
for w in range(1, len(weeks)):
    d = [e[w] - e[w - 1] for e in E.values() if np.isfinite(e[w]) and np.isfinite(e[w - 1])]
    if d:
        M[w] = (M[w - 1] if np.isfinite(M[w - 1]) else 0.0) + float(np.mean(d))
use = [w for w in range(13, len(weeks)) if weeks[w] >= base and all(np.isfinite(x[w]) and np.isfinite(x[w - 13]) for x in (A, Q, M))]
r13 = lambda x: np.array([x[w] - x[w - 13] for w in use])   # noqa: E731
gapQ, gapA = float(np.median(np.abs(r13(Q) - r13(M)))), float(np.median(np.abs(r13(A) - r13(M))))
last = [w for w in range(len(weeks) - 26, len(weeks)) if all(np.isfinite(x[w]) and np.isfinite(x[w - 1]) for x in (Q, A, M))]
vol = lambda x: float(np.std([x[w] - x[w - 1] for w in last], ddof=1) * np.sqrt(52))   # noqa: E731
qw = [w for w in range(1, len(weeks)) if weeks[w] >= base and np.isfinite(Q[w]) and np.isfinite(Q[w - 1])]
jump = max(abs(np.exp(Q[w] - Q[w - 1]) - 1) for w in qw)
q1_bad = [(weeks[w], g, el, st) for w, d in S["quota_log"] for g, (el, st) in d.items() if el >= SEATS and st < SEATS]
res = dict(
    weeks_compared=len(use),
    Q1=dict(passed=not q1_bad, cases=q1_bad[:10], last_seats=S["quota_log"][-1] if S["quota_log"] else None),
    Q2=dict(passed=bool(gapQ < gapA), median_gap_Q=round(gapQ, 4), median_gap_A=round(gapA, 4)),
    Q3=dict(passed=bool(vol(Q) <= 1.5 * vol(M if Q3VS == "M" else A)), against=Q3VS, vol_Q=round(vol(Q), 4), vol_A=round(vol(A), 4), vol_M=round(vol(M), 4)),
    Q4=dict(passed=bool(jump <= 0.15), max_weekly_change=round(float(jump), 4)),
    A_last_basket={g: S["A_baskets"][-1][1].count(g) for g in set(S["A_baskets"][-1][1])} if S["A_baskets"] else None,
    returns_13w_last=dict(A=round(float(A[-1] - A[-14]), 4), Q=round(float(Q[-1] - Q[-14]), 4), M=round(float(M[-1] - M[-14]), 4)),
)
res["adopt"] = bool(all(res[k]["passed"] for k in ("Q1", "Q2", "Q3", "Q4")))
out = os.path.join(os.path.dirname(sys.argv[1]), "summary.json")
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
