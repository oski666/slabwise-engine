"""Deals from fresh eBay listings against the values already published (D112), without running the engine again.

Usage: PYTHONPATH=. python scripts/deals_refresh.py [prototype/data/real.json] [data/raw/ebay/listings.json]
       [data/raw/ebay/counts.json]

D303: the listings file may be missing (the eBay step failed or ran out of time): then no deal is shown (the page says
the listings are not collected yet) but the Slabvalve still uses the counts of the last 48 hours (counts.json, numbers
only, slabwise/slabvalve.py), which this script updates and writes back.

Same rules as the deals block of prototype/build_real_data.py (D72, D73, D98): identity by cert, landed cost in
Italy, the listing mixture and the winner's curse in slabwise.deals.score, only p_deal >= 0.5 shown, never against
an estimate under review. The value of each card and grade is the published one (log mean = log value, sd from the
80% range), which is the engine's estimate of the last week. Writes deals, deals_asof and deal_stats back into the
data file, plus a summary of every listing scored (deal_funnel) for the owner.
"""
import json
import math
import os
import sys

import numpy as np

from slabwise import slabvalve
from slabwise.deals import landed_eur, max_landed, price_for_landed, score

HERE = os.path.dirname(os.path.abspath(__file__))
data_p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "prototype", "data", "real.json")
lst_p = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "data", "raw", "ebay", "listings.json")
cnt_p = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(lst_p), "counts.json")
DEALS_MIN = 0.5
OFFER_MIN = 0.70        # D113: offers below 70% of the asking price are not shown
OFFERS_SHOWN = 60
Z = 1.2816

R = json.load(open(data_p))
try:
    L = json.load(open(lst_p))
except (OSError, ValueError):
    print(f"Annunci di questo giro assenti ({lst_p}): niente occasioni, Slabvalve dai conteggi delle ultime 48 ore")
    L = {"asof": None, "listings": [], "queried": {}}
try:
    old_counts = json.load(open(cnt_p))
except (OSError, ValueError):
    old_counts = {}
EUR = R["eur_rate"]
sigma_q = (R.get("params") or {}).get("sigma_q", 0.07)
certs_p = os.path.join(HERE, "..", "prototype", "data", "certs.json")
known = json.load(open(certs_p))["certs"] if os.path.exists(certs_p) else {}
by_card = {c["id"]: c for c in R["cards"]}
rows = []
skipped = {"carta non nel catalogo": 0, "voto senza stima": 0, "cert di un'altra carta": 0}
for r in L["listings"]:
    if r.get("auction"):                 # D318: an open auction counts in the Slabvalve but has no price to judge as a deal
        continue
    c = by_card.get(r["card"])
    if not c:
        skipped["carta non nel catalogo"] += 1
        continue
    g = next((g for g in c["grades"] if g["grade"] == r["grade"]), None)
    if not g or not g.get("value") or not g.get("sales_all") or g.get("off"):
        skipped["voto senza stima"] += 1
        continue
    if r.get("cert") and r["cert"] in known:
        last = known[r["cert"]][-1]
        if last[1].split("/")[0] != r["card"] or last[2] != r["grade"]:
            skipped["cert di un'altra carta"] += 1
            continue
    cost = landed_eur(r["ask_usd"] * EUR, r["ship_usd"] * EUR, r.get("country"))
    m = math.log(g["value"])
    s = (math.log(g["hi"]) - math.log(g["lo"])) / (2 * Z)
    rows.append((r, c, g, cost, m, s))
for c in R["cards"]:
    c["deals"] = []
R["offers"] = []
# D225, D303: copies on sale now, per card and grade, for the Slabvalve: this run's counts merged with those of the
# last 48 hours (each card keeps the date it was counted)
counts = slabvalve.merge(slabvalve.counts_from_listings(L) if L["asof"] else {}, old_counts)
os.makedirs(os.path.dirname(cnt_p) or ".", exist_ok=True)
json.dump(counts, open(cnt_p, "w"), separators=(",", ":"))
print(f"Slabvalve: {slabvalve.apply(R, counts)} carte con il conteggio degli annunci")
# D314: the Sito build no longer searches eBay (its searches used up the daily limit and left Occasioni with none). With no
# listings of its own, it keeps the deals already on the live page while they are under 6 hours old (they are what the
# page shows anyway; nothing is stored beyond what is published).
CARRY = os.environ.get("SLABWISE_CARRY_DEALS")
if not L["asof"] and CARRY:
    try:
        import re as _re
        import urllib.request as _ur
        from datetime import datetime as _dt, timezone as _tz
        _h = _ur.urlopen(_ur.Request(CARRY, headers={"User-Agent": "slabwise-build"}), timeout=60).read().decode("utf-8")
        _P, _ = json.JSONDecoder().raw_decode(_h[_h.index("const D = ") + 10:])
        _a = _P.get("deals_asof")
        if _a and (_dt.now(_tz.utc) - _dt.strptime(_a, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_tz.utc)).total_seconds() < 6 * 3600:
            _dl = {c["id"]: c.get("deals") or [] for c in _P["cards"]}
            for c in R["cards"]:
                c["deals"] = _dl.get(c["id"], [])
            for k in ("offers", "deals_asof", "deal_stats", "deal_funnel"):
                R[k] = _P.get(k)
            json.dump(R, open(data_p, "w"), ensure_ascii=False, separators=(",", ":"))
            print(f"Occasioni riprese dalla pagina pubblicata ({_a}): {sum(len(v) for v in _dl.values())}")
            sys.exit(0)
        print("Occasioni della pagina pubblicata assenti o più vecchie di 6 ore: nessuna occasione")
    except Exception as ex:
        print("Occasioni della pagina pubblicata non lette:", ex)

