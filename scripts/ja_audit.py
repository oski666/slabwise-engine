"""D152: check every Japanese printing (catalogue and queue) against the English card it is linked to.

Usage: PYTHONPATH=. python scripts/ja_audit.py
Writes en_same (true/false/null) and en_check (the reason) on each row of prototype/data/cards_ja.json and of the
Japanese rows of prototype/data/candidates_queue.json; a queued row that is another Pokémon becomes "scartata".
"""
import json
import os
import sys
import re
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card_requests as cr  # noqa: E402
from slabwise.print_match import same_print  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data")


def tcgdex_card(lang, cid):
    try:
        return cr.get(f"{cr.TCGDEX}/{lang}/cards/{urllib.parse.quote(cid)}")
    except Exception:
        return {}


def tcgdex_id(cid):
    """ja:sv2a-201 -> SV2a-201, ja:sm11b-054 -> SM11b-054 (letters before the digits upper case)."""
    s, no = cid[3:].rsplit("-", 1)
    i = next((k for k, ch in enumerate(s) if ch.isdigit()), len(s))
    return s[:i].upper() + s[i:] + "-" + no


PCC = "https://www.pokemon-card.com"


def official_image(name, set_id, no):
    """The card's image from the official Japanese card database (registered in DATA_SOURCES, D151): search by
    Japanese name, keep the hits in the set's folder, read each one's number on its page."""
    try:
        hits = json.loads(cr.get(f"{PCC}/card-search/resultAPI.php?" + urllib.parse.urlencode(
            {"keyword": name, "regulation_sidebar_form": "all", "sm_and_keyword": "true"}), raw=True)).get("cardList") or []
        for h in hits:
            if f"/{set_id.upper()}/" not in (h.get("cardThumbFile") or "").upper():
                continue
            page = cr.get(f"{PCC}/card-search/details.php/card/{h['cardID']}", raw=True)
            m = re.search(r"(\d{1,3})(?:&nbsp;| )?/(?:&nbsp;| )?\d{1,3}", page)
            if m and int(m.group(1)) == int(no):
                return PCC + h["cardThumbFile"]
    except Exception:
        return None
    return None


def ja_image(row, ja):
    if ja.get("image"):
        return ja["image"] + "/high.webp"
    tid = row.get("tcgdex") or tcgdex_id(row["id"])
    set_id, no = tid.rsplit("-", 1)
    serie = re.match(r"[A-Za-z]+", set_id).group(0).upper()
    url = f"https://assets.tcgdex.net/ja/{serie}/{set_id}/{no}/high.webp"
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20)
        return url
    except Exception:
        pass
    name = row.get("ja_name") or row.get("n") or ja.get("name")
    return official_image(name, set_id, no) if name and no.isdigit() else None


def check(row, ja_img, hires):
    ja = tcgdex_card("ja", row.get("tcgdex") or tcgdex_id(row["id"]))
    en = tcgdex_card("en", row["en"])
    ja_img = ja_img or ja_image(row, ja)
    en_img = hires.get(row["en"]) or (en.get("image") and en["image"] + "/high.webp")
    return same_print(ja, en, ja_img, en_img)


def main():
    hires = json.load(open(os.path.join(DATA, "hires.json")))
    cp = os.path.join(DATA, "cards_ja.json")
    cards = json.load(open(cp))
    for c in cards:
        ok, why = check(dict(c, tcgdex=c.get("tcgdex")), c.get("img"), hires)
        c.update(en_same=ok, en_check=why)
        print(f"  {c['id']:14s} -> {c['en']:14s} {ok}: {why}")
    json.dump(cards, open(cp, "w"), ensure_ascii=False, indent=1)
    qp = os.path.join(DATA, "candidates_queue.json")
    queue = json.load(open(qp))
    have = {c["id"]: c for c in cards}
    for k, r in queue.items():
        if r.get("lang") != "ja" or not r.get("en"):
            continue
        if k in have:
            ok, why = have[k]["en_same"], have[k]["en_check"]
        else:
            ok, why = check(r, None, hires)
        r.update(en_same=ok, en_check=why)
        if ok is False and why in ("Pokémon diverso", "tipo di carta diverso") and r["status"] != "aggiunta":
            r.update(status="scartata", detail=f"non è la stampa giapponese di {r['en']}: {why} (D152)")
        print(f"  coda {k:14s} -> {r['en']:14s} {ok}: {why} [{r['status']}]")
    json.dump(queue, open(qp, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
