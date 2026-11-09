// Audit of the rendered card pages (D242): every sentence the page writes must agree with the numbers it shows.
// The data checks (scripts/coherence_check.py, D211) look at the data; this looks at what a reader actually sees,
// in Italian, on every card and every grade with a value.
// Usage: node scripts/page_audit.js <site folder or https url> <report.json> [max cards]
// With a folder (the build), the pages are served locally and /api/card/<id> is answered from x/cards/ like the
// Cloudflare function does.
// Exit code 0 always; the report lists each rule with its cases. The build posts the summary (sito.yml).
// Rules:
//   P1 era: the sentence on the card against its era says the direction of both (no "corre/sale" when the card falls)
//   P2 same period, same number: the 90-day change tile and the "in 3 mesi" sentences agree (within 1 point)
//   P3 SlabRange: the numbers in the sentence are the ends of the bar, and the Slabprice is between them
//   P4 how often: "ogni N giorni" agrees with the 90-day sales tile (N = 91 / sales)
//   P5 confidence: "Affidabilità alta" only with >= 3 sales in 13 weeks
//   P6 Gem Rate: the same percentage everywhere on the page
//   P7 market cap: the tile is the Slabprice times the PSA population of the grade (within 3%)
//   P8 broken text: no NaN, undefined, null, Infinity, "+-", "−-" anywhere on the page
const {chromium} = require("playwright");
const fs = require("fs");
const http = require("http");
const path = require("path");

const [where, out, maxArg] = process.argv.slice(2);
const TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".webp": "image/webp",
               ".png": "image/png", ".svg": "image/svg+xml", ".jpg": "image/jpeg"};
