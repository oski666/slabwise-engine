# Registro delle decisioni · stato attuale

**Consolidato l'11 novembre 2026 su richiesta di Oscar (D267).** Qui c'è solo quello che vale oggi, diviso per argomento, con le voci da cui viene. Le versioni vecchie del sito e del motore, le prove chiuse, le regole sostituite e i loro perché sono in `docs/archive/DECISIONS_STORICO.md` (D1–D266, testo integrale e invariato): i numeri D citati in codice, documenti e commit si cercano lì.

Come si usa (CLAUDE.md, regola 2): un pilastro, il metodo o il perimetro si cambiano scrivendo prima una voce nuova in fondo a questo file ("Decisioni nuove", da D267), poi aggiornando la sezione di stato qui sotto e i documenti, poi il codice. Le voci nuove non si cancellano; quando una regola cambia, si riscrive la riga di stato e si cita la voce nuova.

Documenti che descrivono il dettaglio: `docs/PILLARS.md` (pilastri, P12 v1.2), `docs/METHOD.md` (il codice del motore, degli indici e delle misure), `docs/BACKTEST_PROTOCOL.md` (ogni prova con criteri ed esito), `docs/DATA_SOURCES.md` (fonti, permessi e rischi), `docs/DESIGN.md` (identità e parole del sito).

---

## 1. Come decidiamo

| Regola in vigore | Da |
|---|---|
| Il proprietario è Oscar; le scelte di perimetro, spesa e pubblicazione sono sue. Si lavora in autonomia e gli si scrive solo quando deve decidere o agire. | D243 |
| Prove prima delle opinioni (P12 v1.2): un cambiamento al metodo entra se batte il metodo in uso in una prova registrata prima dei risultati; le soglie non si toccano dopo l'esito. | D3, D265 |
| **Campione contro sfidante, prove ricorrenti**: motore e indici in uso sono il campione; le prove si ripetono ogni mese e ogni volta che il catalogo cresce di un quarto; una variante entra quando batte il campione in due giri di fila, con l'intervallo al 95% della differenza dalla parte giusta. Le varianti bocciate con un catalogo più piccolo di metà di quello di oggi si riprovano. | D265 |
| **Soglie come quote o rispetto al campione, mai come conteggi assoluti** ("per 1.000 voci", "per 10.000 titoli", "non peggio del campione"), perché il catalogo cresce. Le prove già chiuse restano chiuse con le loro soglie. | D264, D265 |
| Eccezione del proprietario (P12): Oscar può adottare una variante che manca un solo criterio, con voce motivata e verifica prospettica già registrata. | D250 |
| Dalla v1.20 del motore non si torna indietro. | D241 |
| Nessuna spesa senza una voce in questo registro (P19). Oggi la spesa è zero. | D4 |
| Mai presentare risultati del mercato simulato come reali (P14). | D18 |
| Ogni modifica al sito si prova prima su un ramo con l'anteprima `<ramo>.slabwise.pages.dev`; i test (`pytest`) girano da soli a ogni modifica. | D230, D260 |

## 2. Cosa misuriamo

| Regola in vigore | Da |
|---|---|
| Solo carte gradate PSA 7–10; le carte raw sono fuori dal progetto. | D1, D165 |
| La lingua fa parte dell'identità: giapponese, coreano e cinese sono stampe separate; le lingue europee sono la stessa carta con uno scarto di lingua. Le giapponesi sono un catalogo a sé, collegato alle inglesi solo dalla "gemella" (stessa carta e stessa illustrazione). | D28, D152, D166 |
| 1st Edition e Shadowless sono stampe con una pagina loro; le varianti ambigue nei titoli si escludono (per esempio Pikachu guance rosse o gialle). | D81, D141 |
| Un'asta non pagata non è una vendita; i voti con riserva (OC, MK, ST, PD, MC) non sono il voto pieno. | D46, D50, D221 |

## 3. Il motore dei prezzi

