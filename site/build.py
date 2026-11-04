"""Build site/engine.html from the template, results/summary.json and the example chart."""
import base64
import io
import json
import os

from PIL import Image

here = os.path.dirname(__file__)
src = open(os.path.join(here, "engine.src.html")).read()
S = json.load(open(os.path.join(here, "..", "results", "summary.json")))
keep = {k: S[k] for k in ("EV", "EVb", "RC", "FLOOD", "RB", "DP", "DR", "ALT_EV", "ALT_EVb", "ALT_DP", "criteria")}
im = Image.open(os.path.join(here, "..", "results", "charts", "examples.png"))
im = im.crop((0, 0, im.size[0], int(im.size[1] * 0.645)))
buf = io.BytesIO()
im.save(buf, "WEBP", quality=82)
uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
out = src.replace("__SUMMARY__", json.dumps(keep, ensure_ascii=False)).replace("__EXAMPLE__", uri)
open(os.path.join(here, "engine.html"), "w").write(out)
print(len(out))
