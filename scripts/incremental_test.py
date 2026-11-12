"""Protocol §60 (D270): adding cards without a rebuild.

  drop    GROUP_JSON SALES_CSV OUT_CSV      the sales without the group's cards (and their variants)
  compare GROUP_JSON A_OUT B_OUT C_OUT B_SECONDS C_SECONDS RESULT_JSON
          I1 old cards: B identical to A; I2 new cards: |log(B/C)| median <= 2%, 95th percentile <= 10%;
          I3 new cards: SlabRange coverage of their sales of the last 13 weeks, B >= C - 2 points;
          I4 time of the whole incremental build under 10 minutes, whatever the group's size (stricter than '20 cards')
"""
import csv
import json
import math
import sys
from datetime import date, timedelta


def _base(c):
    return c.split("/")[0]


def drop(group, src, out):
    g = set(json.load(open(group)))
    with open(src, newline="") as fi, open(out, "w", newline="") as fo:
        r = csv.DictReader(fi)
        w = csv.DictWriter(fo, fieldnames=r.fieldnames)
        w.writeheader()
        n = k = 0
        for row in r:
            n += 1
            if row["card"] in g or _base(row["card"]) in g:
                continue
            w.writerow(row)
            k += 1
    print(f"§60: {n - k} vendite del gruppo tolte su {n}")


def _vals(path):
    d = json.load(open(path))
    out, sales, asof = {}, {}, d.get("asof")
    for c in d["cards"]:
        for g in c.get("grades", []):
            out[(c["id"], g.get("grade"))] = (g.get("value"), g.get("slo"), g.get("shi"))
        sales[c["id"]] = c.get("sales", [])
    return out, sales, asof


def _pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def _coverage(vals, sales, ids, asof):
    since = str(date.fromisoformat(asof) - timedelta(weeks=13))
    n = hit = 0
    for cid in ids:
        for s in sales.get(cid, []):
            if s["date"] < since or (s.get("pgen") or 0) < 0.5:
                continue
            v = vals.get((cid, s["grade"]))
            if not v or v[1] is None or v[2] is None:
                continue
            n += 1
            hit += v[1] <= s["price"] <= v[2]
    return (hit / n if n else None), n


def compare(group, a_out, b_out, c_out, b_sec, c_sec, result):
    g = set(json.load(open(group)))
    a, _, _ = _vals(a_out)
    b, b_sales, asof = _vals(b_out)
    c, c_sales, _ = _vals(c_out)
    old = [k for k in a]
    i1_diff = [f"{k[0]} PSA {k[1]}" for k in old if a[k] != b.get(k)]
    new = [k for k in b if k not in a and (k[0] in g or _base(k[0]) in g)]
    errs = [abs(math.log(b[k][0] / c[k][0])) for k in new if k in c and b[k][0] and c[k][0]]
    new_ids = sorted({k[0] for k in new})
    cov_b, nb = _coverage(b, b_sales, new_ids, asof)
    cov_c, nc = _coverage(c, c_sales, new_ids, asof)
    secs = float(open(b_sec).read().strip())
    res = dict(
        group=group, cards_new=len(new_ids), atoms_new=len(new), atoms_old=len(old),
        I1=dict(different=len(i1_diff), examples=i1_diff[:10], passed=not i1_diff),
        I2=dict(n=len(errs), median=_pct(errs, 0.5), p95=_pct(errs, 0.95),
                passed=bool(errs) and _pct(errs, 0.5) <= 0.02 and _pct(errs, 0.95) <= 0.10),
        I3=dict(coverage_B=cov_b, coverage_C=cov_c, sales=nb,
                passed=cov_b is not None and cov_c is not None and cov_b >= cov_c - 0.02),
        I4=dict(seconds_B=secs, seconds_C=float(open(c_sec).read().strip()), passed=secs < 600),
    )
    res["passed"] = all(res[k]["passed"] for k in ("I1", "I2", "I3", "I4"))
    json.dump(res, open(result, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"drop": drop, "compare": compare}[sys.argv[1]](*sys.argv[2:])
