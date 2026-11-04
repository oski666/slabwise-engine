"""Keep every tcgcharts sale seen so far (the site shows a rolling 90-day window): old + new, one per sale.

Usage: python scripts/tcgcharts_accumulate.py <old sales.json> <new sales.json> <out sales.json>
"""
import json
import os
import sys

old_p, new_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
old = json.load(open(old_p)) if os.path.exists(old_p) else []
new = json.load(open(new_p))
seen, merged = set(), []
for s in new + old:                    # the newest copy of a sale wins (payment flags can change)
    k = (s.get("platform"), s.get("sale_id"), s.get("card"))
    if k in seen:
        continue
    seen.add(k)
    merged.append(s)
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
json.dump(merged, open(out, "w"), ensure_ascii=False)
print(f"{len(old)} vecchie + {len(new)} nuove -> {len(merged)} vendite in {out}")
