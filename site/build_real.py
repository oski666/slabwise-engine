"""Build site/real.html from site/real.src.html and results/real/report.json (real sales, P14)."""
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(here, "..")
version = sys.argv[1] if len(sys.argv) > 1 else "LVM"
rep = json.load(open(os.path.join(root, "results", "real", "report.json")))
rep["version"] = version
names = {c["id"]: c["n"] for c in json.load(open(os.path.join(root, "prototype", "data", "cards.json")))}
src = open(os.path.join(here, "real.src.html")).read()
out = src.replace("__DATA__", json.dumps(rep, ensure_ascii=False, separators=(",", ":"))) \
         .replace("__NAMES__", json.dumps(names, ensure_ascii=False))
open(os.path.join(here, "real.html"), "w").write(out)
print(len(out))
