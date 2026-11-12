"""Daily check of the cards requested by visitors (D97).

Usage: PYTHONPATH=. python scripts/card_requests.py [prototype/data/requests_status.json]

For each requested card (most requested first, at most MAX_CHECKS per run, cards on hold checked again after
7 days): the card on TCGdex (name, set, number, release year), the same card on tcgcharts (same number,
language and set, base printing), its PSA 7-10 sales of the last 365 days on every platform (D232), and how many of
their titles our own title matcher assigns to that card with the right grade. Admission rule of D97 and D232:
  unique card on tcgcharts; >= 27 recognised sales (90% of 30); >= 5 sales in at least 2 grades (1 for a Japanese
  card, D231); >= 60% recognised.
Writes {"<lang>:<id>": {status, detail, checked, n, recognised, share, tc_id}}. Adding an admitted card to the
catalogue is a separate step (status "pronta" -> "aggiunta").
"""
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

from slabwise.sources import auction_titles as at
ASSIGN = os.environ.get("SLABWISE_ASSIGN", "1") == "1"   # D258 (protocol §56): the providers' card unless the title contradicts it

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://slabwise.pages.dev/api/richieste"
TCGDEX = "https://api.tcgdex.net/v2"
TCG = "https://tcgcharts.com"
UA = "Mozilla/5.0 (Slabwise research; permission from tcgcharts, 27 Oct 2026)"
PAUSE_S = 3.0
MAX_CHECKS = 15
MIN_SALES, MIN_GRADE_SALES, MIN_GRADES, MAX_CONTRA = 10, 5, 1, 0.40   # D266: 10 sales in a year, 5 in one grade; D281: at most 40% contradicting titles
GRAIL_RANK, GRAIL_MIN_SALES = 100, 10          # D150, D266: same threshold for every card now


def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(5):               # 7 Nov: tcgcharts answers 503 after a long run; wait and slow down, never hammer
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                body = r.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == 4 or not url.startswith(TCG):
                raise
            time.sleep(60 * (attempt + 1))
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
    no = int(card['no']) if card['no'].isdigit() else re.sub(r"^([A-Za-z]+)0+(\d)", r"\1\2", card['no'])   # D219: "H09" is "H9" there
    q = f"{en_name or card['name']} {no}" + (" japanese" if lang == "ja" else "")
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
    hint = norm(SET_ALIAS.get(en_set or card["set"], en_set or card["set"]))
    exact = [it for it in cands if hint and norm(it.get("set")) == hint]          # D219: "Dragon" is not "Dragon Frontiers"
    if len(exact) == 1:
        return exact[0]
    same_set = [it for it in cands if hint and (hint in norm(it.get("set")) or norm(it.get("set")) in hint)]
    return same_set[0] if len(same_set) == 1 else None


SET_ALIAS = {"SVP Black Star Promos": "Scarlet & Violet Black Star Promos"}   # D219: TCGdex and tcgcharts names of the same set


def name_re(name):
    """Title regex for a card name. Sellers mostly leave out the δ of delta species cards ("Rayquaza 16/110 Holon
    Phantoms"): the set and the number already tell them apart, so the name keeps only the Pokémon."""
    n = re.sub(r"\s*(?:[δ☆★]|\bstar\b)\s*", " ", name.lower()).strip()            # gold star: "Charizard ☆"
    if at.NEW_EN_RULES:                                   # D216: "Charizard-GX" is "Charizard GX"
        n = re.sub(r"-(gx|ex|vmax|vstar|v)\b", r" \1", n)
    m3 = re.match(r"(.+?)\s*&\s*(.+?)\s*&\s*(.+?)(\s+(?:gx|ex|v|vmax|legend))?$", n) if at.NEW_EN_RULES else None
    m = re.match(r"(.+?)\s*&\s*(.+?)(\s+(?:gx|ex|v|vmax|legend))?$", n)
    if m3:                                                # D216: three names, in the printed order, "&" or "and" or nothing
        parts = [re.escape(x) for x in m3.groups()[:3]]
        r = (r"\s*(?:&|and)?\s*".join(parts) + re.escape(m3.group(4) or "")).replace(r"\ ", " ")
    elif m:                                                 # D168: tag teams are written in both orders ("Latios & Latias")
        a, b, suf = re.escape(m.group(1)), re.escape(m.group(2)), re.escape(m.group(3) or "")
        r = rf"(?:{a}\s*(?:&|and)\s*{b}|{b}\s*(?:&|and)\s*{a}){suf}".replace(r"\ ", " ")
    else:
        r = re.escape(n).replace(r"\ ", " ")
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


