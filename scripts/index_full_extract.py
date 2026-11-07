"""D149 (protocol §29 passed): the site's indices come from the run with the long history.

Usage: PYTHONPATH=. python scripts/index_full_extract.py <real.json of the run with SLABWISE_TC_HISTORY=1> [out]
Writes prototype/data/index_full.json (rule in slabwise/index_full.py). Since D228 the site's build does this
inside its single run (SLABWISE_INDEX_SELF=1); this script stays for the tests and by hand.
"""
import json
import os
import sys

from slabwise.index_full import extract

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hist = json.load(open(sys.argv[1]))
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "prototype", "data", "index_full.json")
res = extract(hist)
json.dump(res, open(out, "w"), separators=(",", ":"))
print("indici dallo storico:", sorted(res["indexes"]), "generale:", bool(res["index_all"]), "set:", sorted(res["index_sets"]))
