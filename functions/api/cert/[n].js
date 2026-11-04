// The history of one PSA cert (D63, D104), read from the bucket of its last two digits.
import {limited, json} from "../../../lib/cf_limit.js";

export async function onRequestGet({request, params, env}) {
  if (await limited(request, 60)) return json({error: "limit"}, 429);
  const n = String(params.n || "").replace(/\D/g, "");
  if (n.length < 5 || n.length > 12) return json({error: "bad_cert"}, 400);
  const r = await env.ASSETS.fetch(new URL(`/x/certs/${n.slice(-2)}.json`, request.url));
  if (!r.ok) return json({error: "not_found"}, 404);
  const b = await r.json();
  return b[n] ? json({cert: n, sales: b[n]}) : json({error: "not_found"}, 404);
}
