"""D158: give every English catalogue card its Japanese printing (same illustration), starting from the card.

Usage: PYTHONPATH=. python scripts/ja_complete.py [--max N] [--no-tc] [--retry]

For each English base card (variants and cards already matched are skipped):
1. TCGdex (en): Pokédex numbers, card type, illustrator.
2. TCGdex (ja): every card with the same Pokédex number; kept when the illustrator is the same (case and spaces ignored).
3. Image of each kept card: TCGdex, the official Japanese card database, or (comparison only, never published)
   tcgcharts; illustration distance to the English image (D152, slabwise/print_match.py), kept when <= 80/256.
4. The closest one is the Japanese printing. Its tcgcharts page (for sales) is found by a search on name and number.
State per English card in prototype/data/ja_match.json (resumable). Matched cards go into cards_ja.json as pending
pages (no price) and into the candidate queue, where the usual rules (D97, engine gate) give them a price.
--no-tc: skip tcgcharts (no comparison image from it, no sales page); those cards are retried later.
A tcgcharts 503 stops the tcgcharts part for the rest of the run (it answers 503 after a burst).
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.error
import urllib.request
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card_requests as cr  # noqa: E402
from ja_audit import official_image  # noqa: E402
from slabwise.print_match import ART_MAX, art_distance, load as load_img  # noqa: E402
from slabwise.series import is_promo  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "prototype", "data")
STATE = os.path.join(DATA, "ja_match.json")
MAX = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10 ** 6
NO_TC = "--no-tc" in sys.argv
RETRY = "--retry" in sys.argv                                 # look again at cards left without a comparison image
today = str(date.today())
tc_ok = not NO_TC


def j(p, d):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d


def dex(path):
    """TCGdex with a short pause and retries (it answers 503 to bursts)."""
    import time
    for k in range(4):
        try:
            time.sleep(0.2)
            return json.loads(urllib.request.urlopen(urllib.request.Request(cr.TCGDEX + path, headers={"User-Agent": "slabwise/0.1"}), timeout=40).read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(3 * (k + 1))
        except Exception:
            time.sleep(3 * (k + 1))
    raise RuntimeError("TCGdex non risponde")


norm_ill = lambda s: re.sub(r"[\s.\-_]", "", (s or "").lower())  # noqa: E731


_YEARS = {}


def set_year(d):
    """D214: release year of the TCGdex set of a Japanese card (None if unknown)."""
    sid = (d.get("set") or {}).get("id")
    if sid and sid not in _YEARS:
        _YEARS[sid] = ((dex(f"/ja/sets/{urllib.parse.quote(sid)}") or {}).get("releaseDate") or "")[:4] or None
    return int(_YEARS[sid]) if sid and _YEARS.get(sid) else None


def asset_url(tid):
    """TCGdex keeps images for cards whose API record has none: ja/<serie>/<set>/<number>."""
    set_id, no = tid.rsplit("-", 1)
    serie = re.match(r"[A-Za-z]+", set_id).group(0).upper()
    url = f"https://assets.tcgdex.net/ja/{serie}/{set_id}/{no}/high.webp"
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20)
        return url
    except Exception:
        return None


def tc_search(en_name, no):
    """tcgcharts Japanese base cards with this name and number: [(url, item)]."""
    global tc_ok
    if not tc_ok:
        return None
    q = f"{en_name} {int(no) if str(no).isdigit() else no} japanese"
    try:
        body = cr.get(f"{cr.TCG}/api/search?" + urllib.parse.urlencode({"q": q}), raw=True)
    except Exception as e:
        if "503" in str(e) or "429" in str(e):
            print("  tcgcharts non risponde: mi fermo con tcgcharts per questo giro", flush=True)
            tc_ok = False
        return None
    out = []
    for line in body.splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        for it in d.get("items", []) if d.get("phase") == "cards" else []:
            if (it.get("languageCode") or "").upper() == "JA" and it.get("cardType") == "base" and not it.get("variantType") \
                    and cr.num_key(it.get("cardNumber")) == cr.num_key(no):
                out.append(it)
    return out


def tc_card(it):
    """tcgcharts id, page, set of a search hit (the detail page gives the id the sales API wants)."""
    cid = it.get("id")
    if not cid:
        try:
            cid = (cr.get(cr.TCG + it["url"].replace("/pokemon/", "/api/pokemon/card-detail/", 1)).get("card") or {}).get("id")
        except Exception:
            cid = None
    return dict(id=cid, url=it["url"], set=it.get("set"), type="base") if cid else None


def match(c, hires):
    en = dex(f"/en/cards/{urllib.parse.quote(c['id'])}")
    if en is None:
        return dict(status="errore", detail="carta inglese non trovata su TCGdex")
    if not en.get("dexId"):
        return dict(status="senza_pokedex", detail="carta Allenatore o Energia: per ora non cercata")
    en_img = hires.get(c["id"]) or (en.get("image") and en["image"] + "/high.webp")
    if not en_img:
        return dict(status="senza_immagine", detail="manca l'immagine inglese")
    en_im = load_img(en_img)
    ill = norm_ill(en.get("illustrator") or c.get("ill"))
    cands = dex("/ja/cards?" + urllib.parse.urlencode({"dexId": f"eq:{en['dexId'][0]}"})) or []
    kept = []
    for b in cands:
        d = dex(f"/ja/cards/{urllib.parse.quote(b['id'])}") or {}
        if set(d.get("dexId") or []) != set(en["dexId"]):
            continue
        if ill and d.get("illustrator") and norm_ill(d["illustrator"]) != ill:
            continue
        kept.append(d)
    if not kept:
        return dict(status="nessuna", detail=f"{len(cands)} carte giapponesi dello stesso Pokémon, nessuna dello stesso illustratore")
    best, tried, need_tc = None, [], False
    for d in kept:
        img = (d.get("image") and d["image"] + "/high.webp") or asset_url(d["id"])
        if not img and d.get("name") and d["localId"].isdigit():
            img = official_image(d["name"], d["id"].rsplit("-", 1)[0], d["localId"])
        show = img
        tc_items = None
        if not img:
            tc_items = tc_search(en.get("name") or c["n"], d["localId"])
            if tc_items is None:
                need_tc = True
                continue
            # D214: a tcgcharts picture stands for this TCGdex card only if it is of a set of the same year; otherwise another
            # set with the same number lends its picture (e-series Charizard 103 got the art of Star Birth's Charizard V 103)
            yr = set_year(d)
            tc_items = [it for it in tc_items if yr and it.get("releaseYear") == yr]
            sc = [(art_distance(load_img(it["image"].replace("-small.", "-medium.")), en_im), it) for it in tc_items if it.get("image")]
            sc = sorted([x for x in sc if x[0] is not None], key=lambda x: x[0])
            if sc:                                                    # several sets share the number: keep the closest art
                tc_items = [sc[0][1]]
                img = sc[0][1]["image"].replace("-small.", "-medium.")
        dist = art_distance(load_img(img), en_im) if img else None
        tried.append([d["id"], dist])
        if dist is not None and dist <= ART_MAX and (best is None or dist < best[1]):
            best = (d, dist, show, tc_items)
    if not best and any(d_ is None for _, d_ in tried) and tc_ok:
        # vintage Japanese sets (no numbers on the cards): tcgcharts numbers them by Pokedex number; compare its pictures
        items = tc_search(en.get("name") or c["n"], str(en["dexId"][0])) or []
        scored = [(art_distance(load_img(it["image"].replace("-small.", "-medium.")), en_im), it) for it in items if it.get("image")]
        scored = sorted([x for x in scored if x[0] is not None and x[0] <= ART_MAX], key=lambda x: x[0])
        if scored:
            dist, it = scored[0]
            return dict(status="trovata", tcgdex=None, dist=dist, tried=tried + [[it["url"], dist]], ja_name=None, no=it.get("cardNumber"),
                        set=it.get("set"), tot=None, rarity=None, ill=en.get("illustrator"), img=None, tc=tc_card(it), via="tcgcharts")
    if not best:
        if need_tc:
            return dict(status="da_riprovare", detail="servono le immagini di tcgcharts", tried=tried)
        if any(d_ is None for _, d_ in tried):
            return dict(status="senza_immagine", detail="per alcune stampe giapponesi manca l'immagine da confrontare", tried=tried)
        return dict(status="nessuna", detail=f"{len(kept)} dello stesso illustratore, nessuna con la stessa illustrazione", tried=tried)
    d, dist, show, tc_items = best
    if tc_items is None:
        tc_items = tc_search(en.get("name") or c["n"], d["localId"])
        yr = set_year(d)                                             # D214: the sales page is of a set of the same year
        if tc_items and yr:                                          # year unknown on TCGdex: as before
            tc_items = [it for it in tc_items if it.get("releaseYear") == yr]
    tc = None
    if tc_items:
        if len(tc_items) > 1:                                        # same number in several Japanese sets: the same art
            scored = [(art_distance(load_img(it["image"].replace("-small.", "-medium.")), en_im), it) for it in tc_items if it.get("image")]
            scored = [x for x in scored if x[0] is not None and x[0] <= ART_MAX]
            tc_items = [min(scored, key=lambda x: x[0])[1]] if scored else []
        tc = tc_items[0] if tc_items else None
    return dict(status="trovata", tcgdex=d["id"], dist=dist, tried=tried, ja_name=d.get("name"), no=d.get("localId"),
                set=(d.get("set") or {}).get("name"), tot=((d.get("set") or {}).get("cardCount") or {}).get("official"),
                rarity=d.get("rarity"), ill=d.get("illustrator"), img=show,
                tc=tc_card(tc) if tc else None)


def main():
    cards = j(os.path.join(DATA, "cards.json"), [])
    hires = j(os.path.join(DATA, "hires.json"), {})
    ja = j(os.path.join(DATA, "cards_ja.json"), [])
    done_en = {x["en"] for x in ja if x.get("en_same")}
    state = j(STATE, {})
    todo = [c for c in cards if "/" not in c["id"] and c["id"] not in done_en and not is_promo(c["id"])
            and (state.get(c["id"], {}).get("status") not in ("trovata", "nessuna", "senza_pokedex") + (() if RETRY else ("senza_immagine",))
                 or (state[c["id"]]["status"] == "trovata" and not state[c["id"]].get("tc") and not NO_TC))][:MAX]
    print(f"{len(todo)} carte inglesi da abbinare", flush=True)
    for c in todo:
        if not NO_TC and not tc_ok:                                   # tcgcharts stopped answering: the rest waits
            break
        try:
            r = match(c, hires)
        except Exception as e:
            r = dict(status="errore", detail=str(e)[:100])
        r["checked"] = today
        state[c["id"]] = r
        print(f"  {c['id']:14s} {c['n'][:24]:24s} {r['status']}: {r.get('tcgdex', '')} {r.get('dist', '')} {r.get('detail', '')}", flush=True)
        json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=1)
    publish(state, cards)


def publish(state, cards):
    """Matched printings into cards_ja.json (pending pages) and into the queue (for a price)."""
    from add_cards import webp
    ja_p, q_p = os.path.join(DATA, "cards_ja.json"), os.path.join(DATA, "candidates_queue.json")
    ja, queue = j(ja_p, []), j(q_p, {})
    have = {x["id"]: x for x in ja}
    by_id = {c["id"]: c for c in cards}
    n_new = 0
    for en_id, r in state.items():
        if r.get("status") != "trovata" or en_id not in by_id:
            continue
        key = "ja:" + (r["tcgdex"].lower() if r.get("tcgdex") else
                       r["tc"]["url"].rstrip("/").split("/")[-2].replace("-japanese", "") + "-" + str(r["no"]))   # vintage: from tcgcharts
        if key in have:
            have[key].update(en=en_id, en_same=True, en_check=f"illustrazione uguale (distanza {r['dist']}/256)")
        else:
            e = dict(id=key, en=en_id, en_same=True, en_check=f"illustrazione uguale (distanza {r['dist']}/256)", lang="ja", n=r["ja_name"],
                     no=str(r["no"]), set=r["set"], tot=r["tot"], r=r["rarity"], ill=r["ill"], set_en=(r.get("tc") or {}).get("set"),
                     source="TCGdex ja" if r.get("tcgdex") else "catalogo Slabwise", added="D158", pending=True)
            if r.get("img"):
                try:
                    e.update(img=webp(r["img"], 360), img_url=r["img"])
                except Exception:
                    pass
            ja.append(e)
            have[key] = e
            n_new += 1
        if r.get("tc") and key not in queue:
            en = by_id[en_id]
            queue[key] = dict(id=key, lang="ja", tcgdex=r["tcgdex"], en=en_id, en_same=True, name=f"{en['n']} (giapponese)", ja_name=r["ja_name"],
                              set=r["tc"]["set"], no=r["no"], rank=None, tc_id=r["tc"]["id"], tc_type="base", tc_url=r["tc"]["url"],
                              tc_set=r["tc"]["set"], set_en=r["tc"]["set"],
                              entry=cr.ja_entry(en["n"], r["ja_name"], r["no"], r["tot"], r["tc"]["set"]),
                              status="in_valutazione", detail="stampa giapponese trovata (D158): si controllano le vendite", checked=today)
    json.dump(ja, open(ja_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(queue, open(q_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{n_new} stampe giapponesi nuove nel catalogo (in attesa di prezzo)")


if __name__ == "__main__":
    main()
