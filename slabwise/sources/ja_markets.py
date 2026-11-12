"""D280: SNKRDUNK trades and Cardova closed auctions as sales rows for the Japanese cards of the catalogue.
Only for the preview branch `giappone` (SLABWISE_JA_MARKETS=1): their use in the site's values needs a registered test
(D266, D273). Prices in yen are turned into dollars with the ECB rate of the day (data/fx_jpy.json, D280).

SNKRDUNK: the file of the browser collection (one entry per card of the catalogue, with the last trades per grade).
Cardova: paid closed auctions (bid_payment_status 5) of PSA 7-10, read by our own title reader from a title built
with year, PSA set name, number, name and attribute (P4).
"""
from __future__ import annotations

import glob
import gzip
import json
import os
from collections import Counter

COND = {"trading_card_single_psa10": 10, "trading_card_single_psa9": 9, "trading_card_single_psa8": 8,
        "trading_card_single_psa7": 7}


def _fx(path):
    d = json.load(open(path))["rates"]                 # {date: yen per dollar}
    days = sorted(d)

    def rate(day):
        import bisect
        i = bisect.bisect_right(days, day[:10]) - 1
        return d[days[max(i, 0)]]
    return rate


def ja_market_rows(raw_dir, fx_path):
    why = Counter()
    rows = []
    if not os.path.exists(fx_path):
        why["mercati giapponesi: cambio yen mancante"] += 1
        return rows, why
    rate = _fx(fx_path)
    snk = sorted(glob.glob(os.path.join(raw_dir, "snkrdunk", "*.json")))
    if snk:
        for e in json.load(open(snk[-1])):
            if e.get("status") != "ok":
                continue
            for it in (e.get("items") or {}).values():
                for cond, v in (it.get("cond") or {}).items():
                    g = COND.get(cond)
                    if not g:
                        continue
                    for t in v.get("trades", []):
                        day = t["soldAt"][:10]
                        rows.append({"item_id": f"snk:{it.get('product')}:{cond}:{t['soldAt']}:{t['price']}",
                                     "date": t["soldAt"], "card": e["id"], "grade": g,
                                     "price_usd": round(t["price"] / rate(day), 2), "venue": "snkrdunk_fixed",
                                     "cert": None, "best_offer_hidden": False, "title": f"SNKRDUNK PSA {g}",
                                     "excluded": ""})
                        why["mercati giapponesi: SNKRDUNK"] += 1
    cv = os.path.join(raw_dir, "cardova", "aste_chiuse.json.gz")
    if os.path.exists(cv):
        from .auction_titles import match_title
        for r in json.load(gzip.open(cv, "rt"))["rows"]:
            if r.get("finished") != 1 or r.get("bid_payment_status") != 5 or r.get("authentication_company_code") != "P":
                continue
            try:
                g = int(float(r["grade"]))
            except (TypeError, ValueError):
                continue
            if g < 7 or not r.get("bid_price"):
                continue
            title = f"{r['year']} Pokemon {r['variety']} {r['card_number']} {r['player']} {r.get('attribute') or ''} PSA {g}"
            card, _ = match_title(title)
            if not card or not card.startswith("ja:"):
                why["mercati giapponesi: Cardova non riconosciuta"] += 1
                continue
            day = r["end_date"][:10]
            rows.append({"item_id": f"cardova:{r['ulid']}", "date": r["end_date"], "card": card, "grade": g,
                         "price_usd": round(r["bid_price"] / rate(day), 2), "venue": "cardova",
                         "cert": r.get("certificate_number") or None, "best_offer_hidden": False,
                         "title": title, "excluded": ""})
            why["mercati giapponesi: Cardova"] += 1
    return rows, why
