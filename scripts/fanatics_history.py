"""Download the Fanatics Collect public sales history for every card we follow (D46). Free, no Apify.

Usage: PYTHONPATH=. python scripts/fanatics_history.py data/raw/apify/batch1/keywords.json data/raw/fanatics_history [since] [--deep]
One JSON per card (the raw archive records), plus coverage.json (earliest date read per card).
--deep (D55): the archive returns about 1,000 lots per search, so each card is also searched grade by grade
("... PSA 10" ... "... PSA 7") and, for Wizards-era cards, by edition (1st Edition, Shadowless); files are
named <card>__<variant>.json and merged (deduplicated by lot) when the CSV is built.
"""
import json
import os
import sys
import time

from slabwise.sources.fanatics_history import PAUSE, fetch

JA_KEYWORDS = {                     # Japanese printings (D28): searched in English, matched by the Japanese catalogue
    "ja:sv2a-201": "Japanese 151 Charizard ex",
    "ja:sv2a-208": "Japanese 151 Mew ex",
    "ja:sv2a-168": "Japanese 151 Charmander",
    "ja:sv4a-347": "Japanese Shiny Treasure Mew ex",
    "ja:s6a-095": "Japanese Eevee Heroes Umbreon VMAX",
    "ja:m2-110": "Japanese Mega Charizard X ex",
}
args = [a for a in sys.argv[1:] if not a.startswith("--")]
kw_file, out = args[0], args[1]
since = args[2] if len(args) > 2 else "2023-01-01"
deep = "--deep" in sys.argv
kw = {**json.load(open(kw_file)), **JA_KEYWORDS}
os.makedirs(out, exist_ok=True)
cov = {}
def variants(card, title):
    yield "", title
    if not deep:
        return
    eds = [("", "")] + ([("1st", " 1st Edition"), ("shadowless", " Shadowless")] if card.startswith(("base1-", "base2-", "base3-", "base5-", "neo", "gym")) else [])
    for tag, ed in eds:
        for g in (10, 9, 8, 7):
            yield f"{tag}PSA{g}", f"{title}{ed} PSA {g}"


for card, title in kw.items():
    for tag, q in variants(card, title):
        name = card.replace(":", "_") + (f"__{tag}" if tag else "") + ".json"
        if os.path.exists(os.path.join(out, name)) and (tag or deep):
            continue                                  # resume: each search is downloaded once
        recs = fetch(q, since=since)
        json.dump(recs, open(os.path.join(out, name), "w"))
        cov[card + (f"__{tag}" if tag else "")] = {"title": q, "since": since, "n": len(recs)}
        unpaid = sum((r.get("paymentStatus") or "") != "Paid" for r in recs)
        print(f"{card:14s} {q:52s} {len(recs):5d} lotti, {unpaid} non pagati", flush=True)
        time.sleep(PAUSE)
json.dump(cov, open(os.path.join(out, "coverage.json"), "w"), indent=1)
