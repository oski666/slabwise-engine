"""Illustrative charts from seed 1: a card through the crash, the fake flood, the era index."""
import json
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, ".")
from slabwise.backtest import run  # noqa: E402
from slabwise.model import LVMParams  # noqa: E402
from slabwise.sim import ERAS, SimConfig, simulate  # noqa: E402

params = LVMParams(**json.load(open("results/seed1_c15_A.json"))["params"])
m = simulate(SimConfig(seed=1))
res = run(m, "A", params)
lvm = "Slabwise LVM"
W = m.cfg.weeks
wk = np.arange(W)
z = 1.2816
show = ["tcgcharts (mediana a fasce)", "Card Ladder (ultima vendita × indice)", "Slabwise v0 (regole, tipo TCGBerg)"]
grey = ["#b9bccb", "#8d91a8", "#5f6380"]


def panel(ax, c, gi, title, lo=26, hi=W):
    sl = slice(lo, hi)
    t = m.value[c, gi]
    ax.plot(wk[sl], np.exp(t[sl]), color="#111", lw=2.2, label="Valore vero")
    for n, col in zip(show, grey):
        ax.plot(wk[sl], np.exp(res.est[n][sl, c, gi]), color=col, lw=1.2, label=n.split(" (")[0])
    e = res.est[lvm][sl, c, gi]
    s = res.sd[sl, c, gi]
    ax.fill_between(wk[sl], np.exp(e - z * s), np.exp(e + z * s), color="#6a54f0", alpha=0.15, lw=0)
    ax.plot(wk[sl], np.exp(e), color="#6a54f0", lw=2.2, label="Slabwise LVM (forchetta 80%)")
    sales = res.clean[(res.clean.card == c) & (res.clean.grade == [10, 9, 8, 7][gi]) & (res.clean.week >= lo)
                      & (res.clean.week < hi)]
    ax.scatter(sales.day / 7, sales.price, s=9, color="#e8322b", alpha=0.6, zorder=3, label="Vendite dopo il livello di identità")
    ax.set_title(title, fontsize=11)
    ax.set_yscale("log")
    ax.spines[["top", "right"]].set_visible(False)


e_sv = ERAS.index("sv")
cands = np.where((m.era == e_sv) & (m.rate[:, 0] > 0.25) & (m.rate[:, 0] < 1.0))[0]
cands = [c for c in cands if c != m.flood_card]
card = int(cands[0])
fig, axes = plt.subplots(3, 1, figsize=(9, 12))
panel(axes[0], card, 0, f"Carta dell'era Scarlatto e Violetto attraverso il crollo (settimane {m.cfg.crash_start}–{m.cfg.crash_start + m.cfg.crash_len})", 60, 140)
axes[0].axvspan(m.cfg.crash_start, m.cfg.crash_start + m.cfg.crash_len, color="#e8322b", alpha=0.07)
axes[0].legend(fontsize=7, frameon=False, ncol=2)
panel(axes[1], m.flood_card, 0, "Inondazione di 12 falsi \"PSA 10\" a ~30 $ (settimane 100–102)", 85, 115)
ax = axes[2]
for e, col in ((e_sv, "#6a54f0"), (ERAS.index("wotc"), "#0d8a58"), (ERAS.index("sm_swsh"), "#e8322b")):
    F_true = m.factor[e] - m.factor[e][26]
    F_est = np.array(res.model.F[e][1:]) - res.model.F[e][27]
    ax.plot(wk[26:], 100 * (np.exp(F_true[26:]) - 1), color=col, lw=2, label=f"{ERAS[e]} vero")
    ax.plot(wk[26:], 100 * (np.exp(F_est[26:]) - 1), color=col, lw=1.2, ls="--", label=f"{ERAS[e]} stimato")
ax.set_ylabel("Variazione dalla settimana 26 (%)")
ax.legend(fontsize=7, frameon=False, ncol=3)
ax.set_title("Fattore d'era interno del modello vs vero: attenuato, non ancora un indice pubblicabile", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("results/charts/examples.png", dpi=150)
print("card", card, "flood", m.flood_card)
