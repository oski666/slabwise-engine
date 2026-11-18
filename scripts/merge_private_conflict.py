"""18 Nov 2026 (D328): two jobs saving the private data at the same time (Occasioni's quarter of the tcgcharts
collection and the Japanese checks both rewrite data/raw/tcgcharts/sales.json) stopped the second push on a rebase
conflict and its collection was lost. Run inside the private data clone during a stopped rebase: a JSON list of
sales is merged as the union of both sides (same card, grade and sale id: the side being saved wins); any other
conflicted file takes the side being saved."""
import json
import subprocess
import sys


def show(stage, f):
    return subprocess.run(["git", "show", f":{stage}:{f}"], capture_output=True, text=True).stdout


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
        open(f, "w").write(json.dumps(list(rows.values()), ensure_ascii=False))
        print(f"{f}: unione di {len(a)} e {len(b)} righe -> {len(rows)}")
    else:
        open(f, "w").write(mine)
        print(f"{f}: tenuta la versione da salvare")
    subprocess.run(["git", "add", f], check=True)
sys.exit(0 if files else 1)
