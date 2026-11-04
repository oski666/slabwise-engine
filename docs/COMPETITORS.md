# Concorrenti: metodi pubblici e loro debolezze

Ricostruzioni usate nel backtest (`slabwise/baselines.py`). Dove un sito non pubblica un parametro, lo diciamo e usiamo la lettura più naturale.

## tcgcharts
**Fonte:** pagina metodologia (letta il 22–23 ottobre 2026).
- Vendite eBay (96%), Fanatics Collect e poche case d'asta. Principio "100% sicuri o niente".
- **Prezzo per voto**: mediana semplice della prima finestra con abbastanza vendite: 7+ vendite in 14 giorni → mediana delle ultime 7; altrimenti tutte quelle degli ultimi 28 giorni; poi 90; poi le ultime 3 di qualsiasi età.
- **Guardia sui bassi** (solo fasce 2–4): se ci sono almeno 5 delle 15 vendite precedenti entro un anno, scarta quelle sotto (minimo delle 15) ÷ 4. Le vendite alte non si scartano mai.
- **Market cap** = Σ copie × prezzo per voto. **Indici** PKMN200 e GRAIL25, pesati per valore, senza tetto.
- **Debolezze ammesse da loro**: una vendita da 3,72 milioni su una carta con 3 copie produce 11,2 milioni di market cap; finestre sottili mediano gli outlier (100 $ e 9.999 $ danno 5.049,50 $); vendite mal classificate distorcono i prezzi.
- **Debolezze nostre analisi**: nessun prestito tra voti o carte; nessuna forchetta; la mediana dà ragione alla maggioranza anche se è contaminata (inondazione di falsi).

## TCGBerg
**Fonte:** pagine metodologia, fair value e deal (lette il 23 ottobre 2026).
- Atomo stampa × ente × voto; solo PSA 6–10 valutati; solo vendite concluse.
- **Pila di regole**: più stimatori in parallelo (momentum, valore centrale robusto, ancora alla finestra recente, trend "solo se statisticamente reale") miscelati in base a dispersione, densità di scambi, forza del trend e tempo dall'ultima vendita. Recinto asimmetrico (bassi scartati, alti tenuti se confermati), taglio delle code, aggiustamento con i pari "smorzato e con tetto", scala dei voti stimata insieme, alcuni coefficienti fissati offline.
- **Evidenza** 0–100 da cinque fattori; **deal** = annuncio sotto il fair value + cascata di verifiche (voto, stampa, cert) + punteggio a 4 componenti.
- **Debolezze ammesse**: valori deboli ma pubblicati su campioni sottili; aste e marketplace pesati uguale; parametri non pubblicati.
- **Debolezze nostre analisi**: molti parametri a mano e interazioni tra regole difficili da verificare; il punteggio di evidenza non è una probabilità calibrata; il deal è uno sconto sul fair value, quindi soffre la "maledizione del vincitore".
- Il nostro prototipo precedente (Slabwise v0) era molto simile: lo usiamo nel backtest come rappresentante di questo approccio.

## Card Ladder
**Fonte:** articolo di aiuto "What is Card Ladder Value?".
- **CL Value** = ultima vendita ancorata e mossa ogni giorno dall'indice del giocatore o del mercato; fiducia da 1 a 5 secondo quanto è recente l'ultima vendita.
- **Debolezze**: se l'ultima vendita è anomala, l'errore resta e viene trascinato dall'indice; nessuna media tra vendite.

## PriceCharting
**Fonte:** pagina "Overview of Our Methodology".
- Vendite eBay; considera ultima vendita, mediana, media e media pesata per età; filtri a parole chiave; outlier segnalati e rivisti a mano ogni giorno.
- **Debolezze**: dipende dalla revisione manuale; media aritmetica sensibile alle code; lenta nei cambi di mercato.

## Risultato del confronto
Vedi `results/REPORT.md`.

## GoCollect Collectible Price Index (fumetti; letto il 23 ottobre 2026)

