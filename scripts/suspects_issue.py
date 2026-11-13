"""Review issue of the suspect sales in the private repository (D275). Run where `gh` can reach oski666/slabwise-data
(the private repository's own Actions cannot run: no paid minutes).

  open  PROPOSTE_JSON          opens the issue, if none with the label is open
  close REGISTER_JSON [N]      reads the ticks of the closed issues (or of issue N) and writes them in the register
"""
import datetime
import json
import os
import re
import subprocess
import sys

REPO = "oski666/slabwise-data"
LABEL = "vendite-sospette"
BOX = re.compile(r"- \[( |x|X)\] \*\*escludi\*\* `([^`]+)`")


def gh(*a, inp=None):
    return subprocess.run(["gh", *a], check=True, capture_output=True, text=True, input=inp).stdout


def usd(x):
    return f"${x:,.0f}".replace(",", ".") if x >= 100 else f"${x:.2f}".replace(".", ",")


def body(d):
    L = [f"Vendite che distano più di 5 volte dalla mediana delle altre vendite della stessa carta e voto nelle 26 "
         f"settimane prima e dopo (§61). Ne mostro {len(d['items'])} su {d['total']}, prima quelle che spostano di più "
         "il valore di oggi.", "",
         "**Spunta *escludi* sulle vendite sbagliate, poi chiudi la issue.** Le spuntate escono dal calcolo dalla "
         "ricostruzione dopo (restano visibili con il motivo); le non spuntate restano valide e non te le ripropongo.", ""]
    for k, it in enumerate(d["items"], 1):
        if not it.get("in_use"):
            peso = "fuori dalla finestra del motore: oggi non pesa sul valore"
        else:
            pg = it.get("pgen")
            peso = f"probabilità di essere genuina {pg:.2f}".replace(".", ",") if pg is not None else "peso non letto"
            if pg is not None and pg < 0.05:
                peso += " (il motore la tratta già come anomala)"
            if it.get("pull") is not None:
                p = it["pull"]
                peso += (f" · senza questa vendita il valore PSA {it['grade']} di oggi sarebbe "
                         f"{'più basso' if p > 0 else 'più alto'} del {abs(p) * 100:.1f}%".replace(".", ","))
            if it.get("value"):
                peso += f" (oggi {usd(it['value'])})"
        d8 = it["date"]
        L += [f"### {k}. {it['name']} · `{it['card']}` · PSA {it['grade']}",
              f"- [ ] **escludi** `{it['item_id']}`",
              f"- **{usd(it['price'])}** il {d8[8:10]}/{d8[5:7]}/{d8[:4]} ({it['age_days']} giorni fa) · {it['venue']} · "
              f"[{it['link']}]({it['url']})",
              f"- Titolo: {it['title'][:160]}",
              f"- Vendite vicine: mediana {usd(it['ref'])} su {it['n']} · questa vale {it['ratio']:.3g} volte la mediana",
              f"- Peso oggi: {peso}", ""]
    L.append("_Gli annunci eBay più vecchi di circa 90 giorni spesso non si aprono più: in quel caso decide il titolo._")
    return "\n".join(L)


def main():
    mode = sys.argv[1]
    if mode == "open":
        if json.loads(gh("api", f"repos/{REPO}/issues?labels={LABEL}&state=open")):     # REST only (GraphQL is closed here)
            print("una revisione è già aperta")
            return
        d = json.load(open(sys.argv[2]))
        if not d["items"]:
            print("niente da rivedere")
            return
        try:
            gh("api", f"repos/{REPO}/labels", "-f", f"name={LABEL}", "-f", "color=B60205",
               "-f", "description=Vendite da validare (D275)")
        except subprocess.CalledProcessError:
            pass                                          # the label exists already
        req = dict(title=f"Vendite sospette da validare · {d['date']} · {len(d['items'])}", body=body(d), labels=[LABEL])
        print(json.loads(gh("api", f"repos/{REPO}/issues", "--input", "-", inp=json.dumps(req)))["html_url"])
        return
    p = sys.argv[2]
    reg = json.load(open(p)) if os.path.exists(p) else {}
    nums = [sys.argv[3]] if len(sys.argv) > 3 else [
        str(i["number"]) for i in json.loads(gh("api", f"repos/{REPO}/issues?labels={LABEL}&state=closed&per_page=100"))]
    today = str(datetime.date.today())
    n = {"esclusa": 0, "valida": 0}
    for num in nums:
        txt = json.loads(gh("api", f"repos/{REPO}/issues/{num}"))["body"] or ""
        for box, iid in BOX.findall(txt):
            if iid in reg and reg[iid].get("issue") == int(num):
                continue
            st = "esclusa" if box.strip() else "valida"
            reg[iid] = dict(stato=st, motivo="prezzo lontano dalle vendite vicine (§61)" if st == "esclusa" else None,
                            data=today, chi="Oscar", issue=int(num))
            n[st] += 1
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    json.dump(reg, open(p, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print(n)


if __name__ == "__main__":
    main()
