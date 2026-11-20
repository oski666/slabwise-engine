"""Twins searched the other way round (20 Nov 2026, Oscar: "le carte esistono ma in set diversi, quindi sicuramente la
gemella la hanno"): for each Japanese printing of the catalogue with no English twin, look for an English card with the
same name and the same illustration in ANY set (TCGdex), with the §67 matcher (M1: dHash of the illustration window,
best of the small shifts, <= ART_MAX bits out of 256, the variant adopted in D307).

Usage: PYTHONPATH=. python scripts/ja_reverse_twins.py <work dir> [--apply] [--limit N]
Without --apply: writes <work dir>/reverse.json (one entry per Japanese printing: twin, best distance, candidates seen).
With --apply, in prototype/data/cards_ja.json:
  - twin in our catalogue: en, en_same, en_check (as §67);
  - twin outside the catalogue: en_ext = {id, name, set} and the English card goes in the candidates queue
    (status "in_valutazione", detail "gemella inglese di una stampa giapponese");
  - every candidate with the same name compared, images on both sides, none within ART_MAX: en_none = True
    ("Solo in Giappone" on the site). Missing images leave the printing undecided.
"""
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from slabwise.print_match import ART_BOX, ART_MAX, load  # noqa: E402
from slabwise.ja_names import english  # noqa: E402

DATA = os.path.join(ROOT, "prototype", "data")
TCGDEX = "https://api.tcgdex.net/v2"
work = sys.argv[1]
APPLY = "--apply" in sys.argv
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
os.makedirs(os.path.join(work, "img"), exist_ok=True)

cat = json.load(open(os.path.join(DATA, "cards.json")))
cj = json.load(open(os.path.join(DATA, "cards_ja.json")))
EN = {c["id"]: c["n"] for c in cat}
EXTRA_IMG = json.load(open(os.path.join(work, "ja_images.json"))) if os.path.exists(os.path.join(work, "ja_images.json")) else {}   # {ja id: image url}, e.g. from the ranking export


def get_json(url):
    for k in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "slabwise/0.1"}), timeout=30))
        except Exception:
            time.sleep(2 * (k + 1))
    return None


def cached_image(key, url):
    from PIL import Image
    f = os.path.join(work, "img", hashlib.md5(key.encode()).hexdigest() + ".png")
    if os.path.exists(f):
        if not os.path.getsize(f):
            return None
        try:
            im = Image.open(f)
            im.load()
            return im
        except Exception:
            pass                                          # a damaged cache file: fetch again
    im = load(url) if url else None
    tmp = f"{f}.{os.getpid()}.{id(im)}.tmp"
    if im is None:
        open(tmp, "wb").close()
    else:
        im.thumbnail((600, 840))
        im.save(tmp, format="PNG")
    os.replace(tmp, f)                                    # threads share the cache: write whole files only
    return im


def _hash(im, box, n=16):
    w, h = im.size
    x0, y0, x1, y1 = box
    a = np.asarray(im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).resize((n + 1, n)), dtype=float)
    return (a[:, 1:] > a[:, :-1]).flatten()


def _boxes():
    x0, y0, x1, y1 = ART_BOX
    cx, cy, bw, bh = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    for s in (0.9, 1.0, 1.1):
        for dx in (-0.04, -0.02, 0, 0.02, 0.04):
            for dy in (-0.04, -0.02, 0, 0.02, 0.04):
                w2, h2 = bw * s / 2, bh * s / 2
                b = (cx + dx - w2, cy + dy - h2, cx + dx + w2, cy + dy + h2)
                if b[0] >= 0 and b[1] >= 0 and b[2] <= 1 and b[3] <= 1:
                    yield b


BOXES = list(_boxes())
NONE_MIN = 110        # "no twin" only when every English card of that name is clearly different (different art: 115-133)


def m1(en_im, ja_im):
    e = _hash(en_im, ART_BOX)
    return min(int((e != _hash(ja_im, b)).sum()) for b in BOXES)


_search = {}


def candidates(name):
    """English cards on TCGdex whose name is exactly `name` (with an image)."""
    if name not in _search:
        r = get_json(f"{TCGDEX}/en/cards?name=eq:{urllib.parse.quote(name)}")
        _search[name] = None if r is None else [x for x in r if x.get("image")]
    return _search[name]


