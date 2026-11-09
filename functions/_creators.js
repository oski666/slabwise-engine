// D256: invite codes of the creators, as SHA-256 fingerprints (never the codes). More can be added without a commit in the
// Cloudflare Pages secret CREATOR_CODES (fingerprints separated by commas). Make one: printf %s CODE | sha256sum
export const CREATOR_HASHES = [
  "1de966678adc32663b3368dcb19c562fd7051f916ade35df769cc72d205bc893",   // test code of 9 Nov 2026 (Oscar)
];

export async function sha256(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}

export function knownHashes(env) {
  return new Set([...CREATOR_HASHES, ...String(env.CREATOR_CODES || "").split(",").map(s => s.trim().toLowerCase()).filter(Boolean)]);
}

const cookie = (request, name) => (request.headers.get("cookie") || "").split(/;\s*/).map(c => c.split("=")).find(([k]) => k === name)?.[1];

// who may use the studio: a creator with a valid code (cookie) or the owner (STUDIO_PASSWORD, as before, D126)
export async function studioAccess(request, env) {
  const h = cookie(request, "sw_creator");
  if (h && knownHashes(env).has(h)) return "creator";
  const want = env.STUDIO_PASSWORD;
  if (!want) return "owner";
  const auth = request.headers.get("authorization") || "";
  try { if (auth.startsWith("Basic ") && atob(auth.slice(6)) === `slabwise:${want}`) return "owner"; } catch { /* no */ }
  return null;
}

export const ASK = () => new Response("Studio riservato", {status: 401, headers: {"www-authenticate": 'Basic realm="Slabwise studio", charset="UTF-8"', "cache-control": "no-store"}});
