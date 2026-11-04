"""History of each graded copy by PSA cert number (D63), from the Fanatics Collect public sales archive.

Usage: PYTHONPATH=. python scripts/cert_history.py data/raw/fanatics_history prototype/data/certs.json
Every PSA Pokémon record of the archive that matches a catalogue card (any edition) is kept, auctions and
fixed-price sales alike; unpaid or pending lots keep their status. Fixed-price sales are shown on the site
as information only: the model does not use them (D54).
Output: {"asof": date, "names": {card: [name, set, no, tot, image]}, "certs": {cert: [[date, card, grade, price, kind, status], ...]}}, sales oldest first;
kind is "a" (auction) or "f" (fixed price), status "" (paid / counts) or the removal reason.
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

from slabwise.sources.auction_titles import match_title
from slabwise.sources.fanatics_history import is_auction, is_pokemon, payment_reason, sold_utc

src, out = sys.argv[1], sys.argv[2]
now = datetime.now(timezone.utc)
seen, certs, last = set(), {}, None
for f in sorted(glob.glob(os.path.join(src, "*.json"))):
    if f.endswith("coverage.json"):
        continue
    for h in json.load(open(f)):
        uid = h.get("listingUuid") or h.get("id")
        if uid in seen or not is_pokemon(h) or (h.get("gradingService") or "").upper() != "PSA":
            continue
        seen.add(uid)
        serial, g = str(h.get("serial") or "").strip(), h.get("grade")
        if not serial.isdigit() or g is None or float(g) != int(g):
            continue
        card, _ = match_title(h.get("title") or "")
        if not card:
            continue
        when = sold_utc(h)
        last = max(last or when, when)
        certs.setdefault(serial, []).append([when.strftime("%Y-%m-%d"), card, int(g), round(float(h["purchasePrice"]), 2),
                                             "a" if is_auction(h) else "f", payment_reason(h, now) or ""])
for v in certs.values():
    v.sort()
# names and images of the cards that appear, so the page can show copies of cards it does not price
data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "data")
cat = {c["id"]: c for f in ("cards.json", "cards_ja.json") for c in json.load(open(os.path.join(data, f)))}
thumbs = json.load(open(os.path.join(data, "images.json")))
used = {s[1].split("/")[0] for v in certs.values() for s in v}
real = json.load(open(os.path.join(data, "real.json")))           # cards already on the site bring their own image
shown = {c["id"] for c in real["cards"]} | {c["id"] for c in real.get("ja_pending", [])}
names = {i: [cat[i]["n"], cat[i]["set"], cat[i]["no"], cat[i].get("tot"), None if i in shown else thumbs.get(i) or cat[i].get("img")]
         for i in sorted(used) if i in cat}
json.dump({"asof": last.strftime("%Y-%m-%d") if last else None, "names": names, "certs": certs}, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
rep = sum(1 for v in certs.values() if len(v) > 1)
print(f"{len(certs)} cert, {sum(len(v) for v in certs.values())} vendite, {rep} copie vendute più di una volta -> {out}")
