// The contact messages (D129), for the owner only: same password as the studio (STUDIO_PASSWORD, user "slabwise").
// ?del=<key> deletes one message (a privacy request, or once answered).
export async function onRequest({request, env}) {
  const want = env.STUDIO_PASSWORD;
  const auth = request.headers.get("authorization") || "";
  let ok = false;
  try { ok = !!want && auth.startsWith("Basic ") && atob(auth.slice(6)) === `slabwise:${want}`; } catch { ok = false; }
  if (!ok) return new Response("Riservato", {status: 401, headers: {"www-authenticate": 'Basic realm="Slabwise studio", charset="UTF-8"'}});
  if (!env.REQUESTS) return new Response("KV non collegato", {status: 503});
  const url = new URL(request.url);
  const del = url.searchParams.get("del");
  if (del && del.startsWith("msg:")) {
    await env.REQUESTS.delete(del);
    return Response.redirect(new URL("/studio/messaggi", request.url).toString(), 303);
  }
  const items = [];
  let cursor;
  do {
    const page = await env.REQUESTS.list({prefix: "msg:", cursor});
    for (const k of page.keys) {
      const v = await env.REQUESTS.get(k.name, "json");
      if (v) items.push({key: k.name, ...v});
    }
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);
  items.sort((a, b) => (a.at < b.at ? 1 : -1));
  const esc = s => String(s || "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
  const rows = items.map(m => `<article style="border:1px solid #ddd;border-radius:12px;padding:12px;margin:10px 0">
    <div style="color:#666;font-size:13px">${esc(m.at)}${m.email ? ` · <a href="mailto:${esc(m.email)}">${esc(m.email)}</a>` : " · nessuna email"}
    · <a href="?del=${encodeURIComponent(m.key)}">cancella</a></div><p style="white-space:pre-wrap">${esc(m.msg)}</p></article>`).join("");
  return new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="robots" content="noindex"><title>Messaggi · Slabwise</title><body style="font:16px system-ui;max-width:760px;margin:24px auto;padding:0 16px">
    <h1>Messaggi (${items.length})</h1>${rows || "<p>Nessun messaggio.</p>"}</body>`, {headers: {"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}});
}
