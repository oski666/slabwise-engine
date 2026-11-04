"""Daily check of the cards requested by visitors (D97).

Usage: PYTHONPATH=. python scripts/card_requests.py [prototype/data/requests_status.json]

For each requested card (most requested first, at most MAX_CHECKS per run, cards on hold checked again after
7 days): the card on TCGdex (name, set, number, release year), the same card on tcgcharts (same number,
language and set, base printing), its PSA 7-10 sales of the last 90 days, and how many of their titles our own
title matcher assigns to that card with the right grade. Admission rule of D97:
  unique card on tcgcharts; >= 30 recognised eBay sales; >= 5 sales in at least 2 grades; >= 60% recognised.
Writes {"<lang>:<id>": {status, detail, checked, n, recognised, share, tc_id}}. Adding an admitted card to the
catalogue is a separate step (status "pronta" -> "aggiunta").
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone

from slabwise.sources import auction_titles as at

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://slabwise.pages.dev/api/richieste"
TCGDEX = "https://api.tcgdex.net/v2"
TCG = "https://tcgcharts.com"
UA = "Mozilla/5.0 (Slabwise research; permission from tcgcharts, 27 Oct 2026)"
PAUSE_S = 3.0
MAX_CHECKS = 15
MIN_SALES, MIN_GRADE_SALES, MIN_GRADES, MIN_SHARE = 30, 5, 2, 0.60
GRAIL_RANK, GRAIL_MIN_SALES = 100, 15          # D150: the most valuable cards sell less often


def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        body = r.read().decode("utf-8")
    if url.startswith(TCG):
        time.sleep(PAUSE_S)
    return body if raw else json.loads(body)


def num_key(no):
    """D150: "H09" and "H9", "SL10" and "sl10", "065" and "65" are the same card number."""
    return re.sub(r"^([a-z]*)0*(?=\d)", r"\1", str(no or "").strip().lower())


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def tcgdex(lang, cid):
    c = get(f"{TCGDEX}/{lang}/cards/{urllib.parse.quote(cid)}")
    s = c.get("set") or {}
    year = None
    try:
        year = int(get(f"{TCGDEX}/{lang}/sets/{urllib.parse.quote(s.get('id', ''))}").get("releaseDate", "")[:4])
    except Exception:
        pass
    return dict(name=c.get("name", ""), set=s.get("name", ""), no=str(c.get("localId", "")),
                total=(s.get("cardCount") or {}).get("official"), year=year)


def tc_find(card, lang, en_name=None, en_set=None):
    q = f"{en_name or card['name']} {int(card['no']) if card['no'].isdigit() else card['no']}" + (" japanese" if lang == "ja" else "")
    items = []
    for line in get(f"{TCG}/api/search?" + urllib.parse.urlencode({"q": q}), raw=True).splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("phase") == "cards":
            items += d.get("items", [])
    num = num_key(card["no"])
    want = "JA" if lang == "ja" else "EN"
    cands = [it for it in items if it.get("type") == "card" and it.get("cardType") == "base" and not it.get("variantType")
             and (it.get("languageCode") or "").upper() == want and num_key(it.get("cardNumber")) == num]
    hint = norm(en_set or card["set"])
    same_set = [it for it in cands if hint and (hint in norm(it.get("set")) or norm(it.get("set")) in hint)]
    return same_set[0] if len(same_set) == 1 else None


def name_re(name):
    """Title regex for a card name. Sellers mostly leave out the δ of delta species cards ("Rayquaza 16/110 Holon
    Phantoms"): the set and the number already tell them apart, so the name keeps only the Pokémon."""
    r = re.escape(re.sub(r"\s*(?:[δ☆★]|\bstar\b)\s*", " ", name.lower()).strip()).replace(r"\ ", " ")   # gold star: "Charizard ☆"
    return r.replace("é", "[eé]")


def temp_entry(card, lang, key):
    """A matcher entry for the requested card, built only from its name, set, number and year."""
    name = name_re(card["name"])
    setre = at.set_re(card["set"])                        # D153: "Call of Legends", "FireRed & LeafGreen", promos
    if lang == "ja":
        at.JA_CATALOGUE[key] = (name, int(card["no"]) if card["no"].isdigit() else -1, card["total"] or -1, setre)
    else:
        yrs = (card["year"], card["year"] + 1) if card["year"] else tuple(range(1999, date.today().year + 1))
        at.CATALOGUE[key] = (name, setre, at.card_no(card["no"]), yrs)


def check(req, catalogue_ids):
    lang, cid = req["lang"], req["id"]
    ours = ("ja:" + cid.lower()) if lang == "ja" else cid
    if ours in catalogue_ids:
        return dict(status="aggiunta", detail="")
    card = tcgdex(lang, cid)
    en = None
    if lang == "ja":                                      # English name and set for the search, when TCGdex has the same id
        try:
            en = tcgdex("en", cid)
        except Exception:
            en = None
    it = tc_find(card, lang, en and en.get("name"), en and en.get("set"))
    if not it:
        return dict(status="non_trovata", detail="")
    key = ours                                            # WOTC 1st edition / shadowless titles get a suffix and do not count
    temp_entry(card, lang, key)
    grail = bool(req.get("rank")) and req["rank"] <= GRAIL_RANK            # D150
    return measure(it, key, GRAIL_MIN_SALES if grail else MIN_SALES)


def ja_entry(en_name, ja_name, no, tot, set_en):
    """Title matcher entry for a Japanese counterpart (D134): English or Japanese name, number/total or #number + set."""
    alts = [name_re(en_name)]
    if ja_name:                                           # "ルギアV" is written "ルギアv", "ルギア v", "ルギアV"
        m = re.match(r"(.*?)\s*(ex|gx|vmax|vstar|v)$", ja_name.lower())
        alts.append(re.escape(m.group(1)) + r"\s?" + m.group(2) if m else re.escape(ja_name.lower()))
    words = [w for w in re.findall(r"[a-z0-9]+", (set_en or "").lower()) if w not in ("the", "of", "and", "pokemon", "card", "japanese")]
    setre = r"\b" + r"\W*".join(map(re.escape, words)) + r"\b" if words else None
    return ["|".join(dict.fromkeys(alts)), int(no) if str(no).isdigit() else -1, int(tot) if str(tot or "").isdigit() else -1, setre]


def check_ja(key, it, entry):
    """Admission check (D97 rules) for a Japanese counterpart already found on tcgcharts (D134)."""
    at.JA_CATALOGUE[key] = tuple(entry)
    try:
        return measure(it, key)
    finally:
        at.JA_CATALOGUE.pop(key, None)


def measure(it, key, min_sales=None):
    min_sales = min_sales or MIN_SALES
    n, rec, by_grade = 0, 0, {}
    for g in (10, 9, 8, 7):
        d = get(f"{TCG}/api/card-sales?" + urllib.parse.urlencode({"cardId": it["id"], "cardType": it["cardType"], "sort": "sold_date",
                                                                   "order": "DESC", "page": 1, "limit": 100, "company": "PSA", "grade": g}))["data"]
        for s in d["sales"]:
            if (s.get("platform") or "").lower() != "ebay" or s.get("is_excluded"):
                continue
            n += 1
            k, _ = at.match_title(s.get("title") or "")
            if k == key and at.grade_from_title(s.get("title") or "") == g:
                rec += 1
                by_grade[g] = by_grade.get(g, 0) + 1
    at.CATALOGUE.pop(key, None)
    at.JA_CATALOGUE.pop(key, None)
    share = rec / n if n else 0.0
    out = dict(n=n, recognised=rec, share=round(share, 3), tc_id=it["id"], tc_set=it.get("set"), tc_url=it.get("url"), tc_type=it.get("cardType"))
    if rec < min_sales or sum(v >= MIN_GRADE_SALES for v in by_grade.values()) < MIN_GRADES:
        return dict(out, status="attesa_vendite", detail=f"{rec} vendite PSA riconosciute in 90 giorni (ne servono {min_sales}, con almeno {MIN_GRADE_SALES} in {MIN_GRADES} voti)")
    if share < MIN_SHARE:
        return dict(out, status="attesa_coerenza", detail=f"{round(share * 100)}% dei titoli riconosciuti (serve il {round(MIN_SHARE * 100)}%)")
    return dict(out, status="pronta", detail=f"{rec} vendite PSA in 90 giorni")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "prototype", "data", "requests_status.json")
    try:
        status = json.load(open(out))
    except (OSError, ValueError):
        status = {}
    live = get(SITE)
    if not live.get("active"):
        print("richieste non attive sul sito")
        return
    data = os.path.join(HERE, "..", "prototype", "data")
    ids = {c["id"] for c in json.load(open(os.path.join(data, "cards.json")))} | {c["id"] for c in json.load(open(os.path.join(data, "cards_ja.json")))}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    todo = []
    for r in live["requests"]:
        k = f"{r['lang']}:{r['id']}"
        old = status.get(k)
        if old and (old["status"] in ("aggiunta", "pronta") or (date.fromisoformat(today) - date.fromisoformat(old["checked"])).days < 7):
            continue
        todo.append(r)
    for r in todo[:MAX_CHECKS]:
        k = f"{r['lang']}:{r['id']}"
        try:
            res = check(r, ids)
        except Exception as e:                               # one failed check never stops the run
            print(f"  {k}: errore {str(e)[:80]}")
            continue
        status[k] = dict(res, checked=today, requests=r["n"])
        print(f"  {k} ({r['n']} richieste): {res['status']} {res.get('detail', '')}", flush=True)
    json.dump(status, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(live['requests'])} richieste, {min(len(todo), MAX_CHECKS)} controllate -> {out}")


if __name__ == "__main__":
    main()