todo = [c for c in cj if not c.get("en") and c.get("en_none") is None]
if LIMIT:
    todo = todo[:LIMIT]
out_p = os.path.join(work, "reverse.json")
done = json.load(open(out_p)) if os.path.exists(out_p) else {}


def one(c):
    name = english(c, EN)[0]
    cands = candidates(name)
    if cands is None:
        return c["id"], dict(name=name, state="errore_ricerca")
    ji = cached_image("ja:" + c["id"], c.get("img") or c.get("img_url") or EXTRA_IMG.get(c["id"]))
    if ji is None:
        return c["id"], dict(name=name, state="senza_immagine", n=len(cands))
    best, seen, hits = None, 0, []
    for x in cands:
        ei = cached_image("en:" + x["id"], x["image"] + "/high.webp")
        if ei is None:
            continue
        seen += 1
        d = m1(ei, ji)
        if best is None or d < best:
            best = d
        if d <= ART_MAX:
            hits.append((d, x["id"]))
    if hits:                                              # a reprint shares the art: our catalogue's card first, then the closest
        hits.sort(key=lambda h: (h[1] not in EN, h[0]))
        return c["id"], dict(name=name, state="gemella", en=hits[0][1], d=hits[0][0], all=hits, n=len(cands), seen=seen)
    if cands and seen < len(cands):
        return c["id"], dict(name=name, state="immagini_inglesi_mancanti", n=len(cands), seen=seen, best=best)
    if not cands or best is None or best < NONE_MIN:      # no English card of that name, or a grey zone: undecided
        return c["id"], dict(name=name, state="incerta", n=len(cands), seen=seen, best=best)
    return c["id"], dict(name=name, state="nessuna", n=len(cands), seen=seen, best=best)


t0 = time.time()
rest = [c for c in todo if c["id"] not in done]
with ThreadPoolExecutor(6) as ex:
    for k, (cid, r) in enumerate(ex.map(one, rest)):
        done[cid] = r
        if k % 50 == 0:
            json.dump(done, open(out_p, "w"), ensure_ascii=False)
            print(f"  {k}/{len(rest)} ({int(time.time() - t0)} s)", flush=True)
json.dump(done, open(out_p, "w"), ensure_ascii=False, indent=1)
from collections import Counter  # noqa: E402
st = Counter(r["state"] for r in done.values())
in_cat = sum(1 for r in done.values() if r["state"] == "gemella" and r["en"] in EN)
print(dict(st), "| gemelle nel catalogo:", in_cat, "| fuori:", st["gemella"] - in_cat)

if APPLY:
    queue = json.load(open(os.path.join(DATA, "candidates_queue.json")))
    today = time.strftime("%Y-%m-%d")
    by = {c["id"]: c for c in cj}
    n_link = n_ext = n_q = n_none = 0
    for cid, r in done.items():
        c = by.get(cid)
        if c is None or c.get("en"):
            continue
        if r["state"] == "gemella":
            why = f"illustrazione uguale (distanza {r['d']}/256, §67 M1, ricerca dalla giapponese)"
            if r["en"] in EN:
                c.update(en=r["en"], en_same="True", en_check=why)
                n_link += 1
            else:
                c["en_ext"] = dict(id=r["en"], name=r["name"])
                n_ext += 1
                if r["en"] not in queue:
                    queue[r["en"]] = dict(id=r["en"], name=r["name"], set=None, no=r["en"].rsplit("-", 1)[-1], rank=None,
                                          status="in_valutazione", checked=today, twin_of=cid,
                                          detail="gemella inglese di una stampa giapponese del catalogo (ricerca dalla giapponese)")
                    n_q += 1
        elif r["state"] == "nessuna" and r.get("n"):
            c["en_none"] = True
            n_none += 1
    json.dump(cj, open(os.path.join(DATA, "cards_ja.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(queue, open(os.path.join(DATA, "candidates_queue.json"), "w"), ensure_ascii=False, indent=1)
    print(f"collegate nel catalogo: {n_link}; gemelle fuori dal catalogo: {n_ext} ({n_q} nuove in coda); solo in Giappone: {n_none}")
