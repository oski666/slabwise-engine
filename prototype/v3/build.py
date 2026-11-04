"""Build prototype/v3/slabwise.html from src/app.html and data/demo.json (run prototype/build_data.py first)."""
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "src", "app.html")).read()
data = json.load(open(os.path.join(here, "..", "data", "demo.json")))
out = src.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
open(os.path.join(here, "slabwise.html"), "w").write(out)
print("slabwise.html", len(out))
