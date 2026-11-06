"""Load a character package (prototype/character/<name>/character.json), the single source of the
character, and turn it into what the site needs: an inline SVG with one <symbol> per pose, and CSS
variables for its colours and font. Specification: README.md next to the character.json.

The simplest way to change the character: put PNG files named after the poses (smug.png,
bliss.png, laugh.png, drool.png, shock.png, sleep.png, peek.png) in the folder. A PNG with the
pose's name always wins over what character.json says for that pose. Otherwise a pose is drawn
inline ({"viewBox", "svg"}) or names an image file ({"image": "file.png"}; PNG, WebP or SVG).
Images are embedded as data URIs because the published page cannot load other addresses.
If Pillow is installed, transparent margins are trimmed and big images are scaled to 900 px high.
"""
import base64
import json
import os
import io
import re
import struct

POSES = ("smug", "bliss", "laugh", "drool", "shock", "sleep", "peek")
# optional poses for Slabby's antics (D44, D61): used when <pose>.png is in the folder, otherwise the site
# falls back to a required pose (see EXTRA_FALLBACK, the same table as in slabby.js)
EXTRA = ("run", "cling", "sit", "tongue", "wave", "peek_top", "peek_side", "teacher", "side")   # D201: side = the sidebar
EXTRA_FALLBACK = {"run": "laugh", "cling": "peek", "sit": "smug", "tongue": "laugh", "wave": "bliss",
                  "peek_top": "peek", "peek_side": "smug", "teacher": "smug", "side": "peek"}
COLORS = ("main", "accent", "gold", "ink", "bubble", "bubble_ink")
MIME = {".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


MAX_H = 600                                       # Slabby is drawn at most ~300 px tall: 600 covers 2x screens


def _png_bytes(path):
    """(bytes, mime): trimmed, scaled to MAX_H and saved as WebP when Pillow is available, so the page stays light
    whatever the size of the drawing (the PNGs of 2 November weighed 8 MB); the file is never modified."""
    raw = open(path, "rb").read()
    try:
        from PIL import Image
    except ImportError:
        return raw, "image/png"
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    im = _defringe(im)
    box = im.getchannel("A").getbbox()
    if box:
        im = im.crop(box)
    if im.size[1] > MAX_H:
        im = im.resize((round(im.size[0] * MAX_H / im.size[1]), MAX_H), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=86, method=6)
    _png_bytes.size = im.size
    return buf.getvalue(), "image/webp"


def _defringe(im):
    """Remove the light ring left around a figure cut out of a light background.
    1) In a band a few pixels wide along the transparent edge, light and greyish pixels (the old
       background or a white halo) become transparent; coloured or dark pixels stay.
    2) The remaining partly transparent edge pixels take the darker colour of their neighbourhood.
    Nothing happens when under 15% of the edge band is light: a figure with a dark outline and a few
    light details on the edge (e.g. Slabby's grey "z") is a real drawing, not a halo (a halo is ~30%)."""
    from PIL import Image, ImageFilter
    import numpy as np
    a = np.asarray(im).astype(np.int16)
    alpha = a[..., 3]
    clear = (alpha < 128).astype(np.uint8) * 255
    r = max(3, round(min(im.size) / 260)) | 1                     # band width scales with the image
    band = np.asarray(Image.fromarray(clear).filter(ImageFilter.MaxFilter(2 * r + 1))) > 0
    band &= alpha > 0
    rgb = a[..., :3]
    lum = rgb.mean(2)
    grey = (rgb.max(2) - rgb.min(2)) < 70
    light = band & grey & (lum > 150)
    if band.sum() == 0 or light.sum() < 0.15 * band.sum():
        return im
    alpha = np.where(light, 0, alpha)
    soft = (alpha > 0) & (alpha < 250)
    dark = np.asarray(im.convert("RGB").filter(ImageFilter.MinFilter(5))).astype(np.int16)
    a[..., :3] = np.where(soft[..., None], dark, rgb)
    a[..., 3] = alpha
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    out.putalpha(out.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6)))
    return out


def _png_size(data):
    w, h = struct.unpack(">II", data[16:24])
    return [str(w), str(h)]


def _image_size(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        txt = open(path, encoding="utf-8").read()
        vb = re.search(r'viewBox="([^"]+)"', txt)
        if vb:
            return vb.group(1).split()[2:4]
        w, h = re.search(r'width="([\d.]+)', txt), re.search(r'height="([\d.]+)', txt)
        return [w.group(1), h.group(1)] if w and h else ["200", "200"]
    from PIL import Image
    with Image.open(path) as im:
        return [str(im.size[0]), str(im.size[1])]


def load(folder):
    path = os.path.join(folder, "character.json")
    c = json.load(open(path, encoding="utf-8"))
    poses = dict(c.get("poses", {}))
    for p in POSES + EXTRA:                           # <pose>.png in the folder wins
        if os.path.exists(os.path.join(folder, p + ".png")):
            poses[p] = {"image": p + ".png"}
    c["poses"] = poses
    problems = [f"manca la posa '{p}' (aggiungi {p}.png nella cartella)" for p in POSES if p not in poses]
    problems += [f"manca il colore '{k}'" for k in COLORS if k not in c.get("colors", {})]
    if problems:
        raise SystemExit(f"{path} non rispetta il formato del personaggio: " + "; ".join(problems))
    symbols = []
    for p in POSES + tuple(x for x in EXTRA if x in c["poses"]):
        pose = c["poses"][p]
        if "image" in pose:
            f = os.path.join(folder, pose["image"])
            ext = os.path.splitext(f)[1].lower()
            if ext not in MIME:
                raise SystemExit(f"posa '{p}': formato immagine non supportato ({ext})")
            if ext == ".png":
                data, mime = _png_bytes(f)
                w, h = [str(x) for x in _png_bytes.size] if mime == "image/webp" else _png_size(data)
            else:
                data, mime = open(f, "rb").read(), MIME[ext]
                w, h = _image_size(f)
            uri = f"data:{mime};base64," + base64.b64encode(data).decode()
            symbols.append(f'<symbol id="slabby-{p}" viewBox="0 0 {w} {h}"><image href="{uri}" width="{w}" height="{h}"/></symbol>')
        else:
            symbols.append(f'<symbol id="slabby-{p}" viewBox="{pose["viewBox"]}">{pose["svg"]}</symbol>')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute" aria-hidden="true">'
           f'<defs>{c.get("defs", "")}</defs>' + "".join(symbols) + "</svg>")
    col = c["colors"]
    font = c.get("font", "")
    css = (":root{" + "".join(f"--sb-{k.replace('_', '-')}:{col[k]};" for k in COLORS)
           + (f'--sb-font:"{font}",var(--display);' if font else "--sb-font:var(--display);") + "}")
    return dict(name=c.get("name", "Slabby"), svg=svg, css=css, font=font)
