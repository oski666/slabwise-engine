# Slabwise Engine

Motore di valutazione per carte Pokémon **graded**: dalle vendite grezze al fair value di ogni slab, con forchetta calibrata, indici per era e probabilità di deal.

**Prima di toccare qualsiasi cosa leggi [`docs/PILLARS.md`](docs/PILLARS.md).** È vincolante.

## Documenti

| File | Cosa contiene |
|---|---|
| [`docs/PILLARS.md`](docs/PILLARS.md) | I 20 pilastri del progetto: cosa misuriamo, come calcoliamo, come decidiamo |
| [`docs/METHOD.md`](docs/METHOD.md) | Specifica del Modello a Valore Latente (LVM) |
| [`docs/BACKTEST_PROTOCOL.md`](docs/BACKTEST_PROTOCOL.md) | Metriche e criteri di successo, registrati prima dei risultati |
| [`docs/COMPETITORS.md`](docs/COMPETITORS.md) | Metodi pubblici di tcgcharts, TCGBerg, Card Ladder, PriceCharting e loro debolezze |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Registro delle decisioni |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Identità visiva e principi di esperienza |
| [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) | Fonti di dati: cosa è gratis, cosa costa, piano di spesa proposto |
| [`results/REPORT.md`](results/REPORT.md) | Ultimo report del backtest |

## Anteprime (artifact su claude.ai, sempre aggiornati allo stesso link)

| Pagina | Sorgente | Link |
|---|---|---|
| Sito Slabwise (prototipo v7, "Comic Rush") | `prototype/v7/` (`python prototype/v7/build.py`) | https://claude.ai/artifact/5SqHDZq7pKYDRSiw2avnBn |
| Prototipo v6 (archivio, "Trainer Pop") | `prototype/v6/` | si rigenera dal sorgente |
| Prototipo v5 (archivio, "Promo TCG") | `prototype/v5/` | si rigenera dal sorgente |
| Prototipo v4 (archivio, "Riso pop") | `prototype/v4/` | si rigenera dal sorgente |
| Prototipo v3 (archivio, neo-brutalista) | `prototype/v3/` | si rigenera dal sorgente |
| Prototipo v2 (archivio, stile "caveau") | `prototype/v2/` | si rigenera dal sorgente |
| Prototipo v1 (archivio) | `prototype/v1/` (`python prototype/v1/build.py`) | si rigenera dal sorgente |
| Slabwise Reels (studio dei reel) | `social/reel-studio/` (`python social/reel-studio/build.py`) | https://claude.ai/artifact/RrKrYXHyKffCWFtc5vKeqa |
| Risultati del motore v1.1 | `site/` (`python site/build.py`) | https://claude.ai/artifact/MeVzDdK1ZJqU7DyfmTco7T |
| Vendite vere (motore rigiocato su eBay, Goldin, Fanatics) | `scripts/real_report.py` poi `python site/build_real.py` | https://claude.ai/artifact/HxkBwCQh7ZEPXBjXEuPX9i |
| Slabby (personaggio sostituibile) | `prototype/character/slabby/character.json` | vedi il README della cartella |

Le pagine costruite non si salvano nel repository: si rigenerano dal sorgente.

## Struttura

```
slabwise/
  schema.py      schema dei dati che ogni fonte deve rispettare
  sim.py         mercato simulato con verità nota e contaminazione realistica
  identity.py    livello di identità: duplicati, cert, lotti, Best Offer
  baselines.py   ricostruzioni dei metodi dei concorrenti
  model.py       Modello a Valore Latente (LVM)
  calibrate.py   stima dei parametri sul periodo di addestramento
  backtest.py    backtest walk-forward, metriche, test dei deal
scripts/
  run_seed.py    calibrazione + backtest per un seme
  run_all.sh     tutte le esecuzioni del protocollo
  make_report.py report e grafici
  example_chart.py  grafici illustrativi
tests/           test (incluso: nessun metodo guarda il futuro)
prototype/       prototipo del sito (v1) e dati catalogo/immagini TCGdex
social/          studio dei reel, character sheet di Slabby, versioni archiviate
site/            pagina dei risultati del backtest
```

## Anteprima sul tuo computer

Doppio clic su `anteprima.bat` (Windows) o `./anteprima.sh`: ricostruisce `prototype/v7/slabwise.html` e lo apre. Guida passo passo, compreso il cambio del personaggio con sole PNG: [`docs/GUIDA_LOCALE.md`](docs/GUIDA_LOCALE.md).

## Uso

```bash
pip install numpy scipy pandas matplotlib pytest
python -m pytest -q tests                  # ~10 s
PYTHONPATH=. python scripts/run_seed.py 1  # un seme: ~8 min (calibrazione + backtest)
./scripts/run_all.sh                       # protocollo completo: ~2 ore su 2 core
PYTHONPATH=. python scripts/make_report.py
```

## Dati reali

Qualsiasi fonte di vendite singole si collega convertendola allo schema di `slabwise/schema.py` (colonne osservate, senza le colonne `t_`). La verifica dei cert usa la PSA Public API (token personale; accesso riservato ai clienti approvati). Ogni fonte si registra in `docs/DATA_SOURCES.md` con provenienza e rischi.
