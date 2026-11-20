"""How many PSA 10 does PSA give today (D334)? From GemRate's set population trends (scripts/browser/gemrate_trend.js):
for each set, the daily cumulative PSA 10 ("gems") and gradings since April 2021. The new slabs of a month are the
difference of the cumulative counts; their PSA 10 share is the month's gem rate. Grouped by site era (sets weighted by
their new slabs). Regrades and crossovers count as new gradings, as in PSA's own population (D109).

Usage: PYTHONPATH=. python scripts/gemrate_severity.py data/raw/gemrate/trend.json [out.json]
"""
import json
import sys
from collections import defaultdict

from slabwise.series import series_of

src = json.load(open(sys.argv[1]))
out_p = sys.argv[2] if len(sys.argv) > 2 else None


def monthly(rows):
    """Last cumulative value of each month -> new gems and gradings per month (negative corrections are kept)."""
    last = {}
    for d, g, t in sorted(rows):
        if g is None or t is None:
            continue
        last[d[:7]] = (g, t)
    ms = sorted(last)
    return {m: (last[m][0] - last[p][0], last[m][1] - last[p][1]) for p, m in zip(ms, ms[1:])}


by_era = defaultdict(lambda: defaultdict(lambda: [0, 0]))
by_set = {}
for s in src:
    try:
        era = series_of(f"{s['set']}-1")
    except Exception:
        era = "?"
    mo = monthly(s["rows"])
    by_set[s["set"]] = dict(era=era, year=s["year"], months={m: [g, t] for m, (g, t) in mo.items()})
    for m, (g, t) in mo.items():
        a = by_era[era][m]
        a[0] += g
        a[1] += t

res = {"by_era": {}, "by_set": by_set}
for era, months in by_era.items():
    res["by_era"][era] = {m: dict(gems=g, grades=t, rate=round(g / t, 4) if t > 0 else None) for m, (g, t) in sorted(months.items())}
if out_p:
    json.dump(res, open(out_p, "w"), indent=1)


def window(months, a, b):
    g = sum(v["gems"] for m, v in months.items() if a <= m <= b)
    t = sum(v["grades"] for m, v in months.items() if a <= m <= b)
    return (g / t if t > 0 else None), t


print("era            2021-07..2022-06    2023-07..2024-06    2025-07..2026-04    2026-05..2026-10")
for era, months in sorted(res["by_era"].items()):
    cells = []
    for a, b in (("2021-07", "2022-06"), ("2023-07", "2024-06"), ("2025-07", "2026-04"), ("2026-05", "2026-10")):
        r, t = window(months, a, b)
        cells.append(f"{100 * r:6.2f}% ({t:>8,})" if r is not None else "      -            ")
    print(f"{era:14s} " + "  ".join(cells))
