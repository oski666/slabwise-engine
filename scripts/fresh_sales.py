"""D323: the sales collected after the engine's last run, shown on the card before they count.

Usage: PYTHONPATH=. python scripts/fresh_sales.py prototype/data/real.json data/raw/tcgcharts
The newest tcgcharts pages (sales.json, the daily collection) go through the same checks as in the engine's input
that need no engine (tcgcharts_rows: duplicates, unpaid or excluded sales, another grader in the title, title rules,
assignment to the card); a sale already in the card's list (same day, grade and price) is left out. What remains,
dated from the values. date (`asof`) on, is written in each card's `fresh` list with the label of the page "nuova: entra
nel valore domani". Value, SlabRange and indices do not change: they wait for the engine's next run.
"""
import json
import os
import sys
from collections import Counter

from slabwise.sources.tcgcharts_merge import tcgcharts_rows

VENUE = {"ebay": "eBay", "snkrdunk_fixed": "SNKRDUNK"}


def main(real_p, tc_dir):
    D = json.load(open(real_p))
    asof = D["asof"][:10]
    os.environ.pop("SLABWISE_TC_HISTORY", None)              # only the newest pages: the long history is already in
    rows, why = tcgcharts_rows(tc_dir, set(), ja=True)
    by_id = {c["id"]: c for c in D["cards"]}
    have = {(c["id"], s["grade"], s["date"], round(float(s["price"]))) for c in D["cards"] for s in c.get("sales", [])}
    n = Counter()
    for c in D["cards"]:
        c.pop("fresh", None)
    for r in rows:
        day, card, grade = r["date"][:10], r["card"], int(r["grade"])
        if day < asof or card not in by_id or r.get("excluded"):   # the day of the values too: the dedup keeps out what the engine had
            continue
        key = (card, grade, day, round(float(r["price_usd"])))
        if key in have:
            continue
        have.add(key)
        by_id[card].setdefault("fresh", []).append(dict(date=day, grade=grade, price=float(r["price_usd"]),
                                                        venue=VENUE.get(r["venue"], "Casa d'aste"), new=True))
        n[card] += 1
    for c in D["cards"]:
        if c.get("fresh"):
            c["fresh"].sort(key=lambda s: s["date"], reverse=True)
    D["fresh_asof"] = max((s["date"] for c in D["cards"] for s in c.get("fresh", [])), default=None)
    json.dump(D, open(real_p, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"D323: {sum(n.values())} vendite nuove su {len(n)} carte dopo il {asof} (scartate: {dict(why)})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
