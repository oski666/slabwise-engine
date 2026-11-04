"""Add a batch of catalogue cards chosen by the owner (D111): same steps and checks as the requested cards
(scripts/add_cards.py, D102), with one engine check for the whole batch.

Usage: PYTHONPATH=. python scripts/add_batch.py base1-6 base1-12 ...

Each card is checked like a request (scripts/card_requests.py); the ones that pass are added, then R1 and E2 run
once on all sales; a new card that fails them is removed again (and every file entry of that card with it).
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_cards as ac  # noqa: E402
import card_requests as cr  # noqa: E402

ids = [a for a in sys.argv[1:] if not a.startswith("--")]
GATE_ONLY = "--gate-only" in sys.argv         # cards already written whose engine gate did not run (crash of 4 November)
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
status_p = os.path.join(ac.DATA, "requests_status.json")
status = ac.load(status_p, {})
have = {c["id"] for c in ac.load(os.path.join(ac.DATA, "cards.json"), [])}
added = []
queue = ac.load(os.path.join(ac.DATA, "candidates_queue.json"), {})
sk = lambda cid: cid if cid.startswith("ja:") else f"en:{cid}"                 # status key (D134: Japanese ids carry "ja:")
# D135: the eBay budget no longer stops cards (D118 replaced): it only decides which cards get their listings checked
have |= {c["id"] for c in ac.load(os.path.join(ac.DATA, "cards_ja.json"), []) if not c.get("pending")}   # D158: pending pages still need a price
for cid in ([] if GATE_ONLY else ids):
    if cid in have:
        print(f"  {cid}: già nel catalogo")
        continue
    if cid.startswith("ja:"):                                                   # D134: Japanese counterpart from the queue
        row = queue.get(cid)
        if not row or row.get("lang") != "ja":
            print(f"  {cid}: non è nella coda")
            continue
        try:
            st = cr.check_ja(cid, {"id": row["tc_id"], "cardType": row.get("tc_type") or "base", "set": row.get("tc_set"), "url": row["tc_url"]}, row["entry"])
        except Exception as e:                                                  # a source error never stops the batch
            print(f"  {cid}: errore {str(e)[:100]}")
            continue
        st.update(checked=today, requests=0, source="coda giapponese (D134)")
        status[cid] = st
        if st["status"] != "pronta":
            print(f"  {cid}: {st['status']} {st.get('detail', '')}")
            continue
        try:
            ac.add_ja(cid, row)
        except Exception as e:
            print(f"  {cid}: errore {str(e)[:100]}")
            continue
        added.append(cid)
        print(f"  {cid}: aggiunta in prova ({st['recognised']} vendite riconosciute)", flush=True)
        continue
    try:
        st = cr.check({"lang": "en", "id": cid, "rank": (queue.get(cid) or {}).get("rank")}, have)   # D150: rank for the grail threshold
    except Exception as e:                                                      # a source error never stops the batch
        print(f"  {cid}: errore {str(e)[:100]}")
        continue
    st.update(checked=today, requests=0, source="catalogo (D111)")
    if st["status"] != "pronta":
        status[f"en:{cid}"] = st
        print(f"  {cid}: {st['status']} {st.get('detail', '')}")
        continue
    try:
        ac.add(cid, st)
    except Exception as e:
        print(f"  {cid}: errore {str(e)[:100]}")
        continue
    status[f"en:{cid}"] = st
    added.append(cid)
    print(f"  {cid}: aggiunta in prova ({st['recognised']} vendite riconosciute)", flush=True)


def remove(cid):
    for name in ("cards", "cards_ja"):
        p = os.path.join(ac.DATA, name + ".json")
        if os.path.exists(p):
            keep = [dict(c, pending=True) for c in ac.load(p, []) if c["id"] == cid and c.get("added") == "D158"]   # D158: back to a pending page
            ac.save(p, [c for c in ac.load(p, []) if c["id"] != cid] + keep, **({"indent": 1} if name == "cards_ja" else {}))
    for name in ("images", "hires"):
        p = os.path.join(ac.DATA, name + ".json")
        d = ac.load(p, {})
        d.pop(cid, None)
        ac.save(p, d)
    for p, ind in ((os.path.join(ac.ROOT, "data", "catalogue_extra.json"), 1), (os.path.join(ac.ROOT, "data", "catalogue_ja_extra.json"), 1),
                   (os.path.join(ac.RAW, "tcgcharts", "cards.json"), 1)):
        d = ac.load(p, {})
        d.pop(cid, None)
        ac.save(p, d, indent=ind)
    p = os.path.join(ac.RAW, "tcgcharts", "sales.json")
    ac.save(p, [s for s in ac.load(p, []) if s["card"] != cid])


if GATE_ONLY:
    added = [c for c in ids if c in have]
    for cid in added:
        status.setdefault(sk(cid), {})
if added and "--no-gate" not in sys.argv:
    env = dict(os.environ, PYTHONPATH=ac.ROOT)
    tmp = os.path.join(ac.RAW, "sales_gate.csv")
    subprocess.run([sys.executable, os.path.join(ac.ROOT, "scripts", "build_sales.py"), os.path.join(ac.RAW, "sales_base.csv"),
                    os.path.join(ac.RAW, "alt"), tmp, os.path.join(ac.RAW, "tcgcharts")], check=True, env=env, capture_output=True)
    out = subprocess.run([sys.executable, os.path.join(ac.ROOT, "scripts", "real_r1.py"), tmp, os.path.join(ac.RAW, "era_map.json"), "--adopted"],
                         env=env, capture_output=True, text=True).stdout
    os.remove(tmp)
    lines = [ln for ln in out.splitlines() if ln.startswith("E2r:") or "R1:" in ln]   # E2r since D125 (§23); E2 printed for comparison
    print("\n".join(ln for ln in out.splitlines() if ln.startswith("E2:")))
    print("\n".join(lines))
    for cid in list(added):
        if any(f"'{cid}'" in ln or f"'{cid}/" in ln for ln in lines):
            remove(cid)
            added.remove(cid)
            status[sk(cid)].update(status="attesa_motore", detail="i controlli del motore non tornano ancora")
            print(f"  {cid}: tolta, controlli del motore non superati")
for cid in added:
    status[sk(cid)].update(status="aggiunta", detail="", added=today)
ac.save(status_p, status, indent=1)
print(f"{len(added)} carte aggiunte: {' '.join(added)}")
