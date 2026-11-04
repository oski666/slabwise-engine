# Slabwise · Pilastri

**Versione 1.0 · 23 ottobre 2026 · Stato: vincolante**

Questo documento è la costituzione del progetto. Ogni decisione su metodo, dati e perimetro deve essere coerente con questi pilastri.

**Regola di modifica.** Un pilastro si cambia solo così: prima si aggiorna questo file, con una voce datata in `docs/DECISIONS.md` che spiega perché, e solo dopo si cambia il codice. Claude li segue alla lettera. Se una richiesta li contraddice, lo dice prima di agire.

---

## A. Cosa misuriamo

**P1 · Solo carte graded.** Le carte raw sono escluse da tutto: non entrano come dati, non servono da soglia, non compaiono nei valori. Il prodotto parla solo di slab.

**P2 · L'atomo.** L'unità di valore è *carta × stampa (variante, lingua, edizione) × ente di grading × voto*. Due atomi non si mescolano mai. I voti di enti diversi non sono equivalenti (un CGC 10 non è un PSA 10): ogni ente ha la sua scala dei voti.

**P3 · Solo vendite concluse.** Il valore si costruisce solo da vendite concluse e pagate. Gli annunci attivi non entrano mai nel valore; servono solo per trovare i deal.

**P4 · Prima l'identità, poi il prezzo.** Una vendita entra nel calcolo solo dopo aver stabilito *cosa* è stato venduto: duplicati rimossi, cert verificato quando c'è, lotti e Best Offer senza prezzo accettato esclusi. Ciò che non si riesce ad attribuire a un atomo resta fuori, con il motivo registrato.

**P5 · Due verità separate.** Il *valore di mercato* è in dollari, sul mercato globale, per una copia tipica venduta su eBay. Il *costo per chi compra in Italia* (IVA, dogana, spedizione, cambio BCE) è un calcolo separato. Non si confrontano mai numeri dei due mondi senza conversione esplicita.

## B. Come calcoliamo

**P6 · Un modello, non una pila di regole.** Il valore viene da un unico modello probabilistico (il *Modello a Valore Latente*, `docs/METHOD.md`). Memoria del passato, peso delle vendite anomale, scala dei voti e prestito dalle carte simili sono conseguenze del modello, non regole aggiunte. Nessuna soglia fissata a occhio nel calcolo del valore.

**P7 · I parametri si stimano dai dati.** Ogni parametro del modello è stimato su un periodo di addestramento e congelato prima del periodo di verifica. Le costanti scelte a mano sono ammesse solo come priori deboli, dichiarati in `METHOD.md`.

**P8 · Nessuna vendita sparisce in silenzio.** Ogni vendita riceve una probabilità di essere genuina e, se pesa poco, un motivo leggibile. Le vendite non si cancellano: pesano in proporzione a quanto sono credibili.

**P9 · I cambi di mercato sono veri finché i dati concordano.** Più vendite indipendenti (cert diversi) che indicano lo stesso nuovo livello segnalano un cambio di mercato, non un errore. Il metodo non deve mai "difendere" un prezzo vecchio contro un mercato che si è spostato.

**P10 · Ogni valore ha un intervallo onesto.** Ogni valore esce con un intervallo all'80%. Nel backtest l'intervallo deve contenere il valore vero tra il 75% e l'85% delle volte. L'evidenza mostrata all'utente è questo intervallo (sul sito: "intervallo di valore", in inglese "value range"), non un punteggio inventato.

**P11 · Causalità.** Il valore di un giorno usa solo dati disponibili fino a quel giorno. Il backtest procede in avanti nel tempo (walk-forward), senza mai guardare il futuro.

## C. Come decidiamo

**P12 · Prove prima delle opinioni.** Un cambiamento al metodo entra solo se migliora il backtest secondo le metriche di `docs/BACKTEST_PROTOCOL.md` e non peggiora nessuna fascia di liquidità. Le soglie di successo si fissano prima di vedere i risultati.

**P13 · Confronto con i concorrenti.** Ogni versione del metodo viene messa in gara con le ricostruzioni dei metodi pubblici dei concorrenti (ultima vendita, mediana a fasce di tcgcharts, media pesata per età di PriceCharting, ultima vendita spostata dall'indice di Card Ladder, pila di regole tipo TCGBerg) e con il nostro prototipo precedente. Se non vinciamo, non lo diciamo.

**P14 · Simulato prima, reale poi.** Il metodo si mette alla prova prima su un mercato simulato in cui la verità è nota, poi su vendite reali con la metrica della "vendita successiva". Un risultato simulato non si presenta mai come risultato reale.

## D. Cosa pubblichiamo

**P15 · Deal = probabilità.** Un deal è un annuncio con alta probabilità di valere più del suo costo, per una copia di quell'atomo, dopo il costo finale in Italia. Uno sconto "troppo bello" alza il sospetto, non il punteggio.

**P16 · Rollup onesti.** Market cap, set ed ere separano sempre la crescita dovuta ai prezzi da quella dovuta ai nuovi slab, e mostrano concentrazione (peso delle prime 3 carte) e copertura (quante carte del gruppo seguiamo). Gli indici per era nascono dal fattore di mercato del modello.

**P17 · Trasparenza.** La metodologia pubblica dice come calcoliamo e dove siamo deboli.

## E. Come lavoriamo

**P18 · (rimosso il 23 ottobre 2026, D26).** Era "Fonti lecite". Ogni nuova fonte si registra comunque in `docs/DATA_SOURCES.md` con provenienza, costo e rischi.

**P19 · Costo zero finché non si decide altrimenti.** Nessuna spesa senza una decisione esplicita nel registro. Il codice deve funzionare con qualsiasi fonte che rispetti lo schema dei dati (`slabwise/schema.py`).

**P20 · Requisiti prima del codice.** Le funzioni nuove si concordano prima di costruirle. Il repository è la fonte di verità: ciò che non è qui non è deciso.
