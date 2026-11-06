# Slabby: il personaggio sostituibile

**Il modo più semplice (solo PNG):** metti in questa cartella 7 PNG con lo sfondo trasparente chiamate `smug.png`, `bliss.png`, `laugh.png`, `drool.png`, `shock.png`, `sleep.png`, `peek.png`. Un file con il nome di una posa ha sempre la precedenza su quello che dice `character.json`. Poi doppio clic su `anteprima.bat` nella cartella principale (guida completa: `docs/GUIDA_LOCALE.md`).

Le PNG attuali sono Slabby v2, un personaggio originale (uno slab vivente: custodia lilla, carta nera, etichetta arancione con il voto), disegnato in `prototype/character/draw/slabby_v2.py`. Le pose SVG dentro `character.json` sono lo Slabby v1, usato solo se manca la PNG di una posa.

**Il personaggio vive tutto in questa cartella.** Il sito (`prototype/v6/build.py`) legge `character.json` (colori, carattere, pose di riserva) e le PNG delle pose. Il resto del sito non si tocca.

## Il formato di `character.json`

```json
{
  "name": "Slabby",
  "version": "1",
  "colors": {
    "main": "#2EE6FF", "accent": "#FF2E93", "gold": "#FFC93C", "ink": "#0E1A5C",
    "bubble": "#ffffff", "bubble_ink": "#0E1A5C"
  },
  "font": "Mochiy Pop One",
  "defs": "…parti SVG condivise tra le pose (facoltativo)…",
  "poses": {
    "smug":  {"image": "smug.png"},
    "bliss": {"viewBox": "0 0 200 220", "svg": "<path …/>"},
    "…":     "…"
  }
}
```

| Campo | Cosa fa sul sito |
|---|---|
| `colors.main` | alone dietro Slabby nella testata |
| `colors.ink` | contorno dei fumetti |
| `colors.bubble`, `colors.bubble_ink` | sfondo e testo dei fumetti |
| `colors.accent`, `colors.gold` | a disposizione dei disegni e delle prossime scene |
| `font` | carattere dei fumetti; deve essere un font di Google Fonts, scritto come lì (es. "Mochiy Pop One") |
| `poses` | le 7 pose, tutte obbligatorie |

Ogni posa si può dare in due modi:
- **immagine** nella stessa cartella: `{"image": "smug.png"}`. Vanno bene PNG o WebP con lo sfondo trasparente (meglio almeno 800 px di altezza) oppure SVG. Il sito la incorpora nella pagina, quindi niente indirizzi esterni (non funzionerebbero);
- **disegno SVG dentro il file**: `{"viewBox": "...", "svg": "..."}`. È il modo in cui è scritto lo Slabby attuale.

## Le 7 pose

| Nome | Quando appare |
|---|---|
| `smug` | posa normale: accoglie e presenta le sezioni; grande nella testata |
| `bliss` | spiega qualcosa di cui va fiero (la forchetta) |
| `laugh` | pagina Settimana, cose divertenti |
| `drool` | passi sopra un affare |
| `shock` | vendita sospetta o annuncio falso |
| `sleep` | dopo 45 secondi senza attività |
| `peek` | quando è zittito: spunta solo la testa (più largo che alto) |

### Pose facoltative (i dispetti, D44)

Se nella cartella c'è una PNG con uno di questi nomi, il sito la usa; se manca, usa la posa obbligatoria tra parentesi.

| Nome | Quando appare |
|---|---|
| `run.png` (`laugh`) | corre attraverso lo schermo; disegnalo di profilo, rivolto verso destra (il sito lo specchia quando corre a sinistra) |
| `cling.png` (`peek` capovolto) | appeso al bordo in alto quando scorri troppo veloce; disegnalo già appeso, mani in alto |
| `sit.png` (`smug`) | seduto sopra i titoli delle sezioni, gambe a penzoloni |
| `tongue.png` (`laugh`) | linguaccia quando lo zittisci |
| `wave.png` (`bliss`) | saluta accanto alla ricerca |
| `peek_top.png` (`peek`) | spunta da dietro lo slab quando apri una carta: testa e mani che escono da un bordo in basso (la parte bassa del disegno resta nascosta dietro lo slab) |
| `peek_side.png` (`smug`) | sbuca dal lato destro dello slab quando ci passi sopra: si sporge di lato, mezzo nascosto; disegnalo rivolto verso sinistra |
| `teacher.png` (`smug`) | il maestro: occhiali e bacchetta, spiega la pagella di una carta; disegna la bacchetta alzata verso sinistra (il fumetto è a sinistra); il sito lo fa oscillare leggermente come se battesse la bacchetta |

Per vedere quali file ci sono e quali mancano, apri l'anteprima e vai su **Pose del personaggio** in fondo alla pagina (indirizzo `#pose`): ogni riquadro mostra la posa usata e, se manca, quale la sostituisce.

Ogni posa: personaggio intero e centrato, piedi in basso, nessuna scritta dentro. Se il disegno è SVG, gli id interni hanno un prefisso proprio (oggi `pp-`) per non scontrarsi con il resto della pagina.

## Come si sostituisce

1. Metti le immagini delle pose in questa cartella (es. `smug.png`, `bliss.png` …).
2. In `character.json` scrivi per ogni posa `{"image": "nome-file"}`, aggiorna `colors` e `font`.
3. Carica tutto su GitHub in `prototype/character/slabby/` (o dimmi dove sono): io aggiorno, eseguo `python prototype/v6/build.py` e ripubblico il sito allo stesso link.

Se manca una posa o un colore, la costruzione si ferma e dice cosa manca. La cartella `generations/` conserva i file dei generatori d'immagini: il sito non li usa.


## Pose facoltative aggiunte dopo (D201)

| File | Dove appare | Se manca |
|---|---|---|
| `teacher.png` | quando apri una carta entra accanto al prezzo, ci batte sopra la bacchetta e se ne va | non appare |
| `side.png` | in basso nella barra del menu, sempre visibile (computer) | usa `peek.png` |
