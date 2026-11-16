"""D307: one Japanese printing, one id; then the twins of protocol §67b (variant M0), adopted by the owner (P12 exception).

Usage: PYTHONPATH=. python scripts/ja_dedupe_link.py <links67b_M0.json> [data/raw/tcgcharts/cards.json]
1. The same tcgcharts card registered under two ids (TCGdex's, e.g. ja:sv8a-217, and the tcgcharts slug, e.g.
   ja:terastal-festival-ex-217) is kept once: the id in the catalogue, then the one linked to an English card, then the
   one with a TCGdex id, then the shorter. The other leaves the catalogue (its English link, image and illustrator move
   to the kept id when that has none) and its queue row becomes "scartata" with the reason.
2. The §67b links are written on the kept ids (cards_ja.json and candidates_queue.json: en, en_same, en_check; ja_only
   off), never over an existing link (one Japanese printing goes to one English card, D179).
"""
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "prototype", "data")
links = json.load(open(sys.argv[1]))
cj = json.load(open(os.path.join(DATA, "cards_ja.json")))
queue = json.load(open(os.path.join(DATA, "candidates_queue.json")))
tc_map = json.load(open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "raw", "tcgcharts", "cards.json")))
cj_by = {c["id"]: c for c in cj}


def tc_of(i):
    v = (tc_map.get(i) or {}).get("tc_id") or (queue.get(i) or {}).get("tc_id")
    return str(v) if v else None


groups = defaultdict(list)
for i in set(cj_by) | {k for k, v in queue.items() if v.get("lang") == "ja" and v.get("status") != "scartata"}:   # a rejected row stays as it is
    if tc_of(i):
        groups[tc_of(i)].append(i)
alias, n_cat = {}, 0
for t, ids in groups.items():
    if len(ids) < 2:
        continue
    ids.sort(key=lambda i: (i not in cj_by, not (cj_by.get(i) or queue.get(i) or {}).get("en"),
                            not (queue.get(i) or {}).get("tcgdex"), len(i), i))
    keep = ids[0]
    for drop in ids[1:]:
        alias[drop] = keep
        if drop in cj_by:
            d, k = cj_by.pop(drop), cj_by.get(keep)
            if k is not None:
                for f in ("en", "en_same", "en_check", "img", "img_url", "ill"):
                    if d.get(f) and not k.get(f):
                        k[f] = d[f]
            n_cat += 1
        if drop in queue:
            queue[drop].update(status="scartata", detail=f"doppione di {keep} (stessa carta su tcgcharts, D307)")
        if keep in queue and drop in queue and queue[drop].get("en") and not queue[keep].get("en"):
            queue[keep].update(en=queue[drop]["en"], en_same=queue[drop].get("en_same"), en_check=queue[drop].get("en_check"))
print(f"doppioni: {len(alias)} id tolti ({n_cat} dal catalogo)")

n_l = n_skip = 0
for r in links:
    j = alias.get(r["ja"], r["ja"])
    why = f"illustrazione uguale (distanza {r['d'][0]}/256, §67b M0, D307)"
    c, q = cj_by.get(j), queue.get(j)
    if (c and c.get("en")) or (q and q.get("en") and q["en"] != r["en"]):
        n_skip += 1
        continue
    if c is not None:
        c.update(en=r["en"], en_same="True", en_check=why)
    if q is not None and q.get("status") != "scartata":
        q.update(en=r["en"], en_same=True, en_check=why)
        q.pop("ja_only", None)
    n_l += 1
print(f"gemelle collegate: {n_l}; saltate perché già collegate: {n_skip}")
json.dump([c for c in cj if c["id"] in cj_by], open(os.path.join(DATA, "cards_ja.json"), "w"), ensure_ascii=False, indent=1)
json.dump(queue, open(os.path.join(DATA, "candidates_queue.json"), "w"), ensure_ascii=False, indent=1)
