"""Protocol §45 (D235): four fixes of English title reading must not change how today's catalogue reads any title.

Usage: PYTHONPATH=. python scripts/en_fix_test.py <history.json.gz> <sales.json> [out.json]
X1: no title of a catalogue card goes to another card; X2: none becomes ambiguous or unread; X3: the extra titles
read for catalogue cards are printed (a sample of 20) for reading by hand, with the count for each fix.
"""
import gzip
import json
import random
import re
import sys
from collections import Counter

from slabwise.sources import auction_titles as at

titles = {s.get("title") or "" for s in json.load(gzip.open(sys.argv[1], "rt"))} | {s.get("title") or "" for s in json.load(open(sys.argv[2]))}
titles = sorted(t for t in titles if t and not at.is_japanese(t))
res = {}
for flag in (False, True):
    at.EN_FIX, at.EXCLUDE = flag, at.en_exclude(flag)
    res[flag] = {t: at.match_title(t)[0] for t in titles}
changed = [(t, res[False][t], res[True][t]) for t in titles if res[False][t] and res[True][t] != res[False][t]]
lost = [x for x in changed if x[2] is None]
moved = [x for x in changed if x[2] is not None]
extra = [(t, res[True][t]) for t in titles if res[True][t] and not res[False][t]]


def which(t):
    t = t.lower()
    if re.search(r"mega\W*evolutions", t):
        return "Mega Evolutions"
    if "elite trainer box" in t:
        return "Elite Trainer Box"
    if re.search(r"\((?:199\d|20[0-2]\d)\)", t):
        return "anno fra parentesi"
    return "anni delle promo"


random.seed(42)
out = dict(titles=len(titles), X1_moved=len(moved), X2_lost=len(lost), extra=len(extra), X1=not moved, X2=not lost,
           per_fix=Counter(which(t) for t, _ in extra), moved_items=moved[:20], lost_items=lost[:20],
           X3_sample=random.sample(extra, min(20, len(extra))))
print(json.dumps(out, ensure_ascii=False, indent=1))
if len(sys.argv) > 3:
    json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
