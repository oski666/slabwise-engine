"""Fanatics Collect public sales history (D46): the archive behind the public "Sales History" page,
read without Apify, with each lot's payment status.

Rules (identity layer, P4, registered in D46 before the code):
- a lot "Unpaid" closed more than 14 days ago is removed as "lotto non pagato";
- a more recent "Unpaid" lot is removed as "pagamento in attesa" (it comes back once it reads "Paid");
- a lot collected earlier (Apify) that is no longer in the archive, although the same title search covers
  its date, is removed as "sparito dall'archivio Fanatics".
Only auctions (WEEKLY, PREMIER) are used, like the Apify feed; fixed-price sales are not modelled yet.

D50: the archive only records payment from December 2025. Every lot before that reads "Unpaid" (100% of the
2023-2024 auctions we read, against 0-5% from December 2025), so the flag is ignored before FLAG_FROM.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://sales-history-api.services.fanaticscollect.com/api/v1/pub/sales"
UNPAID_GRACE_DAYS = 14
FLAG_FROM = datetime(2025, 12, 1, tzinfo=timezone.utc)   # D50: payment flag recorded from here on
AUCTIONS = {"WEEKLY", "PREMIER"}
PAUSE = 1.5            # seconds between requests


def _get(url, tries=4):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (slabwise research; low rate)"})
    for k in range(tries):
        try:
            return json.load(urllib.request.urlopen(req, timeout=40))
        except (OSError, ValueError):
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))          # back off; never hammer the archive


def fetch(title: str, since: str = "2023-01-01", max_pages: int = 40, size: int = 50):
    """All archive records whose title matches ``title`` sold since ``since`` (newest first)."""
    out = []
    for page in range(max_pages):
        q = urllib.parse.urlencode({"title": title, "page": page, "size": size})
        d = _get(f"{API}?{q}")
        recs = (d.get("_embedded") or {}).get("SalesRecords", [])
        out += recs
        info = d.get("page", {})
        if not recs or page + 1 >= info.get("totalPages", 0) or min(r["soldDate"][:10] for r in recs) < since:
            break
        time.sleep(PAUSE)
    return [r for r in out if r["soldDate"][:10] >= since]


def sold_utc(r):
    """soldDate is local Pacific time ('2026-07-19T20:41:18.000 PDT'); return an aware UTC datetime."""
    s, tz = r["soldDate"].rsplit(" ", 1)
    off = -7 if tz == "PDT" else -8
    return datetime.fromisoformat(s.split(".")[0]).replace(tzinfo=timezone(timedelta(hours=off))).astimezone(timezone.utc)


def payment_reason(r, now: datetime):
    """None if the lot counts as a sale, otherwise the removal reason (D46)."""
    status = (r.get("paymentStatus") or "").lower()
    when = sold_utc(r)
    if status in ("paid", "complete") or when < FLAG_FROM:
        return None
    age = (now - when).days
    return "lotto non pagato" if age > UNPAID_GRACE_DAYS else "pagamento in attesa"


def is_auction(r):
    return (r.get("auctionType") or "").upper() in AUCTIONS


def is_pokemon(r):
    return "pok" in (r.get("category") or "").lower()
