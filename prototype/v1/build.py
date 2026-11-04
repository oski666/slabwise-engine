"""Build prototype/v1/slabwise.html (the published Slabwise prototype v1) from its template."""
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
data = os.path.join(here, "..", "data")
src = open(os.path.join(here, "src", "v3.html")).read()
cards = json.dumps(json.load(open(os.path.join(data, "cards.json"))), ensure_ascii=False, separators=(",", ":"))
imgs = json.dumps(json.load(open(os.path.join(data, "images.json"))), separators=(",", ":"))
out = src.replace("__CARDS__", cards).replace("__IMGS__", imgs)
open(os.path.join(here, "slabwise.html"), "w").write(out)
print("slabwise.html", len(out))
