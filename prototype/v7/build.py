"""Build prototype/v7/slabwise.html from src/ (app.html + base.css + comic.css + slabby.js), the Slabby
character package (prototype/character/slabby/character.json) and data/demo.json."""
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "src", "app.html"), encoding="utf-8").read()
css = open(os.path.join(here, "src", "base.css"), encoding="utf-8").read() + "\n" + open(os.path.join(here, "src", "comic.css"), encoding="utf-8").read()
js = open(os.path.join(here, "src", "slabby.js"), encoding="utf-8").read()
sys.path.insert(0, os.path.join(here, "..", "character"))
from load import load  # noqa: E402
char = load(os.path.join(here, "..", "character", "slabby"))      # character.json is the only source of Slabby
which = sys.argv[1] if len(sys.argv) > 1 else "real"          # "real" (default since D34) or "demo"
data = json.load(open(os.path.join(here, "..", "data", "real.json" if which == "real" else "demo.json"), encoding="utf-8"))
certs = os.path.join(here, "..", "data", "certs.json")       # D63: history of each copy by PSA cert
if which == "real" and os.path.exists(certs):
    data["certs"] = json.load(open(certs, encoding="utf-8"))
pag = os.path.join(here, "..", "data", "pagella.json")      # D105: public scorecard
if which == "real" and os.path.exists(pag):                     # D108: only the list of seals goes to the page
    data["pagella"] = {"seals": json.load(open(pag, encoding="utf-8")).get("seals", [])}
reqs = os.path.join(here, "..", "data", "requests_status.json")   # D97: daily check of the card requests
if which == "real" and os.path.exists(reqs):
    data["requests_status"] = json.load(open(reqs, encoding="utf-8"))
tcd = os.path.join(here, "..", "..", "data", "raw", "tcgcharts")    # D115: last known sale of a grade with no sales of its own
if which == "real" and os.path.exists(os.path.join(tcd, "sales.json")):
    import gzip
    allsales = json.load(open(os.path.join(tcd, "sales.json"), encoding="utf-8"))
    if os.path.exists(os.path.join(tcd, "history.json.gz")):
        allsales += json.load(gzip.open(os.path.join(tcd, "history.json.gz"), "rt", encoding="utf-8"))
    last = {}
    for s in allsales:
        if s.get("is_excluded") or (s.get("grading_service") or "").upper() != "PSA" or not s.get("price_cents"):
            continue
        k = (s["card"], s["tc_grade"])
        if k not in last or s["sold_date"] > last[k][0]:
            last[k] = (s["sold_date"], round(s["price_cents"] / 100), {"ebay": "eBay"}.get((s.get("platform") or "").lower(), s.get("platform") or ""))
    for c in data["cards"]:
        for g in c["grades"]:
            if not g.get("sales_all") and (c["id"], g["grade"]) in last:
                g["last"] = list(last[(c["id"], g["grade"])])
font_link = (f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={char["font"].replace(" ", "+")}&display=swap">'
             if char["font"] else "")
split = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else None
if split and which == "real":                                # D104: the page keeps the lists, the API serves the rest
    import base64
    os.makedirs(os.path.join(split, "x", "cards"), exist_ok=True)
    os.makedirs(os.path.join(split, "x", "certs"), exist_ok=True)
    os.makedirs(os.path.join(split, "img"), exist_ok=True)
    json.dump({c_["id"]: f'{c_["name"]} · {c_.get("set", "")} #{c_.get("no", "")}' for c_ in data["cards"]},   # D133: names for the studio
              open(os.path.join(split, "x", "names.json"), "w"), ensure_ascii=False)
    certs_all = (data.pop("certs", None) or {})
    by_card = {}
    for n_, l_ in (certs_all.get("certs") or {}).items():
        for cid_ in {s_[1].split("/")[0] for s_ in l_}:
            by_card.setdefault(cid_, {})[n_] = l_
    buckets = {}
    for n_, l_ in (certs_all.get("certs") or {}).items():
        buckets.setdefault(n_[-2:], {})[n_] = l_
    for b_, d_ in buckets.items():
        json.dump(d_, open(os.path.join(split, "x", "certs", f"{b_}.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    seals_dir = os.path.join(here, "..", "..", "data", "seals")       # D105: the sealed snapshots are public
    if os.path.isdir(seals_dir):
        import shutil
        os.makedirs(os.path.join(split, "sigilli"), exist_ok=True)
        for f_ in os.listdir(seals_dir):
            shutil.copy(os.path.join(seals_dir, f_), os.path.join(split, "sigilli", f_))
    data["certs_meta"] = {"names": certs_all.get("names", {}), "asof": certs_all.get("asof"), "count": len(certs_all.get("certs") or {})}
    for c in data["cards"]:
        fid = c["id"].replace(":", "_").replace("/", "_")
        full = {"grades": {str(g["grade"]): g.pop("history", []) for g in c["grades"]}, "sales": c.pop("sales", []),
                "excluded": c.pop("excluded", []), "certs": by_card.get(c["id"], {})}
        json.dump(full, open(os.path.join(split, "x", "cards", f"{fid}.json"), "w"), ensure_ascii=False, separators=(",", ":"))
        c["lazy"] = True
        if not c.get("thumb") and c.get("img"):              # Japanese printings have one image: it serves as thumbnail too
            c["thumb"] = c["img"]
        for k, suf in (("img", ""), ("thumb", "_t")):
            v = c.get(k) or ""
            if v.startswith("data:image/"):
                ext = v[11:v.index(";")]
                open(os.path.join(split, "img", f"{fid}{suf}.{ext}"), "wb").write(base64.b64decode(v.split(",", 1)[1]))
                c[k] = f"img/{fid}{suf}.{ext}"
def self_host_fonts(html, extra_link, folder):
    """D129: the Google Fonts stylesheets are downloaded at build time and served from our own site, so a visitor's
    browser never contacts Google (privacy). On any network error the page keeps the Google links."""
    import re as _re
    import urllib.request as _ur
    links = _re.findall(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/css2\?[^"]+)">', html + extra_link)
    if not links:
        return html, extra_link
    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
    try:
        css_all = ""
        os.makedirs(os.path.join(folder, "fonts"), exist_ok=True)
        for url in links:
            css = _ur.urlopen(_ur.Request(url.replace("&amp;", "&"), headers=ua), timeout=30).read().decode()
            for f in sorted(set(_re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css))):
                name = f.split("/")[-1]
                open(os.path.join(folder, "fonts", name), "wb").write(_ur.urlopen(_ur.Request(f, headers=ua), timeout=30).read())
                css = css.replace(f, "fonts/" + name)
            css_all += css
    except Exception as e:                                        # offline build: keep Google's links
        print("font locali non disponibili:", str(e)[:80])
        return html, extra_link
    html = _re.sub(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\n?', "", html)
    html = _re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?[^"]+">', "", html)
    open(os.path.join(folder, "fonts", "fonts.css"), "w").write(css_all.replace("url(fonts/", "url("))
    return html.replace("<style>", '<link rel="stylesheet" href="fonts/fonts.css">\n<style>', 1), ""


if split:
    src, font_link = self_host_fonts(src, font_link, split)
out = (src.replace("__CHAR_FONT__", font_link).replace("__STYLE__", css + "\n" + char["css"]).replace("__SLABBY_SVG__", char["svg"]).replace("__SLABBY__", js)
       .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
open(os.path.join(split, "index.html") if split else os.path.join(here, "slabwise.html"), "w", encoding="utf-8").write(out)
print("slabwise.html", len(out))
