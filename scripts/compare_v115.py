"""N1-N6 (protocol §5) of v1.15 against v1.14 on the same simulated jobs."""
import glob, json, os
import numpy as np
L = "Slabwise LVM"
B = ("alta", "media", "bassa", "rarissima")
def load(d):
    return {os.path.basename(f): json.load(open(f)) for f in glob.glob(f"{d}/seed*.json")}
a, b = load("results/v1.15"), load("results/v1.14")
jobs = sorted(set(a) & set(b))
base = [j for j in jobs if a[j]["scenario"] == "base" and a[j]["mode"] == "A" and abs(a[j]["contamination"] - 0.15) < 1e-9]
alt = [j for j in jobs if a[j]["scenario"] == "alt"]
med = lambda R, js, f: float(np.median([f(R[j]) for j in js]))
names = a[jobs[0]]["names"]; comps = [n for n in names if n != L]
out = {}
for k in ("EV", "ES", "RC"):
    out[k] = (med(a, base, lambda r: r[k][L]), med(b, base, lambda r: r[k][L]))
N1 = all(x <= 1.02 * y for x, y in out.values())
EVb = {bb: (med(a, base, lambda r: r["EV_bucket"][L][bb]), med(b, base, lambda r: r["EV_bucket"][L][bb])) for bb in B}
N2 = all(x <= 1.05 * y for x, y in EVb.values())
CA = (med(a, base, lambda r: r["CA"]), med(b, base, lambda r: r["CA"]))
N3 = 0.75 <= CA[0] <= 0.85 or abs(CA[0] - 0.8) <= abs(CA[1] - 0.8)
DP = med(a, base, lambda r: r["DEALS"][L]["precision"])
N4 = DP >= 0.80
ALT = (med(a, alt, lambda r: r["EV"][L]), med(b, alt, lambda r: r["EV"][L]))
N5 = ALT[0] <= 1.02 * ALT[1]
def S(R):
    ev = {n: med(R, base, lambda r, n=n: r["EV"][n]) for n in names}
    best = min(comps, key=lambda n: ev[n])
    evb = {bb: {n: med(R, base, lambda r, n=n, bb=bb: r["EV_bucket"][n][bb]) for n in names} for bb in B}
    ru = {n: med(R, base, lambda r, n=n: r["RU"][n]) for n in names}
    rc = {n: med(R, base, lambda r, n=n: r["RC"][n]) for n in names}
    c35 = [j for j in jobs if R[j]["mode"] == "A" and R[j]["scenario"] == "base" and abs(R[j]["contamination"] - 0.35) < 1e-9 and R[j]["seed"] in (1, 2, 3)]
    c35v = med(R, c35, lambda r: r["EV"][L]) if c35 else None
    return {"S1": ev[L] <= 0.8 * ev[best], "S2": all(evb[bb][L] <= min(evb[bb][n] for n in comps) for bb in B),
            "S3": ru[L] <= min(ru[n] for n in comps), "S4": 0.75 <= med(R, base, lambda r: r["CA"]) <= 0.85,
            "S5": bool(c35v) and c35v <= 1.5 * ev[L], "S6": med(R, base, lambda r: r["DEALS"][L]["precision"]) >= 0.8,
            "S7": rc[L] < min(rc[n] for n in comps)}
Sa, Sb = S(a), S(b)
N6 = all(Sa[k] or not Sb[k] for k in Sb)
print(json.dumps(dict(jobs=len(jobs), base=len(base), alt=len(alt), N1=[N1, out], N2=[N2, EVb], N3=[N3, CA], N4=[N4, DP], N5=[N5, ALT],
                      N6=[N6, Sa, Sb]), indent=1, default=str))
