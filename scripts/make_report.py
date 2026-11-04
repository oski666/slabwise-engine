"""Aggregate results/*.json into results/REPORT.md, results/summary.json and charts."""
import glob
import json
import os
from collections import defaultdict

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LVM = "Slabwise LVM"
R = "results"
allruns = [json.load(open(f)) for f in sorted(glob.glob(f"{R}/seed*.json"))]
runs = [r for r in allruns if r.get("scenario", "base") == "base"]
alt = [r for r in allruns if r.get("scenario") == "alt"]
base = [r for r in runs if r["mode"] == "A" and abs(r["contamination"] - 0.15) < 1e-9]
modeB = [r for r in runs if r["mode"] == "B"]
names = base[0]["names"]
comps = [n for n in names if n != LVM]
BUCKETS = ("alta", "media", "bassa", "rarissima")


def med(vals):
    return float(np.median(vals))


def agg(rs, key, sub=None):
    out = {}
    for n in names:
        v = [r[key][n] if sub is None else r[key][n][sub] for r in rs if key in r]
        out[n] = med(v) if v else float("nan")
    return out


S = {"seeds": [r["seed"] for r in base]}
S["EV"] = agg(base, "EV")
S["ES"] = agg(base, "ES")
S["RU"] = agg(base, "RU")
S["RC"] = agg(base, "RC")
S["FLOOD"] = agg(base, "FLOOD")
S["CO"] = agg(base, "CO")
S["EVb"] = {b: agg(base, "EV_bucket", b) for b in BUCKETS}
S["CA"] = med([r["CA"] for r in base])
S["CAb"] = {b: med([r["CA_bucket"][b] for r in base]) for b in BUCKETS}
S["DP"] = {n: med([r["DEALS"][n]["precision"] for r in base]) for n in names}
S["DR"] = {n: med([r["DEALS"][n]["recall"] for r in base]) for n in names}
S["DF"] = {n: med([r["DEALS"][n]["flagged"] for r in base]) for n in names}
S["params"] = [r["params"] for r in base]

rb = defaultdict(lambda: defaultdict(list))
for r in runs:
    if r["mode"] == "A" and r["seed"] in (1, 2, 3):
        for n in names:
            rb[r["contamination"]][n].append(r["EV"][n])
S["RB"] = {f"{c:.2f}": {n: med(v) for n, v in d.items()} for c, d in sorted(rb.items())}
if alt:
    S["ALT_EV"] = agg(alt, "EV")
    S["ALT_ES"] = agg(alt, "ES")
    S["ALT_CA"] = med([r["CA"] for r in alt])
    S["ALT_DP"] = {n: med([r["DEALS"][n]["precision"] for r in alt]) for n in names}
    S["ALT_EVb"] = {b: agg(alt, "EV_bucket", b) for b in BUCKETS}
if modeB:
    S["B_EV"] = agg(modeB, "EV")
    S["B_DP"] = {n: med([r["DEALS"][n]["precision"] for r in modeB]) for n in names}

best = min(comps, key=lambda n: S["EV"][n])
crit = []
crit.append(("S1", "EV totale ≥ 20% sotto il miglior concorrente",
             f"{S['EV'][LVM]:.4f} vs {S['EV'][best]:.4f} ({best}): {100 * (1 - S['EV'][LVM] / S['EV'][best]):.0f}% in meno",
             S["EV"][LVM] <= 0.8 * S["EV"][best]))
worse = [b for b in BUCKETS if S["EVb"][b][LVM] > min(S["EVb"][b][n] for n in comps)]
crit.append(("S2", "EV mai peggiore per fascia", "fasce peggiori: " + (", ".join(worse) or "nessuna"), not worse))
best_ru = min(comps, key=lambda n: S["RU"][n])
crit.append(("S3", "Rumore il più basso", f"{S['RU'][LVM]:.4f} vs {S['RU'][best_ru]:.4f} ({best_ru})",
             S["RU"][LVM] <= S["RU"][best_ru]))
crit.append(("S4", "Calibrazione 75–85%", f"{100 * S['CA']:.1f}%", 0.75 <= S["CA"] <= 0.85))
c35 = S["RB"].get("0.35", {}).get(LVM)
crit.append(("S5", "EV al 35% di contaminazione ≤ 1,5 × EV base",
             f"{c35:.4f} vs {S['EV'][LVM]:.4f}" if c35 else "n/d", bool(c35) and c35 <= 1.5 * S["EV"][LVM]))
crit.append(("S6", "Precisione deal ≥ 80%", f"{100 * S['DP'][LVM]:.0f}%", S["DP"][LVM] >= 0.80))
best_rc = min(comps, key=lambda n: S["RC"][n])
crit.append(("S7", "Errore post-crollo il più basso", f"{S['RC'][LVM]:.4f} vs {S['RC'][best_rc]:.4f} ({best_rc})",
             S["RC"][LVM] < S["RC"][best_rc]))
S["criteria"] = [dict(id=a, name=b, value=c, passed=bool(d)) for a, b, c, d in crit]
# I1 (protocol section 6): share of true era moves captured by the factor, median over eras and seeds
idx = [x for r in base for x in r.get("IDX", [])]
if idx:
    S["IDX"] = float(np.median(idx))
    S["criteria"].append(dict(id="I1", name="Indice d'era: quota dei movimenti veri catturata ≥ 0,80",
                              value=f"{S['IDX']:.2f}", passed=bool(S["IDX"] >= 0.80)))
json.dump(S, open(f"{R}/summary.json", "w"), indent=1, ensure_ascii=False)


def pct(x):
    return f"{100 * x:.1f}%"


