"""Add the requested cards that passed the daily check to the catalogue (D97, D102).

Usage: PYTHONPATH=. python scripts/add_cards.py [--no-gate]

For each card with status "pronta" in prototype/data/requests_status.json (English printings, at most
MAX_PER_DAY added in a day, era known to the engine):
  1. catalogue entry from TCGdex (prototype/data/cards.json) and images (images.json 160 px, hires.json 440 px);
  2. title matcher entry (data/catalogue_extra.json), built from name, set, number and year as in the check;
  3. tcgcharts mapping, PSA populations and the sales of the last 90 days (data/raw/tcgcharts/);
  4. gate: the sales file is rebuilt and the engine checks R1 and E2 (protocol §15); if the new card fails
     either, every step is undone and the card goes back on hold.
Status becomes "aggiunta" (or "attesa_motore" / "attesa_era").
"""
import base64
import io
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card_requests as cr  # noqa: E402

from slabwise.sources.csv_sales import era_of  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "prototype", "data")
RAW = os.path.join(ROOT, "data", "raw")
MAX_PER_DAY = 5                                       # D117: requested cards go in the same day they pass
R1_FLAGS = ["--adopted", "--v120"]                    # the engine the site uses (D110): v1.20 since D210, gate since D213


def load(p, default):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return default


def save(p, x, indent=None):
    json.dump(x, open(p, "w"), ensure_ascii=False, indent=indent)


def webp(url, w):
    from PIL import Image
    req = urllib.request.Request(url, headers={"User-Agent": "slabwise/0.1"})
    im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=40).read())).convert("RGB")
    im.thumbnail((w, w * 2), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=82)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def tc_sales(tc_id, tc_type, cid):
    out = []
    for g in (10, 9, 8, 7):
        page = 1
        while True:
            q = urllib.parse.urlencode({"cardId": tc_id, "cardType": tc_type or "base", "sort": "sold_date", "order": "DESC",
                                        "page": page, "limit": 100, "company": "PSA", "grade": g})
            d = cr.get(f"{cr.TCG}/api/card-sales?" + q)["data"]
            for s in d["sales"]:
                out.append(dict(card=cid, tc_grade=g, **{k: s.get(k) for k in ("platform", "sale_id", "title", "grading_service", "grade",
                                "price_cents", "sold_date", "source", "is_excluded", "exclusion_reason", "payment_pending", "payment_held")}))
            if not d["pagination"].get("has_next"):
                break
            page += 1
    return out


def add(cid, st):
    """Write every file for card cid; return a function that undoes it."""
    paths = {k: os.path.join(DATA, k + ".json") for k in ("cards", "images", "hires")}
    extra_p = os.path.join(ROOT, "data", "catalogue_extra.json")
    tcc_p, tcs_p = os.path.join(RAW, "tcgcharts", "cards.json"), os.path.join(RAW, "tcgcharts", "sales.json")
    before = {p: open(p, "rb").read() if os.path.exists(p) else None for p in list(paths.values()) + [extra_p, tcc_p, tcs_p]}

    def undo():
        for p, b in before.items():
            if b is None:
                if os.path.exists(p):
                    os.remove(p)
            else:
                open(p, "wb").write(b)

    try:                                    # a failure half way (e.g. tcgcharts 503) leaves nothing behind
        c = cr.get(f"{cr.TCGDEX}/en/cards/{urllib.parse.quote(cid)}")
        s = c.get("set") or {}
        info = cr.tcgdex("en", cid)
        cards = load(paths["cards"], [])
        cards.append(dict(id=cid, n=c.get("name"), no=str(c.get("localId")), set=s.get("name"), sid=s.get("id"),
                          tot=str((s.get("cardCount") or {}).get("official") or ""), r=c.get("rarity"), ill=c.get("illustrator"),
                          hp=str(c.get("hp") or ""), ty=c.get("types"), tv=None, tm=None, tl=None, th=None, added="D102"))
        save(paths["cards"], cards)
        if c.get("image"):
            for k, w in (("images", 160), ("hires", 440)):
                im = load(paths[k], {})
                im[cid] = webp(c["image"] + "/high.webp", w)
                save(paths[k], im)
        extra = load(extra_p, {})
        name = cr.name_re(info["name"])
        setre = cr.at.set_re(info["set"])                      # D153
        yrs = [info["year"], info["year"] + 1] if info["year"] else list(range(1999, date.today().year + 1))
        extra[cid] = [name, setre, cr.at.card_no(info["no"]), yrs]
        save(extra_p, extra, indent=1)
        tcc = load(tcc_p, {})
        det = cr.get(cr.TCG + st["tc_url"].replace(cr.TCG, "").replace("/pokemon/", "/api/pokemon/card-detail/", 1))
        cd = det.get("card", {})
        tcc[cid] = dict(tc_id=st["tc_id"], card_type=st.get("tc_type") or "base", url=st["tc_url"], set=st.get("tc_set"), name=info["name"],
                        psa_population=cd.get("psaPopulation"), pop={g: cd.get(f"psa{g}Count") for g in (10, 9, 8, 7)},
                        graded_supply=cd.get("gradedSupply"), added="D102")
        save(tcc_p, tcc, indent=1)
        sales = load(tcs_p, [])
        sales += tc_sales(st["tc_id"], st.get("tc_type"), cid)
        save(tcs_p, sales)
    except Exception:
        undo()
        raise
    return undo