JA_SET_ALIAS = {"expansion pack": r"base\W*set|basic|拡張パック", "jungle": r"jungle|ジャングル", "mystery fossils": r"fossil|化石の秘密",
                "rocket gang": r"rocket|ロケット団", "gold silver to a new world": r"neo\W*genesis|neo\W*1|gold\W*silver|金、?・?銀、?・?新世界へ",
                "crossing ruins": r"neo\W*discovery|neo\W*2|crossing\W*the\W*ruins|遺跡をこえて", "awakening legends": r"neo\W*revelation|neo\W*3|めざめる伝説",
                "darkness to light": r"neo\W*destiny|neo\W*4|闇、?そして光へ", "challenge from darkness": r"gym\W*challenge|gym\W*2|challenge\W*from|闇からの挑戦",
                "leaders stadium": r"gym\W*heroes|gym\W*1|leaders?\W*stadium|リーダーズスタジアム",
                "miracle crystal": r"miracle\W*crystal|きせきの結晶", "golden sky silvery ocean": r"golden\W*sky|金の空、?銀の海",
                "offense defense furthest ends": r"dragon\W*frontiers|furthest\W*ends|さいはての攻防",
                "rulers heavens": r"rulers\W*of\W*the\W*heavens|天空の覇者", "holon phantom": r"holon\W*phantoms?|ホロンの幻影",
                "wind from sea": r"wind\W*from\W*the\W*sea|海からの風", "advent arceus": r"advent\W*of\W*arceus|アルセウス光臨",
                "mega dream ex": r"mega\W*dream|m2a", "tag bolt": r"tag\W*bolt|sm9\b",
                "to have seen battle rainbow": r"battle\W*rainbow|sm3h", "shining legends": r"shining\W*legends|sm3\+"}


# D231: Japanese promo series as titles write them ("XY Promo", "XY-P", "Sun & Moon Promo", "SM-P", "S-P Promo"...)
JA_PROMO_SET = {"xy": r"xy", "sun moon": r"(?:sm|sun\W*(?:&|and)?\W*moon)", "sword shield": r"(?:s|swsh|sword\W*(?:&|and)?\W*shield)",
                "scarlet violet": r"(?:sv|scarlet\W*(?:&|and)?\W*violet)", "mega evolution": r"(?:m|mega(?:\W*evolution)?)",
                "black white": r"(?:bw|black\W*(?:&|and)?\W*white)", "diamond pearl": r"(?:dp|diamond\W*(?:&|and)?\W*pearl)"}


def ja_promo_setre(set_name):
    """D231: set regex of a Japanese promo series ("XY Promos" -> "xy promo" or "xy-p"), None for other sets."""
    low = (set_name or "").lower().replace("black star", " ")
    words = " ".join(w for w in re.findall(r"[a-z0-9]+", low) if w not in ("and", "japanese"))
    m = re.fullmatch(r"(.+?) promos?", words)
    rx = JA_PROMO_SET.get(m.group(1)) if m else None
    return rf"\b{rx}\W*(?:black\W*star\W*)?promo|\b{rx}\W?p\b" if rx else None


