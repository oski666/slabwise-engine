"""D152: is a Japanese printing the same card as an English one? Same Pokémon (Pokédex number) and same illustration."""
import base64
import io
import urllib.request

import numpy as np
from PIL import Image

ART_MAX = 80                                # dHash bits out of 256 (same art: 18-50, different: 115-133 on the catalogue)
ART_BOX = (0.06, 0.09, 0.94, 0.56)          # the illustration window of a card, as fractions of width and height


def load(src):
    """A PIL image from a data URI, an http(s) URL or bytes; None when it cannot be read."""
    try:
        if isinstance(src, bytes):
            raw = src
        elif src.startswith("data:"):
            raw = base64.b64decode(src.split(",", 1)[1])
        else:
            raw = urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": "slabwise/0.1"}), timeout=30).read()
        return Image.open(io.BytesIO(raw)).convert("L")
    except Exception:
        return None


def dhash(im, n=16):
    w, h = im.size
    im = im.crop((int(ART_BOX[0] * w), int(ART_BOX[1] * h), int(ART_BOX[2] * w), int(ART_BOX[3] * h))).resize((n + 1, n))
    a = np.asarray(im, dtype=float)
    return (a[:, 1:] > a[:, :-1]).flatten()


def art_distance(a, b):
    a, b = (x if isinstance(x, Image.Image) or x is None else load(x) for x in (a, b))
    return None if a is None or b is None else int((dhash(a) != dhash(b)).sum())


def same_print(ja, en, ja_img, en_img):
    """ja, en: TCGdex card dicts (dexId, category). Returns (True/False/None, reason). None: cannot verify."""
    if ja.get("category") and en.get("category") and ja["category"] != en["category"]:
        return False, "tipo di carta diverso"
    if ja.get("dexId") and en.get("dexId"):                 # TCGdex does not always have it for Japanese cards
        if set(ja.get("dexId") or []) != set(en.get("dexId") or []):
            return False, "Pokémon diverso"
    d = art_distance(ja_img, en_img)
    if d is None:
        return None, "immagini mancanti"
    return (d <= ART_MAX), f"illustrazione {'uguale' if d <= ART_MAX else 'diversa'} (distanza {d}/256)"
