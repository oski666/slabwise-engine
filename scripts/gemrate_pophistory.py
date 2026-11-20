"""Keep every GemRate read of the card populations, not only the last one (D335).

Usage: python scripts/gemrate_pophistory.py data/raw/gemrate/tap.json data/raw/gemrate/pop_history.json

tap.json (scripts/gemrate_tap.py) holds the last read: per card the PSA population by grade, the read date ("updated"),
the 52-week cumulative trend of all PSA gradings and the new PSA 10 of the last two 30-day periods.
pop_history.json: {card: [[date, psa10, psa9, total, kind], ...]} sorted by date, one row per date.
kind "r": a read (exact counts on that date); "t": total gradings from the weekly trend of a read (psa10, psa9 null);
"d": PSA 10 on the day 30 and 60 days before a read, from the 30-day increments (psa9, total null).
"t" and "d" rows are written only for dates with no "r" row, and a later "r" row on the same date replaces them.
Nothing here enters the prices.
"""
import datetime as dt
import json
import os
import sys

src, dst = sys.argv[1], sys.argv[2]
tap = json.load(open(src))
hist = json.load(open(dst)) if os.path.exists(dst) else {}
RANK = {"r": 2, "t": 1, "d": 1}


def put(rows, row):
    """Add row; on the same date a read wins over a derived row, two derived rows merge their non-null fields."""
    for i, old in enumerate(rows):
        if old[0] == row[0]:
            if RANK[row[4]] > RANK[old[4]]:
                rows[i] = row
            elif RANK[row[4]] == RANK[old[4]] and old[4] != "r":
                rows[i] = [old[0]] + [a if a is not None else b for a, b in zip(old[1:4], row[1:4])] + [old[4]]
            return
    rows.append(row)


n_new = 0
for card, e in tap.items():
    day = (e.get("updated") or "")[:10]
    if not day:
        continue
    rows = hist.setdefault(card, [])
    d0 = dt.date.fromisoformat(day)
    before = len(rows)
    put(rows, [day, e.get("psa10"), e.get("psa9"), e.get("total"), "r"])
    tr = e.get("trend") or []
    for i, v in enumerate(tr[:-1]):                       # the last trend point is the read itself
        put(rows, [str(d0 - dt.timedelta(weeks=len(tr) - 1 - i)), None, None, int(v), "t"])
    p10, p1, p2 = e.get("psa10"), e.get("new_psa10_p1"), e.get("new_psa10_p2")
    if p10 is not None and p1 is not None:
        put(rows, [str(d0 - dt.timedelta(days=30)), p10 - p1, None, None, "d"])
        if p2 is not None:
            put(rows, [str(d0 - dt.timedelta(days=60)), p10 - p1 - p2, None, None, "d"])
    rows.sort(key=lambda r: r[0])
    n_new += len(rows) > before
json.dump(hist, open(dst, "w"), separators=(",", ":"))
reads = sorted({r[0] for v in hist.values() for r in v if r[4] == "r"})
print(f"{len(hist)} carte, {n_new} aggiornate; letture conservate: {len(reads)} ({reads[0] if reads else '-'} .. {reads[-1] if reads else '-'}) -> {dst}")
