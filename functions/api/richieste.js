// Card requests from visitors (D97). Cloudflare Pages Function, KV binding REQUESTS.
// GET  /api/richieste          -> list of requested cards with counts
// POST /api/richieste {id, lang, name, set} -> +1 for that card
// No personal data: a hash of the connection plus today's date limits a connection to 10 requests a day; it expires in 24 h.

const ID = /^[A-Za-z0-9.]{2,24}-[A-Za-z0-9]{1,8}$/;
const LANGS = new Set(["en", "ja"]);
const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: {"content-type": "application/json; charset=utf-8", "cache-control": "no-store"},
});
const clean = (s, n) => String(s || "").replace(/[<>"'`]/g, "").slice(0, n);

export async function onRequestGet({env}) {
  if (!env.REQUESTS) return json({active: false, requests: []});
  const out = [];
  let cursor;
  do {
    const page = await env.REQUESTS.list({prefix: "req:", cursor});
    for (const k of page.keys) {
      const v = await env.REQUESTS.get(k.name, "json");
      if (v) out.push(v);
    }
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);
  out.sort((a, b) => b.n - a.n);
  return json({active: true, requests: out});
}

export async function onRequestPost({request, env}) {
  if (!env.REQUESTS) return json({ok: false, error: "inactive"}, 503);
  let body;
  try { body = await request.json(); } catch { return json({ok: false, error: "bad_json"}, 400); }
  const id = String(body.id || ""), lang = String(body.lang || "en");
  if (!ID.test(id) || !LANGS.has(lang)) return json({ok: false, error: "bad_card"}, 400);
  const day = new Date().toISOString().slice(0, 10);
  const ip = request.headers.get("cf-connecting-ip") || "";
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ip + "|" + day));
  const tag = "ip:" + [...new Uint8Array(digest)].slice(0, 12).map(b => b.toString(16).padStart(2, "0")).join("");
  const used = +(await env.REQUESTS.get(tag) || 0);
  if (used >= 10) return json({ok: false, error: "limit"}, 429);
  await env.REQUESTS.put(tag, String(used + 1), {expirationTtl: 86400});
  const key = `req:${lang}:${id}`;
  const old = await env.REQUESTS.get(key, "json");
  const now = new Date().toISOString();
  const rec = old ? {...old, n: old.n + 1, last: now}
    : {id, lang, name: clean(body.name, 80), set: clean(body.set, 80), n: 1, first: now, last: now};
  await env.REQUESTS.put(key, JSON.stringify(rec));
  return json({ok: true, n: rec.n});
}
