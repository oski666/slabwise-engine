"""Fill in card images that TCGdex does not have (D45), from sources registered in docs/DATA_SOURCES.md:
- English cards: Pokémon TCG API image CDN (images.pokemontcg.io)
- Japanese printings: the official Japanese card database (www.pokemon-card.com)
Images are stored like the others: webp data URIs in prototype/data/images.json (160 px), hires.json (440 px)
and, for Japanese printings, in cards_ja.json (360 px, with img_url and source).

Usage: python scripts/fetch_missing_images.py   (then rebuild prototype/data/real.json as usual)
"""
import base64
import io
import json
import os
import urllib.request

from PIL import Image

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data")
EN = {"svp-085": "https://images.pokemontcg.io/svp/85_hires.png"}
JA = {"ja:m2-110": "https://www.pokemon-card.com/assets/images/card_images/large/M2/048516_P_MRIZADONXEX.jpg",  # card 48516, 110/080
      "ja:m2a-232": "https://www.pokemon-card.com/assets/images/card_images/large/M2a/049992_P_MKAIRIXYUEX.jpg"}  # card 49992, 232/193


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
    return f"https://images.pokemontcg.io/{sid.replace('.', '')}/{no.lstrip('0') if no.isdigit() else no}_hires.png"


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
    todo.update({c["id"]: en_url(c["id"]) for c in cards if c["id"] not in thumbs and c["id"] not in hires and c["id"] not in todo})
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
        if not url or (c.get("img") and c["id"] not in JA):
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


if __name__ == "__main__":
    main()
