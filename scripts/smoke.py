"""Daily check of the published site (D110): every page on a phone and a desktop screen.

Usage: python scripts/smoke.py [https://slabwise.pages.dev/]   (exit code 1 when something is wrong)

For each page: JavaScript errors, broken or missing images, page wider than the screen, data that never loads,
"NaN"/"undefined" in the text, failed requests; on every page each grade button and filter is tapped once
and the page is checked again (an element wider than the screen moves and zooms the whole page on a phone); plus the APIs (/api/card, /api/richieste) and that the data
files are not reachable directly.
"""
import json
import os
import sys
import urllib.request

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://slabwise.pages.dev/"
problems = []
TAPS = ["[data-cg]", "[data-g]", "[data-band]", "[data-sort]", "[data-l]", "[data-fmt]", "[data-min]", "[data-off]"]
# an element that sticks out on the right of the screen, outside any box of its own that scrolls or clips it
# (the page-wide clip on main only hides the problem: the text is cut off and phones zoom out)
CHECK = """() => { const W = document.documentElement.clientWidth; let worst = null;
  for (const el of document.querySelectorAll('#app *')) {
    const r = el.getBoundingClientRect(); if (r.width === 0 || r.right <= W + 2) continue;
    let a = el.parentElement, inside = false;
    while (a && a !== document.body) { const o = getComputedStyle(a).overflowX;
      if (o !== 'visible' && a.tagName !== 'MAIN' && a.id !== 'app') { inside = true; break; } a = a.parentElement; }
    if (!inside && (!worst || r.right > worst[1])) worst = [el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : ''), Math.round(r.right)];
  }
  return {over: worst ? worst[0] + ' fino a ' + worst[1] + 'px su ' + W : false}; }"""


def status(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "slabwise-smoke"}), timeout=30).status
    except urllib.error.HTTPError as e:
        return e.code


with sync_playwright() as pw:
    kw = {"proxy": {"server": os.environ["HTTPS_PROXY"]}} if os.environ.get("HTTPS_PROXY") else {}
    b = pw.chromium.launch(**kw)
    for vw, vh, tag in [(390, 844, "telefono"), (1300, 900, "computer")]:
        p = b.new_page(viewport={"width": vw, "height": vh}, ignore_https_errors=True)
        errs, bad = [], []
        p.on("pageerror", lambda e: errs.append(str(e)[:120]))
        p.on("response", lambda r: bad.append(f"{r.status} {r.url[:90]}") if r.status >= 400 and "favicon" not in r.url else None)
        p.goto(BASE + "#mercato")
        p.wait_for_timeout(3000)
        # 14 Nov: with 1,000+ cards every page no longer fits in 30 minutes: the 15 most valuable, the 15 most traded,
        # 10 Japanese and 10 more spread over the catalogue, different every day
        ids = p.evaluate("""() => { const c = D.cards, v = x => Math.max(0, ...x.grades.map(g => g.value || 0)), n = x => x.n_sales || 0;
          const pick = new Set([...c].sort((a, b) => v(b) - v(a)).slice(0, 15).concat([...c].sort((a, b) => n(b) - n(a)).slice(0, 15),
            c.filter(x => x.lang === 'ja').slice(0, 10)).map(x => x.id));
          const day = Math.floor(Date.now() / 864e5); for (let k = 0; k < 10; k++) pick.add(c[(day * 37 + k * Math.floor(c.length / 10)) % c.length].id);
          return [...pick]; }""")
        idx = p.evaluate("(D.rollups||[]).map(r=>'#indice-'+encodeURIComponent(r.series)).concat(D.index_all?['#indice-tutto']:[], Object.keys(D.index_sets||{}).map(k=>'#indice-'+encodeURIComponent('set:'+k)))")
        # "Le mie carte" (D131) checked full: three followed cards, one long Japanese name, one card no longer listed
        p.evaluate("""() => { const c=D.cards, w={}; [c[0], c[c.length-1], c.find(x=>x.lang==='ja')||c[1]].forEach(x=>{ const g=x.grades[x.grades.length-1]; w[x.id+'|'+g.grade]={v:g.value||null,d:'2026-10-01'}; });
          w['xx-gone|10']={v:5,d:'2026-10-01'}; localStorage.setItem('sw-watch', JSON.stringify(w)); }""")
        for r in ["#mercato", "#deal", "#metodo", "#richieste", "#privacy", "#termini", "#contatti", "#mie"] + idx + ["#indici-voto"] + ["#c-" + i for i in ids]:
            errs.clear()
            p.goto(BASE + r)
            p.wait_for_timeout(1800)
            i = p.evaluate(CHECK)
            for sel in TAPS:
                for k in range(min(4, p.locator(sel).count())):   # 14 Nov: the first 4 of each kind (the market page has hundreds)
                    try:
                        p.locator(sel).nth(k).click(timeout=1500)
                    except Exception:
                        continue
                    p.wait_for_timeout(250)
                    j = p.evaluate(CHECK)
                    if j["over"] and not i["over"]:
                        i["over"] = f"dopo il tocco su {sel} n.{k + 1}: {j['over']}"
            i0 = p.evaluate("""() => { const im=[...document.querySelectorAll('#app img')];
              const t=document.querySelector('#app').innerText;
              return {broken: im.filter(x=>x.complete&&x.naturalWidth===0).length,
                      loading: /Carico i dati|Loading data/.test(t), fail: /Non riesco|can't load/.test(t), nan: /\\bNaN\\b|\\bundefined\\b/.test(t)}; }""")
            i.update({k: v for k, v in i0.items() if v})
            what = [k if v is True or isinstance(v, int) else f"{k} ({v})" for k, v in i.items() if v] + (["errori JS: " + "; ".join(errs)] if errs else [])
            if what:
                problems.append(f"{tag} {r}: {', '.join(what)}")
        problems += [f"{tag} richiesta fallita: {x}" for x in sorted(set(bad))]
        p.close()
    b.close()
if status(BASE + "api/card/swsh7-215") != 200:
    problems.append("API /api/card non risponde")
if status(BASE + "api/richieste") != 200:
    problems.append("API /api/richieste non risponde")
if status(BASE + "x/studio") != 404:
    problems.append("lo studio è raggiungibile senza passare dalla sua pagina")
if status(BASE + "x/cards/swsh7-215.json") != 404:
    problems.append("i file dei dati sono raggiungibili direttamente")
print("\n".join(problems) if problems else "tutto in ordine")
sys.exit(1 if problems else 0)
