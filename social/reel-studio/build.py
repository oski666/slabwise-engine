"""Build social/reel-studio/studio.html (Slabwise Reels) with the high-res TCGdex card images."""
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
data = os.path.join(here, "..", "..", "prototype", "data")
src = open(os.path.join(here, "src", "reel3.html")).read()
img = json.load(open(os.path.join(data, "hires.json")))
cards = {c["id"]: c for c in json.load(open(os.path.join(data, "cards.json")))}
meta = {k: {"n": cards[k]["n"], "set": cards[k]["set"],
            "no": f'{cards[k]["no"]}/{cards[k]["tot"]}' if cards[k].get("tot") else cards[k]["no"]} for k in img}
# real values of the site (P14: the reels say they are real only when they come from here), in euros
real = {}
try:
    r = json.load(open(os.path.join(data, "real.json")))
    eur = r["eur_rate"]
    for c in r["cards"]:
        if c["id"] not in img:
            continue
        gs = {}
        for g in c["grades"]:
            if not g.get("value") or not g.get("sales_all") or g.get("off"):      # D66, D98
                continue
            hist = []                       # D104: the weekly history comes from /api/card when the studio loads a card
            gs[str(g["grade"])] = dict(v=round(g["value"] * eur, 2), ch90=g.get("ch90"), s90=g.get("sales90"), pop=g.get("pop"), hist=hist, tier=g.get("tier"))
        if gs:
            real[c["id"]] = dict(asof=r.get("asof") or r.get("date"), grades=gs, eur=eur)
except (OSError, KeyError, ValueError):
    pass
out = (src.replace("__IMG__", json.dumps(img)).replace("__META__", json.dumps(meta, ensure_ascii=False))
       .replace("__REAL__", json.dumps(real, ensure_ascii=False)))
open(os.path.join(here, "studio.html"), "w").write(out)
print("studio.html", len(out))
