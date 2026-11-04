"""Deals from fresh eBay listings against the values already published (D112), without running the engine again.

Usage: PYTHONPATH=. python scripts/deals_refresh.py [prototype/data/real.json] [data/raw/ebay/listings.json]

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

from slabwise.deals import landed_eur, max_landed, price_for_landed, score

HERE = os.path.dirname(os.path.abspath(__file__))
data_p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "prototype", "data", "real.json")
lst_p = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "data", "raw", "ebay", "listings.json")
DEALS_MIN = 0.5
OFFER_MIN = 0.70        # D113: offers below 70% of the asking price are not shown
OFFERS_SHOWN = 60
Z = 1.2816

R = json.load(open(data_p))
L = json.load(open(lst_p))
EUR = R["eur_rate"]
sigma_q = (R.get("params") or {}).get("sigma_q", 0.07)
certs_p = os.path.join(HERE, "..", "prototype", "data", "certs.json")
known = json.load(open(certs_p))["certs"] if os.path.exists(certs_p) else {}
by_card = {c["id"]: c for c in R["cards"]}
rows = []
skipped = {"carta non nel catalogo": 0, "voto senza stima": 0, "cert di un'altra carta": 0}
for r in L["listings"]:
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
