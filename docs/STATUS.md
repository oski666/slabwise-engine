# Slabwise · Stato del progetto

**Aggiornato il 16 novembre 2026, sera** (punti 1–4 della revisione del 16 novembre: D303–D306). Fotografia per chi riprende il lavoro (una chat nuova, o Oscar). Non sostituisce le regole: prima di toccare qualcosa leggi `CLAUDE.md` e `docs/PILLARS.md`; le scelte stanno in `docs/DECISIONS.md` (ultima voce D313), il metodo in `docs/METHOD.md`, le prove in `docs/BACKTEST_PROTOCOL.md`, le fonti in `docs/DATA_SOURCES.md`.

## In breve

- **Sito**: slabwise.pages.dev, in sviluppo; Oscar lo usa come anteprima di quello che vedrà il pubblico. Nessuna anteprima separata (l'anteprima `giappone` è stata eliminata, D290).
- **Catalogo**: 820 carte inglesi e 559 stampe giapponesi (16 novembre).
- **Motore**: v1.20 (D210), con il ricalcolo veloce del §60 tutti i giorni tranne il 1° del mese (D286); ricostruzione completa a mano con l'opzione `full` del workflow Sito.
- **Repository**: `oski666/slabwise-engine` (pubblico, codice e sito) e `oski666/slabwise-data` (privato: dati grezzi, D163). Le Actions del repository privato sono bloccate dalla fatturazione: tutto gira nelle Actions del repository pubblico, che legge e scrive i dati privati con il segreto `DATA_TOKEN`.
- **Proprietario**: Oscar. Si scrive in italiano.

## Cosa è cambiato negli ultimi giorni (D274–D302)

| Area | Stato | Decisioni |
|---|---|---|
| Vendite sospette | Regola che le segnala (prezzo oltre 5 volte o sotto un quinto della mediana vicina); revisione settimanale di Oscar su una issue del repository privato (la n. 1 è aperta, 30 vendite); le escluse vanno in `data/raw/eccezioni/registro.json` | D274, D275 |
| Pulizia dei titoli | §62 (titoli in giapponese) adottato con verifica al 26 novembre; §64 adottato; §63 e §63b non passati | D281–D285 |
| Ricalcolo veloce | §60 adottato: le carte nuove entrano senza ricostruire tutto | D277, D279, D286 |
| Mercati giapponesi | SNKRDUNK (prezzo fisso) e Cardova (aste pagate) nei valori del sito, in dollari al cambio BCE; decisione di Oscar senza prova; citazione di Cardova da decidere prima del lancio pubblico. Dal 16 novembre anche le vendite SNKRDUNK lette da tcgcharts (Marek le ha integrate; circa 3 volte le nostre, storico da agosto): per carta × voto × settimana resta la copia con più scambi. Ricostruzione completa fatta il 16 | D280, D292, D302 |
| Nomi giapponesi | Nome e set in inglese, didascalia "Solo in Giappone" o "Stampa giapponese" con il nome originale | D291 |
| Immagini | Database ufficiale giapponese (151 carte) e, per le carte che nessun'altra fonte copre, tcgcharts con il permesso di Marek (primo giro: 43 su 294; molti errori 500 di tcgcharts) | D288, D298 |
| SlabRange | Adottato il §61b Q2: la forchetta è dove sono cadute 8 vendite su 10 della carta (percentili 10 e 90 degli scarti, mescolati con l'era × fascia di voto). Copertura 81%. Secondo giro al giro mensile; Classica e Di mezzo (74%, 76%) da guardare | D293–D295 |
| Indici per voto | PSA 10, 9, 8 per era sul sito: pagina `#indici-voto`, riquadro nelle pagine d'era, confronto voto per voto sulla pagina della carta | D296 |
| Raccolta tcgcharts | Era ferma dal 5 al 14 novembre (il giro non stava più nei 90 minuti). Ora legge per scadenza e si ferma in tempo | D297 |
| Gemelle giapponesi | Ricerca rifatta senza bisogno di TCGdex (workflow "Gemelle giapponesi"), le più popolate prima; senza TCGdex una gemella vale solo con illustrazione uguale (D301; 15 collegamenti sbagliati del primo giro tolti il 14 novembre). Al 16 novembre 214 inglesi su 820 con la gemella collegata, 190 ancora da cercare (4-5 giri da mezz'ora, uno alla volta nella coda tcgcharts) | D299, D301 |
| Ingresso carte | 14 novembre 206 entrate, 15 novembre 39, 16 novembre 100 (tutte). Coda al 16 novembre: 51 pronte non ancora entrate, 104 in attesa di vendite, 47 del motore, 44 di coerenza, 10 d'era, 1.848 giapponesi da valutare. La coda ora segue l'esito del controllo all'approvazione e riconosce le giapponesi entrate | — |
| Annunci eBay | A rotazione: 120 carte più care ogni giro più una fetta delle altre (il giro superava tempo e limite di eBay) | D300 |
| Slabvalve | Era sparita dal sito: nel Sito la ricerca eBay (13 minuti) veniva fermata dal passo da 10 prima di scrivere il file, e ogni ricostruzione cancellava anche le occasioni. Ora la ricerca si ferma a 5 minuti e mezzo, i conteggi (solo numeri) restano 48 ore in un artifact condiviso con Occasioni, i mesi di scorta usano le vendite eBay (`n30e`). Prima costruzione dopo la correzione: Slabvalve su 78 carte, occasioni su 4; cresce con i giri di Occasioni | D303 |
| SlabRange | Mai più uno Slabprice fuori dalla sua forchetta (29 voti al 15 novembre): in quei casi si mostra la forchetta D224; controllo C11. Prova §65: la variante P (senza le vendite non credibili) passa tutto al primo giro ed è adottata subito per decisione di Oscar; il giro di dicembre è la verifica | D304, D308 |
| Indici | Sul tratto ricostruito la pagina non mostra più in cifre livello, 6 mesi, da inizio anno, 1 anno e calo massimo (Classica risultava +1.056% da gennaio 2024 con le carte di oggi). Restano 1 settimana, 1 mese, 3 mesi, margine, volatilità | D305 |
| Gemelle giapponesi | §67/§67b: stesso nome normalizzato, stessa era, stessa illustrazione; adottato per decisione di Oscar (G2 mancato per i doppioni). 268 gemelle nuove: carte inglesi con la gemella 262 nel catalogo, 586 con quelle in coda. Tolti 120 id giapponesi doppi (34 erano sul sito due volte). Verifica a dicembre | D307 |
| Storici lunghi | In corso dal 16 novembre sera nel browser del PC di Oscar (database `swhist_1116`): 326 carte senza storico e 19 giapponesi con SNKRDUNK; poi esportazione e `scripts/tc_history_merge.py` | — |
| Regole aggiornate | Documento "Slabwise: regole da aggiornare" approvato: Slabvalve unica col Rubinetto dentro (D309), P12 e P16 riscritti (D310), indici a 100 alla partenza dal vivo (D311), storici ogni lunedì sera e un id per stampa giapponese (D312), pulizia (D313) | D309–D313 |
| Altri enti nei titoli | §66 adottato: fuori i titoli con un altro ente e un voto ("TAG 10 = PSA 10"), circa 150 vendite su 1,6 milioni. Ricostruzione completa lanciata il 16 novembre | D306 |

## Workflow (GitHub Actions)

**Coda tcgcharts.** `raccolta-tcgcharts`, `candidati`, `immagini-tcgcharts` e `gemelle` sono nello stesso gruppo di concorrenza `raccolta-tcgcharts`: ne gira uno alla volta e **un solo giro può stare in attesa; una nuova richiesta in attesa annulla quella che c'era**. Lanciare un giro solo quando quello prima è partito, mai due di fila. Il ritmo verso tcgcharts è sempre una richiesta ogni 3 secondi (permesso di Marek).

| Workflow | Quando | Cosa fa |
|---|---|---|
| `raccolta-tcgcharts` | ogni giorno 04:11 UTC (dall'orologio), lunedì anche mappa e popolazioni | vendite recenti per scadenza (D297) e controllo delle richieste di carte; salva nel privato. Non aggiunge carte (il controllo del motore dura ~2 ore) |
| `candidati` | dopo la raccolta | coda delle carte dalla classifica tcgcharts, issue "Coda delle carte" (n. 2); salva la coda prima di riprovare le carte fermate dal motore (limite 200 minuti) |
| `sito` | a ogni push sul codice e dopo la raccolta | ricostruisce valori e pagine, pubblica su Cloudflare Pages |
| `controllo` | dopo il sito | prova un campione di ~50 carte su telefono e computer (12 minuti circa) |
| `occasioni` | ogni 6 ore | annunci eBay e offerte (D300) |
| `prezzi-giapponesi` | a catena | SNKRDUNK per le giapponesi, 60 carte a giro, salta quelle viste da meno di 7 giorni |
| `immagini-tcgcharts`, `gemelle` | a mano | D298, D299 |
| `approva` (a mano, input `ids`; ~3 ore per 100 carte), `richieste` (ogni 3 ore, limite 3 ore), `avvisi`, `raccolta-pokecolor`, `raccolta-alt`, `test` | vari | ingresso delle carte approvate, richieste, avvisi, altre fonti, test |
| `prova-slabrange`, `prova-indici`, `prova-motore` | a mano | prove del protocollo: SlabRange (giro di dicembre, D308), indici, mercato simulato (P14) |

## Problemi aperti

1. **tcgcharts**: dal 15 novembre circa 4 secondi a richiesta (il 14 erano 40), ma ogni tanto ancora errori 503 durante l'ingresso delle carte (il 15: 28 carte rimaste fuori). Fonti: eBay, Goldin, ALT, Fanatics e ora SNKRDUNK (D302). Il controllo del motore (R1/E2 in `add_cards`/`approva`) dura ormai ~2 ore con 1.400 carte: per questo raccolta, candidate e richieste sono state separate (15 novembre). Da valutare se si può accorciare.
2. **Schede incomplete** (report del 14 novembre, artifact "Slabwise: stato al 14 novembre"): 163 schede complete su 1.096. Le mancanze principali: gemella giapponese non trovata (447 inglesi, in lavoro con D299), immagine (circa 250 giapponesi), SNKRDUNK ambigua (141) o non trovata (47), nessuna asta Cardova riconosciuta (131), rarità e illustratore mancanti (circa 380 giapponesi).
3. ~~Misura delle occasioni~~: tolta il 16 novembre (D313).
4. ~~Pulizia~~: fatta il 16 novembre (D313): tolti 10 workflow chiusi e 6 rami vecchi.
5. **Eevee Base Set promo 11** mescola stampe diverse; **Mew Legend Maker PSA 9** ha un valore discutibile.
6. **Ritardo nelle ere veloci** (Scarlatto e Violetto): il valore insegue il mercato con qualche settimana di ritardo; nessuna idea nuova da provare per ora.
7. **Valori giapponesi da tenere d'occhio dopo il D302** (16 novembre): su 12 stampe il valore PSA 10 sta in mediana sul prezzo SNKRDUNK delle ultime due settimane (rapporto 1,00), ma alcune sono sotto (sv8-132 0,71; sv11b-174 0,76; sv11w-174 0,83) e m2a-199 sopra (1,62). Se non si allineano, proporre una prova.
8. **Coda**: 50 carte risultano ancora "pronta" nella issue n. 2 anche se sono già nel catalogo; si sistemano al prossimo giro delle candidate (17 novembre).

9. **Corsa di Classica e Di mezzo** (settembre–ottobre 2026): le vendite eBay delle voci dei panieri sono salite di circa l'80% in due mesi (Lugia ex Unseen Forces PSA 10 da 2–5 mila a 90–156 mila dollari, titoli e sedi coerenti); l'indice segue con ritardo (+52% contro +79% delle vendite). È mercato, non un errore dei dati; il ritardo resta il problema 6, ora anche per le ere vecchie.
10. **Esito della prova §65** (workflow "Prova SlabRange", 16 novembre): da scrivere nel protocollo quando arriva (`results/slabrange/summary_P.json`).

## In attesa di Oscar

- Revisione delle vendite sospette (issue n. 1 del repository privato).
- Messaggio a Cardova (grazie e ritmo) e citazione di Cardova prima del lancio pubblico.
- Ticket eBay.

## Controlli programmati

Le verifiche erano promemoria della vecchia chat (sessione `session_016TCLcyHqdTbGZah9QAR3rE`): arrivano lì, non nella chat nuova. La chat nuova deve rifarle a mano o riprogrammarle.

- 18 novembre: verifica Y7 della v1.20 (servono 2.000 vendite pulite dopo il 6 novembre; se non bastano, rinviare). Promemoria ancora attivo nella vecchia chat (non è stato possibile disattivarlo da lì).
- 20 novembre: risultati di PredicTCG (promemoria disattivato il 16 novembre: rifarlo a mano).
- 26 novembre: verifica prospettica del §62.
- 1° febbraio 2027: verifiche §52 e §55 sugli indici (promemoria ancora attivo nella vecchia chat).
- Ogni lunedì: curiosità per i copioni dei reel (D182). È un'attività programmata che apre una sessione nuova da sola: continua a girare.

## Regole da non dimenticare

- Mai stampare token e chiavi (`~/.slabwise`); mai inserire password; mai aggirare blocchi anti-bot o Cloudflare; niente raccolta da un sito senza permesso (Cardboard Terminal no: le sue condizioni vietano ogni accesso automatico).
- Nessun nome della fonte sul sito (D108). Annunci eBay mostrati solo se letti nelle ultime 6 ore.
- Prima di ogni commit `python -m pytest -q tests`. Una prova si registra prima di vedere i risultati e le soglie non si cambiano dopo.
- Su GitHub dalla sessione: solo `gh api` REST (GraphQL è bloccato), quindi niente `gh issue`, `gh pr`, `gh repo clone`.
- Firma dei commit: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
