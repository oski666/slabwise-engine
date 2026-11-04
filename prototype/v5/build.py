"""Build prototype/v5/slabwise.html from src/ (app.html + style.css + slabby.js) and data/demo.json."""
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "src", "app.html")).read()
css = open(os.path.join(here, "src", "base.css")).read() + "\n" + open(os.path.join(here, "src", "promo.css")).read()
js = open(os.path.join(here, "src", "slabby.js")).read()
data = json.load(open(os.path.join(here, "..", "data", "demo.json")))
out = (src.replace("__STYLE__", css).replace("__SLABBY__", js)
       .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
open(os.path.join(here, "slabwise.html"), "w").write(out)
print("slabwise.html", len(out))
