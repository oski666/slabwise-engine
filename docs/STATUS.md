# Slabwise · Stato del progetto

**Aggiornato il 14 novembre 2026, primo pomeriggio.** Fotografia per chi riprende il lavoro (una chat nuova, o Oscar). Non sostituisce le regole: prima di toccare qualcosa leggi `CLAUDE.md` e `docs/PILLARS.md`; le scelte stanno in `docs/DECISIONS.md` (ultima voce D300), il metodo in `docs/METHOD.md`, le prove in `docs/BACKTEST_PROTOCOL.md`, le fonti in `docs/DATA_SOURCES.md`.

## In breve

- **Sito**: slabwise.pages.dev, in sviluppo; Oscar lo usa come anteprima di quello che vedrà il pubblico. Nessuna anteprima separata (l'anteprima `giappone` è stata eliminata, D290).
- **Catalogo**: 574 carte inglesi (più le varianti: 1.096 schede in tutto con le giapponesi) e 502 stampe giapponesi.
- **Motore**: v1.20 (D210), con il ricalcolo veloce del §60 tutti i giorni tranne il 1° del mese (D286); ricostruzione completa a mano con l'opzione `full` del workflow Sito.
- **Repository**: `oski666/slabwise-engine` (pubblico, codice e sito) e `oski666/slabwise-data` (privato: dati grezzi, D163). Le Actions del repository privato sono bloccate dalla fatturazione: tutto gira nelle Actions del repository pubblico, che legge e scrive i dati privati con il segreto `DATA_TOKEN`.
- **Proprietario**: Oscar. Si scrive in italiano.

## Cosa è cambiato negli ultimi giorni (D274–D300)

| Area | Stato | Decisioni |
|---|---|---|
| Vendite sospette | Regola che le segnala (prezzo oltre 5 volte o sotto un quinto della mediana vicina); revisione settimanale di Oscar su una issue del repository privato (la n. 1 è aperta, 30 vendite); le escluse vanno in `data/raw/eccezioni/registro.json` | D274, D275 |
| Pulizia dei titoli | §62 (titoli in giapponese) adottato con verifica al 26 novembre; §64 adottato; §63 e §63b non passati | D281–D285 |
| Ricalcolo veloce | §60 adottato: le carte nuove entrano senza ricostruire tutto | D277, D279, D286 |
| Mercati giapponesi | SNKRDUNK (prezzo fisso) e Cardova (aste pagate) nei valori del sito, in dollari al cambio BCE; decisione di Oscar senza prova; citazione di Cardova da decidere prima del lancio pubblico | D280, D292 |
| Nomi giapponesi | Nome e set in inglese, didascalia "Solo in Giappone" o "Stampa giapponese" con il nome originale | D291 |
| Immagini | Database ufficiale giapponese (151 carte) e, per le carte che nessun'altra fonte copre, tcgcharts con il permesso di Marek (primo giro: 43 su 294; molti errori 500 di tcgcharts) | D288, D298 |
| SlabRange | Adottato il §61b Q2: la forchetta è dove sono cadute 8 vendite su 10 della carta (percentili 10 e 90 degli scarti, mescolati con l'era × fascia di voto). Copertura 81%. Secondo giro al giro mensile; Classica e Di mezzo (74%, 76%) da guardare | D293–D295 |
| Indici per voto | PSA 10, 9, 8 per era sul sito: pagina `#indici-voto`, riquadro nelle pagine d'era, confronto voto per voto sulla pagina della carta | D296 |
| Raccolta tcgcharts | Era ferma dal 5 al 14 novembre (il giro non stava più nei 90 minuti). Ora legge per scadenza e si ferma in tempo | D297 |
| Gemelle giapponesi | Ricerca rifatta senza bisogno di TCGdex (workflow "Gemelle giapponesi"), le più popolate prima; 386 carte inglesi da ricercare | D299 |
| Annunci eBay | A rotazione: 120 carte più care ogni giro più una fetta delle altre (il giro superava tempo e limite di eBay) | D300 |

## Workflow (GitHub Actions)

**Coda tcgcharts.** `raccolta-tcgcharts`, `candidati`, `immagini-tcgcharts` e `gemelle` sono nello stesso gruppo di concorrenza `raccolta-tcgcharts`: ne gira uno alla volta e **un solo giro può stare in attesa; una nuova richiesta in attesa annulla quella che c'era**. Lanciare un giro solo quando quello prima è partito, mai due di fila. Il ritmo verso tcgcharts è sempre una richiesta ogni 3 secondi (permesso di Marek).

| Workflow | Quando | Cosa fa |
|---|---|---|
| `raccolta-tcgcharts` | ogni giorno 04:11 UTC (dall'orologio), lunedì anche mappa e popolazioni | vendite recenti per scadenza (D297), richieste di carte di Oscar, salva nel privato |
| `candidati` | dopo la raccolta | coda delle carte dalla classifica tcgcharts, issue "Coda delle carte" (n. 2) |
| `sito` | a ogni push sul codice e dopo la raccolta | ricostruisce valori e pagine, pubblica su Cloudflare Pages |
| `controllo` | dopo il sito | prova un campione di ~50 carte su telefono e computer (12 minuti circa) |
| `occasioni` | ogni 6 ore | annunci eBay e offerte (D300) |
| `prezzi-giapponesi` | a catena | SNKRDUNK per le giapponesi, 60 carte a giro, salta quelle viste da meno di 7 giorni |
| `immagini-tcgcharts`, `gemelle` | a mano | D298, D299 |
| `approva`, `richieste`, `avvisi`, `raccolta-pokecolor`, `raccolta-alt`, `test` | vari | ingresso delle carte approvate, richieste, avvisi, altre fonti, test |
| `prova-*` | a mano | prove del protocollo; `prova-slabrange` serve ancora per il giro di dicembre |

## Problemi aperti

1. **tcgcharts è lento e dà errori 500** (14 novembre: circa 40 secondi a richiesta invece di 3). Marek ha detto a Oscar che è un problema loro. Si continua normalmente; la raccolta recupera i giorni persi man mano. Quando torna normale, controllare che il giro giornaliero legga di nuovo migliaia di combinazioni.
2. **Schede incomplete** (report del 14 novembre, artifact "Slabwise: stato al 14 novembre"): 163 schede complete su 1.096. Le mancanze principali: gemella giapponese non trovata (447 inglesi, in lavoro con D299), immagine (circa 250 giapponesi), SNKRDUNK ambigua (141) o non trovata (47), nessuna asta Cardova riconosciuta (131), rarità e illustratore mancanti (circa 380 giapponesi).
3. **Misura delle occasioni** (`misura-occasioni`) fallisce dall'11 novembre: da rivedere o togliere.
4. **Pulizia**: 12 workflow di prova o usati una volta (vedi elenco), 6 rami vecchi (`coerenza`, `creator`, `d228-veloce`, `metodo-v120`, `pagina-carta`, `veloce`). Non toccati: chiedere a Oscar.
5. **Eevee Base Set promo 11** mescola stampe diverse; **Mew Legend Maker PSA 9** ha un valore discutibile.
6. **Ritardo nelle ere veloci** (Scarlatto e Violetto): il valore insegue il mercato con qualche settimana di ritardo; nessuna idea nuova da provare per ora.

## In attesa di Oscar

- 253 carte pronte nella coda delle candidate (issue n. 2): spuntarle o dire di farle entrare tutte.
- Revisione delle vendite sospette (issue n. 1 del repository privato).
- Messaggio a Cardova (grazie e ritmo) e citazione di Cardova prima del lancio pubblico.
- Ticket eBay.

## Controlli programmati (in questa sessione)

- 18 novembre: verifica Y7 della v1.20 (rinviata, servono 2.000 vendite pulite dopo il 6 novembre).
- 20 novembre: risultati di PredicTCG.
- 26 novembre: verifica prospettica del §62.
- 1° febbraio 2027: verifiche §52 e §55 sugli indici.
- Ogni lunedì: curiosità per i copioni dei reel (D182).

## Regole da non dimenticare

- Mai stampare token e chiavi (`~/.slabwise`); mai inserire password; mai aggirare blocchi anti-bot o Cloudflare; niente raccolta da un sito senza permesso (Cardboard Terminal no: le sue condizioni vietano ogni accesso automatico).
- Nessun nome della fonte sul sito (D108). Annunci eBay mostrati solo se letti nelle ultime 6 ore.
- Prima di ogni commit `python -m pytest -q tests`. Una prova si registra prima di vedere i risultati e le soglie non si cambiano dopo.
- Su GitHub dalla sessione: solo `gh api` REST (GraphQL è bloccato), quindi niente `gh issue`, `gh pr`, `gh repo clone`.
- Firma dei commit: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
