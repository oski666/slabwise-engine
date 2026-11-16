"""Protocol §66 (D306): titles naming another grading company with a grade, on tcgcharts' long history.

Usage: PYTHONPATH=. python scripts/other_grader_test.py <tcgcharts dir> [results/other_grader/result.json]
The rule is applied off and on to history.json.gz without the sales already looked at in sales.json (the rule was
written after looking at those). G1 is read by hand from the listed titles; G2 and G3 are computed here.
"""
import gzip
import json
import os
import random
import sys
import tempfile
from collections import Counter
from datetime import date, timedelta

tc = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "other_grader", "result.json")
seen = {s["sale_id"] for s in json.load(open(os.path.join(tc, "sales.json")))}
hist = [s for s in json.load(gzip.open(os.path.join(tc, "history.json.gz"), "rt"))
        if s["sale_id"] not in seen and (s.get("sold_date") or "") >= "2022-07-01"]
work = tempfile.mkdtemp()
json.dump(hist, open(os.path.join(work, "sales.json"), "w"))
del hist

from slabwise.sources import auction_titles as at  # noqa: E402
from slabwise.sources.tcgcharts_merge import tcgcharts_rows  # noqa: E402

os.environ.pop("SLABWISE_TC_HISTORY", None)
at.OTHER_GRADER_ON = False
off, _ = tcgcharts_rows(work, set(), (), ja=True)
at.OTHER_GRADER_ON = True
on, why = tcgcharts_rows(work, set(), (), ja=True)
kept = {r["item_id"] for r in on}
removed = [r for r in off if r["item_id"] not in kept]

last = max(r["date"][:10] for r in off)
since = (date.fromisoformat(last) - timedelta(days=365)).isoformat()
n_off, n_on = Counter(r["card"] for r in off if r["date"][:10] >= since), Counter(r["card"] for r in on if r["date"][:10] >= since)
below = sorted(c for c in n_off if n_off[c] >= 10 and n_on[c] < 10)

random.seed(66)
sample = removed if len(removed) <= 40 else random.sample(removed, 40)
res = dict(n_off=len(off), n_on=len(on), removed=len(removed), share=round(len(removed) / max(1, len(off)), 6),
           G2=len(removed) / max(1, len(off)) <= 0.001, below_threshold=below, G3=not below,
           by_company=Counter(at.OTHER_GRADER.search(r["title"]).group(0).split()[0].upper().rstrip("0123456789") for r in removed),
           to_read=[dict(card=r["card"], grade=r["grade"], venue=r["venue"], date=r["date"][:10]) for r in sample])
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if k != "to_read"}, ensure_ascii=False))
for r in sample:                       # titles printed for reading, never written to the public results (D163)
    print(f"  {r['card']} PSA {r['grade']} ${r['price_usd']} {r['venue']} {r['date'][:10]} | {r['title']}")