def ja_entry(en_name, ja_name, no, tot, set_en):
    """Title matcher entry for a Japanese counterpart (D134): English or Japanese name, number/total or #number + set."""
    alts = [name_re(en_name)]
    if "-wearing" in en_name.lower():                       # D231: "Poncho-wearing Pikachu" is also "Poncho Wearing", "Poncho Pikachu"
        alts.append(re.escape(en_name.lower()).replace(r"\-wearing", r"\W*(?:wearing\W*)?").replace(r"\ ", " ").replace("-wearing", r"\W*(?:wearing\W*)?"))
    if ja_name:                                           # "ルギアV" is written "ルギアv", "ルギア v", "ルギアV"
        m = re.match(r"(.*?)\s*(ex|gx|vmax|vstar|v)$", ja_name.lower())
        alts.append(re.escape(m.group(1)) + r"\s?" + m.group(2) if m else re.escape(ja_name.lower()))
    words = [w for w in re.findall(r"[a-z0-9]+", (set_en or "").lower()) if w not in ("the", "of", "and", "pokemon", "card", "japanese")]
    setre = r"\b" + r"\W*".join(map(re.escape, words)) + r"\b" if words else None
    promo = ja_promo_setre(set_en)                         # D231
    if promo:
        return ["|".join(dict.fromkeys(alts)), int(no) if str(no).isdigit() else -1, -1, promo]
    alias = JA_SET_ALIAS.get(" ".join(words))              # D158: vintage Japanese sets go by their English names in titles
    if alias:                                             # Japanese words have no \b between them: no boundaries there
        asc = [a for a in alias.split("|") if re.match(r"^[\x00-\x7f]+$", a)]
        jp = [a for a in alias.split("|") if a not in asc]
        setre = r"(?:\b(?:" + "|".join(asc + ([setre[2:-2]] if setre else [])) + r")\b" + "".join("|" + a for a in jp) + ")"
    return ["|".join(dict.fromkeys(alts)), int(no) if str(no).isdigit() else -1, int(tot) if str(tot or "").isdigit() else -1, setre]


def check_ja(key, it, entry):
    """Admission check (D97 rules) for a Japanese counterpart already found on tcgcharts (D134)."""
    at.JA_CATALOGUE[key] = tuple(entry)
    try:
        return measure(it, key)
    finally:
        at.JA_CATALOGUE.pop(key, None)


WINDOW_DAYS, TOLERANCE, MAX_PAGES = 365, 1.0, 6   # D232: a year of sales on every platform; D266: no tolerance below 10


def measure(it, key, min_sales=None):
    """D97 admission rules on the sales of the last WINDOW_DAYS days, on every platform tcgcharts lists (D232)."""
    min_sales = min_sales or MIN_SALES
    need = math.ceil(min_sales * TOLERANCE)
    since = (date.today() - timedelta(days=WINDOW_DAYS)).isoformat()
    n, rec, contra, by_grade = 0, 0, 0, {}
    for g in (10, 9, 8, 7):
        for page in range(1, MAX_PAGES + 1):
            d = get(f"{TCG}/api/card-sales?" + urllib.parse.urlencode({"cardId": it["id"], "cardType": it["cardType"], "sort": "sold_date",
                                                                       "order": "DESC", "page": page, "limit": 100, "company": "PSA", "grade": g}))["data"]
            old = False
            for s in d["sales"]:
                if (s.get("sold_date") or "")[:10] < since:
                    old = True
                    continue
                if s.get("is_excluded"):
                    continue
                n += 1
                ok, why = at.accept_assigned(s.get("title") or "", key)   # D258: the providers' card unless the title contradicts it
                if not ASSIGN:
                    ok = at.match_title(s.get("title") or "")[0] == key
                if not ok and why != "stampa non detta":  # D281: a title that only leaves the printing unsaid does not count against
                    contra += 1
                if ok and at.grade_from_title(s.get("title") or "") == g:
                    rec += 1
                    by_grade[g] = by_grade.get(g, 0) + 1
            if old or not d["pagination"].get("has_next"):
                break
    at.CATALOGUE.pop(key, None)
    at.JA_CATALOGUE.pop(key, None)
    share = rec / n if n else 0.0
    out = dict(n=n, recognised=rec, share=round(share, 3), contradicting=round(contra / n, 3) if n else 0.0, tc_id=it["id"], tc_set=it.get("set"), tc_url=it.get("url"), tc_type=it.get("cardType"))
    min_grades = 1 if str(key).startswith("ja:") else MIN_GRADES   # D231: a Japanese card may trade in PSA 10 only
    if rec < need or sum(v >= MIN_GRADE_SALES for v in by_grade.values()) < min_grades:
        return dict(out, status="attesa_vendite", detail=f"{rec} vendite PSA riconosciute in un anno (ne servono {need}, con almeno {MIN_GRADE_SALES} in {min_grades} vot{'o' if min_grades == 1 else 'i'})")
    if n and contra / n > MAX_CONTRA:                  # D281: replaces "at least 60% recognised"
        return dict(out, status="attesa_coerenza", detail=f"{round(contra / n * 100)}% dei titoli contraddice la carta (al massimo il {round(MAX_CONTRA * 100)}%)")
    return dict(out, status="pronta", detail=f"{rec} vendite PSA in un anno")


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
