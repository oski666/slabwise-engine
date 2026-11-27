"""The stories of the week for the creators (D347, docs/specs/2026-11-reel-scene.md).

Each story is a piece of news found in our own data, not the card that moved most: a Japanese and an English printing
of the same card at very different prices, the share of PSA 10 of an era, more copies against the price, a jump or a
fall, a new all-time high. Every story carries the whole script (hook, numbers, why it matters, closing question) and
the scenes of the reel with their short texts. Prices in euros at the day's rate (Oscar, 27 Nov 2026).

Pure functions on the data the build already has: build_real_data.py calls week_stories() once a week.
"""
import math

ERA_ORDER = ["Vintage", "Classica", "Di mezzo", "Moderna", "Spada e Scudo", "Scarlatto e Violetto"]
MAX_STORIES = 6
MAX_PER_KIND = 2


def eur(v, rate):
    """1.234 € / 12,5 € (Italian separators)."""
    x = v * rate
    s = f"{x:,.0f}" if x >= 100 else f"{x:,.1f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".") + " €"


def num(n):
    return f"{n:,.0f}".replace(",", ".")


def p1(x):
    return f"{x * 100:.1f}%".replace(".", ",")


def il(t):
    """Italian article before a percentage: l'8,1%, l'11%, il 3,6%."""
    return ("l'" if t.startswith(("8", "11", "18")) else "il ") + t


def pct(x, sign=True):
    s = f"{abs(x) * 100:.0f}%"
    return ("+" if x >= 0 else "−") + s if sign else s


def _g(c, grade=10):
    for g in c.get("grades") or []:
        if g["grade"] == grade:
            return g
    return None


def _ok(g, n=8):
    return g and g.get("value") and (g.get("sales90") or 0) >= n and not g.get("off") and not g.get("stale")


def _label(c):
    return c["name"] + (" giapponese" if c.get("lang") == "ja" else "") + (" cinese" if c.get("lang") == "zh" else "")


def _story(kind, title, score, hook, numbers, why, close, scenes, cards, check=False, **extra):
    voice = " ".join(x for x in (hook, numbers, why, close) if x)
    return dict(kind=kind, title=title, score=round(float(score), 4), hook=hook, numbers=numbers, why=why, close=close,
                voice=voice, scenes=scenes, cards=cards, check=check, **extra)


def twin_gap(cards, rate):
    """Same card, Japanese and English: the price gap and the PSA 10 copies behind it (D347)."""
    by = {c["id"]: c for c in cards}
    out = []
    for j in cards:
        if j.get("lang") != "ja" or j.get("en_same") is not True or j.get("en") not in by:
            continue
        e = by[j["en"]]
        a, b = _g(j), _g(e)
        if not (_ok(a) and _ok(b)) or not a.get("pop") or not b.get("pop"):
            continue
        r = b["value"] / a["value"]
        hi, lo = (e, j) if r >= 1 else (j, e)
        gh, gl = (b, a) if r >= 1 else (a, b)
        rr = max(r, 1 / r)
        if rr < 2.5 or rr > 25 or min(a["pop"], b["pop"]) < 100 or "promo" in (e["set"] + j["set"]).lower():
            continue                                     # a gap beyond 25 or a promo is more often a wrong pairing than a story
        popr = gl["pop"] / gh["pop"] if gh["pop"] else None
        ja_more = r < 1
        hook = (f"Di solito la carta giapponese costa meno dell'inglese. {e['name']} fa il contrario." if ja_more else
                f"Stessa illustrazione, stesso {e['name']}. Uno vale {eur(gl['value'], rate)}, l'altro {eur(gh['value'], rate)}.")
        numbers = (f"{e['name']} di {e['set']}, PSA 10: inglese {eur(b['value'], rate)}, giapponese ({j['set']}) {eur(a['value'], rate)}. "
                   f"In PSA 10 ci sono {num(a['pop'])} copie giapponesi e {num(b['pop'])} inglesi.")
        if ja_more:
            why = "Qui l'offerta non spiega il prezzo: lo spiega chi compra. Prima di dire «la giapponese costa meno», controlla la carta."
        elif popr and popr >= 2:
            why = (f"Il prezzo non lo fa l'illustrazione, lo fa quante copie perfette esistono: {popr:.0f} volte tante, "
                   f"{rr:.0f} volte meno care.")
        else:
            why = "Le copie in PSA 10 sono simili: la differenza la fa chi compra. Se ti importa l'illustrazione e non la lingua, è la stessa carta."
        close = "Tu quale terresti in vetrina?" if not ja_more else "Conosci un'altra carta dove la giapponese vale di più?"
        scenes = [
            dict(t="statement", big=f"{eur(gl['value'], rate)} contro {eur(gh['value'], rate)}", small=f"Stesso {e['name']}."),
            dict(t="vs", a=dict(card=j["id"], label="Giapponese", sub=f"{j['set']} · PSA 10", value=eur(a["value"], rate)),
                 b=dict(card=e["id"], label="Inglese", sub=f"{e['set']} · PSA 10", value=eur(b["value"], rate)),
                 tag=f"{rr:.0f} volte il prezzo".replace(".", ",")),
            dict(t="bars", title="Copie in PSA 10", items=[dict(label="Giapponese", value=a["pop"], text=num(a["pop"])),
                                                         dict(label="Inglese", value=b["pop"], text=num(b["pop"]))]),
            dict(t="statement", big="Conta chi compra." if ja_more else "Lo fa quante copie perfette esistono.",
                 small="Qui l'offerta non spiega il prezzo." if ja_more else "Il prezzo non lo fa il disegno."),
            dict(t="question", text=close)]
        out.append(_story("twin", "Giapponese contro inglese", (math.log(rr) + (0.7 if ja_more else 0)) * min(1, min(a["sales90"], b["sales90"]) / 20), hook, numbers, why, close,
                          scenes, [j["id"], e["id"]], ja_more=ja_more))
    return out