L = []
L.append("# Report del backtest · fase S (mercato simulato)\n")
L.append(f"Semi: {S['seeds']} · contaminazione base 15% · modalità A (stesso livello di identità per tutti). "
         "Valori = mediana tra i semi. Errore = mediana di |log(stima/valore vero)|, circa uguale all'errore percentuale.\n")
L.append("> Risultati su dati simulati (P14): dicono quale formula è migliore a parità di condizioni note, "
         "non quanto sarà preciso il sito sui dati reali.\n")
L.append("## Criteri pre-registrati\n")
L.append("| # | Criterio | Risultato | Esito |\n|---|---|---|---|")
for c in S["criteria"]:
    L.append(f"| {c['id']} | {c['name']} | {c['value']} | {'✅' if c['passed'] else '❌'} |")
L.append("\n## Errore sul valore vero\n")
L.append("| Metodo | Totale | Alta | Media | Bassa | Rarissima | Vendita successiva | Rumore | Post-crollo | Inondazione falsi |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for n in names:
    L.append(f"| {n} | {pct(S['EV'][n])} | " + " | ".join(pct(S["EVb"][b][n]) for b in BUCKETS) +
             f" | {pct(S['ES'][n])} | {pct(S['RU'][n])} | {pct(S['RC'][n])} | {pct(S['FLOOD'][n])} |")
L.append("\nFasce di liquidità: alta ≥ 1 vendita/settimana, media ≥ 1/mese, bassa ≥ 1/trimestre, rarissima meno.\n")
L.append("## Forchetta all'80% (solo LVM)\n")
L.append("Copertura: " + pct(S["CA"]) + " · per fascia: " + ", ".join(f"{b} {pct(S['CAb'][b])}" for b in BUCKETS) + "\n")
L.append("## Deal\n")
L.append("| Metodo | Segnalati | Precisione | Richiamo |\n|---|---|---|---|")
for n in names:
    L.append(f"| {n} | {S['DF'][n]:.0f} | {pct(S['DP'][n])} | {pct(S['DR'][n])} |")
L.append("\nTutti i metodi hanno lo stesso controllo del cert sugli annunci. Concorrenti: segnalato se la stima è almeno 20% sopra il prezzo. "
         "LVM: probabilità di deal ≥ 0,80 (`docs/METHOD.md` §7).\n")
L.append("## Robustezza alla contaminazione (semi 1–3)\n")
L.append("| Contaminazione | " + " | ".join(names) + " |\n|---|" + "---|" * len(names))
for c, d in S["RB"].items():
    L.append(f"| {float(c) * 100:.0f}% | " + " | ".join(pct(d[n]) for n in names) + " |")
if modeB:
    L.append("\n## Modalità B (filiera completa: i concorrenti senza verifica del cert)\n")
    L.append("| Metodo | Errore totale | Precisione deal |\n|---|---|---|")
    for n in names:
        L.append(f"| {n} | {pct(S['B_EV'][n])} | {pct(S['B_DP'][n])} |")
if alt:
    L.append("\n## Scenario sfavorevole (modello fuori dalle sue ipotesi)\n")
    L.append("Picchi da evento sul 30% delle carte, rumore di vendita 0,13 invece di 0,09, 30% delle carte con l'era sbagliata. "
             f"Semi: {[r['seed'] for r in alt]}.\n")
    L.append("| Metodo | Errore totale | Rarissima | Vendita successiva | Precisione deal |\n|---|---|---|---|---|")
    for n in names:
        L.append(f"| {n} | {pct(S['ALT_EV'][n])} | {pct(S['ALT_EVb']['rarissima'][n])} | {pct(S['ALT_ES'][n])} | {pct(S['ALT_DP'][n])} |")
    L.append(f"\nCopertura della forchetta LVM: {pct(S['ALT_CA'])}\n")
L.append("\n## Parametri stimati (P7)\n")
for p in S["params"]:
    L.append(f"- q_L={p['q_L']}, q_d={p.get('q_d')}, σ_e={p['sigma_e']}, σ_q={p['sigma_q']}, τ_f={p['tau_f']}")
open(f"{R}/REPORT.md", "w").write("\n".join(L) + "\n")

# charts
os.makedirs(f"{R}/charts", exist_ok=True)
short = {n: n.split(" (")[0] for n in names}
col = {n: ("#6a54f0" if n == LVM else "#9aa0b8") for n in names}
fig, ax = plt.subplots(figsize=(8, 4))
x = np.arange(len(BUCKETS))
wd = 0.8 / len(names)
for i, n in enumerate(names):
    ax.bar(x + i * wd, [100 * S["EVb"][b][n] for b in BUCKETS], wd, label=short[n],
           color=col[n] if n == LVM else plt.cm.Greys(0.35 + 0.1 * i))
ax.set_xticks(x + wd * (len(names) - 1) / 2, ["Alta", "Media", "Bassa", "Rarissima"])
ax.set_ylabel("Errore mediano (%)")
ax.set_title("Errore sul valore vero per liquidità")
ax.legend(fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{R}/charts/ev_bucket.png", dpi=150)

fig, ax = plt.subplots(figsize=(7, 4))
cs = sorted(S["RB"])
for i, n in enumerate(names):
    ax.plot([100 * float(c) for c in cs], [100 * S["RB"][c][n] for c in cs], marker="o", label=short[n],
            color=col[n] if n == LVM else plt.cm.Greys(0.35 + 0.1 * i), lw=2.5 if n == LVM else 1.2)
ax.set_xlabel("Vendite contaminate (%)")
ax.set_ylabel("Errore mediano (%)")
ax.set_title("Robustezza alla contaminazione")
ax.legend(fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(f"{R}/charts/robustness.png", dpi=150)
print("\n".join(L[:14]))
