"""Run calibration + full backtest for one seed and save metrics as JSON."""
import json
import sys
from dataclasses import asdict

from slabwise.backtest import metrics, run
from slabwise.calibrate import calibrate
from slabwise.sim import SimConfig, simulate

seed = int(sys.argv[1])
cont = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15
mode = sys.argv[3] if len(sys.argv) > 3 else "A"
params_file = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
scenario = sys.argv[5] if len(sys.argv) > 5 else "base"
extra = dict(spike_share=0.30, sale_noise=0.13, era_mislabel=0.30) if scenario == "alt" else {}
m = simulate(SimConfig(seed=seed, contamination=cont, **extra))
if params_file:
    from slabwise.model import LVMParams
    p = LVMParams(**json.load(open(params_file)))
else:
    p, score, _ = calibrate(m, verbose=False)
res = run(m, mode, p)
out = metrics(res)
out["params"] = asdict(p)
out["seed"], out["contamination"], out["mode"], out["scenario"] = seed, cont, mode, scenario
tag = "" if scenario == "base" else f"_{scenario}"
json.dump(out, open(f"results/seed{seed}_c{int(cont*100)}_{mode}{tag}.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: out[k] for k in ("EV", "CA", "DEALS")}, indent=1, ensure_ascii=False))
