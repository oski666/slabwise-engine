// The studio (reel studio and the weekly scripts, D126) is for the owner only. The page lives under /x/ (not reachable
// directly, functions/x) and is served here after a password: Cloudflare Pages secret STUDIO_PASSWORD, user "slabwise".
// Once in, a cookie opens the weekly page of the site (#settimana). Without the secret the studio stays open as before.
export async function onRequest({request, env}) {
  const want = env.STUDIO_PASSWORD;
  if (want) {
    const auth = request.headers.get("authorization") || "";
    let ok = false;
    try { ok = auth.startsWith("Basic ") && atob(auth.slice(6)) === `slabwise:${want}`; } catch { ok = false; }
    if (!ok) return new Response("Studio riservato", {status: 401, headers: {"www-authenticate": 'Basic realm="Slabwise studio", charset="UTF-8"', "cache-control": "no-store"}});
  }
  const page = await env.ASSETS.fetch(new URL("/x/studio", request.url));
  const out = new Response(page.body, {status: page.status, headers: {"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}});
  out.headers.append("set-cookie", "sw_staff=1; Path=/; Max-Age=2592000; Secure; SameSite=Lax");
  return out;
}