| Regola in vigore | Da |
|---|---|
| Un solo modello probabilistico (LVM), non una pila di regole. Versione in uso: **v1.20** (v1.15 più storico lungo nei prezzi, salti di un singolo voto, revisione sulle vendite recenti). Descrizione esatta in METHOD §2–§6. | D2, D210 |
| Fattore di mercato del motore su tre gruppi (WOTC, SM/SWSH, SV). La prova con le sei ere del sito (§57) ha ridotto il ritardo nelle ere veloci ma non abbastanza: il lavoro sul ritardo resta aperto e si rifà con le regole del D265. | D117, D264 |
| Salti di prezzo per carta, deriva per carta, scala dei voti per era, trend del fattore: provati, spenti. | D30, D36, D58, D156 |
| Un voto senza vendite proprie non ha un valore pubblicato: mostra l'ultima vendita, i voti vicini e la rarità. Una stima a più di 2 volte dalla mediana delle vendite recenti va "in revisione"; così anche un voto con vendite eBay e d'asta incompatibili. | D66, D98, D115, D226 |
| Una variazione a 30 o 90 giorni si mostra solo se il voto aveva già 3 vendite sue all'inizio del periodo. | D161 |
| Il sito non pubblica mai valori vecchi; ogni settimana l'istantanea dei valori e degli indici si sigilla (OpenTimestamps). | D105, D227, D262 |
| Previsioni a 1, 3 e 6 mesi: calcolate, non pubblicate (intervalli troppo larghi). Volatilità per carta: provata, non pubblicata. | D107, D127 |

## 4. Fonti di dati

Dettaglio, permessi e rischi in `docs/DATA_SOURCES.md`. Dati grezzi solo nel repository privato `slabwise-data`; codice pubblico (D163, D164). Nessun nome di fonte o concorrente sul sito (D108).

| Fonte | Stato | Da |
|---|---|---|
| tcgcharts | fonte principale di vendite (eBay, aste, marketplace) e popolazioni; permesso del titolare; raccolta giornaliera, storico lungo scaricato dal browser di Oscar; vendite assegnate dalle sue fonti tenute salvo contraddizioni | D76, D77, D80, D89, D258 |
| GemRate | popolazioni PSA per stampa e un anno di gradazioni a settimana, per tutti i set del catalogo che hanno una pagina; permesso; letto dal browser di Oscar | D189, D257, D261 |
| eBay Browse API | annunci attivi per occasioni e Slabvalve, mai salvati, mostrati solo se controllati nelle ultime 6 ore | D72, D112, D225 |
| Fanatics Collect (archivio pubblico) | vendite con flag di pagamento e storia dei cert | D46, D50, D63 |
| Pokecolor | vendite concluse, permesso; raccolta, nei prezzi solo dopo una prova | D180 |
| Cardova | aste chiuse giapponesi con certificato, voto, prezzo e pagamento; permesso per lo sviluppo, per mostrarle serve il permesso finale con citazione | D273 |
| SNKRDUNK | permesso di raccolta continua con l'account di Oscar per lo sviluppo; per pubblicare serve un accordo nuovo; nei prezzi solo dopo una prova | D266 |
| Alt | permesso; raccolta ferma (le sue vendite eBay arrivano già da tcgcharts) | D64, D89 |
| Immagini | TCGdex, CDN della Pokémon TCG API, database ufficiale giapponese; mai le immagini di tcgcharts sul sito | D45, D151, D152 |
| Escluse | Courtyard e marketplace in cassaforte o a pacchetti; prezzi raw | D1, D147 |
| Valutate, non attive | Yahoo! Auctions, Mercari, Aucfan (giapponesi); PokemonPriceTracker, Scrydex, PriceCharting (a pagamento) | D144, D266 |

## 5. Riconoscimento dei titoli

| Regola in vigore | Da |
|---|---|
| Una vendita è di una carta se il titolo la nomina senza contraddizioni (numero, set, nome, lingua, stampa, voto); più carte possibili = nessuna. Regole e sigle in METHOD §4b ("Titoli inglesi", "Titoli giapponesi"). | D153, D214, D233–D239 |
| Le vendite che tcgcharts riceve già legate a una carta si tengono salvo contraddizioni. | D258, D259 |
| Sigle di lingua (ITA, GER, KOR…) e coreane brevi escludono la vendita o l'annuncio. | D160, D239 |
| Le regole nuove sui titoli entrano solo con una prova registrata. | D214, D216 |

