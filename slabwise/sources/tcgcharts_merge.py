"""tcgcharts single sales -> rows of the sales CSV (D77): our own title recognition decides the card (P4), no double
counting with the sales we already have. D121: also the auction houses (Fanatics, Goldin, Alt), since our own
collections from them stopped in October; a sale already in our files (same card and grade, 3 days, 2%) is skipped."""
import gzip
import json
import os
from collections import Counter

import os

from .auction_titles import accept_assigned, grade_from_title, match_title

ASSIGN = os.environ.get("SLABWISE_ASSIGN", "1") == "1"   # D258 (protocol §56 passed): keep the providers' card unless the title contradicts it


# D121/D124: on with the v1.15 engine (R1 0 with and without them); SLABWISE_TC_AUCTIONS=0 turns them off
AUCTION = {"fanatics collect": "fanatics", "fanatics": "fanatics", "goldin": "goldin", "alt": "alt"}


def _same_sale(index, card, grade, day, price):
    """An auction sale we already have from our own collections: same card and grade, within 3 days and 2% of price."""
    from datetime import date
    d = date.fromisoformat(day[:10])
    return any(abs((date.fromisoformat(r_day) - d).days) <= 3 and abs(r_price / price - 1) <= 0.02
               for r_day, r_price in index.get((card, grade), ()))


def tcgcharts_rows(tc_dir, have_ebay, have_auction=()):
    """have_auction: (card, grade, date, price) of the auction sales we already have (Fanatics, Goldin, Alt), D121."""
    why = Counter()
    rows, have = [], set(have_ebay)
    auc = {}
    for card, grade, day, price in have_auction:
        auc.setdefault((card, int(grade)), []).append((day[:10], float(price)))
    sales = json.load(open(os.path.join(tc_dir, "sales.json")))
    hist = os.path.join(tc_dir, "history.json.gz")   # D80: full history read once with Oscar's account
    if os.path.exists(hist) and os.environ.get("SLABWISE_TC_HISTORY") == "1":   # D83: only once H1-H4 pass
        sales += [s for s in json.load(gzip.open(hist, "rt")) if (s.get("sold_date") or "") >= "2022-07-01"]   # D85
    for s in sales:
        plat = (s.get("platform") or "").lower()
        venue = "ebay" if plat == "ebay" else AUCTION.get(plat) if os.environ.get("SLABWISE_TC_AUCTIONS", "1") == "1" else None
        if not venue:
            why["tcgcharts: piattaforma non seguita"] += 1
            continue
        key = f"ebay:{s['sale_id']}" if venue == "ebay" else f"tc-{venue}:{s['sale_id']}"
        if key in have:
            why["tcgcharts: doppione eBay"] += 1
            continue
        if s.get("is_excluded") or s.get("payment_pending") or s.get("payment_held"):
            why["tcgcharts: esclusa o in attesa"] += 1
            continue
        if ASSIGN:
            keep, reason = accept_assigned(s.get("title") or "", s["card"])
            card = s["card"] if keep else None
        else:
            card, reason = match_title(s.get("title") or "")
        if card != s["card"]:
            why["tcgcharts: titolo di un'altra stampa o non riconosciuto"] += 1
            continue
        g = grade_from_title(s.get("title") or "")
        if g != s["tc_grade"] or (s.get("grading_service") or "").upper() != "PSA":
            why["tcgcharts: voto non confermato dal titolo"] += 1
            continue
        if venue != "ebay" and _same_sale(auc, card, g, s["sold_date"], s["price_cents"] / 100):
            why["tcgcharts: asta già nelle nostre raccolte"] += 1
            continue
        rows.append({"item_id": key, "date": s["sold_date"] + "T12:00:00Z", "card": card, "grade": g,
                     "price_usd": round(s["price_cents"] / 100, 2), "venue": venue, "cert": None,
                     "best_offer_hidden": False, "title": s.get("title"), "excluded": ""})
        have.add(key)
    why["aggiunte da tcgcharts"] += len(rows)
    return rows, why
