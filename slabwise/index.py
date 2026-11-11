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
    def __init__(self, era, n_eras, start_week=26, rebalance=REBALANCE, min_sales=MIN_SALES, k=K, one_per_card=False, strata=0, quota=None, grades=None):
        self.era = np.asarray(era)
        self.E = n_eras
        self.start, self.reb, self.min_sales, self.k = start_week, rebalance, min_sales, k
        self.one_per_card = one_per_card                 # D130: each card enters once, with its most traded grade
        self.strata = strata                             # D143 (protocol §28): seats reserved for each grade
        self.quota = None if quota is None else np.asarray(quota)   # D245 (protocol §51): equal seats for each sub-group (era)
        self.grades = None if grades is None else set(grades)   # §59 (D266): only these grade indices (0 = PSA 10, 1 = PSA 9...)
        self.quota_log = []                              # (week, {sub-group: (eligible, seats)}) at each rebalance
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
            atoms = [(n, a) for a, n in counts.items() if self.era[a[0]] == e and n >= self.min_sales
                     and (self.grades is None or a[1] in self.grades)]
            atoms.sort(key=lambda x: (-x[0], x[1]))
            if self.one_per_card:
                seen, uniq = set(), []
                for n, a in atoms:
                    if a[0] not in seen:
                        seen.add(a[0])
                        uniq.append((n, a))
                atoms = uniq
            if self.quota is not None:                   # D245: k / G seats per sub-group, free seats shared by eligible counts
                groups = sorted({int(self.quota[a[0]]) for _, a in atoms if self.quota[a[0]] >= 0})
                by = {g: [a for _, a in atoms if self.quota[a[0]] == g] for g in groups}
                base = self.k // max(1, len(groups))
                seats = {g: min(base, len(by[g])) for g in groups}
                free = self.k - sum(seats.values())
                while free > 0:
                    room = {g: len(by[g]) - seats[g] for g in groups if len(by[g]) > seats[g]}
                    if not room:
                        break
                    tot = sum(room.values())
                    give = {g: min(r, max(1 if free else 0, int(free * r / tot))) for g, r in room.items()}
                    for g in sorted(give, key=lambda g: -room[g]):
                        take = min(give[g], free)
                        seats[g] += take
                        free -= take
                        if not free:
                            break
                self.basket[e] = [a for g in groups for a in by[g][:seats[g]]]
                self.quota_log.append((w, {g: (len(by[g]), seats[g]) for g in groups}))
                self.history.append((w, e, list(self.basket[e])))
                continue
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