## 6. Il catalogo: chi entra

| Regola in vigore | Da |
|---|---|
| Una coda sola (`prototype/data/candidates_queue.json`): richieste dei visitatori (anche tramite Slabby), classifica per capitalizzazione di tcgcharts (prime 3.000, D271), stampe giapponesi gemelle e carte solo giapponesi (promo, serie vecchie e, dal D269, espansioni moderne senza gemella). Le carte entrano senza l'ok di Oscar una per una; lui riceve il riepilogo. | D97, D100, D122, D218, D231, D243, D269 |
| **Soglia d'ingresso**: almeno **10 vendite PSA 7–10 riconosciute in 365 giorni**, su tutte le piattaforme, almeno 5 nello stesso voto; almeno il 60% dei titoli riconosciuti; poi il controllo del motore sulla carta (R1/E2r), con il motore del sito. | D213, D232, D266 |
| Le carte fermate dal motore si riprovano ogni settimana, 8 per giro. | D157 |
| Le carte poco scambiate entrano con la frase "poco scambiata: il prezzo segue l'ultima vendita". | D232 |
| Le ere senza un gruppo proprio nel motore entrano nel più vicino. | D117, D183 |
| Aperto: la regola del 60% è nata prima del D258; Oscar decide se sostituirla con "quota di titoli che contraddicono la carta". | D266 |

## 7. Le ere

| Regola in vigore | Da |
|---|---|
| Sei ere, le stesse ovunque (schede, indici, frasi): Vintage, Classica, Di mezzo, Moderna, Spada e Scudo, Scarlatto e Violetto. Le giapponesi seguono la stessa divisione. Verifica prospettica il 1° febbraio 2027 (§55). | D121, D154, D255 |
| Scarlatto e Violetto e Mega Evoluzione sono ancora in stampa: il loro indice si presenta come indice delle nuove uscite. | D255, D262 |

## 8. Gli indici

| Regola in vigore | Da |
|---|---|
| Indici come quelli veri: generale (SlabDex), sei ere, Giappone (SlabJap) e set con almeno 8 carte; pesi uguali, concatenati, panieri rivisti ogni 13 settimane con le voci più scambiate (almeno 6 vendite credibili in 13 settimane), regolamento e componenti sulla pagina. Dettaglio in METHOD §4b. | D38, D136, D142, D203 |
| Paniere: **40 voci** per era e Giappone, 60 per lo SlabDex (10 per era); Giappone con posti uguali per le sue ere; le promo restano fuori dagli indici. | D169, D250, D252, D268 |
| Calcolati con lo storico lungo, base comune 100. | D121, D149 |
| **Ricostruito e dal vivo**: fino alla data di partenza decisa da Oscar (`prototype/data/index_live.json`, oggi nessuna) la linea è ricostruita con il catalogo di oggi, a puntini. Dalla partenza le variazioni settimanali si sigillano e non si riscrivono. La partenza è prevista quando le carte seguite coprono il 90% della capitalizzazione delle prime 3.000 di tcgcharts (11 novembre: 62%). | D262, D265, D271 |
| Ingressi e uscite sul modello degli indici veri: chi entra sposta l'indice solo in avanti; una carta vecchia aggiunta ora entra al ribilanciamento senza attesa; una carta appena uscita dopo l'attesa delle vendite minime; chi perde scambi esce. "Entrata rapida" da provare. | D265 |
| Margine a 1 mese (±N punti) su ogni indice. | D262 |
| In prova: indici fatti con un voto solo, PSA 10, 9 o 8 (§59, solo misura); SlabDex a quote, verifica prospettica il 1° febbraio 2027 (§52). | D249, D263, D266 |

## 9. La pagina della carta e le misure