stats, funnel = None, {"annunci": len(L["listings"]), "scartati": skipped, "valutati": len(rows)}
if rows:
    pg, pdl, stats = score([r["ask_usd"] for r, *_ in rows], [x[3]["landed_eur"] / EUR for x in rows],
                           np.array([x[4] for x in rows]), np.array([x[5] for x in rows]), [bool(r.get("cert")) for r, *_ in rows], sigma_q)
    under = 0
    for (r, c, g, cost, m, s), pg_, pd_ in zip(rows, pg, pdl):
        if cost["landed_eur"] < g["value"] * EUR:
            under += 1
        if pd_ < DEALS_MIN:
            continue
        c["deals"].append(dict(grade=r["grade"], ask_usd=r["ask_usd"], cert=bool(r.get("cert")),
                               **{k: round(v, 2) if isinstance(v, float) else v for k, v in cost.items()},
                               value_eur=round(g["value"] * EUR, 2), p_gen=round(float(pg_), 3), p_deal=round(float(pd_), 3),
                               suspicious=False, url=r["url"], title=r["title"], market=r["market"], seller_pct=r.get("seller_pct"),
                               seller_n=r.get("seller_n"), authenticity=r.get("authenticity", False), best_offer=r.get("best_offer", False)))
    for c in R["cards"]:
        c["deals"].sort(key=lambda d: -d["p_deal"])
    # D113: the highest offer that makes each listing a deal with 80% probability, landed in Italy
    ml = max_landed([r["ask_usd"] for r, *_ in rows], np.array([x[4] for x in rows]), np.array([x[5] for x in rows]),
                    sigma_q, stats["mu_l"], stats["s_l"])
    offers = []
    for (r, c, g, cost, m, s), pg_, pd_, lmax in zip(rows, pg, pdl, ml):
        if pd_ >= DEALS_MIN or pg_ < 0.5:
            continue                                    # already a deal at the asking price, or not a credible listing
        offer_eur = price_for_landed(float(lmax) * EUR, cost["ship_eur"], r.get("country"))
        ask_eur = r["ask_usd"] * EUR
        if offer_eur <= 0 or offer_eur >= ask_eur:
            continue
        ratio = offer_eur / ask_eur
        if ratio < OFFER_MIN:
            continue                                    # an offer this far below the ask is very unlikely to be accepted
        offers.append(dict(card=c["id"], grade=r["grade"], ask_eur=round(ask_eur, 2), offer_eur=round(offer_eur, 2),
                           discount=round(1 - ratio, 3), best_offer=bool(r.get("best_offer")), origin=cost["origin"],
                           ship_eur=round(cost["ship_eur"], 2), value_eur=round(g["value"] * EUR, 2), url=r["url"], title=r["title"],
                           market=r["market"], cert=bool(r.get("cert")), seller_pct=r.get("seller_pct"), seller_n=r.get("seller_n")))
    offers.sort(key=lambda o: (not o["best_offer"], o["discount"]))
    R["offers"] = offers[:OFFERS_SHOWN]
    funnel.update(offerte_possibili=len(offers), offerte_con_proposta=sum(o["best_offer"] for o in offers))
    funnel.update(sotto_il_valore=under, p_deal=[round(float(x), 3) for x in sorted(pdl, reverse=True)[:20]],
                  occasioni=sum(len(c["deals"]) for c in R["cards"]))
R["deals_asof"], R["deal_stats"], R["deal_funnel"] = L["asof"], stats, funnel
json.dump(R, open(data_p, "w"), ensure_ascii=False, separators=(",", ":"))
print(json.dumps(funnel, ensure_ascii=False), stats)
