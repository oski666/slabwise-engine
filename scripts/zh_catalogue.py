"""Chinese (simplified) catalogue, D336: the ZH-CN cards among the first 2,000 positions of the tcgcharts ranking.

Usage: PYTHONPATH=. python scripts/zh_catalogue.py <ranking.json> [<work dir>]
<ranking.json>: positions of the ranking (as written by scripts/candidates.py to prototype/data/zh_rank.json).
Writes prototype/data/cards_zh.json, one entry per Chinese card, like the Japanese catalogue:
id "zh:<set slug>-<number>", English name and set as tcgcharts gives them, number, illustrator, tcgcharts id and
page (for the sales, as for the Japanese printings), image, position and market cap at the last reading; and the
English twin when an English card with the same name has the same illustration (§67 M1, as scripts/ja_reverse_twins.py):
en (our catalogue) or en_ext (outside it). Entries already present keep their fields; prices are not built yet.
"""
import json
import os
import sys
import urllib.parse

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from slabwise.print_match import ART_MAX, load  # noqa: E402

DATA = os.path.join(ROOT, "prototype", "data")
rank = json.load(open(sys.argv[1]))
work = sys.argv[2] if len(sys.argv) > 2 else "/tmp/zh"
os.makedirs(work, exist_ok=True)
EN = {c["id"]: c for c in json.load(open(os.path.join(DATA, "cards.json")))}
out_p = os.path.join(DATA, "cards_zh.json")
cur = {c["id"]: c for c in (json.load(open(out_p)) if os.path.exists(out_p) else [])}


def twin(name, img):
    """Best English twin on TCGdex: (id, distance) within ART_MAX, our catalogue's card first; None if none."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("rt", os.path.join(ROOT, "scripts", "_m1.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    zi = load(img)
    if zi is None:
        return None
    import urllib.request
    r = json.load(urllib.request.urlopen(f"https://api.tcgdex.net/v2/en/cards?name=eq:{urllib.parse.quote(name)}", timeout=30))
    hits = []
    for x in r:
        if not x.get("image"):
            continue
        ei = load(x["image"] + "/high.webp")
        if ei is None:
            continue
        d = m.m1(ei, zi)
        if d <= ART_MAX:
            hits.append((x["id"] not in EN, d, x["id"]))
    return min(hits)[1:] [::-1] if hits else None


for x in rank:
    if (x.get("languageCode") or "").upper() != "ZH-CN" or x.get("variantType"):
        continue
    slug = x["set"]["slug"].removesuffix("-chinese")
    no = str(x.get("cardNumber") or "").split("/")[0].strip() or str(x["id"])
    cid = f"zh:{slug}-{no}"
    e = cur.get(cid, {})
    e.update(id=cid, lang="zh", n=x["name"], set=x["set"]["name"], no=no, ill=x.get("artist"), tc_id=int(x["id"]),
             url=f"/pokemon/{x['set']['slug']}/{x.get('slug')}", img_url=x.get("imageUrlHires") or x.get("imageUrl"),
             rank=x.get("pos") or x.get("marketCapRank"), cap=x.get("marketCap"))
    if "en" not in e and "en_ext" not in e:
        t = twin(x["name"], e["img_url"])
        if t:
            (e.__setitem__("en", t[0]) if t[0] in EN else e.__setitem__("en_ext", dict(id=t[0], name=x["name"])))
            e["en_check"] = f"illustrazione uguale (distanza {t[1]}/256, §67 M1)"
    cur[cid] = e
    print(cid, x["name"], "|", x["set"]["name"], "->", e.get("en") or (e.get("en_ext") or {}).get("id") or "-", flush=True)
json.dump(sorted(cur.values(), key=lambda c: c.get("rank") or 9e9), open(out_p, "w"), ensure_ascii=False, indent=1)
print(f"catalogo cinese: {len(cur)} carte, con gemella nel catalogo {sum(1 for c in cur.values() if c.get('en'))}, fuori {sum(1 for c in cur.values() if c.get('en_ext'))}")
