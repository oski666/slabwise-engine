"""Build prototype/v6/slabwise.html from src/ (app.html + base.css + trainer.css + slabby.js), the Slabby
character package (prototype/character/slabby/character.json) and data/demo.json."""
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "src", "app.html"), encoding="utf-8").read()
css = open(os.path.join(here, "src", "base.css"), encoding="utf-8").read() + "\n" + open(os.path.join(here, "src", "trainer.css"), encoding="utf-8").read()
js = open(os.path.join(here, "src", "slabby.js"), encoding="utf-8").read()
sys.path.insert(0, os.path.join(here, "..", "character"))
from load import load  # noqa: E402
char = load(os.path.join(here, "..", "character", "slabby"))      # character.json is the only source of Slabby
which = sys.argv[1] if len(sys.argv) > 1 else "real"          # "real" (default since D34) or "demo"
data = json.load(open(os.path.join(here, "..", "data", "real.json" if which == "real" else "demo.json"), encoding="utf-8"))
font_link = (f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={char["font"].replace(" ", "+")}&display=swap">'
             if char["font"] else "")
out = (src.replace("__CHAR_FONT__", font_link).replace("__STYLE__", css + "\n" + char["css"]).replace("__SLABBY_SVG__", char["svg"]).replace("__SLABBY__", js)
       .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
open(os.path.join(here, "slabwise.html"), "w", encoding="utf-8").write(out)
print("slabwise.html", len(out))
