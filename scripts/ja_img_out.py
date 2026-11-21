"""Keep card images out of the catalogue JSON (21 Nov 2026): cards_ja.json held every Japanese image as a data URI
and had reached 58 MB, on its way to GitHub's 100 MB limit. Each data URI in prototype/data/cards_ja.json (img,
thumb) is written to prototype/data/img/<id>[_t].<ext> and replaced by "file:img/<id>[_t].<ext>"; the site build
copies the file (prototype/v7/build.py), slabwise.print_match.load reads it.

Usage: python scripts/ja_img_out.py [--stage]   (--stage: git add the files written; the pre-commit hook uses it)
"""
import base64
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "prototype", "data")
p = os.path.join(DATA, "cards_ja.json")
cards = json.load(open(p))
os.makedirs(os.path.join(DATA, "img"), exist_ok=True)
written = []
for c in cards:
    fid = c["id"].replace(":", "_").replace("/", "_")
    for k, suf in (("img", ""), ("thumb", "_t")):
        v = c.get(k) or ""
        if v.startswith("data:image/"):
            ext = v[11:v.index(";")]
            rel = f"img/{fid}{suf}.{ext}"
            open(os.path.join(DATA, rel), "wb").write(base64.b64decode(v.split(",", 1)[1]))
            c[k] = "file:" + rel
            written.append(os.path.join("prototype", "data", rel))
if written:
    json.dump(cards, open(p, "w"), ensure_ascii=False, indent=1)
    if "--stage" in sys.argv:
        subprocess.run(["git", "add", p, *written], cwd=ROOT, check=True)
print(f"immagini spostate fuori da cards_ja.json: {len(written)}")
