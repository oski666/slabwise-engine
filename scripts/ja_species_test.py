"""Protocol §47 (D237): Japanese species names (PokeAPI) must not change how today's catalogue reads any title.

Usage: PYTHONPATH=. python scripts/ja_promo_noname_test.py <history.json.gz> <sales.json> [out.json]
Z1: no title of a catalogue card goes to another card; Z2: none becomes ambiguous or unread; Z3: the extra titles
read for catalogue cards are printed (a sample of 20) for reading by hand.
"""
import gzip
import json
import random
import sys

from slabwise.sources import auction_titles as at

titles = {s.get("title") or "" for s in json.load(gzip.open(sys.argv[1], "rt"))} | {s.get("title") or "" for s in json.load(open(sys.argv[2]))}
titles = sorted(t for t in titles if t and at.is_japanese(t))
res = {}
for flag in (False, True):
    at.JA_SPECIES = flag
    res[flag] = {t: at.match_title(t)[0] for t in titles}
changed = [(t, res[False][t], res[True][t]) for t in titles if res[False][t] and res[True][t] != res[False][t]]
lost = [x for x in changed if x[2] is None]
moved = [x for x in changed if x[2] is not None]
extra = [(t, res[True][t]) for t in titles if res[True][t] and not res[False][t]]
random.seed(42)
out = dict(titles=len(titles), Z1_moved=len(moved), Z2_lost=len(lost), extra=len(extra), Z1=not moved, Z2=not lost,
           moved_items=moved[:20], lost_items=lost[:20], Z3_sample=random.sample(extra, min(40, len(extra))))
print(json.dumps(out, ensure_ascii=False, indent=1))
if len(sys.argv) > 3:
    json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
