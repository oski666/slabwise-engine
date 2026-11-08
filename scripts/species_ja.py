"""D237: Japanese species names from PokeAPI (BSD-3) -> data/species_ja.json (Japanese name -> English name, lower case).

Usage: python scripts/species_ja.py <pokemon_species_names.csv> [commit]
Only names are kept; the PokeAPI sprites are not used (see docs/DATA_SOURCES.md).
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
en = {r["pokemon_species_id"]: r["name"].lower() for r in rows if r["local_language_id"] == "9"}
names = {}
for r in rows:
    if r["local_language_id"] in ("1", "11") and r["pokemon_species_id"] in en and r["name"].strip():
        names.setdefault(r["name"].strip(), en[r["pokemon_species_id"]])
out = {"_licence": "PokeAPI (github.com/PokeAPI/pokeapi), BSD-3-Clause, (c) 2013-2023 Paul Hallett and PokeAPI contributors. "
                   "Pokemon and Pokemon character names are trademarks of Nintendo.",
       "_source": "data/v2/csv/pokemon_species_names.csv" + (f" @ {sys.argv[2]}" if len(sys.argv) > 2 else ""),
       "names": dict(sorted(names.items()))}
json.dump(out, open(os.path.join(HERE, "..", "data", "species_ja.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(names), "nomi")
