"""D320: the 1st Edition and Shadowless printings of tcgcharts' ranking whose base card is in the catalogue get their own
entry in the tcgcharts mapping, so the daily collection reads their sales (cardType "variant") and the long history can
be downloaded for them. Until now only the base printing was read from tcgcharts: the 1st Edition sales that tcgcharts
keeps on the variant page never reached us (e.g. Shining Charizard 1st Edition, Neo Destiny).

Usage: PYTHONPATH=. python scripts/tc_variants.py <ranking.json> [data/raw/tcgcharts/cards.json] [--top 3000]
The ranking is the export of tcgcharts' market cap ranking (id = -internal id for a variant, url, v = variant type).
No request to tcgcharts: the base page is the variant's address without the variant word; populations come later
from the weekly refresh (D77) or, meanwhile, from GemRate (D257).
"""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
rank = json.load(open(args[0]))
map_p = args[1] if len(args) > 1 else os.path.join(ROOT, "data", "raw", "tcgcharts", "cards.json")
top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 3000
mapping = json.load(open(map_p))
DATA = os.path.join(ROOT, "prototype", "data")
catalogue = {c["id"] for c in json.load(open(os.path.join(DATA, "cards.json")))} | \
            {c["id"] for c in json.load(open(os.path.join(DATA, "cards_ja.json"))) if not c.get("pending")}
queue = json.load(open(os.path.join(DATA, "candidates_queue.json")))
url2our = {m["url"]: k for k, m in mapping.items() if "/" not in k}
for k, v in queue.items():
    if v.get("tc_url") and k in catalogue:
        url2our.setdefault(v["tc_url"], k)

SUFFIX = {"1st Edition": "1st", "Shadowless": "shadowless",
          "Reverse Foil": "reverse", "No Rarity Symbol": "norarity", "Master Ball Reverse Holo": "masterball"}   # D337
added, no_base, have = [], [], 0
for x in rank:
    if x.get("r", 1e9) > top or x.get("v") not in SUFFIX:
        continue
    slug = x["v"].lower().replace(" ", "-")
    base_url = re.sub(rf"-{re.escape(slug)}(?=-[^-/]+$)", "", x["url"])
    base = url2our.get(base_url)
    if not base or base not in catalogue:
        no_base.append((x["r"], x["n"], x.get("sn"), x.get("lang")))
        continue
    vid = f"{base}/{SUFFIX[x['v']]}"
    if vid in mapping:
        have += 1
        continue
    mapping[vid] = dict(tc_id=-int(x["id"]), card_type="variant", url=x["url"], set=x.get("sn"), name=f"{x['n']} ({x['v']})",
                        psa_population=None, pop={}, graded_supply=x.get("gs"), pop_at=0, variant_of=base)
    added.append((x["r"], vid, x["n"], x.get("sn")))
json.dump(mapping, open(map_p, "w"), ensure_ascii=False, indent=1)
print(f"varianti aggiunte alla mappa: {len(added)}; già presenti: {have}; senza la carta base nel catalogo: {len(no_base)}")
for a in added[:20]:
    print("  +", a)
for b in sorted(no_base)[:15]:
    print("  base mancante:", b)
