"""Pages "gemella individuata, prezzo in arrivo" (22 Nov 2026, Oscar: "fai pure tutto quanto"): every Japanese twin
found for an English card of the catalogue that has no priced twin yet gets a pending page (D158) now, linked to the
English card, instead of waiting until its sales pass the entry threshold. The price comes by itself when the printing
enters through the queue (scripts/add_batch.py replaces the pending page). Prices: unchanged.

Usage: PYTHONPATH=. python scripts/twin_pending.py
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from add_cards import webp  # noqa: E402

DATA = os.path.join(ROOT, "prototype", "data")
cj_p = os.path.join(DATA, "cards_ja.json")
cj = json.load(open(cj_p))
q = json.load(open(os.path.join(DATA, "candidates_queue.json")))
en = {c["id"] for c in json.load(open(os.path.join(DATA, "cards.json")))}
have = {c["id"]: c for c in cj}
priced_twin = {c.get("en") for c in cj if c.get("en") and not c.get("pending")}
pend_twin = {c.get("en") for c in cj if c.get("en") and c.get("pending")}
n = 0
for k, r in q.items():
    if not (isinstance(r, dict) and r.get("lang") == "ja" and r.get("en") in en) or k in have:
        continue
    if r["en"] in priced_twin or r["en"] in pend_twin or r.get("status") not in ("in_valutazione", "attesa_vendite", "attesa_coerenza", "pronta", "attesa_motore"):
        continue
    if r.get("en_same") in (False, "False"):
        continue
    url = r.get("img_url")
    if not url and r.get("tc_url") and r.get("no"):
        p = r["tc_url"].strip("/").split("/")
        url = f"https://images.tcgcharts.com/pokemon/{p[1]}/{str(r['no']).split('/')[0]}-large.webp"
    e = dict(id=k, en=r["en"], en_same=True, en_check=r.get("en_check"), lang="ja", n=r.get("ja_name") or r.get("name"),
             no=str(r.get("no") or ""), set=r.get("set"), set_en=r.get("set_en") or r.get("set"), source="coda giapponese (D134)",
             added="D158", pending=True)
    if url:
        try:
            e.update(img=webp(url, 360), img_url=url)
        except Exception:
            pass
    cj.append(e)
    pend_twin.add(r["en"])
    n += 1
json.dump(cj, open(cj_p, "w"), ensure_ascii=False, indent=1)
print(f"pagine 'gemella individuata, prezzo in arrivo' nuove: {n}; inglesi con gemella (con prezzo o in arrivo): {len((priced_twin | pend_twin) & en)}")
