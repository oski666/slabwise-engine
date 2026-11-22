"""Twins of the English cards still without one, searched among the Japanese printings we already know (22 Nov 2026,
Oscar: "le gemelle non stanno aumentando… ci portiamo in pari con le gemelle?").

The search on tcgcharts (scripts/ja_twins.py, D299) needs the same name and the same illustrator, and tcgcharts often
has no illustrator for Japanese cards: 279 English cards were searched and found nothing. Here every English card of
the catalogue without a Japanese twin is compared with every Japanese printing of the catalogue and of the candidate
queue with the same Pokémon name, on the illustration (§67 M1, <= ART_MAX, as scripts/ja_reverse_twins.py).
A match in the catalogue gets the link (en, en_same, en_check); a match in the queue gets en and goes first in the
Japanese chain (scripts/ja_due.py).

Usage: PYTHONPATH=. python scripts/en_forward_twins.py <work dir> [--apply]
"""
import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from slabwise.print_match import ART_MAX, load  # noqa: E402
from slabwise.ja_names import english  # noqa: E402
import _m1  # noqa: E402

DATA = os.path.join(ROOT, "prototype", "data")
work = sys.argv[1]
os.makedirs(os.path.join(work, "img"), exist_ok=True)
cat = json.load(open(os.path.join(DATA, "cards.json")))
cj = json.load(open(os.path.join(DATA, "cards_ja.json")))
q = json.load(open(os.path.join(DATA, "candidates_queue.json")))
EN = {c["id"]: c for c in cat}
IMGS = json.load(open(os.path.join(DATA, "images.json")))   # English images (data URIs)
ENN = {c["id"]: c["n"] for c in cat}
linked = {c.get("en") for c in cj if c.get("en")}
key = lambda s: re.sub(r"[^a-z0-9]", "", re.sub(r"\s*\((?:giapponese|japanese)\)\s*$", "", (s or "").lower()))  # noqa: E731

pool = {}                                                  # name key -> [(ja id, image, where)]
for c in cj:
    if c["id"].startswith("ja:") and not c.get("en"):
        pool.setdefault(key(english(c, ENN)[0]), []).append((c["id"], c.get("img") or c.get("img_url"), "cat"))
for k, r in q.items():
    if isinstance(r, dict) and r.get("lang") == "ja" and not r.get("en") and r.get("tc_url"):
        p = r["tc_url"].strip("/").split("/")
        img = r.get("img_url") or (f"https://images.tcgcharts.com/pokemon/{p[1]}/{r.get('no')}-large.webp" if r.get("no") else None)
        pool.setdefault(key(r.get("name")), []).append((k, img, "coda"))


def img(k, url):
    f = os.path.join(work, "img", hashlib.md5(k.encode()).hexdigest() + ".png")
    from PIL import Image
    if os.path.exists(f):
        try:
            return Image.open(f) if os.path.getsize(f) else None
        except Exception:
            pass
    im = load(url) if url else None
    tmp = f + f".{os.getpid()}.{id(im)}.tmp"
    if im is None:
        open(tmp, "wb").close()
    else:
        im.thumbnail((600, 840))
        im.save(tmp, format="PNG")
    os.replace(tmp, f)
    return im


def one(c):
    cands = pool.get(key(c["n"]), [])
    if not cands:
        return c["id"], None, 0
    ei = img("en:" + c["id"], c.get("img") or IMGS.get(c["id"]))
    if ei is None:
        return c["id"], None, -1
    best = None
    for jid, url, where in cands:
        ji = img("ja:" + jid, url)
        if ji is None:
            continue
        d = _m1.m1(ei, ji)
        if d <= ART_MAX and (best is None or d < best[0]):
            best = (d, jid, where)
    return c["id"], best, len(cands)


todo = [c for c in cat if c["id"] not in linked and "/" not in c["id"]]
res = {}
with ThreadPoolExecutor(6) as ex:
    for cid, best, n in ex.map(one, todo):
        res[cid] = dict(best=best, n=n)
json.dump(res, open(os.path.join(work, "forward.json"), "w"), indent=1)
found = {k: v["best"] for k, v in res.items() if v["best"]}
taken = {}
for cid, (d, jid, where) in sorted(found.items(), key=lambda x: x[1][0]):   # one Japanese printing for one English card
    taken.setdefault(jid, (cid, d, where))
print(f"inglesi senza gemella: {len(todo)}; con candidati per nome: {sum(1 for v in res.values() if v['n'] > 0)}; "
      f"gemella trovata: {len(taken)} (nel catalogo {sum(1 for v in taken.values() if v[2] == 'cat')}, in coda {sum(1 for v in taken.values() if v[2] == 'coda')})")
if "--apply" in sys.argv:
    by = {c["id"]: c for c in cj}
    for jid, (cid, d, where) in taken.items():
        why = f"illustrazione uguale (distanza {d}/256, §67 M1, ricerca dalla inglese fra le giapponesi note)"
        if where == "cat":
            by[jid].update(en=cid, en_same="True", en_check=why)
        else:
            q[jid].update(en=cid, en_same=True, en_check=why)
            if q[jid].get("status") in ("attesa_vendite", "attesa_coerenza", "scartata"):
                pass                                    # its sales check stays as it is
    json.dump(cj, open(os.path.join(DATA, "cards_ja.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(q, open(os.path.join(DATA, "candidates_queue.json"), "w"), ensure_ascii=False, indent=1)
    print("applicato")
