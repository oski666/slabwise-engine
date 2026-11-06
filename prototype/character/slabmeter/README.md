# Slab-Meter: il personaggio del termometro (D194, D196, D197)

Metti in questa cartella **una PNG con lo sfondo trasparente per ogni stato del mercato**. Il sito mostra quella dello stato di oggi nella sezione Slab-Meter della home. Se una PNG manca, il sito usa il termometro disegnato di serie (SVG, in `prototype/v7/src/app.html`, funzione `thermoSvg`).

| File | Stato | Quando | Cosa dovrebbe esprimere la posa |
|---|---|---|---|
| `esplode.png` | esplode | punteggio ≥ 80 (≥ 40,2°) | febbre: mercurio in cima, tappo che salta, occhi a spirale |
| `caldo.png` | caldo | 60–80 (38,4°–40,2°) | suda, si sventola |
| `tiepido.png` | tiepido | 40–60 (36,6°–38,4°) | tranquillo, sorride |
| `freddo.png` | freddo | 20–40 (34,8°–36,6°) | sciarpa, trema |
| `gelo.png` | gelo | < 20 (< 34,8°) | congelato, chiuso nel ghiaccio |

**Formato consigliato:** verticale, circa 600×1100 px (proporzione 1:1,9 come il disegno di serie), personaggio centrato in basso, sfondo trasparente. Il build ritaglia i bordi vuoti, rimpicciolisce a 900 px di altezza e incorpora l'immagine nella pagina; i file originali non vengono toccati.

**Il movimento lo aggiunge il sito**, uguale per ogni posa, quindi la PNG può essere ferma:
- esplode: saltella; stelline che volano e vapore sopra la testa;
- caldo: rimbalza veloce; vapore;
- tiepido: dondola piano;
- freddo e gelo: tremano; neve che cade (gelo: anche il cubo di ghiaccio che si crepa e va in pezzi davanti).

Tutto si ferma per chi ha chiesto meno animazioni nel sistema. Per vedere tutte le pose, comprese quelle che mancano, apri `#pose` sul sito dopo essere entrato nello studio.
