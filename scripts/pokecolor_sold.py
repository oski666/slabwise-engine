"""Concluded sales of graded Pokemon cards from Pokecolor's public sales history (D180).

Usage: PYTHONPATH=. python scripts/pokecolor_sold.py data/raw/pokecolor
Permission: email from the Pokecolor team to Oscar, 6 Nov 2026 (public endpoints, "in a timely manner").
Reads the same public list the site's "Sales History" page reads, PSA only (D165: same grading company), newest first,
until a whole page is already known; then the detail of each new sale (the card's set code, number and language).
One request every 4 seconds. Keeps no buyer or seller data. Writes <dir>/sold.json, one entry per sale (uid).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.pokecolor.com/api/overseas/trade/sellorder/"
PAUSE = 4.0
UA = "Mozilla/5.0 (compatible; slabwise-collector)"
KEEP = ["uid", "display_title", "order_deal_on", "price", "price_usd", "rate_usd", "rate_type", "rate_score",
        "sell_mode_category", "sell_mode_name", "status", "display_status", "bid_total", "card_category"]


def get(url):
    for k in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.load(r)
            time.sleep(PAUSE)
            if d.get("code") != 100:
                raise RuntimeError(d.get("msg"))
            return d["data"]
        except Exception as e:
            print("  riprovo:", url[-80:], e, flush=True)
            time.sleep(PAUSE * (k + 3))
    raise RuntimeError("Pokecolor non risponde")


def card_of(d):
    c = d.get("card") or {}
    box = c.get("card_box") or {}
    ct = c.get("card_type") or {}
    return dict(id=c.get("id"), name=c.get("name"), number=c.get("number"), rare=c.get("rare"), year=c.get("year"),
                language=ct.get("language"), type=ct.get("name"), box_number=box.get("number"), box_name=box.get("name"))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "sold.json")
    have = json.load(open(path)) if os.path.exists(path) else {}
    new = []
    for page in range(1, 200):
        q = urllib.parse.urlencode(dict(status_filter="sold_finish", order_by="-order_deal_on", card_category="PTCG",
                                        rate_type="PSA", page=page, page_size=50))
        d = get(API + "?" + q)
        rows = d.get("results") or []
        fresh = [r for r in rows if r["uid"] not in have]
        new += fresh
        if not fresh or not d.get("next"):
            break
    print(f"{len(new)} vendite nuove", flush=True)
    for r in new:
        e = {k: r.get(k) for k in KEEP}
        try:
            e["card"] = card_of(get(API + urllib.parse.quote(r["uid"]) + "/"))
        except Exception as ex:
            e["card"] = None
            print("  dettaglio mancante", r["uid"], ex, flush=True)
        e["fetched"] = time.strftime("%Y-%m-%d")
        have[r["uid"]] = e
        json.dump(have, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(have, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{len(have)} vendite in archivio")


if __name__ == "__main__":
    main()
