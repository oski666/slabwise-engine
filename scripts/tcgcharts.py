"""PSA populations and single sales of our catalogue cards from tcgcharts (D76; DATA_SOURCES "tcgcharts").

Usage: PYTHONPATH=. python scripts/tcgcharts.py [data/raw/tcgcharts] [--recent]

--recent (D89, daily): only the newest page (100 sales) of each card and grade, with the card mapping already in
data/raw/tcgcharts/cards.json; no search, no card page, no populations. About 120 requests.

For each catalogue card: the site's search finds the card (number, language, set, no variant), the card page
gives the PSA population per grade, the sales list gives every single sale it shows. Without an account the
site shows the last 90 days; the older sales are counted ("hidden_count") but not listed. One request every
PAUSE_S seconds, a local copy of every answer. Output: <dir>/cards.json (mapping and populations) and
<dir>/sales.json (single sales, PSA 7-10).
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://tcgcharts.com"
UA = "Mozilla/5.0 (Slabwise research; permission from tcgcharts, 27 Oct 2026)"
PAUSE_S = 3.0
HERE = os.path.dirname(os.path.abspath(__file__))


def get(path, raw=False):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                body = r.read().decode("utf-8")
            time.sleep(PAUSE_S)
            return body if raw else json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(20 * (attempt + 1))
                continue
            raise


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def find(card):
    """The tcgcharts card of a catalogue card: same number, language and set, base printing."""
    ja = card["id"].startswith("ja:")
    en = card.get("en_name") or card["n"]
    q = f"{en} {int(card['no']) if card['no'].isdigit() else card['no']}" + (" japanese" if ja else "")
    items = []
    for line in get("/api/search?" + urllib.parse.urlencode({"q": q}), raw=True).splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("phase") == "cards":
            items += d.get("items", [])
    want_lang = "JA" if ja else "EN"
    num = re.sub(r"^([a-z]*)0*(?=\d)", r"\1", str(card["no"]).strip().lower())   # D150: "H09" == "H9"
    cands = [it for it in items if it.get("type") == "card" and it.get("cardType") == "base" and not it.get("variantType")
             and (it.get("languageCode") or "").upper() == want_lang and re.sub(r"^([a-z]*)0*(?=\d)", r"\1", str(it.get("cardNumber") or "").strip().lower()) == num]
    set_hint = norm(card.get("set_en") or card["set"])
    cands.sort(key=lambda it: (set_hint not in norm(it.get("set")) and norm(it.get("set")) not in set_hint, -int(it.get("psaPopulation") or 0)))
    return cands[0] if cands else None


def recent(out):
    mapping = json.load(open(os.path.join(HERE, "..", "data", "raw", "tcgcharts", "cards.json")))
    sales = []
    for cid, m in mapping.items():
        for g in (10, 9, 8, 7):
            q = urllib.parse.urlencode({"cardId": m["tc_id"], "cardType": m["card_type"], "sort": "sold_date", "order": "DESC",
                                        "page": 1, "limit": 100, "company": "PSA", "grade": g})
            try:
                d = get("/api/card-sales?" + q)["data"]
            except urllib.error.HTTPError as e:
                print(f"  {cid} PSA {g}: errore {e.code}", flush=True)
                continue
            for s in d["sales"]:
                sales.append(dict(card=cid, tc_grade=g, **{k: s.get(k) for k in ("platform", "sale_id", "title", "grading_service", "grade",
                                  "price_cents", "sold_date", "source", "is_excluded", "exclusion_reason", "payment_pending", "payment_held")}))
    json.dump(sales, open(os.path.join(out, "sales.json"), "w"), ensure_ascii=False)
    print(f"{len(mapping)} carte, {len(sales)} vendite recenti -> {out}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0] if args else "data/raw/tcgcharts"
    os.makedirs(out, exist_ok=True)
    if "--recent" in sys.argv:
        return recent(out)
    data = os.path.join(HERE, "..", "prototype", "data")
    cards = json.load(open(os.path.join(data, "cards.json"))) + json.load(open(os.path.join(data, "cards_ja.json")))
    en_of = {c["id"]: c for c in cards}
    for c in cards:                                   # Japanese printings are searched with the English name and set
        if c["id"].startswith("ja:") and c.get("en") in en_of:
            c["en_name"] = en_of[c["en"]]["n"]
    SET_EN = {"ja:sv2a": "151", "ja:sv4a": "Shiny Treasure", "ja:m2": "Inferno X", "ja:s6a": "Eevee Heroes"}
    for c in cards:
        for pre, s in SET_EN.items():
            if c["id"].startswith(pre + "-"):
                c["set_en"] = s
    mapping, sales = {}, []
    for c in cards:
        try:
            it = find(c)
        except urllib.error.HTTPError as e:
            print(f"  {c['id']}: ricerca, errore {e.code}", flush=True)
            continue
        if not it:
            print(f"  {c['id']}: non trovata", flush=True)
            continue
        det = get(it["url"].replace("/pokemon/", "/api/pokemon/card-detail/", 1))
        json.dump(det, open(os.path.join(out, f"detail_{c['id'].replace(':', '_')}.json"), "w"), ensure_ascii=False)
        cd = det.get("card", {})
        pop = {g: cd.get(f"psa{g}Count") for g in (10, 9, 8, 7)}
        mapping[c["id"]] = dict(tc_id=it["id"], card_type=it["cardType"], url=it["url"], set=it.get("set"), name=it.get("name"),
                                psa_population=cd.get("psaPopulation"), pop=pop, graded_supply=cd.get("gradedSupply"))
        n_card, hidden = 0, None
        for g in (10, 9, 8, 7):
            page = 1
            while True:
                q = urllib.parse.urlencode({"cardId": it["id"], "cardType": it["cardType"], "sort": "sold_date", "order": "DESC",
                                            "page": page, "limit": 100, "company": "PSA", "grade": g})
                d = get("/api/card-sales?" + q)["data"]
                for s in d["sales"]:
                    sales.append(dict(card=c["id"], tc_grade=g, **{k: s.get(k) for k in ("platform", "sale_id", "title", "grading_service", "grade",
                                      "price_cents", "sold_date", "source", "is_excluded", "exclusion_reason", "payment_pending", "payment_held")}))
                    n_card += 1
                hidden = (hidden or 0) + (d.get("gate") or {}).get("hidden_count", 0) if page == 1 else hidden
                if not d["pagination"].get("has_next"):
                    break
                page += 1
        mapping[c["id"]]["hidden_sales"] = hidden
        print(f"  {c['id']} -> {it['set']} · {it['name']}: pop PSA10 {pop[10]}, {n_card} vendite visibili, {hidden} nascoste", flush=True)
        json.dump(mapping, open(os.path.join(out, "cards.json"), "w"), ensure_ascii=False, indent=1)
        json.dump(sales, open(os.path.join(out, "sales.json"), "w"), ensure_ascii=False)
    print(f"{len(mapping)} carte, {len(sales)} vendite -> {out}")


if __name__ == "__main__":
    main()
