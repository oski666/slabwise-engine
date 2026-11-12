"""Suspect sales for Oscar's review (D275).

  flag   SALES_CSV REGISTER OUT_IDS
         the sales the §61 rule flags (slabwise/suspects.py), minus those Oscar already decided in the register
  report SALES_CSV IDS IMPACT REAL_JSON OUT
         the list for the review: card, grade, price, date and age, link to the original listing when there is one,
         the median of the nearby sales, the weight the engine gives the sale today and how much it moves today's value
"""
import csv
import json
import os
import sys
from datetime import date
from urllib.parse import quote_plus

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from slabwise.suspects import flag  # noqa: E402

MAX_ITEMS = 30          # one review at a time stays readable on a phone
MAX_MEASURED = 150      # the engine measures the pull of at most this many each week (the farthest from their neighbours)


def link(item_id, title, venue):
    src, _, raw = str(item_id).partition(":")
    if src == "ebay" and raw.isdigit():
        return f"https://www.ebay.com/itm/{raw}", "annuncio eBay"
    q = quote_plus(f"{title or ''} {venue}".strip())
    return f"https://www.google.com/search?q={q}", "cerca il titolo"


def main():
    mode = sys.argv[1]
    rows = list(csv.DictReader(open(sys.argv[2], newline="")))
    if mode == "flag":
        reg = json.load(open(sys.argv[3])) if os.path.exists(sys.argv[3]) else {}
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data")
        ids = set()                                     # only catalogue cards (the site shows a subset of them)
        for fn in ("cards.json", "cards_ja.json"):
            if os.path.exists(os.path.join(here, fn)):
                ids |= {c["id"] for c in json.load(open(os.path.join(here, fn)))}
        if ids:
            rows = [r for r in rows if r["card"].split("/")[0] in ids or r["card"] in ids]
        f = {k: v for k, v in flag(rows).items() if k not in reg}
        total = len(f)
        import math
        f = dict(sorted(f.items(), key=lambda kv: -abs(math.log(max(kv[1]["ratio"], 1e-12))))[:MAX_MEASURED])
        f["__total__"] = total
        json.dump(f, open(sys.argv[4], "w"))
        print(f"D275: {len(f)} vendite sospette da decidere")
        return
    ids = json.load(open(sys.argv[3]))
    total = ids.pop("__total__", len(ids))
    imp = json.load(open(sys.argv[4])) if os.path.exists(sys.argv[4]) else {}
    real = json.load(open(sys.argv[5]))
    names = {c["id"]: c.get("name") or c["id"] for c in real.get("cards", [])}
    by = {r["item_id"]: r for r in rows}
    today = date.today()
    items = []
    for iid, f in ids.items():
        r = by.get(iid)
        if not r or r["card"] not in names:             # only cards on the site
            continue
        m = imp.get(iid, {})
        pull = m.get("pull") if isinstance(m.get("pull"), dict) else {}
        g = str(int(float(r["grade"])))
        url, kind = link(iid, r.get("title"), r["venue"])
        items.append(dict(item_id=iid, card=r["card"], name=names[r["card"]], grade=g, price=float(r["price_usd"]),
                          date=r["date"][:10], age_days=(today - date.fromisoformat(r["date"][:10])).days,
                          venue=r["venue"], title=r.get("title") or "", url=url, link=kind, ref=f["ref"], n=f["n"],
                          ratio=f["ratio"], in_use=bool(m.get("in_use")), pgen=m.get("pgen"), value=m.get("value"),
                          pull=pull.get(g), pull_all=pull))
    items.sort(key=lambda x: -abs(x["pull"] or 0))
    json.dump(dict(date=str(today), total=total, measured=len(items), items=items[:MAX_ITEMS]), open(sys.argv[6], "w"),
              ensure_ascii=False, indent=1)
    print(f"D275: {len(items)} vendite sospette sulle carte del sito, {min(len(items), MAX_ITEMS)} nella revisione")


if __name__ == "__main__":
    main()