def era_share(psa10_share):
    """The share of PSA 10 of an era, then and now (D334, D347)."""
    if not psa10_share:
        return []
    eras = psa10_share.get("eras") or {}
    out = []
    rows = [(e, v) for e, v in eras.items() if v.get("now") and v.get("start")]
    if not rows:
        return []
    e, v = min(rows, key=lambda x: x[1]["now"] / x[1]["start"])            # the era that lost most
    up = max(rows, key=lambda x: x[1]["now"] / x[1]["start"])
    if v["now"] / v["start"] > 0.6:
        return []
    one_in = round(1 / v["now"]) if v["now"] else None
    hook = f"Mandi a gradare una carta dell'era {e}: quante possibilità hai di prendere 10? Una su {one_in}."
    numbers = (f"Era {e}: nel 2021–22 prendeva PSA 10 {il(p1(v['start']))} delle carte gradate"
               + (f", un anno fa {il(p1(v['y1']))}" if v.get("y1") else "") + f", negli ultimi sei mesi {il(p1(v['now']))}."
               + (f" Per {up[0]}, nello stesso periodo, la quota è passata dal {up[1]['start'] * 100:.0f}% al {up[1]['now'] * 100:.0f}%."
                  if up[0] != e and up[1]["now"] > up[1]["start"] else ""))
    why = "Le copie perfette delle carte vecchie sono già state gradate: quello che arriva oggi è il resto. Prima di spedire, conta sul 9."
    close = "Hai mai preso un 10 su una carta più vecchia di te?"
    items = [dict(label="2021–22", value=v["start"], text=p1(v["start"]))]
    if v.get("y1"):
        items.append(dict(label="un anno fa", value=v["y1"], text=p1(v["y1"])))
    items.append(dict(label="ultimi 6 mesi", value=v["now"], text=p1(v["now"])))
    scenes = [dict(t="statement", big=f"1 su {one_in}", small=f"prende PSA 10 oggi · era {e}"),
              dict(t="bars", title=f"Quota di PSA 10 · {e}", items=items)]
    if up[0] != e and up[1]["now"] > up[1]["start"]:
        scenes.append(dict(t="statement", big=f"{up[1]['start'] * 100:.0f}% → {up[1]['now'] * 100:.0f}%", small=f"intanto, {up[0]}"))
    scenes += [dict(t="statement", big="Sul vintage conta sul 9.", small="Le copie perfette sono già state gradate."),
               dict(t="question", text=close)]
    out.append(_story("era_share", "Il PSA 10 per era", -math.log(v["now"] / v["start"]), hook, numbers, why, close,
                      scenes, [], era=e))
    return out


