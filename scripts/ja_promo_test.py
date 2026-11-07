"""Protocol §41 (D231): the Japanese promo number rule must not change how today's catalogue reads any title.

Usage: PYTHONPATH=. python scripts/ja_promo_test.py <history.json.gz> <sales.json> [out.json]
U1: no title of a catalogue card goes to another card; U2: none becomes ambiguous or unread; U3: the extra titles
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
    at.NEW_JA_PROMO = flag
    res[flag] = {t: at.match_title(t)[0] for t in titles}
changed = [(t, res[False][t], res[True][t]) for t in titles if res[False][t] and res[True][t] != res[False][t]]
lost = [x for x in changed if x[2] is None]
moved = [x for x in changed if x[2] is not None]
extra = [(t, res[True][t]) for t in titles if res[True][t] and not res[False][t]]
random.seed(41)
out = dict(titles=len(titles), U1_moved=len(moved), U2_lost=len(lost), extra=len(extra), U1=not moved, U2=not lost,
           moved_items=moved[:20], lost_items=lost[:20], U3_sample=random.sample(extra, min(20, len(extra))))
print(json.dumps(out, ensure_ascii=False, indent=1))
if len(sys.argv) > 3:
    json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
