"""Published era index (v1.4, D38; specification in docs/METHOD.md section 4b).

A basket of liquid (card, grade) atoms per era, chosen every REBALANCE weeks from the past only:
atoms with at least MIN_SALES genuine sales (posterior > 0.5) in the previous REBALANCE weeks,
at most K per era, the most traded first. Equal weights. The index is chain-linked: each week it
moves by the mean change of the log fair values of the basket's atoms between this week and the
previous one, which keeps it continuous when the basket changes (the role of a divisor).
The estimation model is not changed by the index.
"""
from __future__ import annotations

import numpy as np

REBALANCE = 13
MIN_SALES = 6
K = 10
STRATA_MIN = 4                                   # D143: sales needed for a reserved grade seat


class EraIndex:
    def __init__(self, era, n_eras, start_week=26, rebalance=REBALANCE, min_sales=MIN_SALES, k=K, one_per_card=False, strata=0):
        self.era = np.asarray(era)
        self.E = n_eras
        self.start, self.reb, self.min_sales, self.k = start_week, rebalance, min_sales, k
        self.one_per_card = one_per_card                 # D130: each card enters once, with its most traded grade
        self.strata = strata                             # D143 (protocol §28): seats reserved for each grade
        self.basket = {e: [] for e in range(n_eras)}
        self.level = {e: [] for e in range(n_eras)}     # (week, log level); starts at 0 when an era gets a basket
        self.history = []                                # (week, era, basket) at each rebalance
        self.prev = None

    def _rebalance(self, w, lvm):
        counts = {}
        for c, (ob, f) in enumerate(zip(lvm.obs, lvm.fit)):
            if f is None:
                continue
            for o, pg in zip(ob, f["pgen"]):
                if w - self.reb < o["t"] <= w + 1 and pg > 0.5:
                    counts[(c, o["g"])] = counts.get((c, o["g"]), 0) + 1
        for e in range(self.E):
            atoms = [(n, a) for a, n in counts.items() if self.era[a[0]] == e and n >= self.min_sales]
            atoms.sort(key=lambda x: (-x[0], x[1]))
            if self.one_per_card:
                seen, uniq = set(), []
                for n, a in atoms:
                    if a[0] not in seen:
                        seen.add(a[0])
                        uniq.append((n, a))
                atoms = uniq
            if self.strata:
                low = [(n, a) for a, n in counts.items() if self.era[a[0]] == e and n >= STRATA_MIN]
                low.sort(key=lambda x: (-x[0], x[1]))
                pick = []
                for g in range(4):                       # grades 10, 9, 8, 7 (index 0..3)
                    pick += [a for _, a in low if a[1] == g][:self.strata]
                pick = pick[:self.k]
                pick += [a for _, a in atoms if a not in pick][:self.k - len(pick)]
                self.basket[e] = pick
            else:
                self.basket[e] = [a for _, a in atoms[:self.k]]
            self.history.append((w, e, list(self.basket[e])))

    def update(self, w, lvm, est):
        """Call once per week after the model has ingested week w; est = lvm estimates at week w."""
        if w >= self.start and (w - self.start) % self.reb == 0:
            self._rebalance(w, lvm)
        if self.prev is not None:
            for e in range(self.E):
                b = self.basket[e]
                if not b:
                    continue
                d = [est[c, g] - self.prev[c, g] for c, g in b if np.isfinite(est[c, g]) and np.isfinite(self.prev[c, g])]
                last = self.level[e][-1][1] if self.level[e] else 0.0
                self.level[e].append((w, last + (float(np.mean(d)) if d else 0.0)))
        self.prev = est.copy()

    def series(self, e, weeks):
        """Log level of era e for each week in range(weeks) (NaN before the era has a basket)."""
        out = np.full(weeks, np.nan)
        for w, v in self.level[e]:
            if w < weeks:
                out[w] = v
        return out
