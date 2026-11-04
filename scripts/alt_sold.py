"""Recent sales of our catalogue cards from Alt's public "Sold listings" pages (D64).

Usage: PYTHONPATH=. python scripts/alt_sold.py [data/raw/alt] [--cards base1-4,swsh7-215] [--grades 10,9,8,7]

Alt allowed us (27 Oct 2026) to read its website gently, with a reasonable number of requests per day.
Rules of D64: a real browser opens the same public page a visitor sees; only the first page of each
search is shown to visitors (15 sales), so there is one search per card and grade, repeated every day;
at most MAX_PAGES pages per run, one every PAUSE_S seconds or more; no internal keys, no sign-up wall
bypass, no photos, no sellers.
Output: <dir>/<date>.json with the sales seen today, and <dir>/alt_sold.json with every sale seen so far
(key: Alt item id). Fanatics Collect sales are kept in the raw file but marked: the site takes them from
the Fanatics archive (D46).
"""
import json
import os
import re
import sys
import time
from datetime import date, datetime
from urllib.parse import quote


MAX_PAGES = 150
PAUSE_S = 8
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
URL = "https://alt.xyz/browse?category=POKEMON_CARDS&query={q}&soldListings=true&sortBy=newest_first"
# search words per catalogue card, as Alt titles them ("Year Pokemon Set Variety / Subject #No")
QUERY = {
    "base1-4": "Charizard Base Set Holo #4", "base1-2": "Blastoise Base Set Holo #2", "base1-15": "Venusaur Base Set Holo #15",
    "base1-10": "Mewtwo Base Set Holo #10", "base1-3": "Chansey Base Set Holo #3", "base1-1": "Alakazam Base Set Holo #1",
    "base1-8": "Machamp Base Set Holo #8", "base1-58": "Pikachu Base Set #58", "base2-11": "Snorlax Jungle Holo #11",
    "base3-5": "Gengar Fossil Holo #5", "base3-4": "Dragonite Fossil Holo #4", "base5-4": "Dark Charizard Team Rocket Holo #4",
    "neo1-9": "Lugia Neo Genesis Holo #9", "neo3-14": "Suicune Neo Revelation Holo #14", "gym2-1": "Blaine's Arcanine Gym Challenge #1",
    "gym2-13": "Misty's Gyarados Gym Challenge #13", "sv03.5-199": "Charizard Ex 151 #199", "sv03.5-205": "Mew Ex 151 #205",
    "sv04.5-232": "Mew Ex Paldean Fates #232", "swsh7-215": "Umbreon Vmax Evolving Skies #215", "svp-085": "Pikachu Grey Felt Hat #085",
    "me02-125": "Mega Charizard X Ex Phantasmal Flames #125", "sv03.5-168": "Charmander 151 #168",
    "ja:sv2a-201": "Charizard Ex 151 Japanese #201", "ja:sv2a-208": "Mew Ex 151 Japanese #208", "ja:sv2a-168": "Charmander 151 Japanese #168",
    "ja:sv4a-347": "Mew Ex Shiny Treasure Japanese #347", "ja:m2-110": "Mega Charizard X Ex Inferno X Japanese #110",
    "ja:s6a-095": "Umbreon Vmax Eevee Heroes Japanese #095",
}
READ = """() => [...document.querySelectorAll('[data-testid^="grade-"]')].map(g => {
  let el = g; for (let i = 0; i < 10 && el; i++) { el = el.parentElement; if (/Sold/.test(el.innerText) && /\\$/.test(el.innerText)) break; }
  const t = s => { const x = el.querySelector(`[data-testid^="${s}"]`); return x ? x.innerText.trim() : null; };
  const lines = el.innerText.split('\\n').map(s => s.trim()).filter(Boolean);
  const imgs = [...el.querySelectorAll('img')].map(i => i.src), links = [...el.querySelectorAll('a')].map(a => a.href);
  return {head: t('year-brand-variety'), subject: t('subject-card-number'), grade: t('grade'), price: t('sold-price'),
          kind: lines[lines.indexOf(t('sold-price')) + 1] || null, date: lines[lines.length - 1],
          item: (links.find(h => /\\/itm\\//.test(h)) || '').split('/itm/')[1]?.split('/')[0] || null,
          image: imgs[0] || null, logo: (imgs.find(s => /auction-house-logos/.test(s)) || '').split('/').pop().split('?')[0],
          external: links.find(h => !/alt\\.xyz/.test(h)) || null};
})"""


