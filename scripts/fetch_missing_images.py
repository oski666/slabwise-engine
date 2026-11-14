"""Fill in card images that TCGdex does not have (D45), from sources registered in docs/DATA_SOURCES.md:
- English cards: Pokémon TCG API image CDN (images.pokemontcg.io)
- Japanese printings: the official Japanese card database (www.pokemon-card.com)
- with --tcgcharts, last: the cards still without an image, from tcgcharts (Marek's permission, D298), one request every
  3 seconds, only for cards in the tcgcharts map (data/raw/tcgcharts/cards.json, private data)
Images are stored like the others: webp data URIs in prototype/data/images.json (160 px), hires.json (440 px)
and, for Japanese printings, in cards_ja.json (360 px, with img_url and source).

Usage: python scripts/fetch_missing_images.py [--tcgcharts]   (then rebuild prototype/data/real.json as usual)
"""
import base64
import io
import json
import os
import re
import sys
import urllib.request

from PIL import Image

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data")
EN = {"svp-085": "https://images.pokemontcg.io/svp/85_hires.png"}
JA = {"ja:m2-110": "https://www.pokemon-card.com/assets/images/card_images/large/M2/048516_P_MRIZADONXEX.jpg",  # card 48516, 110/080
      "ja:m2a-232": "https://www.pokemon-card.com/assets/images/card_images/large/M2a/049992_P_MKAIRIXYUEX.jpg"}  # card 49992, 232/193
_OFF = os.path.join(HERE, "..", "..", "data", "ja_official_images.json")   # 13 Nov: found in the official database by name, set and number
if os.path.exists(_OFF):
    JA.update({k: v["url"] for k, v in json.load(open(_OFF, encoding="utf-8")).items() if v and not k.startswith("_")})


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "slabwise/0.1 (prototype)"})
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")


def uri(im, w, q=82):
    im = im.copy()
    im.thumbnail((w, w * 2), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=q)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def en_url(cid):
    """Pokémon TCG API image of a TCGdex card id: same set id without the dot ("sm3.5" -> "sm35"), same number."""
    sid, no = cid.rsplit("-", 1)
    sid = sid.replace(".5", "pt5").replace(".", "")                    # "swsh12.5gg" -> "swsh12pt5gg", "sm3.5" -> "sm35"
    no = no.lstrip("0") if no.isdigit() else re.sub(r"^([A-Z]+)0+(?=\d)", r"\1", no)   # "H09" -> "H9"
    return f"https://images.pokemontcg.io/{sid}/{no}_hires.png"


JA_SERIES = (("sv", "SV"), ("sm", "SM"), ("s", "S"))


def ja_url(cid):
    """TCGdex (ja) image asset, also for cards whose API record has no image field (e.g. ja/SM/SM9/103)."""
    sid, no = cid[3:].rsplit("-", 1)
    serie = next((v for k, v in JA_SERIES if sid.lower().startswith(k)), None)
    return f"https://assets.tcgdex.net/ja/{serie}/{sid[:1].upper() + sid[1:2].upper() + sid[2:]}/{no}/high.webp" if serie else None


def main():
    """D151: every catalogue card gets an image; the cards without one are filled from the registered sources."""
    thumbs = json.load(open(os.path.join(HERE, "images.json")))
    hires = json.load(open(os.path.join(HERE, "hires.json")))
    cards = json.load(open(os.path.join(HERE, "cards.json")))
    todo = dict(EN)
    todo.update({c["id"]: en_url(c["id"]) for c in cards if not thumbs.get(c["id"]) and not hires.get(c["id"]) and c["id"] not in todo})   # a None entry is retried
    for cid, url in todo.items():
        try:
            im = get(url)
        except Exception as e:
            print("en", cid, "manca ancora:", str(e)[:60])
            continue
        thumbs[cid], hires[cid] = uri(im, 160), uri(im, 440)
        print("en", cid, im.size)
    json.dump(thumbs, open(os.path.join(HERE, "images.json"), "w"))
    json.dump(hires, open(os.path.join(HERE, "hires.json"), "w"))
    ja = json.load(open(os.path.join(HERE, "cards_ja.json"), encoding="utf-8"))
    for c in ja:
        url = JA.get(c["id"]) or (None if c.get("img") else ja_url(c["id"]))
        if not url or (c.get("img") and (c["id"] not in JA or c.get("img_url") == url)):
            continue
        try:
            im = get(url)
        except Exception as e:
            print("ja", c["id"], "manca ancora:", str(e)[:60])
            continue
        c["img"], c["img_url"] = uri(im, 360), url
        c["source"] = "TCGdex ja (dati); immagine " + ("dal database ufficiale pokemon-card.com" if "pokemon-card.com" in url else "TCGdex ja")
        print("ja", c["id"], im.size)
    json.dump(ja, open(os.path.join(HERE, "cards_ja.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if "--tcgcharts" in sys.argv:
        from_tcgcharts(thumbs, hires, cards, ja)


def from_tcgcharts(thumbs, hires, cards, ja):
    """D298: the cards still without an image, from tcgcharts (permission from Marek, 14 Nov 2026)."""
    import time
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tcgcharts as tc
    mp = os.path.join(HERE, "..", "..", "data", "raw", "tcgcharts", "cards.json")
    if not os.path.exists(mp):
        print("tcgcharts: mappa assente (dati privati)")
        return
    mapping = json.load(open(mp))
    t0, budget = time.time(), float(os.environ.get("TC_BUDGET_MIN", "80")) * 60
    want = [c["id"] for c in cards if not thumbs.get(c["id"]) and not hires.get(c["id"])] + [c["id"] for c in ja if not c.get("img")]
    got = 0
    for cid in want:
        m = mapping.get(cid)
        if not m or time.time() - t0 > budget:
            continue
        try:
            cd = tc.get(m["url"].replace("/pokemon/", "/api/pokemon/card-detail/", 1)).get("card", {})
            url = cd.get("imageUrlHires") or cd.get("imageLarge") or cd.get("imageUrl")
            if not url:
                print("tcgcharts", cid, "senza immagine")
                continue
            im = get(url)
            time.sleep(tc.PAUSE_S)                       # the image is a request too: same pace
        except Exception as e:
            print("tcgcharts", cid, "manca ancora:", str(e)[:60])
            continue
        if cid.startswith("ja:"):
            c = next(x for x in ja if x["id"] == cid)
            c["img"], c["img_url"], c["source"] = uri(im, 360), url, "immagine da tcgcharts (permesso, D298)"
        else:
            thumbs[cid], hires[cid] = uri(im, 160), uri(im, 440)
        got += 1
        print("tcgcharts", cid, im.size, flush=True)
    json.dump(thumbs, open(os.path.join(HERE, "images.json"), "w"))
    json.dump(hires, open(os.path.join(HERE, "hires.json"), "w"))
    json.dump(ja, open(os.path.join(HERE, "cards_ja.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"tcgcharts: {got} immagini su {len(want)} carte senza immagine ({sum(1 for c in want if c in mapping)} nella mappa)")


if __name__ == "__main__":
    main()
