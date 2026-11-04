"""Weekly history of PSA populations (D109): one row per card and date, appended after the Monday tcgcharts run.

Usage: python scripts/pop_history.py data/raw/tcgcharts/cards.json data/raw/tcgcharts/pop_history.json

The pop report counts gradings, not copies: a card cracked and resubmitted can be counted again when its old label
is not returned. Levels are biased; changes over time (how fast the 9s grow compared with the 10s, and with sales)
say more. This file keeps them so a later version can test that.
"""
import json
import sys
from datetime import date

src, out = sys.argv[1], sys.argv[2]
cards = json.load(open(src))
try:
    hist = json.load(open(out))
except (OSError, ValueError):
    hist = []
today = date.today().isoformat()
hist = [h for h in hist if h["date"] != today]
for cid, m in cards.items():
    if m.get("pop"):
        hist.append({"date": today, "card": cid, "total": m.get("psa_population"), "pop": m["pop"]})
json.dump(hist, open(out, "w"), ensure_ascii=False)
print(len(hist), "righe ->", out)
