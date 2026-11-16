"""Protocol §67 (D307): Japanese twins from the Japanese printings we already know (catalogue and queue).

Usage: PYTHONPATH=. python scripts/ja_twin_match.py <work dir> [--apply M0|M1]
Without --apply: fetches the images it needs (cached in <work dir>/img), computes M0 and M1 for the known twins (G1),
the same-name non-twins (G2) and the new pairs, and writes <work dir>/pairs.json and results/ja_twins/summary.json.
G3 is read by eye on <work dir>/sheet_*.png. With --apply: writes the new links of the adopted variant into
prototype/data/cards_ja.json and prototype/data/candidates_queue.json (en, en_same, en_check; ja_only off).
"""
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.parse
from collections import defaultdict

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from slabwise.print_match import ART_BOX, ART_MAX, load  # noqa: E402
import card_requests as cr  # noqa: E402

DATA = os.path.join(ROOT, "prototype", "data")
work = sys.argv[1]
APPLY = sys.argv[sys.argv.index("--apply") + 1] if "--apply" in sys.argv else None
os.makedirs(os.path.join(work, "img"), exist_ok=True)


def key(s):
    """§67 name normalisation."""
    s = (s or "").lower()
    s = re.sub(r"\((?:giapponese|unlimited|1st edition|shadowless|holo)\)", "", s)
    s = s.replace("☆", " star ").replace("gold star", " star ").replace("δ", " delta ").replace("delta species", " delta ")
    s = s.replace("&", " and ").replace("é", "e").replace("’", "'")
    s = re.sub(r"\bpokemon\b", "", s)
    s = re.sub(r"[-\s]+(gx|ex|v|vmax|vstar|lv\.?x|prime|legend|break)\b", r" \1", s)
    return re.sub(r"[^a-z0-9]", "", s)


cat = json.load(open(os.path.join(DATA, "cards.json")))
cj = json.load(open(os.path.join(DATA, "cards_ja.json")))
queue = json.load(open(os.path.join(DATA, "candidates_queue.json")))
hires = json.load(open(os.path.join(DATA, "hires.json")))
images = json.load(open(os.path.join(DATA, "images.json")))

pool = {}
for v in queue.values():
    if v.get("lang") == "ja":
        pool[v["id"]] = dict(id=v["id"], name=v.get("name"), en=v.get("en"), tc_url=v.get("tc_url"), tcgdex=v.get("tcgdex"),
                             img=v.get("img_url"), set=v.get("set_en") or v.get("set"), no=v.get("no"))
for c in cj:
    p = pool.setdefault(c["id"], dict(id=c["id"], name=None, tc_url=None, tcgdex=None, img=None, set=c.get("set"), no=c.get("no")))
    p.update(en=c.get("en"), cat_img=c.get("img"), img=c.get("img_url") or p.get("img"))
    if not p["name"]:
        p["name"] = c.get("n_en") or c.get("name_en") or c.get("n")
by_key = defaultdict(list)
for p in pool.values():
    by_key[key(p["name"])].append(p)
en_by = {c["id"]: c for c in cat}
twins = defaultdict(set)
for p in pool.values():
    if p.get("en"):
        twins[p["en"]].add(p["id"])

pos = [(en, j) for en, js in twins.items() if en in en_by for j in js if j in {c["id"] for c in cj}]
neg, new = [], []
for c in cat:
    for p in by_key.get(key(c["n"]), []):
        if c["id"] in twins:
            if p["id"] not in twins[c["id"]] and not p.get("en"):
                neg.append((c["id"], p["id"]))
        elif not p.get("en"):
            new.append((c["id"], p["id"]))
print(f"G1 coppie note {len(pos)}, G2 stesso nome non gemelle {len(neg)}, coppie nuove {len(new)}", flush=True)


def cache_path(i):
    return os.path.join(work, "img", hashlib.md5(i.encode()).hexdigest() + ".png")


last_tc = [0.0]


def ja_image(p, fetch=True):
    """Grey image of a Japanese printing, cached; None when none can be found. fetch=False: cache and catalogue only."""
    f = cache_path(p["id"])
    if os.path.exists(f):
        return Image.open(f) if os.path.getsize(f) else None
    if not fetch and not p.get("cat_img"):
        return None
    im = None
    for src in (p.get("cat_img"), p.get("img")):
        if src and im is None:
            im = load(src)
    if im is None and p.get("tcgdex"):
        try:
            jc = cr.get(f"{cr.TCGDEX}/ja/cards/{urllib.parse.quote(p['tcgdex'])}")
            im = jc.get("image") and load(jc["image"] + "/high.webp")
        except Exception:
            im = None
    if im is None and p.get("tc_url"):
        wait = cr.PAUSE_S - (time.time() - last_tc[0])
        if wait > 0:
            time.sleep(wait)
        try:
            cd = cr.get(cr.TCG + p["tc_url"].replace("/pokemon/", "/api/pokemon/card-detail/", 1)).get("card", {})
            u = cd.get("imageUrlHires") or cd.get("imageLarge")
            im = load(u) if u else None
        except Exception:
            im = None
        last_tc[0] = time.time()
    if im is None:
        open(f, "wb").close()
        return None
    im = im.convert("L")
    im.thumbnail((600, 840))
    im.save(f)
    return im


