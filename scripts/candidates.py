"""Candidate cards for the catalogue (D118): the most valuable English cards we do not follow yet, checked with the
same admission rule as the visitors' requests (D97), proposed to the owner, added only after his ok.

Usage: PYTHONPATH=. python scripts/candidates.py <out dir> [--top 400] [--checks 25]

1. The market-cap ranking of tcgcharts (English, base printing; 1st edition and shadowless are variants of a
   catalogue card, so they are not candidates of their own).
2. Each card is mapped to its TCGdex id by set name and number and kept in one queue
   (prototype/data/candidates_queue.json, D122) with its state: ready, waiting (and why), added.
3. Up to --checks checks per run: half for the waiting cards checked more than RECHECK_DAYS ago, the rest for new
   cards from the ranking. Check = card_requests.check (recognised eBay sales in 90 days, grades with sales, share
   of titles recognised) plus an era known to the engine.
Writes <out>/issue.md: the queue for the owner, one checkbox per ready card (and one for all of them). The workflow
"Candidate" keeps it in a single open issue; "Approva candidate" adds the ticked cards with the engine gate
(scripts/add_batch.py) and the site rebuilds itself.
"""
import json
import os
import re
import sys
import urllib.parse
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card_requests as cr  # noqa: E402

from slabwise.sources.csv_sales import era_of  # noqa: E402
from slabwise.print_match import same_print  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "prototype", "data")
HIRES = json.load(open(os.path.join(DATA, "hires.json"))) if os.path.exists(os.path.join(DATA, "hires.json")) else {}
out_dir = sys.argv[1]
TOP = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 400
CHECKS = int(sys.argv[sys.argv.index("--checks") + 1]) if "--checks" in sys.argv else 40
FILL = int(sys.argv[sys.argv.index("--fill") + 1]) if "--fill" in sys.argv else 0      # D139, off since D154: no filling of eras
FILL_TOP, FILL_TARGET = 3000, 12                 # D139: ranking read for the thin eras; cards wanted per era
os.makedirs(out_dir, exist_ok=True)
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def norm(s):
    s = (s or "").lower().replace("&", "and")
    s = re.sub(r"\b(pokemon|pokémon|tcg|the|set)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)


ALIASES = {norm("Scarlet & Violet Black Star Promos"): "svp", norm("Sword & Shield Black Star Promos"): "swshp",
           norm("Sun & Moon Black Star Promos"): "smp", norm("XY Black Star Promos"): "xyp",
           norm("Wizards Black Star Promos"): "basep", norm("Base"): "base1",
           # D150: tcgcharts writes the HGSS sets with an "HS—" prefix
           norm("HS—Unleashed"): "hgss2", norm("HS—Undaunted"): "hgss3", norm("HS—Triumphant"): "hgss4",
           norm("HeartGold & SoulSilver"): "hgss1", norm("HGSS Black Star Promos"): "hgssp"}
sets = {norm(s["name"]): s["id"] for s in cr.get(f"{cr.TCGDEX}/en/sets")}
sets.update(ALIASES)
set_cards = {}


def tcgdex_id(card):
    sid = sets.get(norm(card["set"]["name"]))
    if not sid:
        return None
    if sid not in set_cards:
        try:
            set_cards[sid] = cr.get(f"{cr.TCGDEX}/en/sets/{urllib.parse.quote(sid)}").get("cards", [])
        except Exception:
            set_cards[sid] = []
    num = cr.num_key(card.get("cardNumber"))
    hits = [c["id"] for c in set_cards[sid] if cr.num_key(c.get("localId")) == num]
    return hits[0] if len(hits) == 1 else None


def ranking(top=None):
    top = top or TOP
    out, page = [], 1
    while len(out) < top:
        d = cr.get(f"{cr.TCG}/api/pokemon/cards?" + urllib.parse.urlencode(
            {"sort": "market_cap", "order": "desc", "limit": 100, "page": page, "language": "EN"}))
        out += [c for c in d["cards"] if c.get("languageCode") == "EN" and not c.get("variantType")]
        if not d["pagination"].get("hasNextPage"):
            break
        page += 1
    return out[:top]


JA_SCANS = 20                                         # D134: catalogue cards searched for Japanese counterparts per run


def strip_no(name):
    return re.sub(r"\s*#\S+$", "", name or "").strip()


def ja_counterparts(c, tc_map):
    """Japanese printings of catalogue card c (D134). Candidates: the cards tcgcharts relates to it and its search
    "<name> japanese"; kept when the name and the illustrator are the same and TCGdex (ja) has exactly one card with
    that number and illustrator (its id, image and set). Returns queue rows, not yet checked; and how many were found
    without a TCGdex card."""
    cands = {}
    if c["id"] in tc_map:
        det = cr.get(cr.TCG + tc_map[c["id"]]["url"].replace("/pokemon/", "/api/pokemon/card-detail/", 1))
        for r in (det.get("relatedCards") or {}).get("relatedCards") or []:
            if (r.get("setSlug") or "").endswith("-japanese") and r.get("slug"):
                cands[f"/pokemon/{r['setSlug']}/{r['slug']}"] = r.get("name")
    for line in cr.get(f"{cr.TCG}/api/search?" + urllib.parse.urlencode({"q": f"{c['n']} japanese"}), raw=True).splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        for it in d.get("items", []) if d.get("phase") == "cards" else []:
            if it.get("type") == "card" and it.get("cardType") == "base" and not it.get("variantType") and (it.get("languageCode") or "").upper() == "JA":
                cands[it["url"]] = strip_no(it.get("name"))
    out, no_tcgdex, en_card = [], 0, None
    for url, name in cands.items():
        if norm(name) != norm(c["n"]):
            continue
        cd = cr.get(cr.TCG + url.replace("/pokemon/", "/api/pokemon/card-detail/", 1)).get("card", {})
        if not c.get("ill") or norm(cd.get("artist")) != norm(c["ill"]) or cd.get("variantType") or not cd.get("id"):
            continue
        no = cr.num_key(cd.get("cardNumber")) or "0"
        hits = cr.get(f"{cr.TCGDEX}/ja/cards?" + urllib.parse.urlencode({"localId": no, "illustrator": c["ill"]}))
        hits = [h for h in hits if cr.num_key(h.get("localId")) == no] if isinstance(hits, list) else []
        if len(hits) != 1:                                        # not on TCGdex, or ambiguous: no id and no image
            no_tcgdex += 1
            continue
        tid = hits[0]["id"]
        jc = cr.get(f"{cr.TCGDEX}/ja/cards/{urllib.parse.quote(tid)}")
        if en_card is None:                                       # D152: same Pokémon and same illustration
            en_card = cr.get(f"{cr.TCGDEX}/en/cards/{urllib.parse.quote(c['id'])}")
        same, why = same_print(jc, en_card, jc.get("image") and jc["image"] + "/high.webp",
                               HIRES.get(c["id"]) or (en_card.get("image") and en_card["image"] + "/high.webp"))
        if same is False and why in ("Pokémon diverso", "tipo di carta diverso"):
            continue                                              # TCGdex gave another card for that number
        tot = ((jc.get("set") or {}).get("cardCount") or {}).get("official")
        set_en = re.sub(r"\s*japanese\s*$", "", cd.get("setName") or "", flags=re.I)
        out.append(dict(id="ja:" + tid.lower(), lang="ja", tcgdex=tid, en=c["id"], en_same=same, en_check=why, name=f"{c['n']} (giapponese)", ja_name=jc.get("name"),
                        set=set_en, no=cd.get("cardNumber"), rank=None, pop10=cd.get("psa10Count"), pop9=cd.get("psa9Count"),
                        tc_id=cd["id"], tc_type="base", tc_url=url, tc_set=cd.get("setName"), set_en=set_en,
                        entry=cr.ja_entry(c["n"], jc.get("name"), cd.get("cardNumber"), tot, set_en)))
    return out, no_tcgdex


RECHECK_DAYS = 7                                      # D122: a card waiting for sales is checked again after a week


def main():
    have = {c["id"] for c in json.load(open(os.path.join(DATA, "cards.json")))}
    n_cat = len(have) + len(cr_load(os.path.join(DATA, "cards_ja.json"), []))
    status = cr_load(os.path.join(DATA, "requests_status.json"), {})
    q_p = os.path.join(DATA, "candidates_queue.json")             # D122: one queue, kept between runs
    queue = cr_load(q_p, {})
    era_map = cr_load(os.path.join(ROOT, "data", "raw", "era_map.json"), {})
    for cid, r in queue.items():                                  # what happened since the last run
        st = status.get(f"en:{cid}", {})
        if cid in have:
            r.update(status="aggiunta", added=r.get("added") or st.get("added") or today)
        elif st.get("status") == "attesa_motore":
            r.update(status="attesa_motore", detail="i controlli del motore non tornano ancora: si riprova ogni settimana (D157)")
    checks = 0

    def check(cid, row):
        nonlocal checks
        checks += 1
        try:
            era_of(cid, era_map)
        except KeyError:
            return dict(row, status="attesa_era", detail="epoca non coperta dal motore", checked=today)
        if row.get("lang") == "ja":
            st = cr.check_ja(cid, {"id": row["tc_id"], "cardType": row["tc_type"], "set": row.get("tc_set"), "url": row["tc_url"]}, row["entry"])
            return dict(row, **{k: v for k, v in st.items() if k in ("status", "detail", "recognised", "share", "n")}, checked=today)
        st = cr.check({"lang": "en", "id": cid, "rank": row.get("rank")}, have)
        return dict(row, **{k: v for k, v in st.items() if k in ("status", "detail", "recognised", "share", "n")}, checked=today)

    for cid, r in sorted(queue.items(), key=lambda kv: kv[1].get("rank") or 9999):     # the waiting ones, once a week
        if checks >= CHECKS // 2:
            break
        if r["status"] in ("attesa_vendite", "attesa_coerenza", "non_trovata") and \
                (date.fromisoformat(today) - date.fromisoformat(r["checked"])).days >= RECHECK_DAYS:
            try:
                queue[cid] = check(cid, r)
                print(f"  di nuovo #{r['rank']} {cid}: {queue[cid]['status']} {queue[cid].get('detail', '')}", flush=True)
            except Exception as e:
                print(f"  {cid}: errore {str(e)[:80]}")
    unmapped = 0
    for rank, c in enumerate(ranking(), 1):                      # new cards, highest market cap first
        if checks >= CHECKS:
            break
        cid = tcgdex_id(c)
        if not cid:
            unmapped += 1
            continue
        if cid in have or cid in queue:
            if cid in queue:
                queue[cid]["rank"] = rank
            continue
        row = dict(id=cid, name=c["name"], set=c["set"]["name"], no=c.get("cardNumber"), rank=rank,
                   pop10=c.get("psaGrade10"), pop9=c.get("psaGrade9"))
        if status.get(f"en:{cid}", {}).get("status") == "attesa_motore":      # already stopped by the engine gate
            queue[cid] = dict(row, status="attesa_motore", checked=today,
                              detail="i controlli del motore non tornano ancora: si riprova ogni settimana (D157)")
            continue
        try:
            queue[cid] = check(cid, row)
        except Exception as e:
            print(f"  {cid}: errore {str(e)[:80]}")
            continue
        print(f"  #{rank} {cid} {c['name']}: {queue[cid]['status']} {queue[cid].get('detail', '')}", flush=True)
    # D139: eras whose indices have too few cards get extra checks, deeper in the ranking, before anything else waits
    from slabwise.series import series_of
    cnt = {}
    for cid in have:
        cnt[series_of(cid)] = cnt.get(series_of(cid), 0) + 1
    for r in queue.values():
        if r["status"] == "pronta" and r.get("lang") != "ja" and r["id"] not in have:
            cnt[series_of(r["id"])] = cnt.get(series_of(r["id"]), 0) + 1
    need = {s_: FILL_TARGET - n for s_, n in cnt.items() if n < FILL_TARGET}
    need = {k: v for k, v in need.items() if v > 0 and k != "Altro"}
    print("ere da completare:", need, flush=True)
    fill_checks = 0
    if need and FILL:
        for rank, c in enumerate(ranking(FILL_TOP), 1):
            if fill_checks >= FILL or not need:
                break
            if rank <= TOP:
                continue
            cid = tcgdex_id(c)
            if not cid or cid in have or cid in queue or series_of(cid) not in need:
                continue
            row = dict(id=cid, name=c["name"], set=c["set"]["name"], no=c.get("cardNumber"), rank=rank,
                       pop10=c.get("psaGrade10"), pop9=c.get("psaGrade9"), fill=series_of(cid))
            try:
                queue[cid] = check(cid, row)
            except Exception as e:
                print(f"  {cid}: errore {str(e)[:80]}")
                continue
            fill_checks += 1
            if queue[cid]["status"] == "pronta":
                need[series_of(cid)] -= 1
                need = {k: v for k, v in need.items() if v > 0}
            print(f"  completare {series_of(cid)}: #{rank} {cid} {c['name']}: {queue[cid]['status']} {queue[cid].get('detail', '')}", flush=True)
    have_ja = {c["id"] for c in cr_load(os.path.join(DATA, "cards_ja.json"), []) if not c.get("pending")}
    for cid in [k for k, r in queue.items() if r.get("lang") == "ja" and k in have_ja]:
        queue[cid].update(status="aggiunta", added=queue[cid].get("added") or today)
    scan_p = os.path.join(DATA, "ja_scan.json")                  # D134: catalogue cards already searched for Japanese printings
    scanned = cr_load(scan_p, {})
    ja_en = {c.get("en") for c in cr_load(os.path.join(DATA, "cards_ja.json"), [])}
    cat = sorted(json.load(open(os.path.join(DATA, "cards.json"))), key=lambda c: c["id"])
    todo = [c for c in cat if c["id"] not in scanned and c["id"] not in ja_en][:JA_SCANS]
    tc_map = cr_load(os.path.join(ROOT, "data", "raw", "tcgcharts", "cards.json"), {})
    for c in todo:
        try:
            rows, nt = ja_counterparts(c, tc_map)
        except Exception as e:
            print(f"  {c['id']} giapponese: errore {str(e)[:80]}")
            continue
        scanned[c["id"]] = today
        for row in rows:
            if row["id"] in queue or row["id"] in have_ja:
                continue
            try:
                queue[row["id"]] = check(row["id"], row)
            except Exception as e:
                print(f"  {row['id']}: errore {str(e)[:80]}")
                continue
            print(f"  {row['id']} ({c['id']}): {queue[row['id']]['status']} {queue[row['id']].get('detail', '')}", flush=True)
        if not rows:
            print(f"  {c['id']}: nessuna stampa giapponese con lo stesso illustratore su TCGdex" + (f" ({nt} trovate solo su tcgcharts)" if nt else ""), flush=True)
    json.dump(scanned, open(scan_p, "w"), indent=1)
    json.dump(queue, open(q_p, "w"), ensure_ascii=False, indent=1)
    ready = sorted([r for r in queue.values() if r["status"] == "pronta" and r.get("lang") != "ja"], key=lambda r: r["rank"] or 9999)
    ready_ja = sorted([r for r in queue.values() if r["status"] == "pronta" and r.get("lang") == "ja"], key=lambda r: -(r.get("recognised") or 0))
    wait = sorted([r for r in queue.values() if r["status"] not in ("pronta", "aggiunta")], key=lambda r: r.get("rank") or 9999)
    added = [r for r in queue.values() if r["status"] == "aggiunta"]
    from slabwise.ebay_budget import limit                         # D135: the budget limits deals, not cards
    n_en = len(have)
    md = [f"Coda aggiornata il {today}. Le carte inglesi di maggior valore che non seguiamo ancora, controllate con le regole "
          f"delle richieste (D97). **Spunta le carte da aggiungere** (o `TUTTE`): partono subito i controlli del motore e la "
          f"ricostruzione del sito, e l'esito arriva qui come commento. Le carte in attesa si ricontrollano da sole ogni "
          f"{RECHECK_DAYS} giorni e salgono tra le pronte quando hanno abbastanza vendite.", "",
          f"**Catalogo**: {n_cat} carte · aggiunte da questa coda: {len(added)} · offerte eBay controllate per {min(n_en, limit(today))} "
          f"carte (limite di chiamate eBay); le altre entrano lo stesso, con il prezzo ma senza offerte (D135).", "",
          f"### Pronte ({len(ready)})", ""]
    md += ["- [ ] `TUTTE` le pronte qui sotto"] if ready else []
    md += [f"- [ ] `{r['id']}` **{r['name']}** · {r['set']} #{r['no']} · {r['rank']}ª per capitalizzazione · "
           + (f"completa l'indice {r['fill']} · " if r.get("fill") else "")
           + f"{r.get('recognised', 0)} vendite PSA in 90 giorni ({round(r.get('share', 0) * 100)}% riconosciute) · pop 10/9: {r.get('pop10')}/{r.get('pop9')}"
           for r in ready] or ["Nessuna carta pronta in questo momento."]
    md += ["", f"### Versioni giapponesi pronte ({len(ready_ja)})", "",
           "Stampe giapponesi delle carte del catalogo (stesso nome e stesso illustratore), con le stesse regole di ammissione. "
           "Sono carte a sé, con un loro prezzo (D28)." if ready_ja else "Nessuna versione giapponese pronta in questo momento.", ""]
    md += [f"- [ ] `{r['id']}` **{r['name']}** · {r['set']} #{r['no']} · di [`{r['en']}`] · {r.get('recognised', 0)} vendite PSA in 90 giorni "
           f"({round(r.get('share', 0) * 100)}% riconosciute) · pop 10/9: {r.get('pop10')}/{r.get('pop9')}" for r in ready_ja]
    md += ["", f"<details><summary>In attesa ({len(wait)})</summary>", ""]
    md += [f"- `{r['id']}` {r['name']} · {r['set']}: {r.get('detail') or r['status']}"
           + (f" · prossimo controllo {(date.fromisoformat(r['checked']) + timedelta(days=RECHECK_DAYS)).isoformat()}"
              if r["status"] in ("attesa_vendite", "attesa_coerenza", "non_trovata") else "") for r in wait]
    md += ["", "</details>", "", f"Classifica letta: prime {TOP} carte; {unmapped} non collegate a TCGdex. Controlli in questo giro: {checks}."]
    open(os.path.join(out_dir, "issue.md"), "w").write("\n".join(md) + "\n")
    open(os.path.join(out_dir, "new_ready.txt"), "w").write(str(sum(1 for r in ready + ready_ja if r.get("checked") == today)))
    print(f"{len(ready)} pronte, {len(wait)} in attesa, {len(added)} aggiunte")


def cr_load(p, default):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return default


if __name__ == "__main__":
    main()
