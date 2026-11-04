"""D149 (protocol §29 passed): the site's indices come from the run with the long history.

Usage: PYTHONPATH=. python scripts/index_full_extract.py <real.json of the run with SLABWISE_TC_HISTORY=1> [out]
Keeps each series from its first basket of at least 5 items (15 for the general index) and writes
prototype/data/index_full.json, which prototype/build_real_data.py uses in place of its own indices.
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MIN_BASKET = {"era": 5, "set": 5, "generale": 15}
COMMON = "2024-01-01"                    # every index that already exists then is 100 on its first week of 2024
hist = json.load(open(sys.argv[1]))
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "prototype", "data", "index_full.json")


def trim(ix, kind):
    if not ix:
        return None
    start = next((d for d, n in (ix.get("sizes") or []) if n >= MIN_BASKET[kind]), None)
    if not start:
        return None
    pts = [p for p in ix["points"] if p[0] >= start]
    if len(pts) <= 26:
        return None
    b = next((p for p in pts if p[0] >= COMMON), None) if start <= COMMON else pts[0]   # a later index: 100 at its start
    return dict(ix, start=start, base=b[0], points=[[d, round(v * 100 / b[1], 2)] for d, v in pts])


res = dict(indexes={k: v for k, v in ((k, trim(v, "era")) for k, v in (hist.get("indexes") or {}).items()) if v},
           index_all=trim(hist.get("index_all"), "generale"),
           index_sets={k: v for k, v in ((k, trim(v, "set")) for k, v in (hist.get("index_sets") or {}).items()) if v},
           asof=hist.get("asof"))
res["index_base"] = next((v["base"] for v in res["indexes"].values() if v["start"] <= COMMON), hist.get("index_base"))
json.dump(res, open(out, "w"), separators=(",", ":"))
print("indici dallo storico:", sorted(res["indexes"]), "generale:", bool(res["index_all"]), "set:", sorted(res["index_sets"]))
