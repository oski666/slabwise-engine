// Anonymous visitor counts (D133), for the owner only: same password as the studio. Names from /x/names.json.
export async function onRequest({request, env}) {
  const want = env.STUDIO_PASSWORD, auth = request.headers.get("authorization") || "";
  let pass = false;
  try { pass = !!want && auth.startsWith("Basic ") && atob(auth.slice(6)) === `slabwise:${want}`; } catch { pass = false; }
  if (!pass) return new Response("Riservato", {status: 401, headers: {"www-authenticate": 'Basic realm="Slabwise studio", charset="UTF-8"'}});
  const page = body => new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="robots" content="noindex"><title>Statistiche · Slabwise</title><body style="font:16px system-ui;max-width:860px;margin:24px auto;padding:0 16px">
    <h1>Statistiche dei visitatori</h1>${body}</body>`, {headers: {"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}});
  if (!env.STATS) return page("<p>Il database <code>STATS</code> non è ancora collegato al sito (Cloudflare → Pages → slabwise → Impostazioni → Associazioni → D1).</p>");
  let names = {};
  try { const r = await env.ASSETS.fetch(new URL("/x/names.json", request.url)); if (r.ok) names = await r.json(); } catch { names = {}; }
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
  const nm = id => `<a href="/#c-${encodeURIComponent(id)}">${esc(names[id] || id)}</a>`;
  const q = async (sql, ...a) => { try { return (await env.STATS.prepare(sql).bind(...a).all()).results || []; } catch { return []; } };
  const since = d => new Date(Date.now() - d * 864e5).toISOString().slice(0, 10);
  const [w, c, wg, cg, v7, v30, tot] = await Promise.all([
    q("SELECT id, SUM(n) n FROM owned WHERE k='w' GROUP BY id HAVING n > 0 ORDER BY n DESC LIMIT 30"),
    q("SELECT id, SUM(n) n FROM owned WHERE k='c' GROUP BY id HAVING n > 0 ORDER BY n DESC LIMIT 30"),
    q("SELECT id, g, n FROM owned WHERE k='w' AND n > 0 ORDER BY n DESC LIMIT 30"),
    q("SELECT id, g, n FROM owned WHERE k='c' AND n > 0 ORDER BY n DESC LIMIT 30"),
    q("SELECT id, SUM(n) n FROM views WHERE day >= ?1 GROUP BY id ORDER BY n DESC LIMIT 30", since(7)),
    q("SELECT id, SUM(n) n FROM views WHERE day >= ?1 GROUP BY id ORDER BY n DESC LIMIT 30", since(30)),
    q("SELECT k, SUM(n) n FROM owned GROUP BY k UNION ALL SELECT 'v7', SUM(n) FROM views WHERE day >= ?1", since(7)),
  ]);
  const T = Object.fromEntries(tot.map(r => [r.k, r.n || 0]));
  const table = (title, rows, grade) => `<h2 style="margin-top:28px">${title}</h2>` + (rows.length
    ? `<table style="border-collapse:collapse;width:100%">${rows.map((r, i) => `<tr style="border-bottom:1px solid #eee"><td style="padding:6px 8px;color:#888">${i + 1}</td><td style="padding:6px 8px">${nm(r.id)}${grade ? ` · PSA ${r.g}` : ""}</td><td style="padding:6px 8px;text-align:right;font-weight:700">${r.n}</td></tr>`).join("")}</table>`
    : "<p style='color:#888'>Ancora niente.</p>");
  return page(`<p style="color:#666">Conteggi anonimi e indicativi (D133): nessun identificativo, si possono gonfiare, non entrano nei prezzi.
    Le visite al sito sono in Cloudflare → Web Analytics.</p>
    <p><b>${T.w || 0}</b> carte seguite in tutto · <b>${T.c || 0}</b> copie in collezione · <b>${T.v7 || 0}</b> schede aperte negli ultimi 7 giorni</p>
    ${table("Più seguite", w)}${table("Più possedute", c)}${table("Seguite, per voto", wg, true)}${table("Possedute, per voto", cg, true)}
    ${table("Schede più aperte, 7 giorni", v7)}${table("Schede più aperte, 30 giorni", v30)}
    <p style="margin-top:28px"><a href="/studio">Studio</a> · <a href="/studio/messaggi">Messaggi</a></p>`);
}
