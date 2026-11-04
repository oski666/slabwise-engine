"""Combine Apify results (eBay sold, Goldin, Fanatics Collect) into one sales CSV.

Usage: PYTHONPATH=. python scripts/apify_to_csv.py data/raw/apify data/raw/sales_all.csv [data/raw/fanatics_history [--fixed]] [--alt=data/raw/alt]
Files named ebay_*/probe_* are eBay, names containing "fanatics" Fanatics Collect, the rest Goldin.
Duplicated lots (the same lot found by two searches) are kept once.
With the Fanatics public sales history (D46, scripts/fanatics_history.py) every Fanatics lot gets its payment
status: unpaid, pending and vanished lots stay in the CSV with the reason in the "excluded" column (the identity
layer removes them and keeps the reason), and archive lots the Apify feed missed are added.
"""
import csv
import glob
import json
import os
import re
import sys
from collections import Counter

from slabwise.sources.auction_titles import ebay_rows, to_rows

from datetime import datetime, timezone

from slabwise.sources.auction_titles import match_title
from slabwise.sources.alt_merge import alt_rows
from slabwise.sources.fanatics_history import is_auction, is_pokemon, payment_reason, sold_utc

src, out = sys.argv[1], sys.argv[2]
hist_dir = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
with_fixed = "--fixed" in sys.argv[4:]
alt_dir = next((a.split("=", 1)[1] for a in sys.argv[3:] if a.startswith("--alt=")), None)   # D64                # D51/D53: Fanatics fixed-price sales as a third venue
seen, rows, why = set(), [], Counter()
for f in sorted(glob.glob(os.path.join(src, "**", "*.json"), recursive=True)):
    try:
        recs = json.load(open(f))
    except ValueError:
        continue
    if not isinstance(recs, list):
        continue
    name = os.path.basename(f)
    venue = "ebay" if name.startswith(("ebay_", "probe_")) else "fanatics" if "fanatics" in name else "goldin"
    idk = "itemId" if venue == "ebay" else "lot_id"
    fresh = []
    for r in recs:
        if not isinstance(r, dict) or idk not in r:
            continue
        key = (venue, r[idk])
        if key in seen:
            why["doppione tra ricerche"] += 1
            continue
        seen.add(key)
        fresh.append(r)
    got, w = ebay_rows(fresh) if venue == "ebay" else to_rows(fresh, venue)
    rows += got
    why += w
for r in rows:
    r.setdefault("excluded", "")
if hist_dir:                                          # D46: payment status from the Fanatics archive
    now = datetime.now(timezone.utc)
    hist, cover = {}, {}
    for f in sorted(glob.glob(os.path.join(hist_dir, "*.json"))):
        if f.endswith("coverage.json"):
            continue
        allrecs = [h for h in json.load(open(f)) if is_pokemon(h)]
        recs = [h for h in allrecs if is_auction(h)]
        for h in (allrecs if with_fixed else recs):
            hist[h.get("listingUuid") or h["id"]] = h
        if recs:
            key = os.path.basename(f)[:-5].split("__")[0].replace("ja_", "ja:", 1)
            first = min(sold_utc(h) for h in recs)
            cover[key] = min(first, cover.get(key, first))
    known = set()
    for r in rows:
        if r["venue"] != "fanatics":
            continue
        uid = r["item_id"].split(":", 1)[1]
        known.add(uid)
        h = hist.get(uid)
        if h is not None:
            reason = payment_reason(h, now)
        else:
            d = datetime.fromisoformat(r["date"].replace("Z", "+00:00"))
            base = r["card"].split("/")[0]
            reason = "sparito dall'archivio Fanatics" if base in cover and d >= cover[base] else None
        if reason:
            r["excluded"] = reason
            why[reason] += 1
    added = 0
    for uid, h in hist.items():
        if uid in known or (h.get("gradingService") or "").upper() != "PSA":
            continue
        g = h.get("grade")
        if g is None or float(g) != int(g) or int(g) not in (7, 8, 9, 10):
            continue
        card, reason = match_title(h.get("title") or "")
        if not card:
            continue
        rows.append({"item_id": f"fanatics:{uid}", "date": sold_utc(h).strftime("%Y-%m-%dT%H:%M:%SZ"), "card": card,
                     "grade": int(g), "price_usd": float(h["purchasePrice"]),
                     "venue": "fanatics" if is_auction(h) else "fanatics_fixed",
                     "cert": h.get("serial") or None, "title": h.get("title"), "excluded": payment_reason(h, now) or ""})
        added += 1
        if rows[-1]["excluded"]:
            why[rows[-1]["excluded"]] += 1
    why["aggiunte dall'archivio Fanatics"] += added
if alt_dir:                                           # D64: recent sales read from Alt's public pages
    listed = {}                                       # eBay id -> asking price shown by eBay (Apify)
    for f in sorted(glob.glob(os.path.join(src, "**", "*.json"), recursive=True)):
        try:
            for r in json.load(open(f)):
                if isinstance(r, dict) and r.get("itemId") and r.get("isBestOfferAccepted"):
                    listed[str(r["itemId"])] = float(str(r.get("soldPrice")).replace(",", ""))
        except (ValueError, TypeError):
            continue
    got, w, _ = alt_rows(alt_dir, {r["item_id"] for r in rows if r["venue"] == "ebay"}, listed)
    rows += got
    why += w
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
with open(out, "w", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=["item_id", "date", "card", "grade", "price_usd", "venue", "cert", "best_offer_hidden", "title", "excluded"])
    wr.writeheader()
    wr.writerows(rows)
print(f"{len(rows)} vendite scritte in {out}")
for k, v in why.most_common():
    print(f"  {k}: {v}")
by = Counter((r["card"], r["grade"]) for r in rows)
print("vendite per carta e voto:")
for (c, g), n in sorted(by.items()):
    print(f"  {c:24s} PSA {g:2d}: {n}")
