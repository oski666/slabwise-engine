// Anonymous visitor counts (D133). D1 binding STATS. The browser sends only {k, id, g, d}:
// k "w" followed, "c" owned (d = +1 or -1), "v" card page opened (d = +1). No identifier is stored.
import {limited} from "../../lib/cf_limit.js";

const ok = (status = 204) => new Response(null, {status, headers: {"cache-control": "no-store"}});
const SCHEMA = [
  "CREATE TABLE IF NOT EXISTS owned (k TEXT NOT NULL, id TEXT NOT NULL, g INTEGER NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (k, id, g))",
  "CREATE TABLE IF NOT EXISTS views (day TEXT NOT NULL, id TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, id))",
];
let ready = false;

export async function onRequestPost({request, env}) {
  if (!env.STATS) return ok();                                   // not bound yet: the site works the same
  if (await limited(request, 120)) return ok(429);
  let body;
  try { body = await request.json(); } catch { return ok(400); }
  const ev = (Array.isArray(body.ev) ? body.ev : []).slice(0, 60).filter(e => e && ["w", "c", "v"].includes(e.k)
    && typeof e.id === "string" && /^[A-Za-z0-9:._-]{2,48}$/.test(e.id)
    && (e.k === "v" || (Number.isInteger(e.g) && e.g >= 1 && e.g <= 10 && (e.d === 1 || e.d === -1))));
  if (!ev.length) return ok(400);
  if (!ready) { await env.STATS.batch(SCHEMA.map(s => env.STATS.prepare(s))); ready = true; }
  const day = new Date().toISOString().slice(0, 10);
  await env.STATS.batch(ev.map(e => e.k === "v"
    ? env.STATS.prepare("INSERT INTO views (day, id, n) VALUES (?1, ?2, 1) ON CONFLICT (day, id) DO UPDATE SET n = n + 1").bind(day, e.id)
    : env.STATS.prepare("INSERT INTO owned (k, id, g, n) VALUES (?1, ?2, ?3, max(0, ?4)) ON CONFLICT (k, id, g) DO UPDATE SET n = max(0, n + ?4)").bind(e.k, e.id, e.g, e.d)));
  return ok();
}
