"""PSA populations and single sales of our catalogue cards from tcgcharts (D76; DATA_SOURCES "tcgcharts").

Usage: PYTHONPATH=. python scripts/tcgcharts.py [data/raw/tcgcharts] [--recent]

--recent (D89, D297, daily): the newest page (100 sales) of the cards and grades that are due, with the card mapping already in
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
        except (TimeoutError, urllib.error.URLError, ConnectionError) as e:   # 14 Nov: a slow answer stopped the whole run
            if attempt < 2:
                time.sleep(20 * (attempt + 1))
                continue
            raise urllib.error.HTTPError(BASE + path, 599, f"rete: {e}", None, None)


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


BUDGET_MIN = float(os.environ.get("TC_BUDGET_MIN", "75"))   # D297: the daily run stops in time to save what it got


def recent(out):
    """D89, D297: the newest page (100 sales) of each card and grade, as many as fit in BUDGET_MIN minutes at one
    request every 3 seconds (the permission). With 1,000+ cards they no longer fit in a day, so each card x grade is
    due again after a pause that follows how fast it sells: half the days the last page of 100 sales covered (at least
    1 day, at most 7), 14 days when it had no sales. The most overdue go first; data/raw/tcgcharts/recent_state.json
    keeps when each was last read."""
    raw = os.path.join(HERE, "..", "data", "raw", "tcgcharts")
    mapping = json.load(open(os.path.join(raw, "cards.json")))
    st_p = os.path.join(raw, "recent_state.json")
    state = json.load(open(st_p)) if os.path.exists(st_p) else {}
    now = time.time()

    def due(k):
        s_ = state.get(k)
        if not s_:
            return 1e9                                    # never read: first
        span = s_.get("span_days")
        pause = 14.0 if not s_.get("n") else min(7.0, max(1.0, 0.5 * (span or 2.0)))
        return (now - s_["at"]) / 86400 / pause          # > 1 means overdue
    todo = sorted(((cid, g) for cid in mapping for g in (10, 9, 8, 7)), key=lambda x: -due(f"{x[0]}|{x[1]}"))
    todo = [x for x in todo if due(f"{x[0]}|{x[1]}") >= 1]
    sales, done = [], 0
    t0 = time.time()
    for cid, g in todo:
        if time.time() - t0 > BUDGET_MIN * 60:
            break
        m = mapping[cid]
        q = urllib.parse.urlencode({"cardId": m["tc_id"], "cardType": m["card_type"], "sort": "sold_date", "order": "DESC",
                                    "page": 1, "limit": 100, "company": "PSA", "grade": g})
        try:
            d = get("/api/card-sales?" + q)["data"]
        except urllib.error.HTTPError as e:
            print(f"  {cid} PSA {g}: errore {e.code}", flush=True)
            continue
        days = sorted(str(s.get("sold_date") or "")[:10] for s in d["sales"] if s.get("sold_date"))
        span = None
        if len(days) >= 2:
            import datetime as _dt
            span = (_dt.date.fromisoformat(days[-1]) - _dt.date.fromisoformat(days[0])).days
        state[f"{cid}|{g}"] = dict(at=time.time(), n=len(d["sales"]), span_days=span)
        done += 1
        if done % 100 == 0:                               # saved as it goes: a stopped run keeps what it read
            json.dump(sales, open(os.path.join(out, "sales.json"), "w"), ensure_ascii=False)
            json.dump(state, open(st_p, "w"))
        for s in d["sales"]:
            sales.append(dict(card=cid, tc_grade=g, **{k: s.get(k) for k in ("platform", "sale_id", "title", "grading_service", "grade",
                              "price_cents", "sold_date", "source", "is_excluded", "exclusion_reason", "payment_pending", "payment_held")}))
    json.dump(sales, open(os.path.join(out, "sales.json"), "w"), ensure_ascii=False)
    json.dump(state, open(st_p, "w"))
    print(f"{len(mapping)} carte; lette {done} di {len(todo)} combinazioni carta x voto in scadenza; {len(sales)} vendite -> {out}")


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
    # D297: within BUDGET_MIN minutes, starting from the mapping already there: the cards not mapped yet first (with all
    # their sales), then the populations of the others, oldest refresh first. The newest sales come from --recent.
    old_p = os.path.join(HERE, "..", "data", "raw", "tcgcharts", "cards.json")
    mapping = json.load(open(old_p)) if os.path.exists(old_p) else {}
    sales = []
    t0 = time.time()
    cards.sort(key=lambda c: (c["id"] in mapping, (mapping.get(c["id"]) or {}).get("pop_at", 0)))
    for c in cards:
        if time.time() - t0 > BUDGET_MIN * 60:
            print(f"  tempo finito (D297): {len(mapping)} carte nella mappa", flush=True)
            break
        known = mapping.get(c["id"])
        if known:                                     # only the population and the hidden count again
            try:
                det = get(known["url"].replace("/pokemon/", "/api/pokemon/card-detail/", 1))
            except urllib.error.HTTPError as e:
                print(f"  {c['id']}: scheda, errore {e.code}", flush=True)
                continue
            cd = det.get("card", {})
            known.update(psa_population=cd.get("psaPopulation"), pop={g: cd.get(f"psa{g}Count") for g in (10, 9, 8, 7)},
                         graded_supply=cd.get("gradedSupply"), pop_at=time.time())
            json.dump(mapping, open(os.path.join(out, "cards.json"), "w"), ensure_ascii=False, indent=1)
            continue
        try:
            it = find(c)
        except urllib.error.HTTPError as e:
            print(f"  {c['id']}: ricerca, errore {e.code}", flush=True)
            continue
        if not it:
            print(f"  {c['id']}: non trovata", flush=True)
            continue
        try:
            det = get(it["url"].replace("/pokemon/", "/api/pokemon/card-detail/", 1))
        except urllib.error.HTTPError as e:
            print(f"  {c['id']}: scheda, errore {e.code}", flush=True)
            continue
        json.dump(det, open(os.path.join(out, f"detail_{c['id'].replace(':', '_')}.json"), "w"), ensure_ascii=False)
        cd = det.get("card", {})
        pop = {g: cd.get(f"psa{g}Count") for g in (10, 9, 8, 7)}
        mapping[c["id"]] = dict(tc_id=it["id"], card_type=it["cardType"], url=it["url"], set=it.get("set"), name=it.get("name"),
                                psa_population=cd.get("psaPopulation"), pop=pop, graded_supply=cd.get("gradedSupply"), pop_at=time.time())
        n_card, hidden = 0, None
        for g in (10, 9, 8, 7):
            page = 1
            while True:
                q = urllib.parse.urlencode({"cardId": it["id"], "cardType": it["cardType"], "sort": "sold_date", "order": "DESC",
                                            "page": page, "limit": 100, "company": "PSA", "grade": g})
                try:
                    d = get("/api/card-sales?" + q)["data"]
                except urllib.error.HTTPError as e:
                    print(f"  {c['id']} PSA {g}: errore {e.code}", flush=True)
                    break
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
    json.dump(mapping, open(os.path.join(out, "cards.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(sales, open(os.path.join(out, "sales.json"), "w"), ensure_ascii=False)
    print(f"{len(mapping)} carte, {len(sales)} vendite -> {out}")


if __name__ == "__main__":
    main()
