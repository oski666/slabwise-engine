"""Active eBay listings of our catalogue cards for the deals page (D72), through the official Browse API.

Usage: PYTHONPATH=. python scripts/ebay_listings.py [data/raw/ebay/listings.json]

Keys: ~/.slabwise/ebay_client_id and ~/.slabwise/ebay_client_secret (production keyset), campaign of the eBay
Partner Network in ~/.slabwise/epn_campaign_id. Every run replaces the previous file: no archive of listings
(licence §8.1). Only Buy It Now listings of PSA 7-10 copies that ship to Italy are kept. For listings priced
under the site's value (the only ones that can be deals) the item page of the API is read for the cert number
and the authenticity guarantee.
"""
import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from slabwise.sources.auction_titles import grade_from_title, match_title
# D187: German and French names of Pokémon in the catalogue whose English name differs (a listing may not say the language)
FOREIGN_NAME = re.compile(r"\b(?:glurak|turtok|bisaflor|glumanda|schiggy|bisasam|flamara|aquana|blitza|nachtara|psiana|folipurba|glaziola|feelinara"
                          r"|mewtu|relaxo|garados|simsala|lavados|arktos|despotar|maxax|ultrigaria|pummeluff|dragoran|evoli|smettbo"
                          r"|dracaufeu|tortank|florizarre|salam[eè]che|carapuce|bulbizarre|pyroli|aquali|voltali|noctali|mentali|phyllali|givrali|nymphali"
                          r"|ronflex|l[ée]viator|sulfura|artikodin|[ée]lecthor|tyranocif|dracolosse|[ée]voli|lokhlass|ectoplasma)\b")

HOME = os.path.expanduser("~/.slabwise")
API = "https://api.ebay.com"
MARKETS = {"EBAY_US": "183454", "EBAY_IT": None, "EBAY_DE": None,     # category "CCG individual cards" is known on US only
           "EBAY_ES": None}   # D113: Spain added; France, Netherlands and Austria tried: 24 listings in all, not worth the calls
PAUSE_S = 0.3
DETAIL_MAX = 100                                   # item pages read per run (5,000 eBay calls a day in all)


def key(name):
    return open(os.path.join(HOME, name)).read().strip()


def token():
    cred = base64.b64encode(f"{key('ebay_client_id')}:{key('ebay_client_secret')}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}).encode()
    req = urllib.request.Request(f"{API}/identity/v1/oauth2/token", data=body, method="POST",
                                 headers={"Authorization": f"Basic {cred}", "Content-Type": "application/x-www-form-urlencoded"})
    return json.load(urllib.request.urlopen(req, timeout=30))["access_token"]


def get(path, tok, market, params=None):
    url = f"{API}{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    ctx = f"affiliateCampaignId={key('epn_campaign_id')},contextualLocation=" + urllib.parse.quote("country=IT")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "X-EBAY-C-MARKETPLACE-ID": market,
                                               "X-EBAY-C-ENDUSERCTX": ctx, "Accept-Language": "en-US"})
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=30))
        except urllib.error.HTTPError as e:
            if e.code == 429:                                # the daily limit is used up: retrying only wastes time
                raise QuotaExhausted() from e
            if e.code in (500, 502, 503) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise


class QuotaExhausted(Exception):
    """eBay answered 429: no more calls of this kind until the daily reset (08:00 UTC)."""


_BULK = [True]


def get_items(ids, tok, market):
    """Item pages. getItems (20 per call, its own daily limit) needs an access eBay grants on request: until then
    (403) one getItem per item, which counts against the search limit, so callers keep the list short."""
    out = []
    for i in range(0, len(ids), 20):
        if _BULK[0]:
            try:
                res = get("/buy/browse/v1/item/", tok, market, {"item_ids": ",".join(ids[i:i + 20])})
                out += res.get("items") or []
                time.sleep(PAUSE_S)
                continue
            except urllib.error.HTTPError as e:
                if e.code != 403:
                    raise
                _BULK[0] = False
        for item in ids[i:i + 20]:
            try:
                out.append(get(f"/buy/browse/v1/item/{urllib.parse.quote(item)}", tok, market))
            except urllib.error.HTTPError as e:
                if e.code not in (404, 410):
                    raise
            time.sleep(PAUSE_S)
    return out


def money(x, eur_per_usd):
    """(value in USD, currency) or None for currencies we do not convert."""
    if not x:
        return None
    v, c = float(x["value"]), x.get("currency")
    if c == "USD":
        return v
    if c == "EUR":
        return v / eur_per_usd
    return None