Fonte: [Introducing the GoCollect Collectible Price Index](https://gocollect.com/blog/introducing-the-gocollect-collectible-price-index).

- **Struttura alla Dow Jones**: un paniere scelto a mano di titoli rappresentativi per ogni era (Golden, Silver, Bronze, Copper, Modern, con date precise); es. Copper Age 50 albi, più voti per albo. Paniere rivisto ogni trimestre; un **divisore** rende continuo l'indice quando entrano o escono titoli o voti.
- **Prezzo di ogni voce** = media delle **ultime 4 vendite** valide per quel voto (solo etichetta CGC Universal, vendita verificabile, niente Best Offer con prezzo nascosto). Fasce di voto scelte dai voti più comuni (es. 8.0–9.8).
- **Pesi**: per prezzo (come il Dow), non per capitalizzazione; esclusi i pezzi iconici troppo cari, raccolti in un indice a parte ("Big Spenders", vendite ≥ 250.000 $).
- Aggiornamento settimanale il lunedì, con una settimana di ritardo.
- **Debolezze**: il peso per prezzo fa dominare i titoli cari; la media delle ultime 4 vendite è rumorosa e in ritardo per i voti poco scambiati; niente gestione statistica degli anomali oltre alle regole di validità.
- **Cosa ci serve**: l'idea di un indice d'era **pubblicato separato dal modello**, costruito su un paniere fisso di carte liquide, con divisore e revisione periodica, e le date esplicite delle ere. Al posto della media delle ultime 4 vendite useremmo i nostri fair value (tutte le vendite, pesate per probabilità genuina).


## PokeMarket (pokemarketcap.com; letto il 24 ottobre 2026)

Sito solo Pokémon di una persona (Obsidian Grid LLC), stile "terminale" scuro con accento verde. Premium 9,99 $/mese (storico completo, analisi, tutti i tagli dell'indice, negozio di sigillati sotto prezzo con coda).
- **Indice**: base 100 al 1° gennaio 2021 (337,2 al 23 ottobre 2026); si muove solo con rendimenti concatenati della **stessa carta**, quindi aggiungere carte non lo sposta; 11.648 componenti; tagli per era, set, Pokémon, rarità. Pesi e revisione non dichiarati.
- **Prezzi** (pagina "Methodology"): solo vendite vere, mai prezzi chiesti; nessun risultato del modello rientra come dato; 10 filtri all'ingresso contro variante sbagliata, voto sbagliato, asta "dito grasso"; una vendita isolata contraddetta dalle altre sposta il prezzo solo in parte finché non è confermata; ogni stima ha una **fascia di fiducia dichiarata: LIVE, MODELED, LOW CONFIDENCE**; le carte ferme seguono il loro gruppo **dentro limiti rigidi (al massimo 4× in tutto)**; lo storico si ricalcola con le vendite nuove ma il prezzo di oggi è calcolato a parte e non cambia per il ricalcolo; aste e vendite da 2.500+ catture controllate a mano per le carte che eBay non vede.
- **Dati mostrati**: market cap graded (10,44 mld $), mappa dei set per capitalizzazione, popolazione e tasso di PSA 10 (gem rate), vendite recenti, annunci.
- **Fonti**: non dichiarate.
- **Cosa ci serve**: le tre fasce di fiducia come etichetta leggibile sopra la forchetta; il limite rigido alla deriva delle carte senza vendite; la frase "il prezzo di oggi non è piegato dal ricalcolo dello storico" come principio da verificare nel nostro filtro; mappa dei set per capitalizzazione quando avremo le popolazioni. Il loro indice concatenato sulla stessa carta conferma la scelta della v1.4 (D38–D39).

## Chase Society (chasesociety.com; letto il 24 ottobre 2026)

Sito editoriale quotidiano (newsletter "The Daily Chase", notizie, classifiche) su più giochi; Pokémon inglese e giapponese. Il sito ha un controllo anti-bot (Vercel): letto solo come visitatore, senza aggirarlo.
- **Prezzi**: "prezzo di mercato combinato" preso da **PriceCharting**; avvertenza esplicita: "stime aggregate da più fonti, possono essere sbagliate… da trattare come indicazione, non come prezzo di transazione".
- **Segnali**: cinque per carta (Momentum, Liquidità, Pressione dell'offerta, Verdetto gem, Artista), mostrati come conteggio "5/5 segnali allineati", con la regola "un conteggio descrive oggi, non è una previsione né una fiducia". Le formule non sono pubblicate.
- **Conviene gradarla?**: prezzo raw NM, valore PSA 10, costo di gradazione, probabilità di ogni voto dalla popolazione PSA della carta ("della carta, non di questa copia") → guadagno atteso per copia dopo le spese e voto minimo per andare in pari. Pro (prezzo non indicato): probabilità complete, PSA 9 accanto al 10, foglio d'invio per la gradazione.
- **Fanatics Record Watch**: tutti i lotti Pokémon da 40.000 $ in su su Fanatics Collect, letti dall'archivio vendite pubblico con il **flag di pagamento**: 233 lotti risultano non pagati (26,8 mln $), 59 spariti dall'archivio; caso di studio sul Pikachu Fujishima da 8,4 mln $ prima non pagato, poi sparito, poi annullato. CSV scaricabili.
- **Altro**: annunci eBay più economici per voto, sondaggio "dove va fra 30 giorni?", pulsante "scarica il grafico" per i social, classifiche settimanali.
- **Cosa ci serve**: (1) **i lotti d'asta non pagati o annullati sono vendite false**: il flag di pagamento di Fanatics va letto e usato nel nostro filtro delle vendite (pgen); (2) la pagina "Conviene gradarla?" ma vedi il conflitto con D1 qui sotto; (3) i segnali come conteggio onesto, calcolati dal nostro modello; (4) "scarica il grafico" e il sondaggio per il lato social.
- **Conflitto con D1**: "Conviene gradarla?" ha bisogno del prezzo della carta raw, che D1 ha tolto dal progetto. Si può fare solo con una decisione nuova che riammetta il prezzo raw come dato d'ingresso di questo solo strumento.

## Pikawu 皮卡屋 (pikawu.com; letto il 25 ottobre 2026)

Servizio di Taiwan, in cinese tradizionale, che vive soprattutto in un **bot di LINE**: ricerca prezzi, dati graded, collezione, aste tra privati. Pokémon, One Piece, Dragon Ball. Dichiara oltre 5 milioni di transazioni e un milione di ricerche al mese.
- **Fonti**: vendite PSA 10 (e PSA 9, raw "stato A") da **SNKRDUNK** ed **eBay**; i termini (§5.1) dicono che i dati "non sono generati né verificati" da loro e non includono cambio, commissioni, tasse d'importazione.
- **Metodo**: non pubblicato. Nessun filtro delle vendite anomale dichiarato.
- **Funzioni**: ricerca per testo, per **numero di cert PSA** e per **foto** (riconoscimento); andamento, massimo, media e minimo delle vendite PSA 10 e numero di vendite in N giorni; **grafici a candele** giornalieri e settimanali con medie mobili, supporti e resistenze, volumi; popolazione ("tiratura") e quota di 10 ("滿分率"), un "indice di difficoltà di circolazione"; stima del guadagno dal mandare a gradare; **analisi della centratura da foto** (bordi allineati a mano o in automatico, punteggio per PSA, BGS, TAG; per il PSA 10 il fronte entro 55/45 e il retro entro 75/25); classifiche giornaliere di rialzi, ribassi e volumi su settimana, mese, trimestre, semestre, separate per inglese e giapponese; collezione con costo, guadagno realizzato e non realizzato; sei valute.
- **Prezzi**: gratis (5 analisi al giorno con 24 ore di ritardo), Super 499 NT$/mese (circa 14 €), Master 799 NT$/mese, famiglia 1.249 NT$/mese.
- **Termini**: vietato estrarre dati con bot e aggirare le quote (§三.4), vietato l'uso commerciale dei dati senza consenso scritto (§三.5); nessuna API.
- **Cosa ci serve**: (1) grafico a candele settimanali delle vendite vere sotto la nostra linea del valore, con i volumi; (2) classifiche per finestra (settimana, mese, trimestre, semestre); (3) ricerca per numero di cert, che con i cert dell'archivio Fanatics diventa "la storia di questo slab" (tutte le volte che è stato rivenduto); (4) analisi della centratura da foto, che non ha bisogno dei prezzi raw (D1, D48); (5) un bot di messaggistica (per l'Italia Telegram o WhatsApp) per chiedere un prezzo al volo. **Dove siamo più forti**: metodo pubblico, vendite anomale filtrate, forchetta, costo in euro con IVA e dogana.
