// One card's history, sales used and sales set aside (D104). Files live in the deploy under /x/, unreachable directly.
import {limited, json} from "../../../lib/cf_limit.js";

export async function onRequestGet({request, params, env}) {
  if (await limited(request, 300)) return json({error: "limit"}, 429);
  let id = String(params.id || "");
  try { id = decodeURIComponent(id); } catch { return json({error: "bad_id"}, 400); }   // "ja%3Am2-110" arrives encoded
  if (!/^[A-Za-z0-9.:\/_-]{2,40}$/.test(id)) return json({error: "bad_id"}, 400);
  const url = new URL(`/x/cards/${id.replace(/[:\/]/g, "_")}.json`, request.url);
  const r = await env.ASSETS.fetch(url);
  return r.ok ? json(await r.text()) : json({error: "not_found"}, 404);
}
