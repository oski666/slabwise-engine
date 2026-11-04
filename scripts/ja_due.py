"""D158: Japanese printings in the queue that wait for their sales check (found by scripts/ja_complete.py).

Usage: python scripts/ja_due.py   prints their ids (with a tcgcharts page), one batch of 8 per line.
"""
import json
import os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data")
q = json.load(open(os.path.join(DATA, "candidates_queue.json")))
have = {c["id"] for c in json.load(open(os.path.join(DATA, "cards_ja.json"))) if not c.get("pending")}
ids = [k for k, r in q.items() if r.get("lang") == "ja" and r.get("tc_id") and k not in have
       and r.get("status") in ("in_valutazione", "pronta") and r.get("en_same") is not False]
for i in range(0, len(ids), 8):
    print(" ".join(ids[i:i + 8]))
