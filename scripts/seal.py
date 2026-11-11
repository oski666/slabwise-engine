"""Weekly sealed snapshot of the published values (D105).

Usage: python scripts/seal.py [prototype/data/real.json] [data/seals]

Writes data/seals/<date>.json (canonical JSON: engine version, date, every card and grade with value and 80% range,
and forecasts when present) and prints its SHA-256. The workflow then stamps it with OpenTimestamps
(`ots stamp`), which anchors the hash in Bitcoin: anyone can later prove the file existed, unchanged, at that date.
One snapshot per ISO week: an existing one for this week is left alone.
"""
import hashlib
import json
import math
import os
import sys
from datetime import date

src = sys.argv[1] if len(sys.argv) > 1 else "prototype/data/real.json"
out_dir = sys.argv[2] if len(sys.argv) > 2 else "data/seals"
r = json.load(open(src))
asof = min(r.get("asof") or date.today().isoformat(), date.today().isoformat())      # a seal is never dated in the future
week = date.fromisoformat(asof[:10]).isocalendar()[:2]
os.makedirs(out_dir, exist_ok=True)
for f in os.listdir(out_dir):
    if f.endswith(".json") and date.fromisoformat(f[:10]).isocalendar()[:2] == week:
        print(f"istantanea di questa settimana già presente: {f}")
        sys.exit(0)
P = r.get("params") or {}
snap = {"slabwise": "valori pubblicati", "asof": asof, "engine": r.get("engine") or os.environ.get("SLABWISE_ENGINE", ""),
        "currency": "USD", "rows": []}
for c in sorted(r["cards"], key=lambda c: c["id"]):
    for g in sorted(c["grades"], key=lambda g: -g["grade"]):
        if not g.get("value") or not g.get("sales_all") or g.get("off"):
            continue
        sd = (math.log(g["hi"]) - math.log(g["lo"])) / (2 * 1.2816)
        band = 1.2816 * math.sqrt(sd ** 2 + P.get("sigma_e", 0.1) ** 2 + P.get("sigma_q", 0.07) ** 2)
        row = {"card": c["id"], "grade": g["grade"], "value": g["value"], "lo": g["lo"], "hi": g["hi"],
               "sale_lo": round(g["value"] * math.exp(-band), 2), "sale_hi": round(g["value"] * math.exp(band), 2)}   # next eBay sale, 80%
        if g.get("forecast"):
            row["forecast"] = g["forecast"]
        snap["rows"].append(row)
# D262: the last 6 weeks of every index as published, so the live index can chain the changes as they were sealed
_ix = dict(r.get("indexes") or {})
if r.get("index_all"):
    _ix["tutto"] = r["index_all"]
snap["indexes"] = {k: [list(p) for p in (v.get("points") or [])[-6:]] for k, v in _ix.items() if v}
body = json.dumps(snap, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
path = os.path.join(out_dir, f"{asof[:10]}.json")
open(path, "w").write(body)
print(path, hashlib.sha256(body.encode()).hexdigest(), len(snap["rows"]), "righe")
