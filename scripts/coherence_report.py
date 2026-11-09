"""Coherence report after each build (D242): the data checks (coherence_check.py, D211) and the rendered-page audit
(page_audit.js) in one GitHub issue, "Controlli di coerenza", rewritten at every build; a comment (which notifies the
owner) only when a check other than C7 has cases.

Usage: GH_TOKEN=... python scripts/coherence_report.py results/coherence.json results/page_audit.json
"""
import json
import os
import subprocess
import sys

NAMES = {
    "C1": "Slabprice fuori dallo SlabRange (dati)", "C2": "vendite 90 giorni > vendite totali", "C3": "popolazioni impossibili",
    "C4": "Gem Rate in disaccordo non dichiarato", "C5": "Rubinetto incoerente", "C6": "era sbagliata", "C7": "voto più alto che vale meno (si mostra con la spiegazione)",
    "C8": "variazione su un voto senza vendite proprie", "C9": "Gemma nascosta non giustificata", "C10": "storia con un numero diverso dalla scheda",
    "P0": "scheda che non si apre", "P1": "frase sull'era che contraddice i numeri", "P2": "due numeri diversi per lo stesso periodo",
    "P3": "SlabRange scritto diverso da quello disegnato", "P4": "\"ogni N giorni\" diverso dalle vendite", "P5": "affidabilità alta con poche vendite",
    "P6": "Gem Rate diverso nella stessa pagina", "P7": "Market Cap diverso da prezzo × popolazione", "P8": "testo rotto (NaN, undefined…)",
}
QUIET = {"C7"}   # known and explained on the page (D206)


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def main():
    data, pages = load(sys.argv[1]), load(sys.argv[2])
    rows, alarm = [], []
    if data:
        checks = data.get("checks", {})
        for k in [f"C{i}" for i in range(1, 11)]:
            v = checks.get(k, {})
            rows.append((k, v.get("n", 0), (v.get("examples") or [])[:5]))
    if pages:
        for k in sorted(NAMES):
            if k.startswith("P"):
                ex = pages.get("cases", {}).get(k, [])
                rows.append((k, len(ex), ex[:5]))
    for k, n, _ in rows:
        if n and k not in QUIET:
            alarm.append(f"{k} ({n})")
    run = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    body = ["Riscritta a ogni ricostruzione del sito (D211, D242). Zero ovunque = nulla stona.",
            f"Schede controllate: {pages.get('checked') if pages else 'non eseguito'} · [corsa]({run})", "",
            "| Controllo | Cosa | Casi | Esempi |", "|---|---|---|---|"]
    for k, n, ex in rows:
        body.append(f"| {k} | {NAMES.get(k, k)} | {'**' + str(n) + '**' if n and k not in QUIET else n} | {json.dumps(ex, ensure_ascii=False)[:300] if n else ''} |")
    if not data:
        body.append("\nI controlli sui dati non hanno prodotto il rapporto.")
    if not pages:
        body.append("\nIl controllo delle schede non ha prodotto il rapporto.")
    text = "\n".join(body)
    print(text)
    if not os.environ.get("GH_TOKEN") or not os.environ.get("GITHUB_REPOSITORY"):
        return
    repo = os.environ["GITHUB_REPOSITORY"]
    title = "Controlli di coerenza"
    found = subprocess.run(["gh", "api", f"repos/{repo}/issues?state=open&per_page=100", "-q", f'.[] | select(.title=="{title}") | .number'],
                           capture_output=True, text=True).stdout.split()
    if found:
        num = found[0]
        subprocess.run(["gh", "api", "-X", "PATCH", f"repos/{repo}/issues/{num}", "-f", f"body={text}"], check=True, capture_output=True)
    else:
        num = subprocess.run(["gh", "api", f"repos/{repo}/issues", "-f", f"title={title}", "-f", f"body={text}", "-q", ".number"],
                             capture_output=True, text=True, check=True).stdout.strip()
    if alarm or not data or not pages:
        msg = "Qualcosa stona: " + ", ".join(alarm) if alarm else "Un controllo non è stato eseguito."
        subprocess.run(["gh", "api", f"repos/{repo}/issues/{num}/comments", "-f", f"body={msg} Dettagli nella descrizione. [corsa]({run})"],
                       check=True, capture_output=True)


if __name__ == "__main__":
    main()
