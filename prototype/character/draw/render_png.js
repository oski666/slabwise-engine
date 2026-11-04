// Render prototype/character/draw/svg/<pose>.svg to transparent PNGs in prototype/character/slabby/
// (the files the site picks up). Requires Playwright with Chromium.
const {chromium} = require("playwright");
const fs = require("fs"), path = require("path");
const here = __dirname, out = path.join(here, "..", "slabby");
(async () => {
  const exe = process.env.CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
  const b = await chromium.launch(fs.existsSync(exe) ? {executablePath: exe} : {});
  for (const f of fs.readdirSync(path.join(here, "svg")).filter(f => f.endsWith(".svg"))) {
    const svg = fs.readFileSync(path.join(here, "svg", f), "utf8");
    const vb = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
    const h = 900, w = Math.round(h * vb[2] / vb[3]);
    const p = await b.newPage({viewport: {width: w, height: h}});
    await p.setContent(`<html><body style="margin:0;background:transparent">${svg.replace("<svg ", `<svg width="${w}" height="${h}" `)}</body></html>`);
    await p.screenshot({path: path.join(out, f.replace(".svg", ".png")), omitBackground: true});
    await p.close();
    console.log("ok", f);
  }
  await b.close();
})();