def add_ja(key, row):
    """Japanese counterpart from the candidate queue (D134): cards_ja.json entry with image, title matcher entry
    (data/catalogue_ja_extra.json), tcgcharts mapping and sales. Return a function that undoes it."""
    ja_p, extra_p = os.path.join(DATA, "cards_ja.json"), os.path.join(ROOT, "data", "catalogue_ja_extra.json")
    tcc_p, tcs_p = os.path.join(RAW, "tcgcharts", "cards.json"), os.path.join(RAW, "tcgcharts", "sales.json")
    before = {p: open(p, "rb").read() if os.path.exists(p) else None for p in (ja_p, extra_p, tcc_p, tcs_p)}

    def undo():
        for p, b in before.items():
            if b is None:
                if os.path.exists(p):
                    os.remove(p)
            else:
                open(p, "wb").write(b)

    try:                                    # a failure half way (e.g. tcgcharts 503) leaves nothing behind
        c = cr.get(f"{cr.TCGDEX}/ja/cards/{urllib.parse.quote(row['tcgdex'])}") if row.get("tcgdex") else \
            dict(name=row.get("ja_name") or row.get("name"), localId=row.get("no"), set=dict(name=row.get("set")))   # D158: vintage, from tcgcharts
        s = c.get("set") or {}
        entry = dict(id=key, en=row.get("en"), en_same=row.get("en_same"), en_check=row.get("en_check"), lang="ja", n=c.get("name"), no=str(c.get("localId")), set=s.get("name"),
                     tot=(s.get("cardCount") or {}).get("official"), r=c.get("rarity"), ill=c.get("illustrator"),
                     set_en=row.get("set_en"), source="TCGdex ja", added="D134")
        if c.get("image"):
            entry.update(img=webp(c["image"] + "/high.webp", 360), img_url=c["image"] + "/high.webp")
        ja = load(ja_p, [])
        old = next((x for x in ja if x["id"] == key), None)          # D158: a pending page gets its price, keeps its picture
        if old:
            entry = {**old, **{k: v for k, v in entry.items() if v is not None}, "added": old.get("added") or entry["added"]}
            entry.pop("pending", None)
            ja = [x for x in ja if x["id"] != key]
        ja.append(entry)
        save(ja_p, ja, indent=1)
        extra = load(extra_p, {})
        extra[key] = row["entry"]
        save(extra_p, extra, indent=1)
        tcc = load(tcc_p, {})
        det = cr.get(cr.TCG + row["tc_url"].replace("/pokemon/", "/api/pokemon/card-detail/", 1))
        cd = det.get("card", {})
        tcc[key] = dict(tc_id=row["tc_id"], card_type=row.get("tc_type") or "base", url=row["tc_url"], set=row.get("tc_set"), name=cd.get("name"),
                        psa_population=cd.get("psaPopulation"), pop={g: cd.get(f"psa{g}Count") for g in (10, 9, 8, 7)},
                        graded_supply=cd.get("gradedSupply"), added="D134")
        save(tcc_p, tcc, indent=1)
        sales = load(tcs_p, [])
        sales += tc_sales(row["tc_id"], row.get("tc_type"), key)
        save(tcs_p, sales)
    except Exception:
        undo()
        raise
    return undo


def gate(cid):
    """R1 and E2 with the new card (protocol §15). True when the new card passes."""
    env = dict(os.environ, PYTHONPATH=ROOT, SLABWISE_TC_HISTORY="1")   # D213: the sales of the site, with the long history
    tmp = os.path.join(RAW, "sales_gate.csv")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_sales.py"), os.path.join(RAW, "sales_base.csv"),
                    os.path.join(RAW, "alt"), tmp, os.path.join(RAW, "tcgcharts")], check=True, env=env, capture_output=True)
    out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "real_r1.py"), tmp, os.path.join(RAW, "era_map.json")] + R1_FLAGS,
                         env=env, capture_output=True, text=True).stdout
    os.remove(tmp)
    bad = [ln for ln in out.splitlines() if (ln.startswith("E2r:") or "R1:" in ln) and f"'{cid}" in ln]   # E2r since D125 (§23)
    print("\n".join(ln for ln in out.splitlines() if ln.startswith("E2") or "R1:" in ln))
    return not bad


def main():
    status_p = os.path.join(DATA, "requests_status.json")
    status = load(status_p, {})
    era_map = load(os.path.join(RAW, "era_map.json"), {})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    recent = sum(1 for v in status.values() if v.get("status") == "aggiunta" and v.get("added") == today)
    todo = sorted([(k, v) for k, v in status.items() if v.get("status") == "pronta"], key=lambda kv: -kv[1].get("requests", 0))
    for k, st in todo:
        lang, cid = k.split(":", 1)
        if recent >= MAX_PER_DAY:
            print("limite giornaliero raggiunto")
            break
        if lang != "en":
            st["detail"] = "aggiunta delle carte giapponesi ancora manuale"
            continue
        try:
            era_of(cid, era_map)
        except KeyError:
            st.update(status="attesa_era", detail="era non ancora coperta dal motore")
            continue
        try:
            undo = add(cid, st)
        except Exception as e:                          # a failed addition never breaks the run
            print(f"  {k}: errore {str(e)[:100]}")
            continue
        if "--no-gate" not in sys.argv and not gate(cid):
            undo()
            st.update(status="attesa_motore", detail="i controlli del motore non tornano ancora", checked=today)
            print(f"  {k}: tolta, controlli del motore non superati")
            continue
        st.update(status="aggiunta", detail="", added=today)
        recent += 1
        print(f"  {k}: aggiunta al catalogo")
    save(status_p, status, indent=1)


if __name__ == "__main__":
    main()