def supply_price(cards, pop_history, rate, asof):
    """Many new PSA 10 copies in a month, and what the price did (D347): from the weekly population reads."""
    from datetime import date
    d1 = date.fromisoformat(str(asof)[:10])
    rows = []
    by = {c["id"]: c for c in cards}
    for cid, h in (pop_history or {}).items():
        c = by.get(cid)
        g = _g(c) if c else None
        if not _ok(g) or g.get("ch30") is None:
            continue
        p = sorted((r[0], r[1]) for r in h if r[1])
        p = [x for x in p if x[0] <= str(d1)]
        if len(p) < 2:
            continue
        end = p[-1]
        start = [x for x in p if (date.fromisoformat(end[0]) - date.fromisoformat(x[0])).days >= 25]
        if not start or (d1 - date.fromisoformat(end[0])).days > 14:
            continue
        s = start[-1]
        if s[1] < 200 or end[1] - s[1] < 500:
            continue
        grow = (end[1] - s[1]) / s[1]
        rows.append((grow, end[1] - s[1], g["ch30"], c, s, end))
    out = []
    big = [r for r in rows if r[0] >= 0.08]
    if not big:
        return out
    falls = sorted([r for r in big if r[2] <= -0.1], key=lambda r: r[0] * -r[2], reverse=True)
    for f in falls[:3]:
        _, add, ch, c, s, e = f
        twin = max((r for r in big if r[3]["set"] == c["set"] and r[2] >= 0.1 and r[3]["id"] != c["id"]), key=lambda r: r[2], default=None)
        g = _g(c)
        hook = f"In un mese sono arrivati {num(round(add, -2))} PSA 10 nuovi di {_label(c)}. Il prezzo? {pct(ch)}."
        numbers = (f"{_label(c)} ({c['set']}): da {num(s[1])} a {num(e[1])} copie in PSA 10 in 30 giorni, Slabprice PSA 10 "
                   f"{eur(g['value'], rate)}, {pct(ch)} nel mese.")
        if twin:
            tg = _g(twin[3])
            numbers += (f" {_label(twin[3])}, stesso set: {pct(twin[0])} di copie, ma il prezzo è salito del {pct(twin[2], False)}, "
                        f"a {eur(tg['value'], rate)}.")
        why = ("Più copie non vuol dire sempre prezzo più basso: conta se chi compra cresce più in fretta di chi manda a gradare."
               if twin else "Quando le copie perfette crescono più in fretta dei compratori, il prezzo scende: succede quasi sempre nei mesi dopo l'uscita.")
        close = "Su quale dei due avresti scommesso?" if twin else "Compri adesso o aspetti che si fermi?"
        items = [dict(card=c["id"], label=_label(c), a=dict(label="Copie PSA 10", val=pct(f[0])), b=dict(label="Prezzo PSA 10", val=pct(ch)))]
        if twin:
            items.append(dict(card=twin[3]["id"], label=_label(twin[3]) + " · stesso set", a=dict(label="Copie PSA 10", val=pct(twin[0])),
                              b=dict(label="Prezzo PSA 10", val=pct(twin[2]))))
        scenes = [dict(t="statement", big=f"+{num(round(add, -2))}", small=f"PSA 10 nuovi in un mese · il prezzo? {pct(ch)}"),
                  dict(t="beforeafter", items=items),
                  dict(t="statement", big="Conta chi compra." if twin else "Più copie, prezzo più basso.",
                       small="Più copie non vuol dire prezzo più basso." if twin else "Finché i compratori non arrivano."),
                  dict(t="question", text=close)]
        out.append(_story("supply", "Offerta contro prezzo", f[0] * -ch * 10 + (0.5 if twin else 0), hook, numbers, why, close,
                          scenes, [c["id"]] + ([twin[3]["id"]] if twin else [])))
    return out


