// Contact form (D129). KV binding REQUESTS, keys "msg:<time>". A message keeps only its text and, if given, the
// email for the answer; it expires after 365 days. A hash of the connection plus the day limits sending to 5 a day.
const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: {"content-type": "application/json; charset=utf-8", "cache-control": "no-store"},
});

export async function onRequestPost({request, env}) {
  if (!env.REQUESTS) return json({ok: false, error: "inactive"}, 503);
  let body;
  try { body = await request.json(); } catch { return json({ok: false, error: "bad_json"}, 400); }
  const msg = String(body.msg || "").trim().slice(0, 2000);
  const email = String(body.email || "").trim().slice(0, 120);
  if (msg.length < 3) return json({ok: false, error: "empty"}, 400);
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ok: false, error: "bad_email"}, 400);
  const day = new Date().toISOString().slice(0, 10);
  const ip = request.headers.get("cf-connecting-ip") || "";
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("contact|" + ip + "|" + day));
  const tag = "cip:" + [...new Uint8Array(digest)].slice(0, 12).map(b => b.toString(16).padStart(2, "0")).join("");
  const used = +(await env.REQUESTS.get(tag) || 0);
  if (used >= 5) return json({ok: false, error: "limit"}, 429);
  await env.REQUESTS.put(tag, String(used + 1), {expirationTtl: 86400});
  const at = new Date().toISOString();
  await env.REQUESTS.put(`msg:${at}:${Math.random().toString(36).slice(2, 8)}`, JSON.stringify({at, msg, email}), {expirationTtl: 365 * 86400});
  return json({ok: true});
}