| Regola in vigore | Da |
|---|---|
| Parole del sito: Slabprice, SlabRange (dove finiscono 8 vendite su 10), Bufala o Colpo di fortuna?, Gem Rate, Slabvalve, Slab-Meter, Market Cap PSA, Gemma nascosta. Glossario in DESIGN.md. | D191, D224, D225 |
| Ogni frase della scheda deve dire la stessa cosa dei numeri: frasi sull'era con le parole di Oscar (Entro le aspettative, Occhio!, Deal o Bolla?, In Frenata, In Picchiata, Che fatica!) e controllo automatico delle pagine a ogni ricostruzione (P0–P8), insieme ai controlli sui dati (C1–C10), nella issue "Controlli di coerenza". | D211, D242 |
| Market cap = Slabprice × popolazione PSA del voto, su ogni carta; popolazione da tcgcharts, altrimenti da GemRate quando l'abbinamento è unico. | D186, D257, D261 |
| Gem Rate a confronto con set ed era; "Gem Rate incerto" se le due conte non concordano. | D211, D212 |
| Gemma nascosta: PSA 10 con prezzo basso per la sua rarità, dentro la sua era e lingua. | D209 |
| Pagella per carta ("ti puoi fidare di questo prezzo?"), nessuna pagella generale e nessun nome di concorrente. | D108, D120 |
| Personaggi: Slabby guida il sito; le pose sono PNG che Oscar sostituisce; Slab-Meter con tre personaggi. | D24, D40, D194, D196, D197, D203 |

## 10. Occasioni e annunci

| Regola in vigore | Da |
|---|---|
| Solo annunci con probabilità di occasione ≥ 0,5, costo finale in Italia, margine se la rivendi, "offri fino a…"; nessun annuncio etichettato come sopravvalutato. | D72, D113, D119 |
| Avvisi Telegram a pagamento: non reggono, non si fanno. | D247 |
| Confronto venditori e consegnatari: deciso, in attesa di una fonte con il nome del venditore. | D93 |

## 11. Infrastruttura

| Regola in vigore | Da |
|---|---|
| Tutto gira su GitHub Actions (repository pubblico, minuti illimitati) e Cloudflare Pages; un orologio Cloudflare avvia le corse; le corse partono in fila. | D74, D75, D116, D164 |
| La ricostruzione riparte dall'ultimo stato salvato, con risultato identico al calcolo completo. | D228, D244, D246 |
| Backend leggero: storico e vendite si leggono una carta alla volta da `/api/card/<id>`. | D104 |
| Privacy: nessuna analitica di terzi né cookie di profilazione; modulo contatti senza email pubblicata; statistiche anonime solo per noi. | D129, D133 |
| Studio e pacchetto creator dietro password o codici invito; il pacchetto creator si pubblica dopo l'ok di Oscar. | D126, D256 |

## 12. Aperto, in attesa di Oscar

- Regola dei titoli all'ingresso: 60% riconosciuti oppure quota di titoli che contraddicono (sez. 6).
- Prova sul ritardo del motore con le regole del D265 (sez. 3).
- Data di partenza degli indici dal vivo (sez. 8).
- Immagini delle promo giapponesi dal database ufficiale; spesa per dati giapponesi (PokemonPriceTracker, Scrydex).
- Pagine GemRate da trovare a mano: set PCG9, Machamp Base Set, righe 1st Edition ambigue.
- Pacchetto creator: badge PNG e ok alla pubblicazione.

---

## Decisioni nuove

