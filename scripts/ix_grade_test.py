"""Protocol §59 (D266), report only: the era indices built from one grade (PSA 10, 9 or 8) against the index in use.

Usage: python scripts/ix_grade_test.py results/ix_grade/series.json
For each era: return over the last 13, 26 and 52 weeks of each index; median over the weeks since 2024 of
|13-week return of the PSA 9 index - of the PSA 10 index| (and PSA 8 - PSA 9); correlation of the 4-week changes;
seats at the last rebalance. Writes results/ix_grade/summary.json.
"""
import json
import os
import sys

import numpy as np

S = json.load(open(sys.argv[1]))
weeks = S["weeks"]
arr = lambda v: np.array([np.nan if x is None else x for x in v], float)   # noqa: E731


def ret(x, k):
    ok = [w for w in range(len(x)) if np.isfinite(x[w])]
    return None if not ok or ok[-1] - k < ok[0] else round(float(np.expm1(x[ok[-1]] - x[ok[-1] - k])), 4)


def gap(a, b, k=13):
    use = [w for w in range(k, len(weeks)) if weeks[w] >= "2024-01-05" and all(np.isfinite(v) for v in (a[w], a[w - k], b[w], b[w - k]))]
    if len(use) < 10:
        return None, None, 0
    da = np.array([a[w] - a[w - k] for w in use]); db = np.array([b[w] - b[w - k] for w in use])
    c4 = [w for w in range(4, len(weeks)) if weeks[w] >= "2024-01-05" and all(np.isfinite(v) for v in (a[w], a[w - 4], b[w], b[w - 4]))]
    cor = float(np.corrcoef([a[w] - a[w - 4] for w in c4], [b[w] - b[w - 4] for w in c4])[0, 1]) if len(c4) > 10 else None
    return round(float(np.median(np.abs(np.expm1(da) - np.expm1(db)))), 4), (round(cor, 3) if cor is not None else None), len(use)


out = {}
for era, d in S["eras"].items():
    X = {k: arr(v) for k, v in d.items() if k != "seats"}
    r = {k: {f"w{n}": ret(x, n) for n in (13, 26, 52)} for k, x in X.items()}
    g9_10 = gap(X["psa9"], X["psa10"]); g8_9 = gap(X["psa8"], X["psa9"])
    out[era] = dict(returns=r, seats=d["seats"],
                    gap13_psa9_vs_psa10=dict(median=g9_10[0], corr4w=g9_10[1], weeks=g9_10[2]),
                    gap13_psa8_vs_psa9=dict(median=g8_9[0], corr4w=g8_9[1], weeks=g8_9[2]))
path = os.path.join(os.path.dirname(sys.argv[1]), "summary.json")
json.dump(out, open(path, "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
