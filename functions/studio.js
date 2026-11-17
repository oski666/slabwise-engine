// The studio (reel studio and the weekly scripts, D126; from D256 also for the creators with an invite code). The page
// lives under /x/ (not reachable directly, functions/x) and is served here. Who may enter: functions/_creators.js.
// /studio?invito=CODE: checks the code, stores the cookies on this device and opens the studio.
import {sha256, knownHashes, studioAccess, ASK} from "./_creators.js";

export async function onRequest({request, env}) {
  const url = new URL(request.url);
  const code = url.searchParams.get("invito");
  if (code) {
    const h = await sha256(code.trim());
    if (!knownHashes(env).has(h)) return new Response("Codice invito non valido", {status: 403, headers: {"cache-control": "no-store"}});
    const r = new Response(null, {status: 302, headers: {location: "/studio", "cache-control": "no-store"}});
    r.headers.append("set-cookie", `sw_creator=${h}; Path=/; Max-Age=31536000; Secure; HttpOnly; SameSite=Lax`);
    r.headers.append("set-cookie", "sw_creator_ui=1; Path=/; Max-Age=31536000; Secure; SameSite=Lax");
    return r;
  }
  const who = await studioAccess(request, env);
  if (!who) return ASK();
  const page = await env.ASSETS.fetch(new URL("/x/studio", request.url));
  const out = new Response(page.body, {status: page.status, headers: {"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}});
  if (who === "owner") out.headers.append("set-cookie", "sw_staff=1; Path=/; Max-Age=2592000; Secure; SameSite=Lax");
  return out;
}