def jumps(cards, rate, asof):
    """A jump or a fall of the last weeks, on real sales (D347). A jump far beyond the card's past goes out with the
    flag check: the reel waits for Oscar."""
    from datetime import date, timedelta
    d1 = date.fromisoformat(str(asof)[:10])
    recent, year = str(d1 - timedelta(days=60)), str(d1 - timedelta(days=425))
    out = []
    for c in cards:
        for g in c.get("grades") or []:
            if not _ok(g, 6) or g.get("ch30") is None or g.get("hi", 0) / max(g.get("lo", 1), 1e-9) >= 1.6:
                continue
            ch = g["ch30"]
            if abs(ch) < 0.3:
                continue
            ss = [s for s in c.get("sales") or [] if s.get("grade") == g["grade"] and (s.get("pgen") is None or s["pgen"] >= 0.5)]
            new = [s["price"] for s in ss if s["date"] >= recent]
            old = sorted(s["price"] for s in ss if year <= s["date"] < recent)
            if len(new) < 3 or len(old) < 3:
                continue
            med_old = old[len(old) // 2]
            check = max(new) > 3 * med_old or (g.get("pop") or 999) <= 50 and max(new) > 2 * med_old
            prev = g["value"] / (1 + ch)
            up = ch > 0
            hook = (f"{_label(c)} PSA {g['grade']} si vendeva a {eur(prev, rate)}. Oggi a {eur(g['value'], rate)}.")
            numbers = (f"{_label(c)} di {c['set']}, PSA {g['grade']}: Slabprice {eur(g['value'], rate)}, {pct(ch)} in 30 giorni, "
                       f"{len(new)} vendite negli ultimi due mesi." + (f" In PSA {g['grade']} ne esistono {num(g['pop'])}." if g.get("pop") else ""))
            why = ("Con poche copie bastano due compratori decisi per spostare il prezzo: la prossima vendita dirà se è un nuovo livello."
                   if up else "Tante vendite, tutte vere: non è un errore, è il mercato che si è riposizionato.")
            close = "Nuovo prezzo o bolla?" if up else "È il momento di comprare o scende ancora?"
            scenes = [dict(t="statement", big=f"{eur(prev, rate)} → {eur(g['value'], rate)}", small=f"{_label(c)} · PSA {g['grade']}"),
                      dict(t="beforeafter", items=[dict(card=c["id"], label=_label(c), a=dict(label="Un mese fa", val=eur(prev, rate)),
                                                        b=dict(label="Oggi", val=eur(g["value"], rate)))]),
                      dict(t="statement", big="Nuovo prezzo o bolla?" if up else "Il mercato si è riposizionato.",
                           small=f"{len(new)} vendite in due mesi"),
                      dict(t="question", text=close)]
            out.append(_story("jump" if up else "fall", "Il salto" if up else "La caduta", abs(math.log(1 + ch)) * (0.6 if check else 1),
                              hook, numbers, why, close, scenes, [c["id"]], check=check, grade=g["grade"]))
    return out


def new_highs(cards, rate, asof):
    """A card that with this week's sales passes its all-time high, with at least two years of history (D347)."""
    out = []
    for c in cards:
        for g in c.get("grades") or []:
            h = [r for r in (g.get("history") or []) if r[1]]
            if not _ok(g, 8) or len(h) < 104:
                continue
            past = max(r[1] for r in h[:-4])
            if g["value"] <= past * 1.05:
                continue
            first = h[0]
            y = first[0][:4]
            hook = f"{_label(c)} PSA {g['grade']} non è mai costato così tanto."
            numbers = (f"{_label(c)} di {c['set']}, PSA {g['grade']}: Slabprice {eur(g['value'], rate)}, sopra il massimo di sempre "
                       f"({eur(past, rate)}). Nel {y} valeva {eur(first[1], rate)}.")
            why = "Un massimo storico con tante vendite vere non è un caso: chi vendeva al vecchio prezzo ha smesso."
            close = "Lo terresti o venderesti adesso?"
            scenes = [dict(t="statement", big="Massimo storico", small=f"{_label(c)} · PSA {g['grade']}"),
                      dict(t="beforeafter", items=[dict(card=c["id"], label=_label(c), a=dict(label=f"Nel {y}", val=eur(first[1], rate)),
                                                        b=dict(label="Oggi", val=eur(g["value"], rate)))]),
                      dict(t="statement", big=eur(g["value"], rate), small=f"prima il massimo era {eur(past, rate)}"),
                      dict(t="question", text=close)]
            out.append(_story("high", "Nuovo massimo storico", math.log(g["value"] / past) * 4 + 0.3, hook, numbers, why, close,
                              scenes, [c["id"]], grade=g["grade"]))
    return out


def week_stories(cards, psa10_share, pop_history, rate, asof):
    """Up to 6 stories, ordered by how surprising they are, at most 2 of a kind and never the same card twice."""
    allc = twin_gap(cards, rate) + era_share(psa10_share) + supply_price(cards, pop_history, rate, asof) + \
        jumps(cards, rate, asof) + new_highs(cards, rate, asof)
    allc.sort(key=lambda s: -s["score"])
    out, per, used = [], {}, set()
    for s in allc:
        k = "move" if s["kind"] in ("jump", "fall") else s["kind"]
        if per.get(k, 0) >= MAX_PER_KIND or used & set(s["cards"]):
            continue
        out.append(s)
        per[k] = per.get(k, 0) + 1
        used |= set(s["cards"])
        if len(out) >= MAX_STORIES:
            break
    return out