def en_image(cid):
    f = cache_path("en:" + cid)
    if os.path.exists(f):
        return Image.open(f) if os.path.getsize(f) else None
    im = load(hires.get(cid) or images.get(cid) or "")
    if im is None:
        open(f, "wb").close()
        return None
    im = im.convert("L")
    im.thumbnail((600, 840))
    im.save(f)
    return im


def _hash(im, box, n=16):
    w, h = im.size
    x0, y0, x1, y1 = box
    a = np.asarray(im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).resize((n + 1, n)), dtype=float)
    return (a[:, 1:] > a[:, :-1]).flatten()


def boxes():
    x0, y0, x1, y1 = ART_BOX
    cx, cy, bw, bh = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    for s in (0.9, 1.0, 1.1):
        for dx in (-0.04, -0.02, 0, 0.02, 0.04):
            for dy in (-0.04, -0.02, 0, 0.02, 0.04):
                w2, h2 = bw * s / 2, bh * s / 2
                b = (cx + dx - w2, cy + dy - h2, cx + dx + w2, cy + dy + h2)
                if b[0] >= 0 and b[1] >= 0 and b[2] <= 1 and b[3] <= 1:
                    yield b


BOXES = list(boxes())


def dist(en_im, ja_im):
    e = _hash(en_im, ART_BOX)
    m0 = int((e != _hash(ja_im, ART_BOX)).sum())
    m1 = min(int((e != _hash(ja_im, b)).sum()) for b in BOXES)
    return m0, m1


out_p = os.path.join(work, "pairs.json")
done = json.load(open(out_p)) if os.path.exists(out_p) else {}
t0 = time.time()
for kind, pairs in (("G1", pos), ("new", new), ("G2", neg)):     # G2 last, on the images already at hand
    for k, (en, j) in enumerate(pairs):
        kk = f"{en}|{j}"
        if kk in done:
            continue
        ei, ji = en_image(en), ja_image(pool[j], fetch=kind != "G2")
        done[kk] = dict(kind=kind, en=en, ja=j, d=None if ei is None or ji is None else dist(ei, ji))
        if k % 50 == 0:
            json.dump(done, open(out_p, "w"))
            print(f"  {kind} {k}/{len(pairs)} ({int(time.time() - t0)} s)", flush=True)
json.dump(done, open(out_p, "w"))

res = {}
for v, ix in (("M0", 0), ("M1", 1)):
    g1 = [r["d"][ix] <= ART_MAX for r in done.values() if r["kind"] == "G1" and r["d"]]
    g2 = [r["d"][ix] <= ART_MAX for r in done.values() if r["kind"] == "G2" and r["d"]]
    best = {}                                         # one Japanese printing -> the English card with the smallest distance
    for r in done.values():
        if r["kind"] == "new" and r["d"] and r["d"][ix] <= ART_MAX:
            if r["ja"] not in best or r["d"][ix] < best[r["ja"]]["d"][ix]:
                best[r["ja"]] = r
    links = sorted(best.values(), key=lambda r: (r["en"], r["ja"]))
    res[v] = dict(G1=round(float(np.mean(g1)), 4) if g1 else None, G1_n=len(g1), G2=round(float(np.mean(g2)), 4) if g2 else None,
                  G2_n=len(g2), new_links=len(links), new_en=len({r["en"] for r in links}),
                  no_image=sum(1 for r in done.values() if r["kind"] == "new" and not r["d"]))
    json.dump(links, open(os.path.join(work, f"links_{v}.json"), "w"), indent=1)
os.makedirs(os.path.join(ROOT, "results", "ja_twins"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "results", "ja_twins", "summary.json"), "w"), indent=1)
print(json.dumps(res, indent=1))


def sheet(v, n=40):
    """Contact sheets of 40 random new links (English left, Japanese right), 10 per image, for G3."""
    links = json.load(open(os.path.join(work, f"links_{v}.json")))
    random.seed(67)
    pick = random.sample(links, min(n, len(links)))
    json.dump(pick, open(os.path.join(work, f"g3_{v}.json"), "w"), indent=1)
    for s in range(0, len(pick), 10):
        canvas = Image.new("L", (2 * 200 + 20, 10 * 280), 255)
        for k, r in enumerate(pick[s:s + 10]):
            for col, im in enumerate((en_image(r["en"]), ja_image(pool[r["ja"]]))):
                if im is not None:
                    canvas.paste(im.resize((200, 280)), (col * 220, k * 280))
        canvas.save(os.path.join(work, f"sheet_{v}_{s // 10}.png"))


for v in ("M0", "M1"):
    sheet(v)

if APPLY:
    links = json.load(open(os.path.join(work, f"links_{APPLY}.json")))
    ix = 0 if APPLY == "M0" else 1
    cj_by = {c["id"]: c for c in cj}
    n_cat = n_q = 0
    for r in links:
        why = f"illustrazione uguale (distanza {r['d'][ix]}/256, §67 {APPLY})"
        if r["ja"] in cj_by and not cj_by[r["ja"]].get("en"):
            cj_by[r["ja"]].update(en=r["en"], en_same="True", en_check=why)
            n_cat += 1
        qv = queue.get(r["ja"])
        if qv is not None and not qv.get("en"):
            qv.update(en=r["en"], en_same=True, en_check=why)
            qv.pop("ja_only", None)
            n_q += 1
    json.dump(cj, open(os.path.join(DATA, "cards_ja.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(queue, open(os.path.join(DATA, "candidates_queue.json"), "w"), ensure_ascii=False, indent=1)
    print(f"collegate: {n_cat} stampe del catalogo, {n_q} della coda")
