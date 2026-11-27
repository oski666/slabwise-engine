"""tcgcharts single sales -> rows of the sales CSV (D77): our own title recognition decides the card (P4), no double
counting with the sales we already have. D121: also the auction houses (Fanatics, Goldin, Alt), since our own
collections from them stopped in October; a sale already in our files (same card and grade, 3 days, 2%) is skipped."""
import gzip
import json
import os
from collections import Counter

import os

from . import auction_titles as _at
from .auction_titles import accept_assigned, grade_from_title, match_title, other_grader

ASSIGN = os.environ.get("SLABWISE_ASSIGN", "1") == "1"   # D258 (protocol §56 passed): keep the providers' card unless the title contradicts it


# D121/D124: on with the v1.15 engine (R1 0 with and without them); SLABWISE_TC_AUCTIONS=0 turns them off
AUCTION = {"fanatics collect": "fanatics", "fanatics": "fanatics", "goldin": "goldin", "alt": "alt"}


def _same_sale(index, card, grade, day, price):
    """An auction sale we already have from our own collections: same card and grade, within 3 days and 2% of price."""
    from datetime import date
    d = date.fromisoformat(day[:10])
    return any(abs((date.fromisoformat(r_day) - d).days) <= 3 and abs(r_price / price - 1) <= 0.02
               for r_day, r_price in index.get((card, grade), ()))


def _snk_title_ok(title, card):
    """D302: the SNKRDUNK title carries '[<set> <number>/...' and must name the card assigned (ja:<set>-<number>)."""
    import re
    m = re.search(r"\[([A-Za-z0-9-]+)\s+(\d+)/", title or "")
    return bool(m) and card == f"ja:{m.group(1).lower()}-{m.group(2).zfill(3)}"


def tcgcharts_rows(tc_dir, have_ebay, have_auction=(), ja=False):
    """have_auction: (card, grade, date, price) of the auction sales we already have (Fanatics, Goldin, Alt), D121.
    ja: also the SNKRDUNK sales tcgcharts carries (D302), as fixed-price SNKRDUNK sales."""
    why = Counter()
    rows, have = [], set(have_ebay)
    auc = {}
    for card, grade, day, price in have_auction:
        auc.setdefault((card, int(grade)), []).append((day[:10], float(price)))
    sales = json.load(open(os.path.join(tc_dir, "sales.json")))
    if os.environ.get("SLABWISE_TC_HISTORY") == "1":   # D80 full history read with Oscar's account; D83 only once H1-H4 pass
        from slabwise.sources import tc_history          # 27 Nov 2026: year shards (D345)
        sales += [s for s in tc_history.load(tc_dir) if (s.get("sold_date") or "") >= "2022-07-01"]   # D85
    for s in sales:
        plat = (s.get("platform") or "").lower()
        if plat == "snkrdunk":                                   # D302
            if not ja:
                why["tcgcharts: piattaforma non seguita"] += 1
                continue
            if s.get("is_excluded") or s.get("payment_pending") or s.get("payment_held"):
                why["tcgcharts: esclusa o in attesa"] += 1
                continue
            g = int(s.get("tc_grade") or 0)
            if (s.get("grading_service") or "").upper() != "PSA" or str(s.get("grade")) != str(g) or not 7 <= g <= 10:
                why["tcgcharts SNKRDUNK: voto non PSA 7-10"] += 1
                continue
            if _at.OTHER_GRADER_ON and other_grader(s.get("title")):   # D306 (protocol §66)
                why["tcgcharts: altro ente nel titolo"] += 1
                continue
            if not _snk_title_ok(s.get("title"), s["card"]):
                why["tcgcharts SNKRDUNK: set o numero del titolo diversi"] += 1
                continue
            key = f"tc-snkrdunk:{s['sale_id']}"
            if key in have:
                continue
            rows.append({"item_id": key, "date": s["sold_date"] + "T12:00:00Z", "card": s["card"], "grade": g,
                         "price_usd": round(s["price_cents"] / 100, 2), "venue": "snkrdunk_fixed", "cert": None,
                         "best_offer_hidden": False, "title": s.get("title"), "excluded": ""})
            have.add(key)
            why["tcgcharts SNKRDUNK: aggiunte"] += 1
            continue
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
        if _at.OTHER_GRADER_ON and other_grader(s.get("title")):   # D306 (protocol §66)
            why["tcgcharts: altro ente nel titolo"] += 1
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
