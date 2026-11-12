"""D280: yen per dollar for every working day since July 2022, from the ECB reference rates (via frankfurter.app,
free, no key), into data/fx_jpy.json. Used only to turn Japanese marketplace prices (SNKRDUNK, Cardova) into dollars."""
import json
import sys
import urllib.request

out = sys.argv[1] if len(sys.argv) > 1 else "data/fx_jpy.json"
with urllib.request.urlopen("https://api.frankfurter.app/2022-07-01..?from=USD&to=JPY", timeout=60) as r:
    d = json.load(r)
rates = {day: v["JPY"] for day, v in sorted(d["rates"].items())}
json.dump({"source": "ECB via frankfurter.app", "base": "USD", "rates": rates}, open(out, "w"), separators=(",", ":"))
print(f"cambio yen: {len(rates)} giorni, ultimo {max(rates)} = {rates[max(rates)]}")