| # | Data | Decisione | Perché |
|---|---|---|---|
| D267 | 2026-11-11 | **Registro consolidato.** Oscar autorizza a togliere da questo file tutto ciò che riguarda versioni vecchie del sito e a ricostruirlo coerente con lo stato attuale ("ti autorizzo ad eliminare tutte le informazioni relative a quanto faceva riferimento a vecchie versioni del sito e a ricostruire un file coerente"). Il registro completo D1–D266 si sposta, invariato, in `docs/archive/DECISIONS_STORICO.md`; qui restano lo stato per argomento e le voci nuove. Le regole non cambiano con questa voce | Leggibilità: 266 voci in ordine di data, metà superate, non dicevano più cosa vale oggi |
| D268 | 2026-11-11 | **Esito §58: panieri da 40 voci per era e Giappone.** K30 e K40 passano Q1–Q4 contro K20; per regola registrata si adotta la più grande. Riduzione dell'errore sulle rivendite dello stesso cert da 0,312 a 0,373, rumore invariato, margine massimo a 1 mese da 7,6 a 4,4 punti; Classica e Di mezzo passano da 13 a 29 e 22 carte diverse. SlabDex invariato (60 voci, 10 per era) | §58, D263 |
| D269 | 2026-11-11 | **Esito §59 e carte giapponesi delle espansioni moderne.** (1) **§59, solo misura**: gli indici fatti con un voto solo si muovono insieme ma con ampiezze diverse; nelle ere in stampa il PSA 10 cala mentre PSA 9 e 8 salgono (Scarlatto e Violetto a 52 settimane: PSA 10 −31,7%, PSA 9 +14,7%), nelle ere vecchie il PSA 10 sale di più (Vintage +172% contro +104%). Oscar aveva ragione ad aspettarselo: l'indice d'era in uso mescola voti diversi per era (moderne quasi tutte PSA 10, vecchie PSA 7–9). Prossimo passo da registrare: indici per voto pubblicati accanto a quelli d'era, o un indice d'era a quote per voto. (2) **Giapponesi senza gemella delle espansioni moderne** (Oscar: "perché ste carte non le seguiamo? Mi sembra importante"): la Charizard dell'Expansion Pack 20th Anniversary (CP6), 289ª per capitalizzazione, non entrava in coda perché il D231 dava un id solo alle promo e alle serie vecchie. Da oggi ogni giapponese della classifica senza gemella inglese prende l'id dal nome del set di tcgcharts (`ja:expansion-pack-20th-anniversary-11`), come le vintage (D158), e segue le stesse regole d'ingresso | D231, D158, §59 |
| D270 | 2026-11-11 | **Accelerare l'ingresso delle carte importanti e fermare gli indici** (Oscar: "dobbiamo accelerare l'implementazione delle carte importantissime… velocizzare tutto il processo di ricostruzione… arrivare al punto in cui la ricostruzione non serve praticamente più perché aggiungiamo solo carte nuove… avere gli indici definitivi a cui poi secondo le regole registrate piano piano entreranno carte nuove"). (1) Prova §60: aggiunta incrementale delle carte nuove con il motore fermo all'ultimo stato salvato; la ricostruzione completa diventa mensile. (2) Le carte della classifica per capitalizzazione si controllano 80 per giro invece di 40 finché le prime 500 non sono dentro. (3) Partenza degli indici dal vivo proposta a Oscar quando le carte che abbiamo coprono il 90% della capitalizzazione delle prime 500 di tcgcharts (11 novembre: 73%); la data resta sua (D265) | D244, D265, D266, §60 |
| D271 | 2026-11-11 | **Partenza degli indici dal vivo: 90% della capitalizzazione delle prime 3.000 di tcgcharts** (Oscar: "io direi 90% delle 3000 della classifica"; corregge la proposta del D270, che diceva prime 500). Misura dell'11 novembre: le prime 3.000 posizioni sono 2.265 carte senza varianti; ne seguiamo 721, pari al 62% della capitalizzazione; per arrivare al 90% servono le 546 mancanti di maggior capitalizzazione. La coda dei candidati legge la classifica fino alla posizione 3.000 (prima 1.000). Quando la soglia è raggiunta si propone la data a Oscar e si scrive in `prototype/data/index_live.json` (D265) | D265, D270 |
| D272 | 2026-11-11 | **Ogni carta con la sua controparte giapponese, con immagine e vendite** (Oscar: "queste carte dovranno avere la loro controparte giapponese, tutte con immagine e vendite… prendiamole da SNKRDUNK le immagini… ne mancano anche altre sulle inglesi, sappiamo il motivo?"). (1) Ricerca delle gemelle giapponesi: 80 carte del catalogo per giro invece di 20 (D134); le gemelle entrano con le regole d'ingresso di sempre (vendite giapponesi riconosciute). (2) Immagini inglesi: ne mancavano 10 perché TCGdex non le ha e il ripiego sulla CDN della Pokémon TCG API sbagliava il codice del set ("swsh12.5gg" invece di "swsh12pt5gg") e il numero ("H09" invece di "H9"), e perché una voce vuota non si riprovava più; corretto, 7 riempite, restano 3 promo SV recenti che nessuna delle due fonti ha. (3) Immagini giapponesi dalle foto di SNKRDUNK: il permesso del D266 vale per lo sviluppo e dice che per mostrare i loro dati sul sito pubblico serve un accordo nuovo; prima di pubblicarle si chiede a SNKRDUNK, nella stessa conversazione, se le foto dei prodotti si possono mostrare (con link alla scheda). Nel frattempo le giapponesi moderne e le promo prendono l'immagine dal database ufficiale pokemon-card.com (fonte già registrata, D45) dal browser di Oscar | D45, D134, D151, D266 |
| D273 | 2026-11-12 | **Cardova: storico delle aste chiuse per lo sviluppo** (risposta di Cardova a Oscar, 12 novembre: "as long as the history remains in a development environment, we are good with the request. Once your website will show informations, please reach out again for the final permission. Still, there will be no particular restrictions in reporting sales data for historical purposes as long as we are being credited"). Si scarica una volta tutto lo storico delle aste chiuse Pokémon (certificato, ditta e voto, set, numero, prezzo finale in yen, data, stato del pagamento) dal browser di Oscar, piano, e poi si aggiornano le aste nuove; dati grezzi solo nel repository privato (D163). Per mostrarli sul sito serve il permesso finale di Cardova, con il loro nome citato (eccezione al D108 da decidere quando arriva). Nei prezzi solo dopo una prova registrata, insieme a SNKRDUNK (D266). Le loro condizioni d'uso (art. 43) chiedono il consenso scritto per usi oltre quello privato: è questa risposta | D163, D266 |
| D274 | 2026-11-12 | **Normalizzare per confrontare davvero, e registrare ogni eccezione** (Oscar: "essendo un bene molto volatile, dobbiamo trattare la cosa con cautela e registrare tutte le eccezioni per normalizzare il tutto… non possiamo (solo dove serve) normalizzare tutto per avere delle comparazioni reali?"). Diagnosi del 12 novembre: (a) la dispersione delle vendite per carta e voto va da circa 11% a 45%, ma SlabRange e pesi sono uguali per tutte le carte di un'era; copertura misurata 86%, sopra la forchetta 75–85% del P10; (b) il valore ritarda ed è spostato verso il basso nelle ere vecchie, più per il PSA 10 (Classica +18%, Di mezzo +26% di scarto mediano tra vendita e valore della settimana prima) che per PSA 9 e 8, perché tutti i voti condividono un fattore d'era; (c) vendite assegnate alla carta sbagliata dai fornitori (Garchomp C LV.X PSA 10 a $48 accanto a vendite da $21.000). Si normalizza in tre punti, ognuno con una prova: (1) **dati**: le vendite con prezzo di un'altra stampa finiscono in un registro delle eccezioni (`prototype/data/exceptions.json`: carta, voto, vendite, motivo, data, chi conferma); non si cancellano (P8), pesano zero con il motivo scritto; si segnalano in automatico, Oscar conferma; (2) **misura**: ogni carta giudicata con la sua volatilità (SlabRange e peso delle vendite per carta e voto), così un −10% si legge in proporzione a quanto quella carta si muove di solito; (3) **voti**: un fattore di mercato per PSA 10, PSA 9 e PSA 8 e sotto dentro ogni era. Non si normalizza: il prezzo tra voti diversi (P2), la volatilità vera (una carta ballerina resta con la forchetta larga, P10), i cambi di mercato confermati da più vendite (P9). Prova §61 | P2, P8, P9, P10, D265, §59 |
| D275 | 2026-11-12 | **Revisione delle vendite sospette da parte di Oscar** (Oscar: "l'importante è che io riesca a risalire all'annuncio originale, sapere quanto è vecchia, e sapere quanto pesa e quanto sposta quella vendita nell'attuale metro di calcolo… vogliamo creare una sezione apposita di vendite sospette da monitorare che devo validare io manualmente periodicamente? magari su github? … vedi tu"). Ogni lunedì la ricostruzione del sito prepara l'elenco (regola §61, corretta prima del codice: la vendita si confronta con le altre dello stesso atomo nelle 26 settimane intorno, non con tutto lo storico, perché le carte salite davvero negli anni non risultino sospette) e lo salva nel repository privato; lì una issue con etichetta *vendite-sospette* mostra per ogni vendita carta, voto, prezzo, data ed età, link all'annuncio eBay (o ricerca del titolo per le case d'asta), titolo, mediana delle vendite vicine, probabilità di essere genuina e di quanto si sposterebbe il valore di oggi senza quella vendita. Al massimo 30 per volta, una issue aperta alla volta. Oscar spunta *escludi* e chiude; le decisioni vanno nel registro `data/raw/eccezioni/registro.json` e valgono dalla ricostruzione dopo, per tutte le varianti (P4, come le correzioni d'identità del D81). La issue si apre e le spunte si leggono con `scripts/suspects_issue.py` dalla sessione di lavoro, non dalle Actions del repository privato, che non hanno minuti gratuiti (corsa rifiutata dalla fatturazione il 12 novembre). Su GitHub e non sul sito perché i titoli e i prezzi delle fonti stanno solo nel repository privato (D163); niente agente: costerebbe ogni settimana senza fare più di questo | P4, P8, D81, D163, D274, §61 |
| D276 | 2026-11-12 | **Lettura dei titoli 11 volte più veloce, risultato identico** (Oscar: "muoviamoci… non possiamo più perdere tempo"). Ogni ricostruzione passava 15–20 minuti a rileggere 1,3 milioni di titoli: il lettore confronta ogni titolo con migliaia di nomi del catalogo, e la memoria di Python per le espressioni regolari (512) le ricompilava ogni volta. Ora ogni espressione si compila una volta per corsa. Prova su 3.000 vendite reali: 12,4 secondi prima, 1,1 dopo, righe identiche. Nessun cambio di metodo, quindi nessuna prova del backtest | D82, D258 |
| D277 | 2026-11-12 | **§60 scritto e in prova** (Oscar: "mica avevi detto che la ricostruzione sarebbe stata molto più veloce… cosa lo sta rendendo così lento?"). Misura: con catalogo fermo il motore riparte dallo stato salvato in 2 minuti; con una carta nuova, vendite nuove in settimane vecchie o codice cambiato ricalcola tutto (57–88 minuti). Variante I del §60 come registrata: lo stato salvato della ricostruzione completa si sposta sul catalogo nuovo (`slabwise/incremental.py`); le carte nuove sono *satelliti*: seguono fattori d'era e parametri condivisi stimati senza di loro e non li muovono (`satellite` in `slabwise/model.py`), quindi le carte vecchie non cambiano; le loro vendite nelle settimane già coperte dallo stato si leggono una volta, poi si prosegue con tutte. Le vendite nuove di settimane vecchie delle carte già presenti aspettano la ricostruzione completa. Spenta finché il §60 non passa (`SLABWISE_INCREMENTAL`). Gruppi della prova: 1 = le 164 carte entrate il 10 novembre, 2 = le 32 dell'11 novembre, 3 = le prossime 20 (`results/incr/`). Precisazioni prima dei risultati: I3 usa lo SlabRange di oggi delle carte nuove sulle loro vendite delle ultime 13 settimane con probabilità ≥ 0,5; I4 vale per l'intera corsa incrementale, sotto i 10 minuti qualunque sia la dimensione del gruppo (più severo di "20 carte"). Prova a mano su 51 carte reali: I1 identiche, I2 mediana 1,7% | D244, D270, §60 |
| D278 | 2026-11-12 | **Nomi dei set giapponesi come li scrive PSA** (Oscar: "muoviti a farlo", sul lettore dei titoli per le aste Cardova). Le aste di Cardova (e molti titoli eBay) portano il nome del set dell'etichetta PSA. Misura sulle 101.362 aste Cardova PSA 7–10 pagate: ne riconosciamo 17.387; le altre sono quasi tutte di carte che non seguiamo, ma 6 set del catalogo non si leggono per il nome: "Terastal Fest ex" (noi "Terastal Festival ex"), "Pokemon Card 151", "TAG TEAM GX All Stars" (noi "Tag Team GX Tag All Stars"), "Nihil Zero" (M3, senza nome del set), "MEGA Starter Set MEGA Gengar ex" (parole in altro ordine), e "Pokemon GO", che non passa mai perché il nome del set registrato con "Pokémon" diventa `pok\W*mon` e non legge "pokemon" scritto senza accento. Prova §62 prima del codice | D153, D238, D273, §62 |
