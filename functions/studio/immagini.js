// Upload of the character images from the studio (D198), for the owner only: same password as the studio
// (STUDIO_PASSWORD, user "slabwise"; without it the page is closed). The file name says where the image goes:
// a Slabby pose, a Slab-Meter state or a reliability sticker. Each file is committed to GitHub with the contents API
// (Cloudflare secret GITHUB_UPLOAD_TOKEN: a fine-grained token for oski666/slabwise-engine only, "Contents: read and
// write"); the push starts the site build by itself (sito.yml, D199). Only PNG, at most 8 MB each.
const REPO = "oski666/slabwise-engine";
const TARGETS = {
  "prototype/character/slabby/": ["smug", "bliss", "laugh", "drool", "shock", "sleep", "peek", "run", "cling", "sit", "tongue", "wave",
                                   "peek_top", "peek_side", "teacher", "side"],
  "prototype/character/slabmeter/": ["hot", "warm", "cold", "esplode", "caldo", "tiepido", "freddo", "gelo"],
  "prototype/character/stickers/": ["fresche", "stimato", "poco_sicuro"],
};
const WHERE = {"prototype/character/slabby/": "Slabby", "prototype/character/slabmeter/": "Slab-Meter", "prototype/character/stickers/": "sticker"};
const MAX = 8 * 1024 * 1024;

const esc = s => String(s || "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const pathOf = name => {
  const base = String(name || "").toLowerCase().trim().replace(/\.png$/, "").replace(/[\s-]+/g, "_");
  for (const [dir, names] of Object.entries(TARGETS)) if (names.includes(base)) return dir + base + ".png";
  return null;
};

function authorized(request, env) {
  const want = env.STUDIO_PASSWORD, auth = request.headers.get("authorization") || "";
  try { return !!want && auth.startsWith("Basic ") && atob(auth.slice(6)) === `slabwise:${want}`; } catch { return false; }
}

async function gh(env, method, path, body) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/${path}`, {
    method, body: body ? JSON.stringify(body) : undefined,
    headers: {"authorization": `Bearer ${env.GITHUB_UPLOAD_TOKEN}`, "accept": "application/vnd.github+json", "user-agent": "slabwise-studio",
              "x-github-api-version": "2022-11-28", ...(body ? {"content-type": "application/json"} : {})}});
  return {status: r.status, data: r.status === 204 ? null : await r.json().catch(() => null)};
}

function b64(buf) {
  let s = "";
  const u = new Uint8Array(buf);
  for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode(...u.subarray(i, i + 0x8000));
  return btoa(s);
}

function page(result = "") {
  const list = Object.entries(TARGETS).map(([dir, names]) => `<p><b>${WHERE[dir]}</b>: ${names.map(n => `<code>${n}.png</code>`).join(" ")}</p>`).join("");
  return new Response(`<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Carica immagini · studio</title>
<style>body{font:16px/1.45 system-ui,sans-serif;max-width:760px;margin:0 auto;padding:24px 16px;color:#121214;background:#fff}
h1{font-size:26px}code{background:#f1f1f4;padding:1px 5px;border-radius:4px}
.drop{border:3px dashed #2257ff;border-radius:16px;padding:34px 16px;text-align:center;margin:18px 0;background:#f5f7ff}
button{font:700 16px system-ui;padding:10px 18px;border:2px solid #121214;border-radius:10px;background:#ffee33;cursor:pointer}
.ok{color:#0a7a3e}.ko{color:#c4005a}li{margin:4px 0}</style></head><body>
<h1>Carica immagini del sito</h1>
<p>Trascina qui le PNG (sfondo trasparente). Il nome del file decide dove vanno; un file con lo stesso nome sostituisce quello di prima. Dopo il caricamento il sito si ricostruisce da solo (circa 30 minuti).</p>
${list}
<form method="post" enctype="multipart/form-data"><label class="drop" style="display:block">Scegli o trascina i file<br><br><input type="file" name="f" accept="image/png" multiple required></label>
<button type="submit">Carica e aggiorna il sito</button></form>
${result}
<p style="margin-top:28px"><a href="/studio">← Studio</a> · <a href="/#pose">Vedi le pose sul sito</a></p></body></html>`,
    {headers: {"content-type": "text/html; charset=utf-8", "cache-control": "no-store"}});
}

export async function onRequest({request, env}) {
  if (!authorized(request, env))
    return new Response("Riservato", {status: 401, headers: {"www-authenticate": 'Basic realm="Slabwise studio", charset="UTF-8"'}});
  if (request.method !== "POST") return page();
  if (!env.GITHUB_UPLOAD_TOKEN) return page(`<p class="ko">Manca il segreto GITHUB_UPLOAD_TOKEN su Cloudflare: il caricamento non è ancora attivo.</p>`);
  const form = await request.formData();
  const out = [];
  let saved = 0;
  for (const f of form.getAll("f")) {
    if (!f || typeof f === "string") continue;
    const dest = pathOf(f.name);
    if (!dest) { out.push(`<li class="ko">${esc(f.name)}: nome non riconosciuto, non caricato</li>`); continue; }
    const buf = await f.arrayBuffer();
    const sig = new Uint8Array(buf.slice(0, 8));
    if (buf.byteLength > MAX || !(sig[0] === 0x89 && sig[1] === 0x50 && sig[2] === 0x4e && sig[3] === 0x47)) {
      out.push(`<li class="ko">${esc(f.name)}: non è una PNG o supera 8 MB</li>`); continue;
    }
    const cur = await gh(env, "GET", `contents/${dest}?ref=main`);
    const put = await gh(env, "PUT", `contents/${dest}`, {
      message: `Studio: ${WHERE[dest.slice(0, dest.lastIndexOf("/") + 1)]} ${dest.split("/").pop()} caricata da Oscar (D198)`,
      content: b64(buf), branch: "main", ...(cur.status === 200 && cur.data && cur.data.sha ? {sha: cur.data.sha} : {})});
    if (put.status === 200 || put.status === 201) { saved++; out.push(`<li class="ok">${esc(f.name)} → <code>${esc(dest)}</code> ${cur.status === 200 ? "(sostituita)" : "(nuova)"}</li>`); }
    else out.push(`<li class="ko">${esc(f.name)}: GitHub ha risposto ${put.status}</li>`);
  }
  const build = saved ? `<p class="ok">Il sito si ricostruisce da solo (parte con il salvataggio su GitHub, circa 30 minuti).</p>` : "";
  return page(`<h2>Risultato</h2><ul>${out.join("")}</ul>${build}`);
}
