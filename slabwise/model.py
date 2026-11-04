"""Latent Value Model (LVM) - the Slabwise estimator. Specification: docs/METHOD.md.

For card c with era e, a clean sale i of grade g at week t_i, venue v_i, cert k_i:

    y_i = L_c + d_cg + q_k + o_v - beta_c (F_e(now) - F_e(t_i)) + eps_i      (y = log price)

L_c and every d_cg follow random walks (variances q_L, q_d per week), so sales
close in time share most of their deviation; the fit uses that exact covariance.

    L_c   log value of the reference grade (10) today
    d_cg  grade gap of card c (d_c10 = 0), prior N(mu_g, s_g^2) shared by all cards
    q_k   quality of the specific copy, prior N(0, sigma_q^2); estimated only for
          certs seen more than once (repeat sales), otherwise part of the noise
    o_v   venue offset vs eBay: auction houses and fixed-price marketplaces (D51), estimated from the data
    F_e   era market factor, a robust weekly index estimated from all cards
    beta_c sensitivity of card c to its era factor, prior N(1, 0.3^2)
    l_cl  language gap of card c in European language l (English = 0), prior
          N(mu_lang, s_lang^2) shared by all cards (v1.2, D28); Japanese and other
          Asian printings are separate catalogue cards, not a language gap
    eps_i noise whose variance grows with the age of the sale:
          var_i = sigma_v^2 + q_c * (now - t_i) [+ sigma_q^2 for one-off copies]
          where q_c = q_L * kappa_c is the card's own drift (v1.2, D29): kappa_c is
          estimated from the card's one-step prediction errors and pulled towards 1

Every sale is either genuine or contaminated. The contamination model is a
two-sided mixture: P(genuine) = (1-a-b) N(r; 0, var) / [(1-a-b) N + a U_low(r) + b U_high(r)].
The weights a, b are learned from the data and are much smaller for cert-verified
sales. Parameters are fitted by iteratively reweighted least squares; every sale
ends with a posterior probability of being genuine (pillar P8).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .schema import GRADE_INDEX

LOW_SPAN, HIGH_SPAN = 4.0, 2.0          # support of the contamination densities (log units)
FLOOR = 1e-4
LANGS = ("en", "de", "fr", "it", "es", "pt", "nl")   # 0 = English, the reference
VENUES = ("ebay", "auction", "fixed")               # 0 = eBay, the reference (D51)
KAPPA_PRIOR_WEEKS = 52.0                 # prior strength of the card drift, in weeks of evidence
KAPPA_RANGE = (0.5, 8.0)


@dataclass
class LVMParams:
    q_L: float = 0.0004          # weekly variance of a card's own drift
    q_d: float = 0.00002         # weekly variance of the drift of each grade gap
    sigma_e: float = 0.10        # eBay sale noise (log sd)
    sigma_a: float = 0.08        # auction-house sale noise
    sigma_q: float = 0.07        # copy quality sd
    tau_f: float = 0.02          # prior sd of a weekly era-factor move
    tau_s: float = 0.0           # weekly sd of the era-factor slope (v1.3, D33); 0 = no trend (v1.2)
    phi: float = 0.9             # weekly damping of the slope
    window: int = 156            # weeks of history used per card
    max_obs: int = 80            # most recent sales used per card
    iters: int = 8
    card_drift: bool = False     # per-card drift kappa_c (D29); off after the seed-1 check (D30)
    era_gaps: bool = False       # D55: grade-gap prior per era, tied to the shared one with a weight of 10 cards (v1.7)
    venue_gaps: bool = True      # D53, D70-D71: per-card hierarchical venue gaps (v1.6b, adopted with v1.9); False = running mean of D27
    gap_start: bool = True       # D67-D68: third starting point from the card's own grades (v1.8, adopted); False = v1.5
    step_prior: bool = True      # D101: prior on the three grade steps 10->9, 9->8, 8->7 instead of three separate gaps (v1.14)
    pop_steps: bool = True       # D101: each step's prior mean follows log(PSA population lower / upper grade) (v1.14)
    step_t: float = 4.0          # D124: Student-t prior on the grade steps with this many degrees of freedom (v1.15, adopted); 0 = normal (v1.14)
    variant_pops: bool = True    # D124: a printing variant uses its base card's PSA population ratios for the step slopes (v1.15, adopted)
    variant_gaps: bool = False   # D94: a printing variant takes its grade ladder prior from its base card (v1.13)
    variant_sd: float = 0.25     # D94: spread of a variant's gaps around its base card's
    vol_halflife: float = 0.0    # D90: half-life in weeks of the noise factor kappa_t (v1.12); 0 = v1.10, fixed noise
    cov_halflife: float = 0.0    # D128: half-life in weeks of the noise factor kappa_t aimed at 80% coverage (v1.16); 0 = off
    grade_keep: int = 15         # D78/D82: also keep the latest N observations of every grade in the window (v1.10); 0 = v1.9
    roll_bound: float | None = 3.0   # D47/D49: max factor (x or /) a card moves with its era since its last fit; None = no bound
    jump: bool = False           # D155: price jumps confirmed by several recent sales (v1.17, protocol §30)
    jump_weeks: float = 4.0      # D155: recent sales compared with the previous estimate
    jump_n: int = 3              # D155: at least this many of them
    jump_min: float = 0.35       # D155: |median log residual| above this
    jump_agree: float = 0.75     # D155: share of residuals with the median's sign and at least half its size


class LatentValueModel:
    name = "Slabwise LVM"

    def __init__(self, n_cards, era, n_eras, params: LVMParams | None = None):
        self.p = params or LVMParams()
        self.C, self.era, self.E = n_cards, np.asarray(era), n_eras
        self.F = [[0.0] for _ in range(n_eras)]          # cumulative factor, index = week + 1
        self.V = [[0.0] for _ in range(n_eras)]          # cumulative variance of the factor estimate
        self.S = np.zeros(n_eras)                         # era-factor slope (damped local trend, D33)
        self.PS = np.zeros(n_eras)                        # its variance
        self.obs = [[] for _ in range(n_cards)]           # per card: list of dict
        self.fit = [None] * n_cards                       # per card: dict(theta, cov, T, Fe)
        # learned globals (weakly informative starting points, declared in METHOD.md)
        self.mu = np.array([-0.8, -1.35, -1.7])           # mean grade gaps 9, 8, 7 vs 10
        self.s = np.array([0.35, 0.35, 0.35])             # card-to-card sd of the gaps
        self._gap_stats = [[0.0, 0.0, 0.0, 0.0] for _ in range(3)]   # weight, mean, M2, sum of posterior var
        self._gap_last = {}                                # per era (D57): card -> {gap j: (estimate, posterior var)}
        # venue gaps vs eBay (auction, fixed price), hierarchical like the language gaps (D53)
        self.offs = np.zeros(len(VENUES))                 # mean gap mu_v (offs[0] = eBay = 0)
        self.s_venue = np.full(len(VENUES), 0.2)          # card-to-card spread s_v
        self._venue_stats = [[0.0, 0.0, 0.0, 0.0] for _ in VENUES]
        self._venue_w = np.zeros(len(VENUES))             # D27 running-mean counters (when venue_gaps is off)
        NL = len(LANGS) - 1                               # language gaps vs English (D28)
        self.mu_lang = np.full(NL, -0.6)                     # weakly informative start, learned
        self.s_lang = np.full(NL, 0.5)
        self._lang_stats = [[0.0, 0.0, 0.0, 0.0] for _ in range(NL)]
        self._qs = np.zeros(n_cards)                      # card drift evidence: sum of excess r^2
        self._qw = np.zeros(n_cards)                      # ... and of the weeks it covers
        # contamination pseudo-counts: [genuine, low, high]
        self.cont = {False: np.array([40.0, 5.0, 5.0]), True: np.array([45.0, 0.5, 2.5])}
        self.week = -1
        self.pops = None                                  # v1.14 (D101): PSA population per card and grade (10, 9, 8, 7), nan if unknown
        self._step_last = {}                              # v1.14: card -> {step k: (estimate, posterior var)} when pinned down
        self._step_cache = None                           # v1.14: step priors of the week (computed once per ingest)
        self.parent = None                                # v1.13 (D94): base card index of each variant, -1 for none
        self.kappa = 1.0                                  # v1.12 (D90): factor on the noise variances, follows recent sales
        self.kappa_path = []                              # (week, kappa) after each update
        self.n_bounded = 0                                # estimates where the roll-forward bound bit (D47)
        self.jumps = [[] for _ in range(n_cards)]         # v1.17 (D155): per card, (week time, variance) of each jump

    ERA_TIE = 2.0                                         # cards' worth of weight tying an era to the shared prior (v1.7b, D56)

    def set_pops(self, pops):
        """v1.14 (D101): pops[c] = PSA populations of grades 10, 9, 8, 7 (nan when unknown)."""
        self.pops = np.asarray(pops, float)

    def _step_x(self, c):
        """log(pop lower / pop upper) for the three steps of card c, nan when unknown."""
        if self.pops is None:
            return np.full(3, np.nan)
        pp = self.pops[c]
        if self.p.variant_pops and not np.isfinite(pp).any() and self.parent is not None and self.parent[c] >= 0:
            pp = self.pops[self.parent[c]]                # v1.15 (D124): a 1st edition or shadowless takes its base card's ratios
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.array([np.log(pp[k + 1] / pp[k]) if pp[k] > 0 and pp[k + 1] > 0 else np.nan for k in range(3)])

    def _steps_update(self):
        """v1.14: per step, the shared mean and spread (and the population slope) from cards that pin it down."""
        out = []
        base_m = np.array([self.mu[0], self.mu[1] - self.mu[0], self.mu[2] - self.mu[1]])
        for k in range(3):
            pts = [(d[k][0], d[k][1], self._step_x(c)[k]) for c, d in self._step_last.items() if k in d]
            if len(pts) < 8:
                out.append(dict(m=base_m[k], s=0.45, b=0.0, xm=0.0))
                continue
            est = np.array([q[0] for q in pts]); v = np.array([q[1] for q in pts]); x = np.array([q[2] for q in pts])
            tau2 = max(est.var() - v.mean(), 0.02)
            wt = 1 / (v + tau2)
            m = float(np.sum(wt * est) / wt.sum())
            b, xm = 0.0, 0.0
            ok = np.isfinite(x)
            if self.p.pop_steps and ok.sum() >= 8:
                xw = wt[ok]; xx = x[ok]; ee = est[ok]
                xm = float(np.sum(xw * xx) / xw.sum()); em = float(np.sum(xw * ee) / xw.sum())
                sxx = float(np.sum(xw * (xx - xm) ** 2))
                if sxx > 0:
                    b = float(np.sum(xw * (xx - xm) * (ee - em)) / (sxx + 1.0 / 0.5 ** 2))   # weak shrinkage of the slope to 0
                    m = em
                    res = ee - em - b * (xx - xm)
                    tau2 = max(float(np.sum(xw * res ** 2) / xw.sum()) - float(np.mean(v[ok])), 0.02)
            out.append(dict(m=m, s=float(np.clip(np.sqrt(tau2), 0.12, 0.6)), b=b, xm=xm))
        self._step_cache = out

    def step_prior(self, c):
        """(mean of the gaps 9, 8, 7, their prior covariance) for card c under v1.14."""
        if self._step_cache is None:
            self._steps_update()
        x = self._step_x(c)
        ms, ss = np.zeros(3), np.zeros(3)
        for k, st in enumerate(self._step_cache):
            ms[k] = st["m"] + (st["b"] * (x[k] - st["xm"]) if self.p.pop_steps and np.isfinite(x[k]) else 0.0)
            ss[k] = st["s"]
        self._step_ms, self._step_ss = ms, ss               # v1.15: kept for the Student-t version of the same prior
        A = np.tril(np.ones((3, 3)))
        return A @ ms, A @ np.diag(ss ** 2) @ A.T

    def set_parents(self, parent):
        """v1.13 (D94): parent[c] = index of the base card of variant c, or -1."""
        self.parent = list(parent)

    def gap_prior(self, e):
        """(mean, sd) of the grade gaps 9, 8, 7 for a card of era e: shared (v1.5) or per era (v1.7, D55)."""
        if not self.p.era_gaps:
            return self.mu, self.s
        m, sd = self.mu.copy(), self.s.copy()
        for j in range(3):
            pts = [d[j] for c, d in self._gap_last.items() if self.era[c] == e and j in d]
            n = len(pts)
            if n > 0:
                est = np.array([x for x, _ in pts])
                mean = est.mean()
                var_e = est.var() + np.mean([v for _, v in pts])      # law of total variance, as for the shared prior
                m[j] = (n * mean + self.ERA_TIE * self.mu[j]) / (n + self.ERA_TIE)
                sd[j] = float(np.clip(np.sqrt((n * var_e + self.ERA_TIE * self.s[j] ** 2) / (n + self.ERA_TIE)), 0.12, 1.0))
        return m, sd

    @property
    def venue_off(self):                                  # auction offset (kept for callers written before D51)
        return float(self.offs[1])

    # ----------------------------------------------------------------- public
    def ingest(self, w, sales):
        self.week = w
        if self.p.step_prior:
            self._steps_update()
        cards = sales["card"].to_numpy().astype(int)
        gis = np.array([GRADE_INDEX[int(g)] for g in sales["grade"]])
        y = np.log(sales["price"].to_numpy())
        t = sales["day"].to_numpy() / 7.0
        vn = sales["venue"].to_numpy()
        vix = np.where(vn == "auction", 1, np.where(vn == "fixed", 2, 0))
        auction = vix
        cert = sales["cert"].to_numpy()
        cert_ok = sales["cert_ok"].to_numpy().astype(bool)
        lang = (sales["lang"].fillna(0).to_numpy().astype(int) if "lang" in sales
                else np.zeros(len(y), int))

        self._factor_step(w, cards, gis, y, auction, cert_ok, lang)

        touched = set()
        for i in range(len(y)):
            self.obs[cards[i]].append(dict(t=t[i], y=y[i], g=gis[i], a=bool(vix[i] == 1), v=int(vix[i]), l=int(lang[i]),
                                           k=cert[i] if isinstance(cert[i], str) else None,
                                           ok=bool(cert_ok[i]), new=True))
            touched.add(cards[i])
        for c in touched:
            self._refit(c, w)

    def qc(self, c):
        """Weekly drift variance of card c: q_L * kappa_c, kappa_c shrunk towards 1."""
        q = self.p.q_L
        if not self.p.card_drift:
            return q
        est = (KAPPA_PRIOR_WEEKS * q + self._qs[c]) / (KAPPA_PRIOR_WEEKS + self._qw[c])
        return float(np.clip(est / q, *KAPPA_RANGE) * q)

    def estimates(self, w):
        mean, _ = self.estimates_with_sd(w)
        return mean

    def estimates_with_sd(self, w):
        mean = np.full((self.C, 4), np.nan)
        sd = np.full((self.C, 4), np.nan)
        for c, f in enumerate(self.fit):
            if f is None:
                continue
            e = self.era[c]
            dF = self.F[e][w + 1] - f["Fe"]
            dt = (w + 1) - f["T"]
            th, cov = f["theta"], f["cov"]
            for gi in range(4):
                h = np.zeros(len(th))
                h[0] = 1
                if gi:
                    h[gi] = 1
                h[4] = dF
                roll = th[4] * dF
                if self.p.roll_bound:                          # D47: a card without sales moves at most x/÷ roll_bound
                    lim = np.log(self.p.roll_bound)
                    if abs(roll) > lim:
                        roll = float(np.clip(roll, -lim, lim))
                        self.n_bounded += 1
                mean[c, gi] = th[0] + (th[gi] if gi else 0) + roll
                dV = self.V[e][w + 1] - f["V"]                 # factor estimation error since the fit
                sd[c, gi] = np.sqrt(h[:5] @ cov[:5, :5] @ h[:5] + (self.qc(c) + (self.p.q_d if gi else 0)) * dt
                                    + th[4] ** 2 * dV)
        return mean, sd

    def forecast_var_week(self):
        """v1.15 (D106): extra variance per week ahead of each card and grade, shape (cards, 4): its own drift (q_c, plus
        q_d for the grade gaps) and the era factor's possible moves (beta_c^2 * tau_f^2). The mean does not move."""
        out = np.full((self.C, 4), np.nan)
        for c, f in enumerate(self.fit):
            if f is None:
                continue
            b2 = float(f["theta"][4]) ** 2 * self.p.tau_f ** 2
            out[c] = [self.qc(c) + b2] + [self.qc(c) + self.p.q_d + b2] * 3
        return out

    def estimates_lang(self, w, lang):
        """(mean, sd) of log value in a European language (1..len(LANGS)-1), shape (cards, 4).
        A card without sales in that language takes the shared gap mu_lang with its spread s_lang."""
        mean, sd = self.estimates_with_sd(w)
        j = lang - 1
        for c, f in enumerate(self.fit):
            if f is None:
                continue
            if lang in f["langs"]:
                k = 5 + f["langs"].index(lang)
                for gi in range(4):
                    h = np.zeros(len(f["theta"]))
                    h[0] = 1
                    if gi:
                        h[gi] = 1
                    h[k] = 1
                    mean[c, gi] += f["theta"][k]
                    base_var = sd[c, gi] ** 2 - h[:5] @ f["cov"][:5, :5] @ h[:5]
                    sd[c, gi] = np.sqrt(max(base_var, 0) + h @ f["cov"] @ h)
            else:
                mean[c] += self.mu_lang[j]
                sd[c] = np.sqrt(sd[c] ** 2 + self.s_lang[j] ** 2)
        return mean, sd

    def sale_posteriors(self, c):
        """Posterior genuineness of the sales currently used for card c."""
        f = self.fit[c]
        return None if f is None else f["pgen"]

    # --------------------------------------------------------------- internals
    def _pis(self, ok):
        n = self.cont[ok]
        return n / n.sum()

    def _mix(self, r, var, ok):
        pg, pl, ph = self._pis(ok)
        ng = np.exp(-0.5 * r * r / var) / np.sqrt(2 * np.pi * var)
        ul = np.where((r < 0) & (r > -LOW_SPAN), 1 / LOW_SPAN, FLOOR)
        uh = np.where((r > 0) & (r < HIGH_SPAN), 1 / HIGH_SPAN, FLOOR)
        a, b, cc = pg * ng, pl * ul, ph * uh
        tot = a + b + cc
        return a / tot, b / tot, cc / tot, np.log(tot)

    def _predict_card(self, c, w_prev):
        """Current estimate of card c projected to the end of week w_prev."""
        f = self.fit[c]
        e = self.era[c]
        dF = self.F[e][w_prev + 1] - f["Fe"]
        dV = self.V[e][w_prev + 1] - f["V"]
        return f["theta"], f["cov"], dF, (w_prev + 1) - f["T"], dV

    def _factor_step(self, w, cards, gis, y, auction, ok, lang):
        p = self.p
        zs, za = [], []
        num = np.zeros(self.E)
        den = np.zeros(self.E)
        for i in range(len(y)):
            c = cards[i]
            if self.fit[c] is None:
                continue
            th, cov, dF, dt, dV = self._predict_card(c, w - 1)
            gi = gis[i]
            h = np.zeros(len(th))
            h[0] = 1
            if gi:
                h[gi] = 1
            h[4] = dF
            l_off, l_var = 0.0, 0.0
            if lang[i]:
                langs = self.fit[c]["langs"]
                if lang[i] in langs:
                    h[5 + langs.index(lang[i])] = 1
                    l_off = th[5 + langs.index(lang[i])]
                else:
                    l_off, l_var = self.mu_lang[lang[i] - 1], self.s_lang[lang[i] - 1] ** 2
            v = int(auction[i])
            if v and not p.venue_gaps:
                l_off += self.offs[v]
            elif v:
                vens = self.fit[c]["venues"]
                if v in vens:
                    kv = 5 + len(self.fit[c]["langs"]) + vens.index(v)
                    h[kv] = 1
                    l_off += th[kv]
                else:
                    l_off += self.offs[v]
                    l_var += self.s_venue[v] ** 2
            qc = self.qc(c)
            pred = (th[0] + (th[gi] if gi else 0) + th[4] * dF + l_off)
            rest = (h @ cov @ h + th[4] ** 2 * dV + l_var
                    + ((p.sigma_a if auction[i] == 1 else p.sigma_e) ** 2 + p.sigma_q ** 2) * self.kappa)
            var = rest + qc * (dt + 0.5)
            r = y[i] - pred
            pg, _, _, _ = self._mix(np.array([r]), var, bool(ok[i]))
            if pg[0] > 0.8:
                zs.append(r * r / var)                    # v1.12: standardised squared residual, estimates of last week
            za.append(abs(r) / np.sqrt(var))              # v1.16: every sale, as coverage counts them
            if pg[0] > 0.8:                               # card drift evidence (D29)
                self._qs[c] += r * r - rest
                self._qw[c] += dt + 0.5
            wt = pg[0] / var
            rc = np.clip(r, -2.0 * np.sqrt(var), 2.0 * np.sqrt(var))     # Huber-style clip
            e = self.era[c]
            num[e] += wt * th[4] * rc
            den[e] += wt * th[4] ** 2
        for e in range(self.E):
            if p.tau_s <= 0:                              # v1.2: increment with a prior centred on zero
                step = num[e] / (den[e] + 1 / p.tau_f ** 2)
                var = 1 / (den[e] + 1 / p.tau_f ** 2)
            else:                                         # v1.3: prior centred on the damped slope
                m = p.phi * self.S[e]
                ps = p.phi ** 2 * self.PS[e] + p.tau_s ** 2
                pd = ps + p.tau_f ** 2                    # prior variance of this week's increment
                if den[e] > 0:
                    z = num[e] / den[e]                   # increment measured by this week's sales
                    R = 1 / den[e]
                    k = 1 / (pd + R)
                    step = m + pd * k * (z - m)
                    var = pd - pd * pd * k
                    self.S[e] = m + ps * k * (z - m)
                    self.PS[e] = ps - ps * ps * k
                else:
                    step, var = m, pd
                    self.S[e], self.PS[e] = m, ps
            self.F[e].append(self.F[e][-1] + step)
            self.V[e].append(self.V[e][-1] + var)
        if p.cov_halflife > 0 and len(za) >= 20:          # v1.16 (D128): aim the 80% band at 80% of the sales
            ratio = (float(np.quantile(za, 0.8)) / 1.2816) ** 2
            lam = 1 - 0.5 ** (1 / p.cov_halflife)
            self.kappa = float(np.clip(self.kappa * max(ratio, 1e-3) ** lam, 0.25, 2.25))
            self.kappa_path.append((w, self.kappa))
        if p.vol_halflife > 0 and len(zs) >= 20:          # v1.12 (D90): robust ratio of observed to expected spread
            ratio = float(np.median(zs)) / 0.455
            lam = 1 - 0.5 ** (1 / p.vol_halflife)
            self.kappa = float(np.clip(self.kappa * max(ratio, 1e-3) ** lam, 0.25, 2.25))
            self.kappa_path.append((w, self.kappa))

    def _refit(self, c, w):
        p = self.p
        T = w + 1.0
        e = self.era[c]
        Fe_now = self.F[e][w + 1]
        ob = [o for o in self.obs[c] if o["t"] > T - p.window]
        if p.grade_keep and len(ob) > p.max_obs:         # v1.10 (D78): low grades of busy cards stay in the window
            keep = set(range(len(ob) - p.max_obs, len(ob)))
            for gg in {o["g"] for o in ob}:
                keep |= set([k for k, o in enumerate(ob) if o["g"] == gg][-p.grade_keep:])
            ob = [o for k, o in enumerate(ob) if k in keep]
        else:
            ob = ob[-p.max_obs:]
        self.obs[c] = ob
        n = len(ob)
        t = np.array([o["t"] for o in ob])
        g = np.array([o["g"] for o in ob])
        a = np.array([o["a"] for o in ob])
        vv = np.array([o.get("v", int(o["a"])) for o in ob])
        ok = np.array([o["ok"] for o in ob])
        ks = [o["k"] for o in ob]
        ls = np.array([o.get("l", 0) for o in ob])
        langs = sorted({int(x) for x in ls if x})
        lidx = {l: 5 + j for j, l in enumerate(langs)}
        NLc = len(langs)
        venues = sorted({int(x) for x in vv if x}) if p.venue_gaps else []   # venue gaps of this card (D53)
        vidx = {v: 5 + NLc + j for j, v in enumerate(venues)}
        NVc = len(venues)
        qc = self.qc(c)
        wk = np.minimum(np.floor(t).astype(int) + 1, w + 1)
        Fe_then = np.array([self.F[e][i] for i in wk])
        Ve_now = self.V[e][w + 1]
        fvar = Ve_now - np.array([self.V[e][i] for i in wk])   # error of the factor shift applied to each sale
        dF = Fe_now - Fe_then
        y = np.array([o["y"] for o in ob])
        if not p.venue_gaps:                                       # v1.5: subtract the shared offsets (D27)
            y = y - self.offs[vv]

        counts = {}
        for k in ks:
            if k is not None:
                counts[k] = counts.get(k, 0) + 1
        rep = [k for k, m in counts.items() if m > 1]
        kidx = {k: 5 + NLc + NVc + j for j, k in enumerate(rep)}
        P = 5 + NLc + NVc + len(rep)
        X = np.zeros((n, P))
        X[:, 0] = 1
        X[:, 4] = -dF
        for i in range(n):
            if g[i]:
                X[i, g[i]] = 1
            if ls[i]:
                X[i, lidx[int(ls[i])]] = 1
            if vv[i] in vidx:
                X[i, vidx[int(vv[i])]] = 1
            if ks[i] in kidx:
                X[i, kidx[ks[i]]] = 1
        one_off = np.array([(k is None) or (k not in kidx) for k in ks])
        age = T - t
        base = (np.where(a, p.sigma_a ** 2, p.sigma_e ** 2) + np.where(one_off, p.sigma_q ** 2, 0)) * self.kappa
        var = base + qc * age                       # marginal variance of each sale today
        shared = qc * np.minimum.outer(age, age)     # sales share the same random-walk path
        same_gap = (g[:, None] == g[None, :]) & (g[:, None] > 0)
        shared = shared + p.q_d * np.minimum.outer(age, age) * same_gap   # grade gaps drift too
        var = var + np.where(g > 0, p.q_d * age, 0.0) + fvar
        shared = shared + np.minimum.outer(fvar, fvar)   # the factor error is shared from the later sale on

        prior_mean = np.zeros(P)
        prior_prec = np.zeros(P)
        gm, gs = self.gap_prior(e)
        if p.variant_gaps and self.parent is not None and self.parent[c] >= 0 and self.fit[self.parent[c]] is not None:
            fp = self.fit[self.parent[c]]               # v1.13 (D94): the base card's ladder, with its uncertainty
            gm = np.asarray(fp["theta"][1:4], float).copy()
            gs = np.sqrt(np.diag(fp["cov"])[1:4] + p.variant_sd ** 2)
        prior_mean[1:4] = gm
        prior_prec[1:4] = 1 / gs ** 2
        prior_mean[4] = 1.0
        prior_prec[4] = 1 / 0.3 ** 2
        for l, j in lidx.items():
            prior_mean[j] = self.mu_lang[l - 1]
            prior_prec[j] = 1 / self.s_lang[l - 1] ** 2
        for v, j in vidx.items():
            prior_mean[j] = self.offs[v]
            prior_prec[j] = 1 / self.s_venue[v] ** 2
        prior_prec[5 + NLc + NVc:] = 1 / (p.sigma_q ** 2 * self.kappa)
        prior_prec[0] = 1e-4
        if p.step_prior and not (p.variant_gaps and self.parent is not None and self.parent[c] >= 0):
            gm2, gcov = self.step_prior(c)                # v1.14 (D101): correlated gaps through independent steps
            prior_mean[1:4] = gm2
            gm = gm2
            P_ = np.diag(prior_prec)
            P_[1:4, 1:4] = np.linalg.inv(gcov)
            prior_prec = P_
            tprior = (self._step_ms.copy(), self._step_ss.copy(), p.step_t) if p.step_t > 0 else None
        else:
            tprior = None

        starts = []
        prev = self.fit[c]
        if prev is not None:
            th0 = prior_mean.copy()
            th0[5 + NLc + NVc:] = 0
            th0[:5] = prev["theta"][:5]
            for l, j in lidx.items():
                if l in prev["langs"]:
                    th0[j] = prev["theta"][5 + prev["langs"].index(l)]
            for v, j in vidx.items():
                if v in prev["venues"]:
                    th0[j] = prev["theta"][5 + len(prev["langs"]) + prev["venues"].index(v)]
            th0[0] += prev["theta"][4] * (Fe_now - prev["Fe"])
            starts.append(th0)
        # robust start: cert-weighted median of grade-adjusted recent prices
        adj = (y + dF - np.concatenate([[0], gm])[g] - np.concatenate([[0], self.mu_lang])[ls]
               - (self.offs[vv] if p.venue_gaps else 0.0))
        wts = np.where(ok, 3.0, 1.0) / var
        th1 = prior_mean.copy()
        th1[5 + NLc + NVc:] = 0
        th1[0] = _wmedian(adj, wts)
        starts.append(th1)
        if p.gap_start:                                  # v1.8 (D67): level from PSA 10 sales, each grade from its own sales
            yy = y + dF - np.concatenate([[0], self.mu_lang])[ls] - (self.offs[vv] if p.venue_gaps else 0.0)
            th2 = th1.copy()
            if (g == 0).any():
                th2[0] = _wmedian(yy[g == 0], wts[g == 0])
            for j in (1, 2, 3):
                if (g == j).sum() >= 2:
                    th2[j] = _wmedian(yy[g == j], wts[g == j]) - th2[0]
            starts.append(th2)

        if p.jump:                                       # v1.17 (D155): level jumps confirmed by recent sales
            if prev is not None:
                last_j = self.jumps[c][-1][0] if self.jumps[c] else -np.inf
                rec = (t > T - p.jump_weeks) & (t > last_j)
                if rec.sum() >= p.jump_n:
                    r = (y - X @ starts[0])[rec]
                    med = float(np.median(r))
                    agree = np.mean((np.sign(r) == np.sign(med)) & (np.abs(r) >= 0.5 * abs(med)))
                    if abs(med) > p.jump_min and agree >= p.jump_agree:
                        self.jumps[c].append((float(t[rec].min()), med * med))
            for tj, J in self.jumps[c]:
                pre = (t < tj).astype(float)
                if pre.any():
                    var = var + J * pre
                    shared = shared + J * np.outer(pre, pre)
        best = None
        for th in starts:
            res = self._irls(X, y, var, base, shared, ok, th, prior_mean, prior_prec, p.iters, tprior)
            if best is None or res[3] > best[3]:
                best = res
        theta, cov, post, obj = best
        K = 5 + NLc + NVc
        self.fit[c] = dict(theta=theta[:K].copy(), cov=cov[:K, :K].copy(), T=T, Fe=Fe_now, V=Ve_now,
                           pgen=post[0], cert=ok.copy(), langs=langs, venues=venues)
        self._learn_globals(c, ob, post, theta, cov, X, y, a, lidx, vidx)

    def _irls(self, X, y, var, base, shared, ok, th, m0, prec0, iters, tprior=None):
        """Robust generalised least squares: the exact posterior of a local-level
        model (random walk + noise) evaluated today, with each sale's noise
        inflated by 1 / P(genuine). Equivalent to a robust Kalman smoother.
        tprior = (step means, step scales, nu): v1.15 (D124), Student-t prior on the three grade steps,
        by reweighting their precision at every iteration (the t as a scale mixture of normals)."""
        D = np.array([[1.0, 0, 0], [-1, 1, 0], [0, -1, 1]])          # gaps -> steps
        if tprior is not None:
            prec0 = np.array(prec0, float, copy=True)

        def tweights(th_):
            ms, ss, nu = tprior
            z = (D @ th_[1:4] - ms) / ss
            return z, (nu + 1) / (nu + z ** 2)

        for _ in range(iters):
            if tprior is not None:
                _, wt = tweights(th)
                prec0[1:4, 1:4] = D.T @ np.diag(wt / tprior[1] ** 2) @ D
            r = y - X @ th
            pg = np.empty(len(r))
            pl = np.empty(len(r))
            ph = np.empty(len(r))
            for flag in (False, True):
                sel = ok == flag
                if sel.any():
                    pg[sel], pl[sel], ph[sel], _ = self._mix(r[sel], var[sel], flag)
            S = shared + np.diag(base / np.maximum(pg, 1e-4))
            SX = np.linalg.solve(S, np.column_stack([X, y]))
            A = X.T @ SX[:, :-1] + (prec0 if prec0.ndim == 2 else np.diag(prec0))
            b = X.T @ SX[:, -1] + (prec0 @ m0 if prec0.ndim == 2 else prec0 * m0)
            th = np.linalg.solve(A, b)
        r = y - X @ th
        obj = 0.0
        pg = np.empty(len(r))
        pl = np.empty(len(r))
        ph = np.empty(len(r))
        for flag in (False, True):
            sel = ok == flag
            if sel.any():
                pg[sel], pl[sel], ph[sel], ll = self._mix(r[sel], var[sel], flag)
                obj += ll.sum()
        dth = th[1:] - m0[1:]
        if tprior is not None:                           # v1.15: t penalty on the steps, quadratic on the rest
            pr = prec0.copy()
            pr[1:4, 1:4] = 0
            z, _ = tweights(th)
            obj -= 0.5 * (dth @ pr[1:, 1:] @ dth) + float(np.sum((tprior[2] + 1) / 2 * np.log1p(z ** 2 / tprior[2])))
        else:
            obj -= 0.5 * (dth @ prec0[1:, 1:] @ dth if prec0.ndim == 2 else np.sum(prec0[1:] * dth ** 2))
        cov = np.linalg.inv(A)
        return th, cov, (pg, pl, ph), obj

    def _learn_globals(self, c, ob, post, theta, cov, X, y, a, lidx, vidx=None):
        pg, pl, ph = post
        for i, o in enumerate(ob):
            if o["new"]:
                self.cont[o["ok"]] += np.array([pg[i], pl[i], ph[i]])
                o["new"] = False
        for flag in (False, True):                       # forget slowly: last ~2000 sales dominate
            tot = self.cont[flag].sum()
            if tot > 2000:
                self.cont[flag] *= 2000 / tot
        # grade gaps: learn from cards whose own data pin the gap down
        for j in range(3):
            v = cov[1 + j, 1 + j]
            if v < 0.5 * self.s[j] ** 2:
                st = self._gap_stats[j]
                wgt = 1.0
                st[0] += wgt
                d = theta[1 + j] - st[1]
                st[1] += wgt * d / st[0]
                st[2] += wgt * d * (theta[1 + j] - st[1])
                st[3] += wgt * v
                if st[0] > 30:
                    self.mu[j] = st[1]
                    # law of total variance: shrunk estimates are less spread than the truth
                    self.s[j] = float(np.clip(np.sqrt((st[2] + st[3]) / st[0]), 0.12, 0.6))
        if self.p.step_prior:                             # v1.14: latest estimate of each card's steps, when pinned down
            Ainv = np.array([[1, 0, 0], [-1, 1, 0], [0, -1, 1]], float)
            st_ = Ainv @ theta[1:4]
            sc_ = Ainv @ cov[1:4, 1:4] @ Ainv.T
            last = self._step_last.setdefault(c, {})
            prev = self._step_cache or [dict(s=0.45)] * 3
            for k in range(3):
                if sc_[k, k] < 0.5 * prev[k]["s"] ** 2:
                    last[k] = (float(st_[k]), float(sc_[k, k]))
        if self.p.era_gaps:                               # per era: the latest estimate of each card counts once (D57)
            _, gs = self.gap_prior(self.era[c])
            last = self._gap_last.setdefault(c, {})
            for j in range(3):
                v = cov[1 + j, 1 + j]
                if v < 0.5 * gs[j] ** 2:
                    last[j] = (float(theta[1 + j]), float(v))
        # language gaps: same rule as the grade gaps (D28)
        for l, k in lidx.items():
            j = l - 1
            v = cov[k, k]
            if v < 0.5 * self.s_lang[j] ** 2:
                st = self._lang_stats[j]
                st[0] += 1.0
                d = theta[k] - st[1]
                st[1] += d / st[0]
                st[2] += d * (theta[k] - st[1])
                st[3] += v
                if st[0] > 10:
                    self.mu_lang[j] = st[1]
                    self.s_lang[j] = float(np.clip(np.sqrt((st[2] + st[3]) / st[0]), 0.08, 0.8))
        # v1.5 (venue_gaps off): running mean of the residuals, cards with sales in another venue too (D27)
        if not self.p.venue_gaps:
            vv = np.array([o.get("v", int(o["a"])) for o in ob])
            for v in range(1, len(VENUES)):
                here = vv == v
                if here.any() and (~here).any():
                    r = y - X @ theta + self.offs[v]     # residual before the offset
                    for ri in r[here & (pg > 0.8)]:
                        self._venue_w[v] += 1
                        self.offs[v] += (ri - self.offs[v]) / min(self._venue_w[v], 500)
        # venue gaps: same rule as the language gaps (D53)
        for v, k in (vidx or {}).items():
            var_k = cov[k, k]
            if var_k < 0.5 * self.s_venue[v] ** 2:
                st = self._venue_stats[v]
                st[0] += 1.0
                d = theta[k] - st[1]
                st[1] += d / st[0]
                st[2] += d * (theta[k] - st[1])
                st[3] += var_k
                if st[0] > 10:
                    self.offs[v] = st[1]
                    self.s_venue[v] = float(np.clip(np.sqrt((st[2] + st[3]) / st[0]), 0.03, 0.5))

def _wmedian(x, w):
    o = np.argsort(x)
    x, w = x[o], w[o]
    cw = np.cumsum(w)
    return float(x[np.searchsorted(cw, 0.5 * cw[-1])])
