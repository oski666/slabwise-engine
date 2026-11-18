"""18 Nov 2026 (D328): two jobs saving the private data at the same time (Occasioni's quarter of the tcgcharts
collection and the Japanese checks both rewrite data/raw/tcgcharts/sales.json) stopped the second push on a rebase
conflict and its collection was lost. Run inside the private data clone during a stopped rebase: a JSON list of
sales is merged as the union of both sides (same card, grade and sale id: the side being saved wins); any other
conflicted file takes the side being saved."""
import gzip
import json
import subprocess
import sys


def show(stage, f):
    b = subprocess.run(["git", "show", f":{stage}:{f}"], capture_output=True).stdout
    return (gzip.decompress(b) if f.endswith(".gz") else b).decode("utf-8")   # sales.json is kept gzipped (18 Nov)


files = subprocess.run(["git", "diff", "--name-only", "--diff-filter=U"], capture_output=True, text=True).stdout.split()
for f in files:
    mine, theirs = show(3, f), show(2, f)          # during a rebase: 3 = the commit being saved, 2 = upstream
    try:
        a, b = json.loads(theirs), json.loads(mine)
    except ValueError:
        a = b = None
    if isinstance(a, list) and isinstance(b, list) and all(isinstance(r, dict) and "sale_id" in r for r in a[:50] + b[:50]):
        key = lambda r: (r.get("card"), r.get("tc_grade"), str(r.get("sale_id")))  # noqa: E731
        rows = {key(r): r for r in a}
        rows.update({key(r): r for r in b})
        out = json.dumps(list(rows.values()), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        open(f, "wb").write(gzip.compress(out, 9, mtime=0) if f.endswith(".gz") else out)
        print(f"{f}: unione di {len(a)} e {len(b)} righe -> {len(rows)}")
    else:
        subprocess.run(["git", "checkout", "--theirs", "--", f], check=True)   # in a rebase "theirs" is the commit being saved
        print(f"{f}: tenuta la versione da salvare")
    subprocess.run(["git", "add", f], check=True)
sys.exit(0 if files else 1)