def catalogue_queries(alt_query):
    """Search words for every catalogue card (D112): Alt's wording when it exists, else name, set and number."""
    from slabwise.ebay_budget import monitored                 # D135: only the cards within the eBay budget
    cards = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data", "cards.json")))
    keep = monitored(cards, datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    queries = {k: v for k, v in alt_query.items() if k in keep}
    for c in cards:
        if c["id"] in keep and c["id"] not in queries:
            no = str(c.get("no") or "").lstrip("0") or str(c.get("no"))
            queries[c["id"]] = f'{c["n"]} {c.get("set") or ""} #{no}'
    return queries


def parse_item(it, market, queries, eur):
    """One eBay item summary -> a listing row, or None when it is not a single PSA 7-10 copy of a catalogue card."""
    title = it.get("title") or ""
    low = title.lower()
    if re.search(r"\b(cgc|bgs|sgc|beckett|tag|ace|pgs|ags|gma|hga|isa|pca|cgs|mnt|ksa|psg)\b", low):
        return None                                          # another grading company in the title
    if not re.search(r"\bpsa\s*(10|9|8|7)\b", low) or len(re.findall(r"\b\d{1,3}\s*/\s*\d{2,3}\b", title)) > 1:
        return None                                          # PSA grade written out; one card only
    if re.search(r"\b(lot|lotto|bundle|sequenzial\w*|sequential|choose|pick|proxy|custom|reprint|digital|complete set|set of|master set|potential|candidate|worthy|ready|possible|raw|ungraded|not graded|grade it|gradable|pre-?grade\w*)\b", low):
        return None
    grade = grade_from_title(title)
    card, _ = match_title(title)
    if card not in queries or grade not in (7, 8, 9, 10):     # catalogue card, base printing only
        return None
    if not card.startswith("ja:") and re.search(r"\b(japanese|japan|jpn|jap|giapponese|japanisch|sv2a|sv4a|s6a|m2|korean|chinese)\b", low):
        return None                                          # an Asian printing is another catalogue card
    if FOREIGN_NAME.search(low):
        return None                                          # D187: German or French name of the Pokémon, so not the English card
    ask = money(it.get("price"), eur)
    ship_opts = it.get("shippingOptions") or []
    ship = money(ship_opts[0].get("shippingCost"), eur) if ship_opts else None
    if ask is None or ship is None:
        return None
    seller = it.get("seller") or {}
    try:                                                  # D73: a seller with no track record is not judged
        if float(seller.get("feedbackPercentage") or 0) < 98 or int(seller.get("feedbackScore") or 0) < 20:
            return None
    except ValueError:
        return None
    return dict(item=it["itemId"], legacy=it.get("legacyItemId"), market=market, card=card, grade=grade, title=title,
                     ask_usd=round(ask, 2), ship_usd=round(ship, 2), country=(it.get("itemLocation") or {}).get("country"),
                     url=it.get("itemAffiliateWebUrl") or it.get("itemWebUrl"), affiliate=bool(it.get("itemAffiliateWebUrl")),
                     seller_pct=seller.get("feedbackPercentage"), seller_n=seller.get("feedbackScore"),
                     programs=it.get("qualifiedPrograms") or [], best_offer="BEST_OFFER" in (it.get("buyingOptions") or []),
                     image=(it.get("image") or {}).get("imageUrl"), cert=None)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "data/raw/ebay/listings.json"
    here = os.path.dirname(os.path.abspath(__file__))
    import importlib.util
    spec = importlib.util.spec_from_file_location("alt_sold", os.path.join(here, "alt_sold.py"))
    alt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alt)
    real = json.load(open(os.path.join(here, "..", "prototype", "data", "real.json")))
    eur = real["eur_rate"]
    value = {(c["id"], g["grade"]): g["value"] for c in real["cards"] for g in c["grades"]}
    tok = token()
    seen, rows, calls = set(), [], 0
    queried = {}                                               # D225: cards searched on every market, and if a search was cut at 200
    queries = catalogue_queries(alt.QUERY)                     # D112: every catalogue card, not only the first 29
    quota_out = False
    for cid, q in queries.items():
        if quota_out:
            break
        for market, cat in MARKETS.items():
            params = {"q": q.replace("#", "") + " PSA", "limit": "200",
                      "filter": "buyingOptions:{FIXED_PRICE},deliveryCountry:IT"}
            if cat:
                params["category_ids"] = cat
            try:
                res = get("/buy/browse/v1/item_summary/search", tok, market, params)
            except QuotaExhausted:
                print("  limite giornaliero eBay finito: mi fermo qui", flush=True)
                quota_out = True
                break
            except urllib.error.HTTPError as e:
                print(f"  {cid} {market}: errore {e.code}", flush=True)
                continue
            calls += 1
            q_ = queried.setdefault(cid, {"markets": 0, "capped": False})
            q_["markets"] += 1
            q_["capped"] = q_["capped"] or int(res.get("total") or 0) > int(params["limit"])
            for it in res.get("itemSummaries", []):
                if it["itemId"] in seen:
                    continue
                seen.add(it["itemId"])
                r_ = parse_item(it, market, queries, eur)
                if r_ is None:
                    continue
                rows.append(r_)
            time.sleep(PAUSE_S)
        print(f"  {cid}: {sum(r['card'] == cid for r in rows)} annunci", flush=True)
    # only listings that can be deals: their item page gives the cert and the authenticity guarantee
    cand = [r for r in rows if value.get((r["card"], r["grade"])) and (r["ask_usd"] + r["ship_usd"]) <= value[(r["card"], r["grade"])]]
    cand.sort(key=lambda r: (r["ask_usd"] + r["ship_usd"]) / value[(r["card"], r["grade"])])
    cand = cand[:DETAIL_MAX]                                     # the cheapest against their value first
    by_market = {}
    for r in cand:
        by_market.setdefault(r["market"], []).append(r)
    for market, rs in by_market.items():                         # item pages in bulk: a separate daily limit
        try:
            items = {it["itemId"]: it for it in get_items([r["item"] for r in rs], tok, market)}
        except (QuotaExhausted, urllib.error.HTTPError):
            continue
        calls += (len(rs) + 19) // 20
        for r in rs:
            it = items.get(r["item"])
            if not it:
                continue
            for a in it.get("localizedAspects") or []:
                if re.search(r"cert", a.get("name", ""), re.I) and re.fullmatch(r"\d{6,10}", (a.get("value") or "").strip()):
                    r["cert"] = a["value"].strip()
            r["authenticity"] = bool(it.get("authenticityGuarantee"))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    queried = {k: v for k, v in queried.items() if v["markets"] == len(MARKETS)}   # D225: counts only where every market was read
    json.dump({"asof": asof, "listings": rows, "queried": queried}, open(out, "w"), ensure_ascii=False)
    print(f"{len(rows)} annunci, {sum(1 for r in rows if r['cert'])} con cert, {calls} chiamate -> {out}")


if __name__ == "__main__":
    main()
