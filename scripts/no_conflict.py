"""Stop a bot commit that would save a broken file: conflict markers, or JSON that does not parse.

Usage: python scripts/no_conflict.py   (checks the staged files; exit 1 and names them if one is broken)
"""
import json
import subprocess
import sys

bad = []
for f in subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=AM"], capture_output=True, text=True).stdout.split():
    try:
        s = open(f, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        continue
    if any(line.startswith(("<<<<<<< ", ">>>>>>> ")) for line in s.splitlines()):
        bad.append(f + ": segni di conflitto")
    elif f.endswith(".json"):
        try:
            json.loads(s)
        except ValueError as e:
            bad.append(f"{f}: JSON non valido ({e})")
if bad:
    print("Non salvo, file rotti:", *bad, sep="\n  ")
    sys.exit(1)
