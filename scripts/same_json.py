"""D228 check: the given real.json files are identical, key by key. Prints every difference (at most 40)."""
import json
import sys

files = sys.argv[1:]
docs = [json.load(open(f)) for f in files]
diffs = []


def walk(a, b, path):
    if len(diffs) >= 40:
        return
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        diffs.append(f"{path}: tipo {type(a).__name__} / {type(b).__name__}")
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                diffs.append(f"{path}.{k}: presente solo in uno")
            else:
                walk(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: lunghezza {len(a)} / {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]")
    elif a != b:
        diffs.append(f"{path}: {str(a)[:80]} / {str(b)[:80]}")


for f, d in zip(files[1:], docs[1:]):
    diffs.clear()
    walk(docs[0], d, "")
    print(f"{files[0]} contro {f}: {'identici' if not diffs else f'{len(diffs)} differenze'}")
    for x in diffs:
        print("  ", x)
    if diffs:
        sys.exit(1)
