"""D299: the Japanese twin of every English card of the catalogue, searched again with the wider rule.

Before (D134) a twin was kept only when TCGdex (ja) had exactly one card with that number and illustrator, so the
Japanese printings TCGdex does not cover (all the vintage, many promos and special sets) were never found. Now a twin
found on tcgcharts with the same name and the same illustrator is kept even without TCGdex: its id comes from its
tcgcharts set (as D158/D231), its era is the English card's when the set has none, and the illustration is compared on
the images (D152, en_same). A twin already in the catalogue without its English link gets the link; a new one goes
into the candidate queue with the usual admission check (sales, coherence), like every other card.

Runs in the tcgcharts queue (one request every 3 seconds), within TC_BUDGET_MIN minutes, the most valuable English
cards first; prototype/data/ja_scan2.json keeps which cards were searched with this rule.

Usage: PYTHONPATH=. python scripts/ja_twins.py
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import candidates as cd  # noqa: E402
import card_requests as cr  # noqa: E402

BUDGET = float(os.environ.get("TC_BUDGET_MIN", "75")) * 60


def main():
    t0 = time.time()
    D = cd.DATA
    cat = json.load(open(os.path.join(D, "cards.json")))
    ja_p = os.path.join(D, "cards_ja.json")
    ja = cd.cr_load(ja_p, [])
    ja_by = {c["id"]: c for c in ja}
    linked = {c.get("en") for c in ja if c.get("en")}
    q_p = os.path.join(D, "candidates_queue.json")
    queue = cd.cr_load(q_p, {})
    queued_en = {r.get("en") for r in queue.values() if r.get("lang") == "ja"}
    scan_p = os.path.join(D, "ja_scan2.json")
    scanned = cd.cr_load(scan_p, {})
    tc_map = cd.cr_load(os.path.join(cd.ROOT, "data", "raw", "tcgcharts", "cards.json"), {})
    era_map = cd.cr_load(os.path.join(cd.ROOT, "data", "raw", "era_map.json"), {})
    imgs = cd.cr_load(os.path.join(D, "images.json"), {})
    value = {c["id"]: float(c.get("value") or 0) for c in cat}           # most valuable first, when the file has it
    todo = [c for c in cat if c["id"] not in linked and c["id"] not in queued_en and c["id"] not in scanned]
    todo.sort(key=lambda c: (-value.get(c["id"], 0), -int((tc_map.get(c["id"]) or {}).get("psa_population") or 0)))
    n_link = n_new = n_none = 0
    for c in todo:
        if time.time() - t0 > BUDGET:
            print("tempo finito (D299)", flush=True)
            break
        try:
            rows, nt = cd.ja_counterparts(c, tc_map, fallback=True)
        except Exception as e:
            print(f"  {c['id']}: errore {str(e)[:80]}", flush=True)
            continue
        scanned[c["id"]] = cd.today
        if not rows:
            n_none += 1
            print(f"  {c['id']} {c['n']}: nessuna stampa giapponese con stesso nome e illustratore", flush=True)
        for row in rows:
            rid = row["id"]
            if rid in ja_by:                                   # already in the catalogue: link it to its English card
                j = ja_by[rid]
                if not j.get("en"):
                    j.update(en=c["id"], en_same=row["en_same"], en_check=row["en_check"])
                    n_link += 1
                    print(f"  {rid} <- {c['id']}: collegata ({row['en_check']})", flush=True)
                continue
            if rid in queue:
                continue
            try:
                cd.era_of(rid, era_map)
                st = cr.check_ja(rid, {"id": row["tc_id"], "cardType": row["tc_type"], "set": row.get("tc_set"), "url": row["tc_url"]},
                                 row["entry"])
                queue[rid] = dict(row, **{k: v for k, v in st.items() if k in ("status", "detail", "recognised", "share", "n")},
                                  checked=cd.today)
            except Exception as e:
                queue[rid] = dict(row, status="attesa_vendite", detail=f"controllo non riuscito: {str(e)[:60]}", checked=cd.today)
            n_new += 1
            print(f"  {rid} ({c['id']}): {queue[rid]['status']} {queue[rid].get('detail', '')}", flush=True)
        json.dump(scanned, open(scan_p, "w"), indent=1)          # saved as it goes
        json.dump(queue, open(q_p, "w"), ensure_ascii=False, indent=1)
        json.dump(ja, open(ja_p, "w"), ensure_ascii=False, indent=1)
    left = len([c for c in cat if c["id"] not in linked and c["id"] not in queued_en and c["id"] not in scanned])
    print(f"D299: {n_link} gemelle già in catalogo collegate, {n_new} nuove in coda, {n_none} senza gemella trovata; "
          f"da cercare ancora {left}")


if __name__ == "__main__":
    main()
