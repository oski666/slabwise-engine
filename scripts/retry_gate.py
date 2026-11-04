"""D157: cards stopped by the engine gate (attesa_motore) are tried again each week, as their sales come in.

Usage: python scripts/retry_gate.py [N]   prints up to N card ids (default 8) whose last attempt is 7 days old or more,
oldest first. The workflow passes them to scripts/add_batch.py: same sales check, same engine gate as any card.
"""
import json
import os
import sys
from datetime import date

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data")
DAYS = 7
N = int(sys.argv[1]) if len(sys.argv) > 1 else 8          # small batches: tcgcharts answers 503 after about 8 cards in a row

status = json.load(open(os.path.join(DATA, "requests_status.json")))
have = {c["id"] for c in json.load(open(os.path.join(DATA, "cards.json")))}
today = date.today()
due = []
for k, v in status.items():
    if not k.startswith("en:") or v.get("status") != "attesa_motore" or k[3:] in have:
        continue
    last = v.get("checked") or v.get("added") or "2000-01-01"
    if (today - date.fromisoformat(last[:10])).days >= DAYS:
        due.append((last, k[3:]))
print(" ".join(cid for _, cid in sorted(due)[:N]))