function serve(dir) {
  return new Promise(ok => {
    const srv = http.createServer((req, res) => {
      let u = decodeURIComponent(req.url.split("?")[0]);
      const m = u.match(/^\/api\/card\/(.+)$/);
      if (m) u = "/x/cards/" + m[1].replace(/[:\/]/g, "_") + ".json";
      else if (u.startsWith("/api/")) { res.writeHead(404); return res.end("{}"); }
      if (u.endsWith("/")) u += "index.html";
      const f = path.join(dir, path.normalize(u));
      if (!f.startsWith(path.resolve(dir)) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
      res.writeHead(200, {"content-type": TYPES[path.extname(f)] || "application/octet-stream"});
      fs.createReadStream(f).pipe(res);
    });
    srv.listen(0, "127.0.0.1", () => ok(srv));
  });
}
const num = s => { // "$3.639" "−10,1%" "1.420" "$5,2 mln" -> number
  if (s == null) return null;
  let t = String(s).replace(/\s/g, "").replace("−", "-").replace(/[$€%]/g, "");
  let k = 1;
  if (/mln$/.test(t)) { k = 1e6; t = t.replace(/mln$/, ""); } else if (/mila$/.test(t)) { k = 1e3; t = t.replace(/mila$/, ""); }
  t = t.replace(/\./g, "").replace(",", ".");
  const v = parseFloat(t);
  return Number.isFinite(v) ? v * k : null;
};

(async () => {
  let url = where, srv = null;
  if (!/^https?:/.test(where)) { srv = await serve(path.resolve(where)); url = `http://127.0.0.1:${srv.address().port}/`; }
  const b = await chromium.launch();
  const ctx = await b.newContext({locale: "it-IT", viewport: {width: 1300, height: 900}});
  const p = await ctx.newPage();
  await p.goto(url, {waitUntil: "networkidle"});
  await p.evaluate(() => { try { localStorage.setItem("sw-lang", "it"); } catch (e) {} });
  await p.reload({waitUntil: "networkidle"});
  const ids = await p.evaluate(() => D.cards.map(c => [c.id, c.grades.filter(g => g.value).map(g => g.grade)]));
  const todo = ids.slice(0, maxArg ? +maxArg : ids.length);
  const rep = {};
  const add = (k, v) => (rep[k] = rep[k] || []).push(v);
  for (const [id, grades] of todo) {
    await p.evaluate(id => { location.hash = "c-" + id; }, id);
    await p.waitForFunction(id => { const c = cardById[id]; return (!c.lazy || c._full || c._err) && document.querySelector(".cardpage"); }, id, {timeout: 15000}).catch(() => {});
    for (const gr of grades) {
      const text = await p.evaluate(gr => { S.cg = gr; route(); const el = document.querySelector(".cardpage"); return el ? el.innerText : ""; }, gr);
      if (!text) { add("P0", [id, gr, "page not rendered"]); continue; }
      const key = [id, gr];
      const lines = text.split("\n").map(s => s.trim()).filter(Boolean);
      // P8
      const bad = text.match(/\bNaN\b|\bundefined\b|\bnull\b|Infinity|\+-|−-/);
      if (bad) add("P8", [...key, bad[0]]);
      // P1
      for (const l of lines) {
        const m = l.match(/^(.*?):\s*([+−-]?[\d.,]+%) in 3 mesi(?:, la sua era| contro) ([+−-]?[\d.,]+%)/);
        if (!m) continue;
        const a = num(m[2]) / 100, e = num(m[3]) / 100, w = m[1].toLowerCase(), d = a - e;
        const wrong = /corre/.test(w) ||                                             // the old wording (9 Nov 2026)
          (w.startsWith("sale") && a < 0.01) || (w.startsWith("scende") && a > -0.01) || (w.startsWith("ferma") && Math.abs(a) >= 0.01) ||
          (w.startsWith("si muove") && Math.abs(d) > 0.031) ||
          (/^sale più|^scende meno/.test(w) && d <= 0) || (/^sale meno|^scende più/.test(w) && d >= 0) ||
          (/era sale/.test(w) && e <= 0) || (/era scende/.test(w) && e >= 0) || (/è ferma/.test(w) && Math.abs(e) >= 0.01);
        if (wrong) add("P1", [...key, l]);
      }
      // P2
      const i90 = lines.indexOf("90 GIORNI");
      const t90 = i90 >= 0 ? num(lines[i90 + 1]) : null;
      for (const l of lines) {
        const m = l.match(/([+−-]?[\d.,]+%) in 3 mesi/);
        if (m && t90 != null && Math.abs(num(m[1]) - t90) > 1) add("P2", [...key, `tile ${t90}% vs "${l}"`]);
      }
      // P3
      const m3 = text.match(/finiscono tra \$([\d.]+) e \$([\d.]+): è lo SlabRange/);
      const iv = lines.findIndex(l => l === "Quanto vale?");
      const val = iv >= 0 ? num(lines[iv + 1]) : null;
      if (m3 && val != null) {
        const lo = num(m3[1]), hi = num(m3[2]);
        const ib = lines.indexOf("8 vendite su 10 finiscono nello SlabRange");
        const blo = ib > 0 ? num(lines[ib - 1]) : null, bhi = ib > 0 ? num(lines[ib + 1]) : null;
        if (!(lo <= val && val <= hi)) add("P3", [...key, `Slabprice ${val} outside ${lo}–${hi}`]);
        if (blo != null && (blo !== lo || bhi !== hi)) add("P3", [...key, `bar ${blo}–${bhi} vs sentence ${lo}–${hi}`]);
      }
      // P4
      const is = lines.indexOf("VENDITE 90 GG");
      const s90 = is >= 0 ? num(lines[is + 1]) : null;
      const m4 = text.match(/una copia in PSA (\d+) ogni (\d+) giorni in media/);
      if (m4 && +m4[1] === gr && s90) {
        const exp = Math.round(91 / s90);
        if (Math.abs(+m4[2] - exp) > 1) add("P4", [...key, `ogni ${m4[2]} giorni vs ${s90} vendite in 90 giorni`]);
      }
      if (/quasi ogni giorno/.test(text) && s90 != null && s90 < 50) add("P4", [...key, `quasi ogni giorno con ${s90} vendite`]);
      // P5
      if (/AFFIDABILITÀ ALTA/.test(text) && s90 != null && s90 < 3) add("P5", [...key, `alta con ${s90} vendite in 90 giorni`]);
      // P6
      const gems = [...text.matchAll(/(?:Gem Rate[^%\d]{0,40}?|solo il |Gem Rate )([\d]+,\d)%/g)].map(m => m[1]);
      if (new Set(gems).size > 1) add("P6", [...key, gems.join(" / ")]);
      // P7
      const ip = lines.indexOf("POP PSA"), im = lines.findIndex(l => /^MARKET CAP( PSA \d+)?$/.test(l));
      if (ip >= 0 && im >= 0 && val) {
        const pop = num(lines[ip + 1]), cap = num(lines[im + 1]);
        const tol = (/mln/.test(lines[im + 1]) ? 0.05e6 : /mila/.test(lines[im + 1]) ? 50 : 0) + 0.5 * pop;   // the tile and the price are rounded
        if (pop && cap && Math.abs(cap - val * pop) > tol + 0.03 * val * pop) add("P7", [...key, `cap ${lines[im + 1]} vs ${val} × ${pop}`]);
      }
    }
  }
  await b.close();
  if (srv) srv.close();
  const summary = Object.fromEntries(Object.entries(rep).map(([k, v]) => [k, v.length]));
  fs.writeFileSync(out, JSON.stringify({checked: todo.length, summary, cases: rep}, null, 1));
  for (const k of ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]) {
    const v = rep[k] || [];
    console.log(`${k}: ${v.length}${v.length ? "  es. " + JSON.stringify(v.slice(0, 4)) : ""}`);
  }
})();