def source_of(r):
    m = re.search(r"/external/([a-z_]+)/", r.get("image") or "")
    s = m.group(1) if m else ""
    logo = (r.get("logo") or "").lower()
    if s.startswith("ebay") or "ebay" in logo:
        return "ebay"
    if s.startswith("pwcc") or "fanatics" in logo:
        return "fanatics"
    if "goldin" in s or "goldin" in logo:
        return "goldin"
    if "heritage" in s or "heritage" in logo:
        return "heritage"
    if not m and "/public/" not in (r.get("image") or ""):
        return "alt"
    return s or logo.split(".")[0] or "alt"


def ebay_id(r):
    m = re.search(r"/external/ebay[^/]*/(?:[^/]+/)*?(\d{9,})\.", r.get("image") or "") or re.search(r"/itm/(\d{9,})", r.get("external") or "")
    return m.group(1) if m else None


def _load(path, default):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return default


def main():
    from playwright.sync_api import sync_playwright   # imported here: other scripts read QUERY without Playwright
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_dir = args[0] if args else "data/raw/alt"
    opt = {a.split("=")[0]: a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
    cards = opt.get("--cards", ",".join(QUERY)).split(",")
    grades = [int(g) for g in opt.get("--grades", "10,9,8,7").split(",")]
    os.makedirs(out_dir, exist_ok=True)
    all_path = os.path.join(out_dir, "alt_sold.json")
    try:
        seen = json.load(open(all_path))
    except (OSError, ValueError):
        seen = {}
    today, got, new = date.today().isoformat(), [], 0
    day_path = os.path.join(out_dir, f"{today}.json")
    try:                                              # a run stopped halfway resumes: done searches are skipped
        got = json.load(open(day_path))
    except (OSError, ValueError):
        got = []
    done = {(r["query_card"], r["query_grade"]) for r in got} | {tuple(x) for x in _load(os.path.join(out_dir, f"done_{today}.json"), [])}
    pages = _load(os.path.join(out_dir, f"pages_{today}.json"), 0)   # the daily cap counts every run of the day

    def save():
        json.dump(got, open(day_path, "w"), ensure_ascii=False)
        json.dump(seen, open(all_path, "w"), ensure_ascii=False)
        json.dump(pages, open(os.path.join(out_dir, f"pages_{today}.json"), "w"))
        json.dump(sorted(done), open(os.path.join(out_dir, f"done_{today}.json"), "w"))
    with sync_playwright() as pw:
        kw = {"args": ["--headless=new"]}
        if os.path.exists(CHROME):
            kw["executable_path"] = CHROME
        if os.environ.get("HTTPS_PROXY"):
            kw["proxy"] = {"server": os.environ["HTTPS_PROXY"]}
        browser = pw.chromium.launch(**kw)
        page = browser.new_page(ignore_https_errors=True, viewport={"width": 1400, "height": 1000})
        for cid in cards:
            for g in grades:
                if pages >= MAX_PAGES:
                    break
                if (cid, g) in done:
                    continue
                q = f"{QUERY[cid]} PSA {g}"
                t0 = time.time()
                try:
                    page.goto(URL.format(q=quote(q)), wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(6000)
                    rows = page.evaluate(READ)
                except Exception as e:                       # one failed page never stops the run
                    print(f"  {cid} PSA {g}: errore {str(e)[:80]}")
                    rows = []
                pages += 1
                for r in rows:
                    if not r.get("item") or not r.get("price"):
                        continue
                    r.update(query_card=cid, query_grade=g, seen=today, source=source_of(r), ebay_id=ebay_id(r),
                             price_usd=float(r["price"].replace("$", "").replace(",", "")),
                             sold=datetime.strptime(r["date"], "%b %d, %Y").date().isoformat() if re.match(r"[A-Z][a-z]{2} \d", r["date"] or "") else None)
                    got.append(r)
                    if r["item"] not in seen:
                        seen[r["item"]] = r
                        new += 1
                done.add((cid, g))
                save()
                print(f"  {cid} PSA {g}: {len(rows)} vendite in pagina", flush=True)
                time.sleep(max(0, PAUSE_S - (time.time() - t0)))
        browser.close()
    save()
    print(f"{pages} pagine, {len(got)} righe lette, {new} vendite nuove, {len(seen)} in tutto -> {all_path}")


if __name__ == "__main__":
    main()
