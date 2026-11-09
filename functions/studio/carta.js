// D256: the content pack of one card for the creators (and the owner): /studio/carta#<card id>/<grade>.
import {studioAccess, ASK} from "../_creators.js";

export async function onRequest({request, env}) {
  if (!(await studioAccess(request, env))) return ASK();
  const page = await env.ASSETS.fetch(new URL("/x/carta", request.url));
  return new Response(page.body, {status: page.status, headers: {"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}});
}
