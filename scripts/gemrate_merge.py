"""Merge a GemRate read from the browser (D261) into data/raw/gemrate/sets.json.

Usage: python scripts/gemrate_merge.py <export.json> <sets.json> <catalogue.json ...>
The export has one entry per page read: {"set", "year", "set_name", "n_rows", "rows"}; a set read from several pages
(promos by year) gets the rows of all of them. Sets already in sets.json are replaced by the new read. The "cards"
of each set (id, name, number) come from the catalogue files (prototype/data/cards.json and cards_ja.json).
"""
import json
import os
import sys

exp, dst, cats = sys.argv[1], sys.argv[2], sys.argv[3:]
new = json.load(open(exp))
new = list(new.values()) if isinstance(new, dict) else new
sets = json.load(open(dst))
SPECIES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "species_ja.json")))["names"]
allc = [c for p in cats for c in json.load(open(p))]
EN = {c["id"]: c.get("n") or "" for c in allc if not c["id"].startswith("ja:")}


def en_name(c):
    """English name used to match the GemRate row: the English twin's, else the name when in Latin letters, else the
    species from the Japanese name (longest species it starts with); "" when none (the row then matches on number)."""
    if c.get("en") in EN:
        return EN[c["en"]]
    n = (c.get("n") or "").replace("(giapponese)", "").strip()
    if n.isascii():
        return n
    hit = max((k for k in SPECIES if k in n), key=len, default=None)
    return SPECIES[hit].replace("-", " ") if hit else ""


cards = {}
for c in allc:
    st, _, no = c["id"].rpartition("-")
    cards.setdefault(st, []).append([c["id"], en_name(c) if c["id"].startswith("ja:") else c.get("n") or "", str(c.get("no") or no)])
by = {}
for e in new:
    if e.get("rows"):
        by.setdefault(e["set"], []).append(e)
for st, pages in by.items():
    pages.sort(key=lambda e: -len(e["rows"]))
    rows, seen = [], set()
    for e in pages:
        for r in e["rows"]:
            if r.get("gemrate_id") not in seen:
                seen.add(r.get("gemrate_id"))
                rows.append(r)
    sets[st] = dict(set=st, year=pages[0]["year"], set_name=pages[0]["set_name"], n_rows=sum(e["n_rows"] for e in pages),
                    pages=[[e["year"], e["set_name"]] for e in pages], cards=cards.get(st, []), rows=rows)
json.dump(sets, open(dst, "w"), ensure_ascii=False)
print(len(by), "set uniti;", len(sets), "in tutto ->", dst)
