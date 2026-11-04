# Guida: aggiornare il repository e vedere l'anteprima sul tuo computer

Questa guida è per Windows. Serve una sola preparazione iniziale; poi ogni modifica si vede con un doppio clic.

## 1. Preparazione (una volta sola)

1. **Git**: scarica e installa *Git for Windows* da git-scm.com (opzioni predefinite). Se sul PC dell'ufficio non puoi installare programmi, usa *GitHub Desktop* (desktop.github.com), che spesso non chiede permessi di amministratore.
2. **Python**: installa Python 3 da python.org; durante l'installazione spunta **"Add python.exe to PATH"**. In alternativa va bene quello del Microsoft Store.
3. **Scarica il repository**. Apri il *Terminale* (o *Prompt dei comandi*) e scrivi:
   ```
   cd %USERPROFILE%\Documents
   git clone https://github.com/oski666/slabwise-engine.git
   cd slabwise-engine
   py -m pip install pillow numpy
   ```
   Con GitHub Desktop: *File → Clone repository → slabwise-engine*, poi apri il terminale nella cartella e scrivi solo l'ultima riga.

Pillow è facoltativo: serve a ritagliare i bordi trasparenti delle pose PNG e a ridurle se sono enormi.

## 2. Vedere l'anteprima

Nella cartella `slabwise-engine` fai **doppio clic su `anteprima.bat`**. Lo script ricostruisce la pagina e la apre nel browser. La pagina è un unico file, `prototype\v7\slabwise.html`: non serve nessun server.

Se preferisci vederla su `localhost` (per esempio dal telefono sulla stessa rete Wi-Fi):
```
py -m http.server 8000
```
poi apri http://localhost:8000/prototype/v7/slabwise.html. Per fermarlo: Ctrl+C nel terminale.

Ogni volta che modifichi un file, rilancia `anteprima.bat` (o ricarica la pagina dopo averlo rilanciato).

## 3. Cambiare il personaggio (solo immagini PNG)

1. Prepara 7 PNG **con lo sfondo trasparente**, una per posa, con questi nomi esatti:

   | File | Quando appare |
   |---|---|
   | `smug.png` | posa normale; grande nella testata |
   | `bliss.png` | contento, quando spiega l'intervallo di valore |
   | `laugh.png` | ride, pagina Settimana |
   | `drool.png` | un affare |
   | `shock.png` | vendita sospetta o falso |
   | `sleep.png` | dorme dopo un po' di inattività |
   | `peek.png` | spunta solo la testa, quando lo zittisci |

   Personaggio intero e centrato, piedi in basso, nessuna scritta. Meglio almeno 800 px di altezza. Margini trasparenti e dimensioni troppo grandi li sistema da solo lo script.
2. Copiale in `prototype\character\slabby\`, **sostituendo** i file con lo stesso nome.
3. (Facoltativo) In `prototype\character\slabby\character.json` cambia i colori del fumetto (`bubble`, `bubble_ink`, `ink`) e il carattere (`font`, un nome di Google Fonts).
4. Doppio clic su `anteprima.bat`.

Basta anche cambiare una posa sola: le altre restano quelle di prima. Se una posa manca del tutto, lo script si ferma e dice quale file aggiungere.

Oltre alle 7 pose obbligatorie ce ne sono 7 facoltative per i dispetti di Slabby (`run`, `cling`, `sit`, `tongue`, `wave`, `peek_top`, `peek_side`). La pagina **Pose del personaggio** (link in fondo all'anteprima, oppure `slabwise.html#pose`) mostra ogni posa, dove appare e quale file la sostituisce finché manca.

## 4. Salvare le modifiche su GitHub

Dal terminale, nella cartella del repository:
```
git pull
git add -A
git commit -m "Descrivi cosa hai cambiato"
git push
```
Con GitHub Desktop: scrivi una descrizione in basso a sinistra, *Commit to main*, poi *Push origin*.

Prima di lavorare fai sempre `git pull` (o *Fetch origin* in GitHub Desktop), così prendi anche le modifiche fatte da me.

## 5. Problemi frequenti

| Messaggio | Cosa fare |
|---|---|
| Lettere strane al posto di accenti o giapponese | Rilancia `anteprima.bat` dopo `git pull`: la pagina ora dichiara la codifica UTF-8 (prima il browser la leggeva come testo Windows) |
| `'py' non è riconosciuto…` | Python non è nel PATH: reinstallalo spuntando "Add python.exe to PATH", oppure usa `python` al posto di `py`. |
| `manca la posa 'peek'…` | Manca un file: aggiungi `peek.png` nella cartella del personaggio. |
| La pagina si apre ma il personaggio ha un riquadro bianco | La PNG non ha lo sfondo trasparente: riesportala con la trasparenza. |
| Il personaggio ha un contorno chiaro attorno | Serve Pillow (`py -m pip install pillow numpy`): lo script toglie da solo l'alone lasciato dallo sfondo chiaro. Se resta, la scontornatura ha lasciato più di qualche pixel di sfondo: rifalla un po' più stretta. |
| `git push` rifiutato | Fai prima `git pull`, poi di nuovo `git push`. |
| Lo script `.bat` è bloccato dal PC aziendale | Apri il terminale nella cartella e scrivi `py prototype\v7\build.py`, poi apri `prototype\v7\slabwise.html` con il browser. |

I dati veri del sito sono in `prototype\data\real.json`: li aggiorno io quando raccolgo nuove vendite. Il motore (stime, backtest) non serve per l'anteprima.
