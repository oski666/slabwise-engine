"""One-week measurement (D114): how many real deals appear among NEW eBay listings, and how long they stay.

Usage: PYTHONPATH=. python scripts/deal_watch.py <real.json> <state dir>

Every hour: the newest "Buy It Now" listings of every catalogue card (eBay US and Italy, sorted by newly listed,
shipping to Italy), kept when they were created since the previous run (D116) and pass the same filters as the deals.
Each one is scored against the published values (score_fixed, with this morning's honest-ask spread). The
listings with deal probability >= 0.5 are remembered by item id, and the following runs check whether they are
still for sale, to measure how long a deal lasts. Only item ids and derived numbers are kept (no titles, images
or prices), for the week of the measurement; the files live as workflow artifacts, never in the repository.
"""
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ebay_listings as el  # noqa: E402

from slabwise.deals import landed_eur, score_fixed  # noqa: E402

R = json.load(open(sys.argv[1]))
state_dir = sys.argv[2]
os.makedirs(state_dir, exist_ok=True)
state_p, log_p = os.path.join(state_dir, "state.json"), os.path.join(state_dir, "log.json")
state = json.load(open(state_p)) if os.path.exists(state_p) else {}
log = json.load(open(log_p)) if os.path.exists(log_p) else []
EUR = R["eur_rate"]
ds = R.get("deal_stats") or {"mu_l": 0.38, "s_l": 0.345}
sigma_q = (R.get("params") or {}).get("sigma_q", 0.07)
by = {c["id"]: c for c in R["cards"]}
now = datetime.now(timezone.utc)
# D116: GitHub's hourly runs arrive late or not at all, so look back to the previous run (at most 24 hours)
prev = datetime.fromisoformat(log[-1]["at"]) if log else now - timedelta(minutes=70)
since = max(prev - timedelta(minutes=10), now - timedelta(hours=24))

import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("alt_sold", os.path.join(os.path.dirname(os.path.abspath(__file__)), "alt_sold.py"))
alt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alt)
queries = el.catalogue_queries(alt.QUERY)
tok = el.token()
rows, seen, calls = [], set(), 0
quota_out = False
for cid, q in queries.items():
    if quota_out:
        break
    for market, cat in (("EBAY_US", "183454"), ("EBAY_IT", None)):
        params = {"q": q.replace("#", "") + " PSA", "limit": "50", "sort": "newlyListed",
                  "filter": "buyingOptions:{FIXED_PRICE},deliveryCountry:IT"}
        if cat:
            params["category_ids"] = cat
        try:
            res = el.get("/buy/browse/v1/item_summary/search", tok, market, params)
        except el.QuotaExhausted:
            print("  limite giornaliero eBay finito: mi fermo qui")
            quota_out = True
            break
        except Exception as e:
            print(f"  {cid} {market}: {str(e)[:60]}")
            continue
        calls += 1
        for it in res.get("itemSummaries", []):
            created = it.get("itemCreationDate")
            if not created or it["itemId"] in seen:
                continue
            if datetime.fromisoformat(created.replace("Z", "+00:00")) < since:
                continue
            seen.add(it["itemId"])
            r = el.parse_item(it, market, queries, EUR)
            if r:
                rows.append(r)
        time.sleep(el.PAUSE_S)
scored = []
for r in rows:
    c = by.get(r["card"])
    g = c and next((g for g in c["grades"] if g["grade"] == r["grade"]), None)
    if not g or not g.get("value") or not g.get("sales_all") or g.get("off"):
        continue
    cost = landed_eur(r["ask_usd"] * EUR, r["ship_usd"] * EUR, r.get("country"))
    scored.append((r, g, cost))
cands = 0
if scored:
    m = np.array([math.log(g["value"]) for _, g, _ in scored])
    s = np.array([(math.log(g["hi"]) - math.log(g["lo"])) / 2.5632 for _, g, _ in scored])
    pg, pdl = score_fixed([r["ask_usd"] for r, _, _ in scored], [cost["landed_eur"] / EUR for *_, cost in scored], m, s, sigma_q, ds["mu_l"], ds["s_l"])
    for (r, g, cost), pg_, pd_ in zip(scored, pg, pdl):
        if pd_ >= 0.5 and r["item"] not in state:
            cands += 1
            state[r["item"]] = {"card": r["card"], "grade": r["grade"], "p_deal": round(float(pd_), 3), "origin": cost["origin"],
                                "landed_vs_value": round(cost["landed_eur"] / (g["value"] * EUR), 3), "first_seen": now.isoformat(), "gone": None}
# are the deals seen before still for sale?
checked = 0
open_items = [item for item, st in state.items() if not st["gone"]]
try:                                                       # item pages in bulk (separate daily limit), 20 per call
    found = {it["itemId"]: it for it in el.get_items(open_items, tok, "EBAY_US")} if open_items else {}
    for item in open_items:
        it = found.get(item)
        if it is None or (it.get("estimatedAvailabilities") or [{}])[0].get("estimatedAvailabilityStatus") == "OUT_OF_STOCK":
            state[item]["gone"] = now.isoformat()             # not returned any more: ended or sold
        checked += 1
except (el.QuotaExhausted, urllib.error.HTTPError) as e:
    print(f"  controllo annunci saltato: {str(e)[:60]}")
log.append({"at": now.isoformat(), "since": since.isoformat(), "calls": calls, "new_listings": len(rows), "scored": len(scored), "new_deals": cands, "checked": checked,
            "p_deal_top": sorted([round(float(x), 3) for x in (pdl if scored else [])], reverse=True)[:5]})
json.dump(state, open(state_p, "w"), indent=1)
json.dump(log, open(log_p, "w"), indent=1)
print(json.dumps(log[-1]))
