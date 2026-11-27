"""Merge an export of scripts/browser/tc_history.js into data/raw/tcgcharts/history.json.gz (D123).

Usage: python scripts/tc_history_merge.py <export.json> [data/raw/tcgcharts/history.json.gz]
A sale already in the archive (same card, grade and tcgcharts sale id) is kept once; payment and exclusion flags
take the newer value, so a sale "payment pending" yesterday becomes a normal sale when tcgcharts confirms it.
The cards with new sales go in rehist.json next to the archive (D326): the next engine run refits them alone.
The archive is read and rewritten one sale at a time (17 Nov 2026: at 2.2 million sales loading it whole was killed
for lack of memory); only the export is held in memory.
"""
import gzip
import json
import os
import sys

new = json.load(open(sys.argv[1]))
path = sys.argv[2] if len(sys.argv) > 2 else "data/raw/tcgcharts/history.json.gz"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from slabwise.sources import tc_history  # noqa: E402   27 Nov 2026: written back in year shards (D345)
tc_dir = os.path.dirname(os.path.abspath(path))
key = lambda r: (r["card"], r["tc_grade"], str(r["sale_id"]))  # noqa: E731
fresh = {key(r): r for r in new}
del new
dec = json.JSONDecoder()


def rows(p):
    with gzip.open(p, "rt") as f:
        buf, pos, started = "", 0, False
        while True:
            chunk = f.read(16 << 20)
            buf = buf[pos:] + chunk
            pos = 0
            while True:
                while pos < len(buf) and buf[pos] in " \n\r\t,[":
                    started = started or buf[pos] == "["
                    pos += 1
                if pos >= len(buf) or buf[pos] == "]":
                    break
                try:
                    obj, end = dec.raw_decode(buf, pos)
                except json.JSONDecodeError:
                    break                                  # object cut by the chunk: read more
                yield obj
                pos = end
            if not chunk:
                return


outs, counts = {}, {}


def write(r):
    global total
    n = tc_history.shard_name(r.get("sold_date"))
    if n not in outs:
        outs[n] = gzip.open(os.path.join(tc_dir, n + ".new"), "wt")
        outs[n].write("[")
        counts[n] = 0
    outs[n].write(("," if counts[n] else "") + json.dumps(r, ensure_ascii=False, separators=(",", ":")))
    counts[n] += 1
    total += 1
    cards.add(r["card"])


seen, total, updated, cards = set(), 0, 0, set()
old_shards = tc_history.paths(tc_dir)
for src in old_shards:
    for r in rows(src):
        k = key(r)
        if k in fresh:
            if fresh[k] != r:
                updated += 1
            r = fresh[k]
            seen.add(k)
        write(r)
added = 0
for k, r in fresh.items():
    if k not in seen:
        write(r)
        added += 1
for n, o in outs.items():
    o.write("]")
    o.close()
for n in outs:
    os.replace(os.path.join(tc_dir, n + ".new"), os.path.join(tc_dir, n))
for src in old_shards:                                   # a shard that received no sale this time would be stale: never the case
    if os.path.basename(src) not in outs:                # (every row is rewritten), but remove it to be sure
        os.remove(src)
# D326 (§68b): the cards that received sales are refitted alone by the next engine run, without a full rebuild
from datetime import date  # noqa: E402
rh_p = os.path.join(os.path.dirname(path), "rehist.json")
rh = json.load(open(rh_p)) if os.path.exists(rh_p) else {}
today = str(date.today())
for k in fresh:
    if k not in seen:
        rh[k[0]] = today
rh = {c: d for c, d in rh.items() if d >= str(date.fromordinal(date.today().toordinal() - 60))}
json.dump(dict(sorted(rh.items())), open(rh_p, "w"), indent=0)
print(f"{added} nuove, {updated} aggiornate, {total} in tutto, {len(cards)} carte")
