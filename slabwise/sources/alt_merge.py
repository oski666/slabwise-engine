"""Sales read from Alt's pages (D64, D73) -> rows of the sales CSV, without double counting.

Used by scripts/apify_to_csv.py (full rebuild from the raw archives) and scripts/build_sales.py (GitHub Actions:
committed base CSV + the Alt sales collected so far).
"""
import json
import os
import re
from collections import Counter

from .auction_titles import match_title


def alt_rows(alt_dir, have_ebay, listed=None):
    """(rows, reasons, b1). ``have_ebay``: item ids already in the CSV ("ebay:<id>"); ``listed``: eBay id -> asking
    price of Best Offer sales from another source, for the B1 check (D64 (6))."""
    why = Counter()
    alt = list(json.load(open(os.path.join(alt_dir, "alt_sold.json"))).values())
    listed = listed or {}
    pairs = [(r["price_usd"], listed[r["ebay_id"]]) for r in alt if r.get("kind") == "Best offer" and r.get("ebay_id") in listed]
    lower = sum(1 for a_, l_ in pairs if a_ < l_ - 0.005)
    b1 = len(pairs) >= 5 and lower >= 0.8 * len(pairs)   # Alt shows the accepted Best Offer price
    print(f"B1: {lower} di {len(pairs)} Best Offer con prezzo Alt più basso dell'annuncio -> {'superato' if b1 else 'non superato'}")
    have = set(have_ebay)
    rows = []
    for r in alt:
        if r.get("source") == "fanatics":
            why["Alt: vendita Fanatics (presa dall'archivio)"] += 1
            continue
        if r.get("ebay_id") and f"ebay:{r['ebay_id']}" in have:
            why["Alt: doppione di eBay già raccolto"] += 1
            continue
        g = re.fullmatch(r"PSA (\d+)", (r.get("grade") or "").strip())
        if not g or int(g.group(1)) not in (7, 8, 9, 10) or not r.get("sold"):
            why["Alt: non PSA 7-10"] += 1
            continue
        card, reason = match_title(f"{r.get('head') or ''} {r.get('subject') or ''} {r['grade']}")
        if not card:
            why["Alt: " + (reason or "altra carta")] += 1
            continue
        bo = r.get("kind") == "Best offer"
        rows.append({"item_id": f"ebay:{r['ebay_id']}" if r.get("ebay_id") else f"alt:{r['item']}", "date": r["sold"] + "T12:00:00Z",
                     "card": card, "grade": int(g.group(1)), "price_usd": r["price_usd"],
                     "venue": "ebay" if r.get("source") == "ebay" else r.get("source") or "alt", "cert": None,
                     "best_offer_hidden": bo and not b1, "title": f"{r.get('head')} {r.get('subject')} {r['grade']}", "excluded": ""})
        if r.get("ebay_id"):
            have.add(f"ebay:{r['ebay_id']}")
    why["aggiunte da Alt"] += len(rows)
    return rows, why, b1
