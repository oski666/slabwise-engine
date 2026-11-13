"""Protocol §63 (D281): Pokémon name required for the sales the providers assign to a card.
N1 sample of 40 removed sales to read by hand; N2 kept share of assigned sales; N3 catalogue cards falling under the
admission threshold (10 recognised PSA 7-10 sales in 365 days). N4 (engine) runs in CI on the sales built both ways.

  python scripts/assign_name_test.py HISTORY_GZ RESULT_JSON
"""
import gzip
import json
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import slabwise.sources.auction_titles as at  # noqa: E402

hist, out = sys.argv[1], sys.argv[2]
since = str(date.today() - timedelta(days=365))
data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data")
cat = {c["id"] for c in json.load(open(os.path.join(data, "cards.json")))} | \
      {c["id"] for c in json.load(open(os.path.join(data, "cards_ja.json")))}
kept = removed = 0
removed_rows, why = [], Counter()
year_before, year_after = defaultdict(int), defaultdict(int)
for s in json.load(gzip.open(hist, "rt")):
    card = s.get("card")
    if not card or s.get("is_excluded") or (s.get("grading_service") or "PSA") != "PSA":
        continue
    t = s.get("title") or ""
    at.ASSIGN_NAME = False
    a, _ = at.accept_assigned(t, card)
    if not a:
        continue
    at.ASSIGN_NAME = True
    b, w = at.accept_assigned(t, card)
    recent = (s.get("sold_date") or "")[:10] >= since and str(s.get("tc_grade") or s.get("grade")) in ("7", "8", "9", "10", "7.0", "8.0", "9.0", "10.0")
    if recent:
        year_before[card] += 1
        year_after[card] += b
    if b:
        kept += 1
    else:
        removed += 1
        why[w] += 1
        removed_rows.append((card, (s.get("sold_date") or "")[:10], s.get("price_cents"), t))
random.seed(63)
below = [c for c in cat if year_before.get(c, 0) >= 10 and year_after.get(c, 0) < 10]
res = dict(assigned_before=kept + removed, kept=kept, removed=removed, why=dict(why),
           N2_kept_share=round(kept / max(1, kept + removed), 4), N2_passed=kept / max(1, kept + removed) >= 0.85,
           N3_cards_below=len(below), N3_share=round(len(below) / len(cat), 4), N3_passed=len(below) / len(cat) <= 0.02,
           N3_examples=below[:20], N1_sample=random.sample(removed_rows, min(40, len(removed_rows))))
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("N1_sample", "N3_examples")}, ensure_ascii=False))
