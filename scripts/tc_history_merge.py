"""Merge an export of scripts/browser/tc_history.js into data/raw/tcgcharts/history.json.gz (D123).

Usage: python scripts/tc_history_merge.py <export.json> [data/raw/tcgcharts/history.json.gz]
A sale already in the archive (same card, grade and tcgcharts sale id) is kept once; payment and exclusion flags
take the newer value, so a sale "payment pending" yesterday becomes a normal sale when tcgcharts confirms it.
"""
import gzip
import json
import sys

new = json.load(open(sys.argv[1]))
path = sys.argv[2] if len(sys.argv) > 2 else "data/raw/tcgcharts/history.json.gz"
hist = json.load(gzip.open(path, "rt"))
key = lambda r: (r["card"], r["tc_grade"], r["sale_id"])  # noqa: E731
at = {key(r): i for i, r in enumerate(hist)}
added = updated = 0
for r in new:
    i = at.get(key(r))
    if i is None:
        hist.append(r)
        at[key(r)] = len(hist) - 1
        added += 1
    elif hist[i] != r:
        hist[i] = r
        updated += 1
json.dump(hist, gzip.open(path, "wt"), ensure_ascii=False, separators=(",", ":"))
print(f"{added} nuove, {updated} aggiornate, {len(hist)} in tutto, {len({r['card'] for r in hist})} carte")
