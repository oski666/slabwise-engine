// Per-connection request limit kept in the memory of each Cloudflare isolate (D104): no storage, no cost.
// Approximate on purpose: it slows down bulk copying, it does not pretend to stop it.
const seen = new Map();
export async function limited(request, max, windowMs = 600000) {
  const ip = request.headers.get("cf-connecting-ip") || "";
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ip));
  const k = [...new Uint8Array(d)].slice(0, 10).join(".");
  const now = Date.now();
  const e = seen.get(k);
  if (!e || now - e.t > windowMs) { seen.set(k, {t: now, n: 1}); }
  else if (++e.n > max) return true;
  if (seen.size > 5000) seen.clear();
  return false;
}
export const json = (body, status = 200, extra = {}) => new Response(typeof body === "string" ? body : JSON.stringify(body), {
  status, headers: {"content-type": "application/json; charset=utf-8", "cache-control": "private, max-age=300", ...extra},
});
