"""Protocol §60 (D270): adding cards without a rebuild; protocol §68 (D322): a long history without a rebuild.

  drop_old GROUP_JSON SALES_CSV OUT_CSV   §68: the sales without the group's sales older than 13 weeks before the last one
  compare68 GROUP_JSON A_OUT B_OUT C_OUT B_SECONDS RESULT_JSON
          H1 cards outside the group: B identical to A; H2 group cards: |log(B/C)| median <= 2%, 95th percentile <= 10%;
          H3 group cards: SlabRange coverage of their sales of the last 13 weeks, B >= C - 2 points; H4 era, Japan and
          general indices: weekly change of the last 13 weeks, median |B - C| <= 0.5 points; H5 time of B under 15 minutes

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


def drop_old(group, src, out):
    g = set(json.load(open(group)))
    with open(src, newline="") as fi:
        last = max(row["date"][:10] for row in csv.DictReader(fi))
    cut = str(date.fromisoformat(last) - timedelta(weeks=13))
    with open(src, newline="") as fi, open(out, "w", newline="") as fo:
        r = csv.DictReader(fi)
        w = csv.DictWriter(fo, fieldnames=r.fieldnames)
        w.writeheader()
        n = k = 0
        for row in r:
            n += 1
            if (row["card"] in g or _base(row["card"]) in g) and row["date"][:10] < cut:
                continue
            w.writerow(row)
            k += 1
    print(f"§68: {n - k} vendite del gruppo prima del {cut} tolte su {n}")


def _weekly(out):
    d = json.load(open(out))
    series = {k: v.get("points") for k, v in (d.get("indexes") or {}).items()}
    if isinstance(d.get("index_all"), dict):
        series["generale"] = d["index_all"].get("points")
    res = {}
    for k, pts in series.items():
        pts = [p for p in (pts or []) if p[1]]
        res[k] = {pts[i][0]: pts[i][1] / pts[i - 1][1] - 1 for i in range(1, len(pts))}
    return res


def compare68(group, a_out, b_out, c_out, b_sec, result):
    g = set(json.load(open(group)))
    a, _, _ = _vals(a_out)
    b, b_sales, asof = _vals(b_out)
    c, c_sales, _ = _vals(c_out)
    ing = lambda k: k[0] in g or _base(k[0]) in g  # noqa: E731
    h1 = [f"{k[0]} PSA {k[1]}" for k in a if not ing(k) and a[k] != b.get(k)]
    grp = [k for k in b if ing(k) and k in c and b[k][0] and c[k][0]]
    errs = [abs(math.log(b[k][0] / c[k][0])) for k in grp]
    ids = sorted({k[0] for k in b if ing(k)})
    cov_b, nb = _coverage(b, b_sales, ids, asof)
    cov_c, _ = _coverage(c, c_sales, ids, asof)
    wb, wc = _weekly(b_out), _weekly(c_out)
    diffs = []
    for k in wb:
        common = sorted(set(wb[k]) & set(wc.get(k, {})))[-13:]
        diffs += [abs(wb[k][x] - wc[k][x]) for x in common]
    secs = float(open(b_sec).read().strip())
    res = dict(
        group=group, cards=len(ids), atoms=len(grp),
        H1=dict(different=len(h1), examples=h1[:10], passed=not h1),
        H2=dict(n=len(errs), median=_pct(errs, 0.5), p95=_pct(errs, 0.95),
                passed=bool(errs) and _pct(errs, 0.5) <= 0.02 and _pct(errs, 0.95) <= 0.10),
        H3=dict(coverage_B=cov_b, coverage_C=cov_c, sales=nb,
                passed=cov_b is not None and cov_c is not None and cov_b >= cov_c - 0.02),
        H4=dict(n=len(diffs), median=_pct(diffs, 0.5), p95=_pct(diffs, 0.95),
                passed=bool(diffs) and _pct(diffs, 0.5) <= 0.005),
        H5=dict(seconds_B=secs, passed=secs < 900),
    )
    res["passed"] = all(res[k]["passed"] for k in ("H1", "H2", "H3", "H4", "H5"))
    json.dump(res, open(result, "w"), indent=1)
    print(json.dumps(res, indent=1))


def compare68b(group, a_out, b_out, c_out, b_sec, c_sec, result):
    """§68b: H1b (other cards, 99th percentile of |log(B/A)| <= 2%) and H5b (B at most a third of C) in place of H1, H5."""
    compare68(group, a_out, b_out, c_out, b_sec, result)
    res = json.load(open(result))
    g = set(json.load(open(group)))
    a, _, _ = _vals(a_out)
    b, _, _ = _vals(b_out)
    d = [abs(math.log(b[k][0] / a[k][0])) for k in a if not (k[0] in g or _base(k[0]) in g) and k in b and a[k][0] and b[k][0]]
    res["H1b"] = dict(n=len(d), p99=_pct(d, 0.99), max=max(d) if d else None, passed=bool(d) and _pct(d, 0.99) <= 0.02)
    sb, sc = float(open(b_sec).read().strip()), float(open(c_sec).read().strip())
    res["H5b"] = dict(seconds_B=sb, seconds_C=sc, passed=sb <= sc / 3)
    res["passed"] = all(res[k]["passed"] for k in ("H1b", "H2", "H3", "H4", "H5b"))
    json.dump(res, open(result, "w"), indent=1)
    print("§68b", {k: res[k]["passed"] for k in ("H1b", "H2", "H3", "H4", "H5b")}, "->", res["passed"])


if __name__ == "__main__":
    {"drop": drop, "compare": compare, "drop_old": drop_old, "compare68": compare68, "compare68b": compare68b}[sys.argv[1]](*sys.argv[2:])
