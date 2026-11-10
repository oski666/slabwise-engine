"""Protocol §56 (D258): today's rule (match_title gives the assigned card) against accept_assigned.

Usage: PYTHONPATH=. python scripts/assign_test.py <history.json.gz> results/d258/
Writes summary.json (A2, A3) and sample.json (100 titles kept by the new rule only, for the hand reading of A1).
"""
import gzip
import json
import os
import random
import sys
from collections import Counter

from slabwise.sources import auction_titles as at

h = json.load(gzip.open(sys.argv[1], "rt"))
out = sys.argv[2]
rows = [r for r in h if (r.get("sold_date") or "") >= "2025-11-10" and (r.get("grading_service") or "PSA") == "PSA" and not r.get("is_excluded")]
old = new = lost = 0
only_new, why = [], Counter()
for r in rows:
    o = at.match_title(r.get("title") or "")[0] == r["card"]
    n, reason = at.accept_assigned(r.get("title") or "", r["card"])
    old += o
    new += n
    why[reason] += 1
    if o and not n:
        lost += 1
    if n and not o:
        only_new.append((r["card"], r.get("title")))
random.seed(56)
sample = random.sample(only_new, min(100, len(only_new)))
res = dict(sales=len(rows), old_share=round(old / len(rows), 4), new_share=round(new / len(rows), 4), A2_lost=lost,
           A3=bool(new / len(rows) >= 0.95), only_new=len(only_new), reasons=dict(why.most_common()))
os.makedirs(out, exist_ok=True)
json.dump(res, open(os.path.join(out, "summary.json"), "w"), indent=1, ensure_ascii=False)
json.dump(sample, open(os.path.join(out, "sample.json"), "w"), indent=0, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
