"""Protocols §48 and §49 (D238): a rule must not change how today's catalogue reads any title.

Usage: PYTHONPATH=. python scripts/ja_d238_test.py setcode|bare <history.json.gz> <sales.json> [out.json]
setcode (§48): all titles, JA_SETCODE off vs on. bare (§49): Japanese titles (with §48's definition), JA_BARE off vs on.
1: no title of a catalogue card goes to another card; 2: none becomes ambiguous or unread; 3: the extra titles
read for catalogue cards are printed (a sample of 40) for reading by hand.
"""
import gzip
import json
import random
import sys

from slabwise.sources import auction_titles as at

which = sys.argv[1]
titles = {s.get("title") or "" for s in json.load(gzip.open(sys.argv[2], "rt"))} | {s.get("title") or "" for s in json.load(open(sys.argv[3]))}
titles = sorted(t for t in titles if t and (which == "setcode" or at.is_japanese(t)))
res = {}
for flag in (False, True):
    setattr(at, "JA_SETCODE" if which == "setcode" else "JA_BARE", flag)
    res[flag] = {t: at.match_title(t)[0] for t in titles}
changed = [(t, res[False][t], res[True][t]) for t in titles if res[False][t] and res[True][t] != res[False][t]]
lost = [x for x in changed if x[2] is None]
moved = [x for x in changed if x[2] is not None]
extra = [(t, res[True][t]) for t in titles if res[True][t] and not res[False][t]]
random.seed(42)
out = dict(rule=which, titles=len(titles), moved=len(moved), lost=len(lost), extra=len(extra), ok_1=not moved, ok_2=not lost,
           moved_items=moved[:20], lost_items=lost[:20], sample=random.sample(extra, min(40, len(extra))))
print(json.dumps(out, ensure_ascii=False, indent=1))
if len(sys.argv) > 4:
    json.dump(out, open(sys.argv[4], "w"), ensure_ascii=False, indent=1)
