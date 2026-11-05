# Protocollo di backtest

**Versione 1.0 · 23 ottobre 2026 · registrato prima di qualsiasi risultato**

Questo protocollo fissa in anticipo come confrontiamo i metodi e quando dichiariamo che un metodo è migliore (pilastro P12). Le soglie qui sotto non si cambiano dopo aver visto i risultati; se servisse, si apre una voce in `DECISIONS.md` e si rifà tutto il confronto.

## 1. Dati

**Fase S (simulata).** Un mercato simulato (`slabwise/sim.py`) di cui conosciamo il valore vero di ogni atomo in ogni settimana. Deve riprodurre i fenomeni reali che conosciamo:

- liquidità a coda lunga (poche carte vendono ogni settimana, la maggior parte poche volte l'anno);
- fattori di mercato per era, con una fase di crescita, un crollo rapido e fasi piatte;
- picchi da evento su singole carte, che poi rientrano;
- scala dei voti diversa da carta a carta;
- qualità della singola copia (centratura, estetica) e rivendite dello stesso slab;
- case d'asta con premio sistematico rispetto a eBay;
- contaminazione: voto sbagliato nel titolo, raw venduta come graded, falsi e ristampe, variante sbagliata, lotti, Best Offer con il prezzo chiesto, aste non pagate o gonfiate, duplicati tra fonti, "inondazione" di annunci falsi su una carta.

Si usano 5 semi casuali diversi; i risultati si riportano come mediana tra i semi.

**Fase R (reale).** Quando avremo vendite reali con singole transazioni, stesso confronto con la metrica 2.2. Nessuna conclusione della fase S si presenta come reale.

## 2. Metriche

Si valuta ogni settimana, dopo 26 settimane di riscaldamento. I parametri del nostro modello si stimano solo sulle prime 52 settimane e poi restano fermi.

1. **Errore sul valore vero (EV).** Mediana di |log(stima / valore vero)|, sugli atomi che hanno almeno una vendita genuina nel passato. Riportata in totale e per fascia di liquidità: alta (≥ 1 vendita a settimana), media (≥ 1 al mese), bassa (≥ 1 a trimestre), rarissima (meno).
2. **Errore sulla vendita successiva (ES).** Mediana di |log(stima del giorno prima / prezzo della vendita genuina successiva)|. È l'unica metrica calcolabile anche sui dati reali; serve a verificare che si muova insieme a EV.
3. **Rumore (RU).** Mediana di |variazione settimanale della stima − variazione vera|: quanto la stima si muove senza motivo.
4. **Ritardo nel crollo (RC).** Nelle settimane dopo il crollo simulato, errore mediano EV dell'era colpita: quanto ci mette la stima a raggiungere il mercato.
5. **Calibrazione (CA).** Quota di casi in cui la forchetta all'80% contiene il valore vero (solo per i metodi che producono una forchetta).
6. **Robustezza (RB).** EV al variare della contaminazione: 0%, 10%, 20%, 35%, 50% delle vendite.
7. **Deal (DP / DR).** Su annunci simulati (genuini e contaminati): precisione = quota dei deal segnalati che sono genuini e valgono davvero almeno il 10% più del prezzo; richiamo = quota dei veri deal trovati.
8. **Copertura (CO).** Quota degli atomi per cui il metodo produce una stima.

## 3. Confronto

Ogni metodo riceve lo stesso flusso di vendite.

- **Modalità A (stimatore puro).** Tutti i metodi ricevono le vendite già passate dal livello di identità (duplicati, cert, lotti, Best Offer). Misura la qualità della formula.
- **Modalità B (filiera completa).** Ogni concorrente riceve il flusso con i soli filtri che dichiara pubblicamente; noi con il nostro livello di identità. Misura il prodotto finito.

Metodi in gara: ultima vendita; mediana a fasce con guardia sui bassi (tcgcharts); media pesata per età (PriceCharting); ultima vendita spostata dall'indice (Card Ladder); prototipo Slabwise v0 (recinto asimmetrico + mediana pesata + riferimento con k=3, simile alla pila di regole TCGBerg); Modello a Valore Latente (LVM).

## 4. Criteri di successo (pre-registrati)

Il Modello a Valore Latente diventa il metodo ufficiale solo se, in modalità A, con contaminazione base:

| # | Criterio | Soglia |
|---|---|---|
| S1 | EV totale | almeno 20% più basso del miglior concorrente |
| S2 | EV per fascia | mai peggiore del miglior concorrente in nessuna fascia |
| S3 | Rumore RU | il più basso tra tutti i metodi |
| S4 | Calibrazione CA | tra 75% e 85% |
| S5 | Robustezza | EV al 35% di contaminazione non più del 50% sopra EV a contaminazione base |
| S6 | Deal | precisione ≥ 80% |
| S7 | Ritardo nel crollo | EV dell'era colpita, nelle 8 settimane dopo il crollo, più basso di tutti i concorrenti |

Se un criterio non è soddisfatto si dice quale, nel report, senza aggiustare le soglie.

## 5. Non regressione della v1.2 (registrato il 23 ottobre 2026, prima del codice)

La v1.2 sostituisce la v1.1 solo se, rifacendo l'intero protocollo con gli stessi semi e gli stessi scenari (risultati v1.1 in `results/v1.1/summary.json`), tutte queste condizioni sono vere:

| # | Condizione |
|---|---|
| N1 | EV totale, ES e RC dell'LVM non più del 2% (relativo) sopra la v1.1 |
| N2 | EV dell'LVM in ogni fascia di liquidità non più del 5% (relativo) sopra la v1.1 |
| N3 | Calibrazione CA tra 75% e 85%, oppure più vicina all'80% della v1.1 (78,6%) |
| N4 | Precisione dei deal ≥ 80% |
| N5 | Scenario sfavorevole: EV dell'LVM non più del 2% sopra la v1.1 |
| N6 | Criteri S1–S7 superati: almeno gli stessi della v1.1 (tutti tranne S3) |

Le lingue non esistono nel mercato simulato di base, quindi gli scarti di lingua lì non entrano in gioco. Si verificano con un test dedicato (`tests/`): mercato simulato con 4 lingue europee e scarti noti; lo scarto stimato di ogni lingua deve stare entro ±0,10 in log da quello vero (L1), e l'errore sul valore delle carte non inglesi deve essere più basso che stimandole come carte separate (L2).

Se una condizione non è soddisfatta, la v1.2 non si adotta: si dice quale, e la parte responsabile si toglie o si rivede con una nuova voce nel registro.

## 6. v1.3: indice d'era (registrato il 23 ottobre 2026, prima del codice)

La v1.3 sostituisce la v1.2 solo se, sullo stesso protocollo completo (risultati v1.2 in `results/v1.2/summary.json`):

- valgono le condizioni N1–N6 del §5, con la v1.2 al posto della v1.1;
- **I1 · Indice che segue il mercato.** Per ogni era e ogni settimana di verifica si confronta la variazione su 12 settimane del fattore stimato `F_e` con quella del fattore vero. La pendenza della retta senza intercetta (stimato su vero) misura quanta parte del movimento vero il fattore cattura; la mediana tra ere e semi (modalità A, contaminazione base) deve essere **≥ 0,80**. Nella v1.1/v1.2 era intorno a 0,5 (D15).

Se I1 passa ma una condizione N fallisce, la v1.3 non si adotta e si annota quale.

## 7. v1.4: indice d'era pubblicato (registrato il 23 ottobre 2026, prima del codice)

Il modello delle stime non cambia (v1.2), quindi N1–N6 restano quelli della v1.2. Sui 5 semi di base (modalità A, contaminazione 15%, parametri della v1.2 già calibrati in `results/v1.2/`), per ogni era con un paniere e ogni settimana di verifica (dalla 64ª) si confrontano le variazioni su 12 settimane dell'indice pubblicato (in log) con quelle del fattore vero:

| # | Criterio | Soglia |
|---|---|---|
| P1 | Quota dei movimenti veri catturata: pendenza della retta senza intercetta (indice su vero), mediana tra ere e semi | tra 0,80 e 1,20 |
| P2 | Correlazione tra le variazioni su 12 settimane dell'indice e del fattore vero, mediana tra ere e semi | ≥ 0,80 |

Se un criterio non passa, l'indice non si pubblica come numero ufficiale e si dice quale.

## 8. v1.5: fasce di fiducia e limite allo spostamento senza vendite (registrato il 24 ottobre 2026, prima del codice; D47)

**Limite allo spostamento (L).** Con il limite acceso (±log 3 su β·ΔF dall'ultima stima con vendite), sul protocollo completo (risultati v1.2 in `results/v1.2/summary.json`) devono valere N1–N6 del §5 con la v1.2 al posto della v1.1. Si riporta anche quante stime il limite tocca. Se una condizione non vale, il limite resta spento e si dice quale.

**Fasce di fiducia (T).** Sui 5 semi di base (modalità A, contaminazione 15%), dalle settimane di verifica, per ogni voto di ogni carta già vista, si assegna la fascia come in D47 e si misura l'errore assoluto in log rispetto al valore vero.

| # | Criterio | Soglia |
|---|---|---|
| T1 | Le fasce ordinano l'errore: mediana dell'errore "Vendite fresche" < "Stimato" < "Poco sicuro", in ogni seme | in tutti e 5 i semi |
| T2 | (solo riportato) copertura della forchetta all'80% in ogni fascia | — |

Se T1 non passa, le fasce non si mostrano sul sito e si dice in quale seme l'ordine si rompe.

## 9. v1.6: terza sede "prezzo fisso" (registrato il 24 ottobre 2026, prima del codice; D51)

Lo scarto di sede `o_v` diventa un vettore: eBay (riferimento, 0), case d'asta, vendite a prezzo fisso di altre piattaforme (es. il marketplace di Fanatics Collect). Ogni scarto si stima come in D27, solo dalle carte che hanno vendite in quella sede e in almeno un'altra; il rumore della sede a prezzo fisso è quello di eBay (`σ_e`).

| # | Criterio | Soglia |
|---|---|---|
| V0 | Il mercato simulato di base ha solo eBay e aste: sul protocollo completo le metriche devono restare identiche alla v1.5 (stesso codice per due sedi), quindi N1–N6 | differenza massima 0 su EV, ES, RC, CA |
| V1 | Test dedicato (`tests/`): mercato simulato in cui il 30% delle vendite eBay diventa "prezzo fisso" con uno scarto vero di +0,10 in log; lo scarto stimato dopo 104 settimane | entro ±0,03 da quello vero |
| V2 | (solo riportato) sui dati reali: scarto stimato per le vendite a prezzo fisso di Fanatics e numero di vendite aggiunte | — |

Se V0 o V1 non passano, le vendite a prezzo fisso restano fuori e si dice quale criterio è fallito.

**Esito della v1.6 (24 ottobre 2026): V1 fallito.** Scarto stimato per la sede a prezzo fisso 0,045 contro 0,10 vero. Lo stesso test mostra che anche lo scarto delle aste è sottostimato (0,033 contro circa 0,11 del simulatore: premio 0,06 più copie migliori). Causa: la media corrente dei residui di D27 è distorta verso zero, perché il livello della carta (cammino casuale) assorbe parte dello scarto delle vendite più recenti. Come da regola, le vendite a prezzo fisso restano fuori.

## 9b. v1.6b: scarti di sede gerarchici (registrato il 24 ottobre 2026, prima del codice; D53)

Lo scarto di ogni sede (aste, prezzo fisso) diventa un parametro **di ogni carta** nella stima congiunta, come gli scarti di lingua (D28): priore comune `N(μ_v, s_v²)`, con `μ_v` e `s_v` appresi dalle carte la cui stima ha varianza < metà di `s_v²` (dopo 10 carte; valori iniziali 0 e 0,2; dispersione limitata a [0,03; 0,5]). Una carta senza vendite in una sede usa `μ_v` con la sua dispersione.

| # | Criterio | Soglia |
|---|---|---|
| V1b | Stesso test di V1 (seme 11, 30% delle vendite eBay a prezzo fisso con scarto +0,10) | `μ_fixed` entro ±0,03 da 0,10 |
| V3 | Protocollo completo contro la v1.5 (il trattamento delle aste cambia anche nel simulatore di base) | N1–N6 del §5, con la v1.5 al posto della v1.1 |
| V4 | (solo riportato) `μ_auction` stimato sui 5 semi di base contro il valore vero del simulatore | — |

Se V1b o V3 non passano, la v1.6b non si adotta, le vendite a prezzo fisso restano fuori e si dice quale criterio è fallito.

**Esito della v1.6b (24 ottobre 2026): V1b e V3 superati** (dettagli in `results/v1.6/REPORT.md`). Sui dati reali però 2–6 voci vintage hanno tutte le vendite PSA 10 giudicate anomale, contro 0 con la v1.5: la v1.6b non si usa per il sito finché non passa anche R1 (§10).

## 10. Controllo sui dati reali (registrato il 24 ottobre 2026, dopo l'esito della v1.6b e prima di qualsiasi nuova versione)

Ogni nuova versione, oltre ai criteri sul mercato simulato, deve superare sui dati reali del sito:

| # | Criterio | Soglia |
|---|---|---|
| R1 | Voci (carta e voto) con almeno 2 vendite e **tutte** con probabilità genuina < 0,5 | non più della versione in uso (oggi 0) |

Il criterio non si confronta con un valore vero (non lo conosciamo): serve a fermare i cambi che sul mercato simulato vanno bene ma sui dati veri buttano via interi gruppi di vendite.

## 11. v1.7: scala dei voti per era (registrato il 24 ottobre 2026, prima del codice; D55)

Il priore comune delle distanze tra voti `N(μ_g, s_g²)` diventa **per era**: `μ_eg` e `s_eg` si stimano come oggi, ma separatamente per ogni era, e restano agganciati alla media di tutte le ere con un peso di 10 carte (`μ_eg = (n_e·m_eg + 10·μ_g)/(n_e + 10)`, stesso per la varianza). Così un'era con poche carte parte dal valore comune e se ne stacca quando le sue carte lo giustificano.

Il simulatore riceve un'opzione `vintage_gap` (default 0, quindi il protocollo di base non cambia): aggiunge quel valore alla distanza 10→9 delle sole carte dell'era "wotc".

| # | Criterio | Soglia |
|---|---|---|
| G1 | Test dedicato (seme 13, 120 carte, 104 settimane, nessuna contaminazione, `vintage_gap = 1,5`): `μ` 10→9 appresa per l'era wotc rispetto alla media vera delle sue carte | entro ±0,20 |
| G2 | Stesso test: quota delle vendite PSA 10 genuine delle carte wotc con probabilità genuina < 0,5 | ≤ 10% |
| G3 | (solo riportato) G1 e G2 con la v1.5 | — |
| N | Protocollo completo contro la v1.5 | N1–N6 del §5, con la v1.5 al posto della v1.1 |
| R1 | Dati reali del sito (§10) | nessuna voce con tutte le vendite sotto 0,5 |

**Prezzo fisso.** Le vendite a prezzo fisso di Fanatics entrano nel sito solo con la v1.7 più gli scarti di sede della v1.6b (`venue_gaps=True`), e solo se questa combinazione passa N1–N6 contro la v1.5 sul protocollo completo e R1 sui dati reali con le vendite a prezzo fisso.

## 12. Fase R: confronto sulle vendite vere (registrato il 24 ottobre 2026, prima del codice; D55)

Sulle vendite reali del sito (dopo il livello di identità), con la stessa calibrazione del sito (prime `max(26, W/3)` settimane), ogni metodo stima ogni settimana; per ogni vendita della settimana *w* successiva alla calibrazione si confronta la stima di quella carta e voto a fine settimana *w−1* con il prezzo (in log). Si usano solo le vendite che tutti i metodi sanno stimare. Concorrenti: gli stessi del protocollo (ultima vendita, tcgcharts, PriceCharting, Card Ladder, Slabwise v0).

| # | Criterio | Soglia |
|---|---|---|
| R2 | Errore mediano assoluto sulla vendita successiva, tutte le vendite | LVM più basso di ogni concorrente |
| R3 | Lo stesso per fascia di liquidità della carta (vendite nelle 52 settimane precedenti: ≥ 26, 6–25, ≤ 5) | LVM mai sopra il miglior concorrente di più del 5% |
| R4 | (solo riportato) quota di vendite dentro la forchetta predittiva all'80% dell'LVM (varianza della stima più rumore di vendita e di copia) | — |

È la prima prova sui dati veri (P14): se R2 o R3 non passano lo diciamo nel sito e nel report, senza cambiare soglie.

**Esito della v1.7 (24 ottobre 2026): G1 fallito.** Distanza 10→9 appresa per l'era wotc −1,84 contro −2,22 vera (soglia ±0,20); G2 superato (0% dei PSA 10 genuini sotto 0,5, su 129). G3, v1.5: −0,97 e 3,9%. Causa: il peso di 10 carte verso il valore comune tiene ancora circa il 40% del valore comune quando un'era ha una quindicina di carte ben misurate. La v1.7 non si adotta.

### 11b. v1.7b (registrato il 24 ottobre 2026, prima di rifare il test; D56)

Unica modifica: il peso che lega un'era al valore comune passa da 10 a **2 carte**. Criteri identici al §11 (G1, G2, N, R1, e la stessa regola per il prezzo fisso).

**Esito della v1.7b: G1 fallito** (−1,77 contro −2,22; G2 0%). Il legame non era la causa: le statistiche per era si accumulano a ogni nuova stima della stessa carta, quindi pesano soprattutto le prime stime, ancora schiacciate sul valore comune.

### 11c. v1.7c (registrato il 24 ottobre 2026, prima del test; D57)

Le statistiche per era usano **l'ultima stima di ogni carta** (una carta conta una volta, con la stima più recente tra quelle che fissano bene la distanza), invece di accumulare tutte le stime. Legame 2 carte. Criteri identici al §11. È l'ultimo tentativo in questa sessione: se fallisce, la scala per era resta spenta e se ne riparla con più dati.

**Esito della v1.7c: G1 fallito** (−1,96 contro −2,22, scarto 0,26 oltre la soglia di 0,20; G2 0%). Come stabilito, la scala dei voti per era resta spenta (`era_gaps=False`) e il test resta nel codice come promemoria (atteso fallito). Nota: nel simulatore anche la v1.5 scarta solo il 3,9% dei PSA 10 vintage genuini, quindi il simulatore non riproduce il problema visto sui dati veri: va prima costruito uno scenario che lo riproduca.


## 13. v1.8: punto di partenza della stima dai voti della carta (registrato il 27 ottobre 2026, prima del codice; D67)

**Problema (D65).** Con le vendite di Alt, il controllo R1 trova 3 voci di carte moderne (Mega Charizard X ex PSA 7, Charizard ex 151 giapponese PSA 7 e PSA 8) con tutte le vendite giudicate anomale, anche se sono coerenti tra loro (es. 10 PSA 7 tra 570 e 678 $). La stima di ogni carta parte da due punti: la stima precedente, oppure il valore comune delle distanze tra voti. Da entrambi le vendite di un voto lontano dal valore comune partono come anomale, il loro peso è quasi zero e la distanza di quel voto non si sposta più: la stima si ferma in un massimo locale.

**Modifica (v1.8, un solo cambiamento).** Un terzo punto di partenza, accanto ai due di oggi: il livello dalla mediana delle vendite PSA 10 della carta (se ce ne sono, altrimenti come oggi) e la distanza di ogni voto con almeno 2 vendite dalla mediana delle sue vendite. Il modello, il priore e la funzione obiettivo non cambiano: tra i punti di partenza vince, come oggi, quello con l'obiettivo più alto. Interruttore `gap_start` in `LVMParams` (spento = v1.5 identica).

| # | Criterio | Soglia |
|---|---|---|
| C1 | R1 sui dati reali **con** le vendite Alt (`data/raw/sales_alt.csv`, 4.587 righe) | 0 voci (v1.5: 3) |
| C2 | R1 sui dati reali del sito, senza Alt (`data/raw/sales_all.csv`) | 0 voci, come la v1.5 |
| C3 | Protocollo completo contro la v1.5 (25 lavori di `results/v1.5/`, stessi parametri calibrati) | N1–N6 del §5 con la v1.5 al posto della v1.1 |
| C4 | Fase R (§12) sui dati reali senza Alt | errore mediano sulla vendita successiva non più di 0,2 punti sopra la v1.5 (10,4%); R3 riportato |

Se un criterio non passa, la v1.8 resta spenta e si dice quale.

**Esito della v1.8 (27 ottobre 2026): adottata.** C1 0 voci (v1.5: 3); C2 0 voci; C3 N1–N6 superati (EV −0,11%, ES −0,10%, RC −0,40%, fasce tra −0,27% e +0,04%, CA 78,7%, deal 86,2%, scenario sfavorevole +0,04%, stessi criteri S); C4 10,42% contro 10,40%, R3 fascia bassa ancora non superata (19,1% contro 16,1%). Report in `results/v1.8/REPORT.md`.

## 14. v1.9: scarti di sede gerarchici sopra la v1.8 (registrato il 27 ottobre 2026, prima del test; D70)

**Cosa abbiamo trovato (D69 rivisto).** Con le vendite Alt la fase R sembrava peggiorare (11,2% contro 10,9% di Card Ladder), ma la causa è lo scarto di sede. Lo stimatore della v1.5 (media mobile dei residui, D27) passa da −0,007 a **−0,122** per le aste quando entrano le vendite eBay recenti, mentre il confronto diretto sulle stesse carte, voti e mesi (30 gruppi da metà luglio, vendite pulite) dà eBay sopra le aste di **0,059** in log (mediana; media 0,066). Il valore pubblicato è "una copia tipica venduta su eBay" e veniva confrontato con prezzi d'asta senza aggiungere lo scarto: corretto con lo scarto della sede, l'errore con Alt è 10,53% contro 10,92% di Card Ladder (riportato da `scripts/real_phase_r.py` come `ES_lvm_venue_adjusted`).

**Modifica (v1.9).** La v1.8 con gli scarti di sede gerarchici per carta già scritti e provati nella v1.6b (`venue_gaps=True`, D53), che sul mercato simulato stimavano bene lo scarto (V1b) ma sui dati di allora scartavano le PSA 10 vintage (D54); la v1.8 potrebbe aver tolto quella causa.

| # | Criterio | Soglia |
|---|---|---|
| D1 | R1 sui dati reali con e senza Alt | 0 voci in entrambi |
| D2 | Scarto d'asta appreso sui dati con Alt | tra −0,109 e −0,009 (confronto diretto −0,059 ± 0,05) |
| D3 | Protocollo completo contro la v1.8 | N1–N6 del §5 con la v1.8 al posto della v1.1 |
| D4 | Fase R: errore con lo scarto della sede (`ES_lvm_venue_adjusted`) sui dati con Alt; errore semplice sui dati senza Alt | con Alt sotto ogni concorrente; senza Alt non più di 0,2 punti sopra la v1.8 (10,42%) |

Se passa, il sito usa le vendite Alt con la v1.9. Se no, resta la v1.8 senza Alt e si dice quale criterio manca.

**Esito della v1.9 (27 ottobre 2026): adottata.** D1 0 voci con e senza Alt; D2 scarto d'asta −0,074 (soglia −0,109…−0,009); D3 N1–N6 contro la v1.8 superati (EV +0,06%, ES +0,15%, RC −0,34%, fasce fino a +0,74%, CA 78,8%, deal 86,1%, scenario sfavorevole +0,21%, stessi criteri S); D4 con Alt 10,77% con lo scarto di sede (10,79% senza) contro 10,92% di Card Ladder, senza Alt 10,41%. R3 resta non superato nella fascia bassa (19,1% contro 16,1%). Copertura della forchetta predittiva (R4) 85,7% con Alt.

## 15. v1.10: finestra delle vendite con una quota per voto (registrato il 27 ottobre 2026, prima del codice; D78)

**Problema.** Con le vendite tcgcharts alcune carte moderne hanno migliaia di vendite in 90 giorni. Ogni carta tiene solo le ultime 80 osservazioni (`max_obs`): restano quasi solo PSA 10 e 9, le vendite dei voti bassi escono dalla finestra e quel voto torna al valore comune delle distanze, che per le carte moderne è sbagliato (D65). Con la v1.9 su questi dati, 6 voci con almeno 5 vendite negli ultimi 90 giorni hanno un valore lontano più di 0,5 in log dalla mediana delle proprie vendite (es. Mega Charizard X ex PSA 7: 71 $ contro una mediana di 635 $ su 9 vendite).

**Modifica (v1.10, un solo cambiamento).** La finestra di ogni carta tiene le ultime 80 osservazioni **più** le ultime 15 di ogni voto (unione). Parametro `grade_keep` (0 = v1.9).

| # | Criterio | Soglia |
|---|---|---|
| E1 | R1 sui dati reali con tcgcharts (`data/raw/sales_tc.csv`) | 0 voci |
| E2 | Voci con almeno 5 vendite negli ultimi 90 giorni e valore a più di 0,5 in log dalla loro mediana | 0 (v1.9: 6) |
| E3 | Protocollo completo contro la v1.9 | N1–N6 del §5 con la v1.9 al posto della v1.1 |
| E4 | Fase R con lo scarto della sede, dati con tcgcharts | LVM sotto ogni concorrente e non più di 0,2 punti sopra la v1.9 (7,32%) |

**Esito (27 ottobre 2026): v1.10 non adottata.**

| # | v1.9 | v1.10 | Superato |
|---|---|---|---|
| E1 | 0 su 190 | 0 su 202 | sì |
| E2 | 8 voci | 2 voci | **no** |
| E3 | | non eseguito: E2 già decide | |
| E4 | 7,32% (tcgcharts 7,55%) | 7,26%; copertura 80,2% | sì |

La quota per voto risolve le 6 voci dei voti bassi delle carte moderne (es. Mega Charizard X ex PSA 7 da 71 $ a vicino alla mediana di 635 $). Le 2 voci rimaste non dipendono dalla finestra (sono uguali con la v1.9): Pikachu Base Set shadowless PSA 10 (1.181 $ contro una mediana di 2.205 $ su 6 vendite) e Machamp Base Set 1ª edizione PSA 9 (1.359 $ contro 252 $ su 5). Sono stampe varianti che il sito non mostra, ma il criterio registrato vale per tutte le voci e non si cambia dopo il risultato. Correzione: nella registrazione la v1.9 era indicata con 6 voci; il controllo completo, che conta anche le varianti, ne trova 8.

**Seconda prova, dopo la correzione delle stampe (D81), stessi criteri e soglie: v1.10 adottata.**

| # | v1.9 | v1.10 | Superato |
|---|---|---|---|
| E1 | 0 su 202 | 0 su 214 | sì |
| E2 | 6 voci | 0 voci | sì |
| E3 | | N1: EV −0,32%, ES +0,07%, RC −1,15%; N2: ogni fascia migliore (fino a −1,99%); N3: CA 78,7%; N4: deal 85,6%; N5: scenario sfavorevole −0,35%; N6: S1, S2, S4–S7 come la v1.9 | sì |
| E4 | 7,26% | 7,21% contro 7,49% di tcgcharts (miglior concorrente); copertura 81,0% | sì |

Fascia bassa ancora dietro (R3: 17,6% contro 14,2%). Risultati in `results/v1.10/` e `results/real/phase_r_v110_d81.json`.

## 16. v1.11: forchetta tarata sulla copertura (registrato il 28 ottobre 2026, prima del codice; D87)

**Problema (D84–D86).** Con lo storico tcgcharts la calibrazione sceglie rumori di vendita e di copia grandi (σ_e 0,15, il massimo della griglia; σ_q 0,07) perché poche vendite sono molto lontane dal prezzo tipico. La forchetta predittiva all'80% ne contiene l'87,5%: troppo larga per le vendite tipiche.

**Modifica (v1.11, un solo cambiamento).** Dopo la calibrazione attuale, i tre rumori (σ_e, σ_a, σ_q) si moltiplicano per un fattore k della griglia 0,5 · 0,6 · … · 1,2, scelto perché la forchetta predittiva all'80% contenga la vendita successiva il più vicino possibile all'80% **nelle settimane di calibrazione** (dopo il riscaldamento), mai nelle settimane di prova. A parità di distanza vince il k più vicino a 1. Parametro `coverage_fit` della calibrazione (spento = v1.10). Sul mercato simulato il fattore si sceglie allo stesso modo sulle prime 52 settimane di ogni prova.

| # | Criterio | Soglia |
|---|---|---|
| F1 | R1 sui dati con storico dal luglio 2022 (`sales_hist`) e sui 90 giorni (`sales_tc`) | 0 voci |
| F2 | Voci con almeno 5 vendite negli ultimi 90 giorni a più di 0,5 in log dalla loro mediana, stessi dati | 0 |
| F3 | Fase R con lo scarto di sede su `sales_hist` | LVM sotto ogni concorrente e copertura R4 tra 75% e 85% |
| F4 | Fase R con lo scarto di sede su `sales_tc` (dati del sito di oggi) | non più di 0,2 punti sopra la v1.10 (7,21%) e copertura R4 tra 75% e 85% |
| F5 | Protocollo completo sul mercato simulato contro la v1.10 | N1–N6 del §5 con la v1.10 al posto della v1.1 |

Se passa, il sito usa la v1.11 e lo storico dal luglio 2022. Se no, resta la v1.10 sui 90 giorni.

**Esito (30 ottobre 2026): v1.11 non adottata.**

| # | v1.10 | v1.11 | Superato |
|---|---|---|---|
| F1 | 0 / 0 | 0 su 214 (`sales_tc`), 0 su 216 (`sales_hist`) | sì |
| F2 | 0 / 0 | 0 / 0 | sì |
| F3 | 6,87%, R4 87,5% | k = 1,0 (copertura in calibrazione 79,0%): 6,87% contro 6,90% di tcgcharts, R4 87,5% | **no** (copertura) |
| F4 | 7,21%, R4 81,0% | k = 1,2: 7,18%, R4 84,7% | sì |
| F5 | | N1: EV +0,34%, ES +0,35%, RC +0,09%; N2 fasce fino a +1,84%; N3 CA 82,8%; N4 deal 86,5%; **N5 scenario sfavorevole +3,01%**; N6 S1, S2, S4–S7 | **no** (N5) |

Il fattore tarato sulle settimane di calibrazione non risolve il problema: sullo storico la forchetta copre già l'80% nel periodo di calibrazione (k = 1,0), e diventa troppo larga solo dopo, cioè le vendite recenti oscillano meno di quelle del 2022–2023. Sul mercato simulato le prime settimane coprono meno dell'80% e il fattore sale quasi sempre a 1,2, peggiorando lo scenario sfavorevole.

## 17. v1.12: rumore che cambia nel tempo (registrato il 30 ottobre 2026, prima del codice; D90)

**Problema (D88).** Sullo storico la forchetta copre l'80% nel periodo di calibrazione ma l'87,5% dopo: le vendite recenti oscillano meno di quelle del 2022–2023, e il motore usa un rumore fisso.

**Modifica (v1.12, un solo cambiamento).** Un fattore κ_t moltiplica le varianze dei rumori di vendita e di copia (σ_e², σ_a², σ_q²). Parte da 1; ogni settimana con almeno 20 vendite credibili (probabilità di genuinità > 0,8) si misura il rapporto robusto r = mediana(residuo² / varianza prevista) / 0,455 (0,455 è la mediana di un χ² a 1 grado) e si aggiorna κ_t ← κ_{t−1} · r^λ, con λ da un'emivita di 13 settimane; κ_t resta tra 0,25 e 2,25. Il residuo di ogni vendita è calcolato con le stime della settimana prima (mai con la vendita stessa). Parametro `vol_halflife` (0 = v1.10). La calibrazione non cambia.

| # | Criterio | Soglia |
|---|---|---|
| G1 | R1 su `sales_hist` e `sales_tc` | 0 voci |
| G2 | Voci con almeno 5 vendite negli ultimi 90 giorni a più di 0,5 in log dalla loro mediana, stessi dati | 0 |
| G3 | Fase R con lo scarto di sede su `sales_hist` | LVM sotto ogni concorrente e copertura R4 tra 75% e 85% |
| G4 | Fase R con lo scarto di sede su `sales_tc` | non più di 0,2 punti sopra la v1.10 (7,21%) e copertura R4 tra 75% e 85% |
| G5 | Protocollo completo sul mercato simulato contro la v1.10 | N1–N6 del §5 con la v1.10 al posto della v1.1 |

Solo riportato (idea delle prove su finestre mobili): errore e copertura della fase R trimestre per trimestre, LVM contro il miglior concorrente.

Se passa, il sito usa la v1.12 e lo storico dal luglio 2022. Se no, resta la v1.10.

**Esito (30 ottobre 2026): v1.12 non adottata.**

| # | v1.10 | v1.12 | Superato |
|---|---|---|---|
| G1 | 0 / 0 | 0 su 214 (`sales_tc`); **1 su 216** (`sales_hist`: Suicune Neo Revelation 1ª ed. PSA 10 sotto la PSA 9) | **no** |
| G2 | 0 / 0 | 0 / 0 | sì |
| G3 | 6,87%, R4 87,5% | 6,73% contro 6,90% di tcgcharts; **R4 71,9%** | **no** (copertura) |
| G4 | 7,21%, R4 81,0% | 7,22%, R4 80,8% | sì |
| G5 | | N1: EV −0,19%, ES +0,17%, RC −0,78%; N2 fasce fino a +0,35%; N3 CA 79,0%; N4 deal 86,6%; N5 −0,03%; N6 S1, S2, S4–S7 | sì |

Trimestre per trimestre (solo riportato): sullo storico la v1.10 copre tra l'83% e il 90% in ogni trimestre; la v1.12 tra il 66% e il 76%, perché κ scende fino al minimo 0,25. Il rapporto basato sulla mediana dei residui misura il centro della distribuzione, che con code pesanti è molto più stretto: corregge troppo. L'errore della v1.12 è il più basso mai misurato sullo storico, ma il vantaggio su tcgcharts trimestre per trimestre è piccolo e non costante (in 3 trimestri su 12 tcgcharts è avanti o pari).

## 18. Prove più severe, per ogni versione registrata dopo il 30 ottobre 2026 (D92)

1. **Incertezza dei confronti sulle vendite vere.** Ogni differenza di errore mediano tra l'LVM e un concorrente si riporta con un intervallo al 95% da bootstrap per carta (si ricampionano carte intere, perché le vendite della stessa carta non sono indipendenti; `slabwise/stats.py`). "Meglio" vuol dire intervallo tutto sotto zero; "non peggio" vuol dire estremo superiore non oltre +0,2 punti.
2. **Periodo tenuto da parte (prova prospettica).** Le vendite avvenute dopo il 30 ottobre 2026 non si usano per scegliere né per correggere versioni. Una versione che passa le prove sui dati vecchi si adotta solo dopo averle ripassate su queste vendite nuove, appena sono almeno 2.000, con gli stessi criteri registrati.
3. **Mercato simulato su larga scala.** Oltre alle 23 prove del §5, un pannello di 40 mercati (30 di base e 10 sfavorevoli, semi 101–130 e 101–110) con la versione adottata; ogni nuova versione si confronta seme per seme. N1 e N5 si giudicano anche con l'intervallo al 95% della differenza media tra semi.

Primo uso (solo riportato, v1.10 sui 90 giorni): errore LVM meno tcgcharts −0,27 punti, intervallo [−0,55; −0,11]: il vantaggio è reale anche se piccolo. Fascia con poche vendite: +2,2 punti, intervallo [−3,4; +6,1]: non si può dire né che siamo peggio né che siamo meglio.

## 19. v1.13: scala dei voti delle stampe varianti dalla carta base (registrato il 30 ottobre 2026, prima del codice; D94)

**Problema (D92).** Una stampa variante (1ª edizione, shadowless, guance rosse/gialle) è stimata come una carta a sé; con poche vendite la sua scala dei voti parte dalla media dell'era, mentre la carta base della stessa illustrazione la conosce molto meglio (es. Alakazam shadowless PSA 10 stimato circa 1.400 $, venduto 6.600 $).

**Modifica (v1.13, un solo cambiamento).** Per una variante (`carta/variante`) la scala dei voti parte da quella stimata per la carta base: media = distanze 9, 8, 7 della base, dispersione = incertezza della base più 0,25 in log (`variant_sd`). Se la base non ha ancora una stima, resta la scala dell'era. Le carte base non cambiano. Parametro `variant_gaps` (spento = v1.10). Sul mercato simulato non ci sono varianti: il codice nuovo non entra mai e il risultato è identico alla v1.10 (verificato su un mercato invece di ripetere le 23 prove).

| # | Criterio (dati `sales_tc`; regole del §18) | Soglia |
|---|---|---|
| V1 | R1 | 0 voci |
| V2 | Voci con almeno 5 vendite negli ultimi 90 giorni a più di 0,5 in log dalla loro mediana | 0 |
| V3 | Errore mediano con scarto di sede sulle vendite delle varianti, v1.13 meno v1.10 | intervallo al 95% tutto sotto zero |
| V4 | Errore mediano con scarto di sede su tutte le vendite, v1.13 meno v1.10 | estremo superiore ≤ +0,2 punti |
| V5 | Copertura R4 | tra 75% e 85% |
| V6 | Prova prospettica: V1–V5 sulle vendite dopo il 30 ottobre, appena sono almeno 2.000 | come sopra |

**Esito (30 ottobre 2026): v1.13 non adottata.** V1 0 voci, V2 0 voci, V4 −0,01 punti [−0,04; +0,03], V5 copertura 80,9%: superati. **V3 no**: sulle 876 vendite di varianti l'errore mediano va da 15,70% a 15,82%, intervallo [−1,04; +0,96]. La modifica corregge proprio i casi per cui era pensata (prime vendite PSA 10 di una variante: Alakazam shadowless da 6,95 a 8,37 in log contro 8,50 venduto; Mewtwo shadowless da 7,02 a 8,31 contro 8,45), e le vendite sbagliate di più del 50% scendono da 100 a 84 (solo riportato), ma sono poche e la mediana non le vede. Il resto dell'errore sulle varianti è un ritardo della PSA 10 di carte come Machamp 1ª edizione, che la scala della carta base non spiega.

## 20. v1.14: scala dei voti a gradini, informata dalle popolazioni PSA (registrato il 30 ottobre 2026, prima del codice; D101)

**Problema (D98).** Sei stime sono a più di 2 volte dalle proprie vendite recenti. Diagnosi sul modello: in tutte le vendite del voto sbagliato hanno credibilità 0. (a) PSA 7 moderne: la carta ha gradini 10→9 e 9→8 piatti (es. Umbreon VMAX −0,64 e −0,17 in log), ma la distanza della PSA 7 parte dalla media comune (−2,89) perché le distanze 9, 8, 7 hanno priori indipendenti; la vendita vera a 1.678 $ sembra impossibile. (b) PSA 10 vintage rarissime (Lugia Neo Genesis, Dragonite Fossil): il gradino 9→10 comune (circa ×5) è troppo piccolo per carte con pochissime PSA 10 rispetto alle PSA 9.

**Modifica (v1.14, la priore della scala dei voti; due ingredienti provati anche da soli, solo riportato).**
1. `step_prior`: la priore non è più su tre distanze indipendenti ma sui tre gradini (10→9, 9→8, 8→7), indipendenti tra loro; le distanze sono le somme dei gradini, quindi una carta con gradini alti piatti ha anche la PSA 7 vicina. Media e dispersione di ogni gradino si imparano dalle carte che lo misurano bene (ultima stima di ogni carta), come le altre priori gerarchiche.
2. `pop_steps`: la media di ogni gradino dipende dal rapporto tra le popolazioni PSA dei due voti, x = log(pop voto basso / pop voto alto), con una regressione pesata sulle carte che misurano bene il gradino (almeno 8 carte con popolazione, altrimenti nessun effetto). Popolazioni da tcgcharts (D76).

**Mercato simulato con popolazioni.** Le popolazioni esistono già nel simulatore ma non dicono nulla sui prezzi (dipendono solo dalla liquidità): sono lo scenario "popolazioni inutili". Si aggiunge lo scenario "popolazioni utili" (`pop_gap`, 0 = come prima): il gradino 10→9 vero aumenta di 0,3 · (x − media di x). Nessun numero casuale in più, quindi con `pop_gap = 0` il mercato resta identico.

| # | Criterio (regole del §18) | Soglia |
|---|---|---|
| L1 | R1 su `sales_tc` | 0 voci |
| L2 | E2 su `sales_tc` | 0 voci |
| L3 | Stime a più di 2 volte dalla mediana delle proprie vendite delle ultime 13 settimane (regola D98), sito ricostruito con `sales_all` | al massimo 1 (v1.10: 6) |
| L4 | Fase R con scarto di sede su `sales_tc`: v1.14 meno v1.10; LVM meno il miglior concorrente | estremo superiore ≤ +0,2 punti; intervallo tutto sotto zero |
| L5 | Copertura R4 su `sales_tc` | tra 75% e 85% |
| L6 | Popolazioni inutili: le 23 prove del §5 contro la v1.10 | N1–N6 |
| L7 | Popolazioni utili: 10 mercati (semi 101–110, parametri del pannello v1.10), v1.14 e v1.10 sugli stessi mercati | EV medio più basso, intervallo al 95% tra semi tutto sotto zero; CA tra 75% e 85% |
| L8 | Prova prospettica: L1, L4 (solo contro la v1.10) e L5 sulle vendite dopo il 30 ottobre, appena sono almeno 2.000 | come sopra |

**Esito provvisorio (30 ottobre 2026): L1–L7 superati, manca L8.** L1 0 voci; L2 0 voci; L3 0 stime fuori di 2 volte (v1.10: 6; solo gradini 1); L4 −0,04 punti [−0,11; +0,05] contro la v1.10 e −0,31 punti [−0,59; −0,13] contro tcgcharts; L5 copertura 81,1%; L6 N1 EV −3,08%, ES +0,09%, RC −0,13%, N2 fasce tra −4,5% e +1,0%, N3 CA 79,5%, N4 deal 85,8%, N5 −4,14%, N6 come la v1.10; L7 EV 0,0557 → 0,0545 (−0,0013, intervallo [−0,0013; −0,0012]), meglio in 10 mercati su 10, CA 77,8%. Solo riportato: fascia con poche vendite da 17,6% a 15,6% (miglior concorrente 14,2%). La v1.14 si adotta solo dopo L8, sulle vendite dopo il 30 ottobre.

**Cambio di regola per la v1.14 (D103, prima di vedere L8).** Su richiesta di Oscar la v1.14 si adotta subito, con L1–L7 superati; L8 resta obbligatoria e si esegue appena ci sono 2.000 vendite dopo il 30 ottobre. Se L8 non passa, il sito torna alla v1.10 (`step_prior` e `pop_steps` False) nello stesso giorno.

## 21. Previsioni a 1, 3 e 6 mesi (registrato il 1° novembre 2026, prima del codice; D106)

**Cosa si pubblica.** Per ogni carta e voto, oltre al valore di oggi, l'intervallo all'80% tra 4, 13 e 26 settimane. Il motore non prevede la direzione (il valore centrale è quello di oggi spostato dal fattore d'era con la sua deriva stimata, che la v1.3 ha mostrato inutile: D36): misura il **rischio**, cioè quanto può muoversi. Varianza a h settimane = varianza di oggi + h·(q_c + varianza del fattore d'era per settimana · β_c²) + rumore di vendita e di copia, come la forchetta predittiva di R4.

| # | Criterio (fase R sulle vendite vere, `sales_tc`, regole del §18) | Soglia |
|---|---|---|
| P1 | Per h = 4, 13, 26: quota delle vendite avvenute tra h−2 e h+2 settimane dopo la stima che cadono nell'intervallo all'80% previsto per h | tra 75% e 85% per ogni h |
| P2 | Stesso confronto, errore mediano della previsione contro "ultima vendita" e "mediana di tcgcharts" a parità di orizzonte | non peggiore di nessuno dei due (estremo superiore dell'intervallo al 95% ≤ 0) |
| P3 | Larghezza mediana dell'intervallo a 13 settimane | riportata (deve crescere con h) |

Se P1 non passa per un orizzonte, quell'orizzonte non si pubblica. Le previsioni entrano nell'istantanea sigillata (D105) e la pagella le confronta con le vendite quando arriva la loro data.

**Esito (1° novembre 2026): previsioni non pubblicate.** Su `sales_tc`, motore v1.14. P1 non superato a nessun orizzonte: copertura 91,6% a 4 settimane, 93,1% a 13, 89,5% a 26 (intervalli troppo larghi; larghezza mediana a 13 settimane ±77%). P2 superato a tutti: errore mediano 10,1% / 18,1% / 32,6% contro ultima vendita 12,0% / 21,4% / 36,1% e mediana tcgcharts 10,6% / 21,2% / 37,7%, intervalli tutti sotto zero. La varianza di deriva (q_L, τ_f) è calibrata per il valore di oggi, non per l'orizzonte: la prossima versione delle previsioni va registrata con una deriva tarata sugli orizzonti.

## 22. v1.15: gradini dalle code pesanti e popolazioni delle varianti (registrato il 2 novembre 2026, prima del codice; D124)

**Problema (D121, D123).** Nelle carte con una scala dei voti molto ripida il motore giudica anomale vendite vere e coerenti tra loro. Diagnosi sui dati del 2 novembre con le vendite d'asta da tcgcharts (`SLABWISE_TC_AUCTIONS=1`): Lugia Neo Genesis 1ª edizione, priore del gradino 10→9 −1,85 in log (×6,4) con dispersione 0,31; le tre vendite PSA 10 vere (360.000, 514.080, 654.000 $) contro un PSA 9 intorno a 17.000 $ chiedono circa −3,2 (×24–38), cioè 4,3 dispersioni: il motore mette il PSA 10 a 108.862 $ e dà credibilità 0 a tutte e tre (R1). Stessa cosa per base2-11/1st (E2) e per le Gold Star fermate il 2 novembre (PSA 7–9 stimati 2–3 volte sopra le proprie vendite). Due cause: (a) la priore normale sui gradini non lascia mai andare, anche contro più vendite coerenti; (b) le stampe varianti (1ª edizione, shadowless) non hanno popolazioni, quindi non ricevono la pendenza delle popolazioni della v1.14 e partono dal gradino medio.

**Modifica (v1.15; i due ingredienti provati anche da soli, solo riportato).**
1. `step_t` = 4: la priore di ogni gradino diventa una t di Student con 4 gradi di libertà, stessa media e stessa scala della v1.14. Nell'IRLS la precisione del gradino k si moltiplica per (ν+1)/(ν+z_k²), con z_k lo scarto standardizzato del gradino stimato; la penalità nella scelta tra i punti di partenza è (ν+1)/2·log(1+z_k²/ν). Con poche vendite resta come la v1.14; con più vendite coerenti lontane dalla priore la priore cede.
2. `variant_pops`: una stampa variante usa i rapporti tra le popolazioni della sua carta base per la pendenza dei gradini.

| # | Criterio (regole del §18) | Soglia |
|---|---|---|
| S1 | R1 su `sales_all` ricostruito oggi, con e senza vendite d'asta da tcgcharts | 0 voci in entrambi |
| S2 | E2 sugli stessi due insiemi | non più voci della v1.14 (oggi 1, base2-11/1st) |
| S3 | Fase R con scarto di sede su `sales_tc`: v1.15 meno v1.14 | estremo superiore dell'intervallo al 95% ≤ +0,2 punti |
| S4 | Copertura R4 su `sales_tc` | tra 75% e 85% |
| S5 | Mercato simulato: le 23 prove del §5 contro la v1.14 | N1–N6 |
| S6 | Prova prospettica: S1, S3 e S4 sulle vendite dopo il 2 novembre, appena sono almeno 2.000 | come sopra |

Solo riportato: le carte EX e Gold Star fermate il 2 novembre (ex13-16, ex13-103, ex14-99, ex14-100, ex15-101) rifatte passare dal controllo d'ingresso (§15) con la v1.15. Se S1–S5 passano, la v1.15 si adotta e S6 diventa obbligatoria come L8 per la v1.14; le vendite d'asta da tcgcharts si accendono solo se S1 passa con loro.

**Esito (2 novembre 2026): S1–S5 superati, la v1.15 si adotta; manca S6.** S1 R1 0 voci senza vendite d'asta e 0 con (v1.14: 0 e 1, neo1-9/1st PSA 10); S2 E2 1 voce in entrambi (base2-11/1st PSA 9, come la v1.14); S3 fase R su `sales_tc` (15.471 vendite), v1.15 meno v1.14 +0,03 punti [−0,08; +0,07] (soglia +0,2); S4 copertura R4 82,8%; S5 sui 23 lavori simulati: N1 EV 0,0558 contro 0,0557, ES 0,0830 contro 0,0831, RC 0,0639 contro 0,0643; N2 fasce entro +0,2%; N3 CA 79,4%; N4 deal 86,1%; N5 scenario sfavorevole 0,0666 contro 0,0664; N6 come la v1.14 (S3 non superato da entrambe). Solo riportato: le cinque carte EX fermate il 2 novembre restano fuori anche con la v1.15. Diagnosi: non è la scala dei voti. Le loro vendite sono raddoppiate nelle ultime 4–6 settimane (es. Alakazam ☆ PSA 7 da 3.200–4.000 $ a 6.500–9.000 $), il motore segue i prezzi recenti e E2 confronta con la mediana di 90 giorni, che il rialzo rende vecchia. Proposta a Oscar, non applicata (D125).

## 23. Controllo d'ingresso E2 sulle vendite recenti (registrato il 2 novembre 2026, prima del codice; D125, ok di Oscar)

**Problema (D125).** E2 (§15) confronta la stima di oggi con la mediana delle vendite degli ultimi 90 giorni. Quando il prezzo di una carta cambia molto nel periodo (Gold Star EX, raddoppiate in ottobre) la mediana è vecchia e il controllo ferma una stima che segue i prezzi recenti.

**Modifica (E2r).** Per ogni voce con almeno 5 vendite negli ultimi 90 giorni, riferimento = mediana delle vendite degli ultimi 30 giorni se sono almeno 5, altrimenti delle ultime 5 vendite del voto; la voce è segnalata se la stima è a più di 0,5 in log dal riferimento. Stessa soglia, stesse vendite pulite.

| # | Criterio | Soglia |
|---|---|---|
| G1 | E2r sul catalogo di oggi, motore v1.15, `sales_all` di oggi | non più voci di E2 (oggi 1) |
| G2 | Sensibilità: con il motore v1.10 (`step_prior`, `pop_steps`, `step_t` spenti), che sbagliava davvero le PSA 7 moderne e le PSA 10 vintage rare (D98), E2r segnala almeno l'80% delle voci che segnala E2 | ≥ 80% |

Solo riportato: le cinque carte EX fermate il 2 novembre rifatte passare con E2r. Se G1 e G2 passano, E2r sostituisce E2 nel controllo d'ingresso delle carte nuove (`add_cards.py`, `add_batch.py`); E2 resta stampato per confronto.

**Esito (2 novembre 2026): G1 e G2 superati, E2r adottato.** G1 E2r 1 voce come E2 (base2-11/1st PSA 9). G2 con il motore v1.10 E2 segnala 1 voce ed E2r la stessa (100%; prova debole: sui dati di oggi la v1.10 sbaglia una sola voce). Solo riportato: con E2r entrano Mew ☆ δ, Mewtwo ☆, Celebi ☆ e Rayquaza δ; Alakazam ☆ resta fuori (PSA 9 stimato 20.579 $ contro 7.000 $ delle vendite recenti).

## 24. Quanto si muove: volatilità e peggior calo (registrato il 3 novembre 2026, prima del codice; D127)

**Cosa si pubblica.** Per ogni carta e voto con vendite proprie e almeno 26 settimane di stime: (a) **quanto si muove**, la deviazione standard delle variazioni a 4 settimane (in log) della stima settimanale del motore nelle ultime 52 settimane, mostrata come ±x% al mese; (b) il **peggior calo**, la discesa massima dal punto più alto nelle ultime 52 settimane. Livelli in parole, fissati ora: *Ferma* sotto il 3%, *Tranquilla* 3–6%, *Mossa* 6–12%, *Agitata* 12–20%, *Ballerina* oltre il 20%. Per ogni serie le stesse due misure sull'indice. È il passato, non una previsione: il sito lo dice.

| # | Criterio (vendite vere, `sales_all` di oggi, motore adottato) | Soglia |
|---|---|---|
| V1 | La volatilità misurata sulle settimane da W−78 a W−26 ordina le voci come i movimenti delle 26 settimane dopo (media dei valori assoluti delle variazioni a 4 settimane): correlazione di Spearman tra le voci con almeno 26 settimane in entrambi i periodi | ≥ 0,30 |
| V2 | Movimento mediano delle 26 settimane dopo nel terzo più volatile contro il terzo meno volatile | almeno 1,5 volte |
| V3 | Correlazione di Spearman tra volatilità e larghezza della forchetta di oggi | riportata (deve dire una cosa diversa dall'incertezza) |

Se V1 o V2 non passano, la volatilità non si pubblica.

**Esito (3 novembre 2026): V1 e V2 non superati, la volatilità non si pubblica.** 208 voci: V1 Spearman 0,085 (soglia 0,30); V2 1,10 volte (soglia 1,5); V3 0,21 (riportato). Come si è mossa la stima nell'ultimo anno non dice quasi niente di come si muoverà nei sei mesi dopo.

**§24b, seconda prova registrata prima di eseguirla (3 novembre 2026).** Stessa domanda su un orizzonte più lungo: volatilità = deviazione standard delle variazioni a 13 settimane, misurata sulle settimane da W−130 a W−26; movimento dopo = valore assoluto della variazione tra W−26 e W−13 e tra W−13 e l'ultima settimana (media dei due). Stesse soglie V1 ≥ 0,30 e V2 ≥ 1,5 volte. Se non passa, la volatilità per carta non si pubblica e la proposta si chiude.

**Esito §24b (3 novembre 2026): non superato.** 208 voci: V1 Spearman 0,115; V2 1,09 volte. La volatilità per carta non si pubblica; la proposta è chiusa (D127).

## 25. v1.16: rumore tarato sulla copertura delle vendite recenti, e lo storico lungo nei prezzi (registrato il 3 novembre 2026, prima del codice; D128)

**Problema (D86, D88, D91).** Con lo storico lungo di tcgcharts (vendite dal luglio 2022) la forchetta all'80% contiene l'87,5% delle vendite: le vendite recenti oscillano meno di quelle del 2022–2023, ma il rumore resta quello calibrato sugli anni vecchi. La v1.12 lo faceva seguire con la mediana dei residui delle sole vendite credibili, che con code pesanti scende troppo (copertura 71,9%). D91 indica la strada: puntare direttamente alla copertura.

**Modifica (v1.16, `cov_halflife` = 13).** Ogni settimana, su tutte le vendite della settimana (anche quelle poco credibili, come conta R4), si misura il quantile 80% di |residuo| / deviazione standard prevista; il fattore sui rumori κ si moltiplica per (quantile / 1,2816)², con mezza vita 13 settimane (κ ← κ · rapporto^λ), limitato a [0,25; 2,25]. Usa solo vendite passate. Senza storico (90 giorni) deve cambiare poco.

| # | Criterio (regole del §18) | Soglia |
|---|---|---|
| K1 | R1 su `sales_all` di oggi con e senza storico (`SLABWISE_TC_HISTORY=1`) | 0 voci in entrambi |
| K2 | E2r sugli stessi due insiemi | non più voci della v1.15 |
| K3 | Con lo storico: fase R, LVM contro il miglior concorrente; copertura R4 | intervallo al 95% tutto sotto zero; R4 tra 75% e 85% |
| K4 | Senza storico (`sales_tc`): v1.16 meno v1.15; copertura R4 | estremo superiore ≤ +0,2 punti; R4 tra 75% e 85% |
| K5 | Mercato simulato: le 23 prove contro la v1.15 | N1–N6 |
| K6 | Periodo tenuto da parte: con lo storico, copertura R4 sulle sole vendite dopo il 1° settembre 2026 | tra 75% e 85% |

Se K1–K6 passano, la v1.16 si adotta e lo storico lungo entra nei prezzi; prova prospettica sulle vendite dopo il 3 novembre come per le versioni precedenti.

## 26. Indice: una carta, un voto nel paniere (registrato il 3 novembre 2026, prima del codice; D130)

**Problema (Oscar).** Il paniere dell'indice (v1.4) prende le 10 combinazioni carta e voto più vendute: la stessa carta può entrare due o tre volte con voti diversi (es. Dragonite Fossil PSA 7 e PSA 8), quindi pesa doppio o triplo e i suoi movimenti, molto legati tra un voto e l'altro, contano più di quelli delle altre carte.

**Modifica (`one_per_card`).** Al ribilanciamento, per ogni carta resta solo il suo voto più venduto (con le stesse regole: almeno 6 vendite credibili nelle 13 settimane); poi le 10 carte più vendute. Pesi uguali, concatenamento e base comune come prima.

| # | Criterio (§7, 5 semi del mercato simulato, parametri della v1.2) | Soglia |
|---|---|---|
| P1' | Quota dei movimenti veri a 12 settimane catturata, mediana tra ere e semi | tra 0,80 e 1,20 |
| P2' | Correlazione con i movimenti veri, mediana tra ere e semi | ≥ 0,80, e non più di 0,03 sotto la v1.4 sugli stessi semi |

Se passano, il sito usa il nuovo paniere; la pagina di ogni indice mostra le carte (una riga per carta) e il voto usato.

## 27. Storia degli indici ricostruita con lo storico lungo (registrato il 3 novembre 2026, prima del codice; D138)

**Idea.** Lo storico lungo (vendite dal 2016) non entra nei prezzi (D128). Qui serve solo a raccontare il passato degli indici: motore e indici (v1.4 con i gruppi di D136) girano sulle vendite con lo storico; la serie ricostruita di ogni indice si scala perché valga 100 nella settimana di base dell'indice pubblicato, e si mostra solo prima di quella settimana. Prezzi e indice pubblicato restano identici.

**Paniere minimo (regola, non criterio).** La storia di un indice parte dalla prima revisione in cui il paniere ha almeno 5 voci (indici d'era e di set) o almeno 15 (indice generale).

| # | Criterio | Soglia |
|---|---|---|
| H1 | Mercato simulato, 5 semi del §7 (`results/index_seedN.json`), settimane 38–63 (dati ancora scarsi, prima del periodo del §7): quota dei movimenti veri a 12 settimane catturata, mediana tra ere e semi; correlazione, mediana | quota tra 0,70 e 1,30; correlazione ≥ 0,70 |
| H2 | Vendite vere ripetute dello stesso cert (archivio delle case d'asta), coppie consecutive nello stesso voto, entrambe prima della base e dopo l'inizio della storia del loro indice d'era: retta Δlog prezzo su Δlog indice | pendenza tra 0,70 e 1,30, con intervallo al 95% (bootstrap per carta) sopra 0,30 |
| H3 | Stesse coppie: errore quadratico medio di Δlog prezzo corretto con l'indice contro senza indice (Δlog prezzo meno la sua media) | almeno il 10% in meno |
| H4 | Coerenza: dalla base a oggi, correlazione tra le variazioni a 4 settimane dell'indice ricostruito e di quello pubblicato, mediana tra gli indici pubblicati | ≥ 0,80 |

Se H1–H4 passano, il sito mostra la storia ricostruita con un tratto distinto e la scritta "ricostruito con le vendite passate". Se uno non passa, non si mostra e si dice quale. H2–H3 usano vendite che il motore ha visto: sono una prova di coerenza, non fuori campione; per questo c'è H1.

**Esito §25 (3 novembre 2026): v1.16 non adottata, lo storico lungo resta fuori dai prezzi.** K1 superato (R1 0 voci in tutti e quattro i casi). K2 **no**: con lo storico E2r 2 voci contro 1 della v1.15 (in più base1-8 PSA 10, stimato 3.047 $ contro 8.000 $ delle vendite recenti). K3 sì nei numeri: con lo storico errore 6,69% contro 6,89% di tcgcharts, R4 80,3% (la v1.15 con lo storico: 6,76%, R4 86,6%). K4 **no**: senza storico R4 85,3% (soglia 85%), errore 7,40% contro 7,38%. K5 **no**: N1 RC +4,5% e N5 scenario sfavorevole +3,0% (soglia 2%). K6 sì: dopo il 1° settembre copertura 76,4% (v1.15: 86,6%). La direzione è giusta per lo storico (forchetta di nuovo all'80%) ma il fattore peggiora il resto: sui 90 giorni allarga la forchetta e nel mercato simulato reagisce troppo ai crolli.

**Esito §26 (3 novembre 2026): non superato, il paniere resta per carta e voto.** Sui 5 semi (25 ere): con una carta un voto P1 0,97 (sì) ma P2 0,765 (soglia 0,80) e 0,042 sotto la v1.4 (0,807; soglia 0,03). Tenere un solo voto per carta butta via vendite vere: l'indice segue il mercato peggio. La pagina dell'indice raggruppa comunque le righe per carta.

**Esito §27 (3 novembre 2026): non superato, la storia ricostruita non si mostra.** H1 sì (5 semi, 25 ere, settimane 38–63: quota 0,945, correlazione 0,747). H2 sì (476 coppie di rivendite dello stesso cert su 25 carte: pendenza 0,99, intervallo al 95% 0,74–1,16). H3 sì (errore quadratico −29,6%). H4 **no**: dalla base a oggi le variazioni a 4 settimane dell'indice ricostruito e di quello pubblicato hanno correlazione mediana 0,66 (Mega Evoluzione 0,81, Scarlatto e Violetto 0,70, generale 0,69, Spada e Scudo 0,63, Wizards of the Coast 0,25, Base Set 0,00; soglia 0,80). Con lo storico il motore racconta un'altra storia recente, soprattutto nel vintage: è lo stesso nodo di D128 (lo storico cambia le stime, non solo il passato). Gli indici ricostruiti seguono bene le rivendite vere prima della base, ma attaccarli a quelli pubblicati non è coerente. Risultati in `results/index_history/summary.json` e `results/index_history_H1.json`.

## 28. Indice: paniere a strati per voto (registrato il 3 novembre 2026, prima del codice; D143)

**Problema (Oscar).** Il paniere prende le 10 combinazioni carta e voto più vendute: nel vintage restano solo PSA 7 e 8 (Wizards of the Coast e Base Set: nessun PSA 9 o 10), nel moderno solo PSA 10. L'indice racconta un solo strato di mercato.

**Modifica (`strata` = 2).** Al ribilanciamento, prima si riservano fino a 2 posti per ognuno dei voti 10, 9, 8 e 7 alle combinazioni di quel voto con almeno 4 vendite credibili nelle 13 settimane (le più vendute); poi i posti rimasti (fino a 10) alle più vendute in assoluto con la regola attuale (almeno 6). Pesi uguali, concatenamento e base comune come prima.

| # | Criterio (§7, 5 semi del mercato simulato, parametri della v1.2) | Soglia |
|---|---|---|
| S1 | Quota dei movimenti veri a 12 settimane catturata, mediana tra ere e semi | tra 0,80 e 1,20 |
| S2 | Correlazione con i movimenti veri, mediana tra ere e semi | ≥ 0,80, e non più di 0,03 sotto la v1.4 sugli stessi semi |
| S3 | (solo riportato) sui dati veri: quante voci per voto nei panieri di oggi | — |

Se S1 e S2 passano, il sito usa il paniere a strati.

**Esito §28 (3 novembre 2026): non superato, il paniere resta quello della v1.4.** Sui 5 semi (25 ere): con i posti riservati per voto S1 1,03 (sì) ma S2 0,760 (soglia 0,80) e 0,046 sotto la v1.4 (0,807; soglia 0,03). I voti alti con poche vendite rendono l'indice più rumoroso: segue peggio il mercato vero. Risultati in `results/index_seedN_strata.json` e `results/index_strata_summary.json`.

## 29. Indici calcolati interamente con lo storico lungo (registrato il 3 novembre 2026, prima del codice; D148)

**Idea (diversa da §27).** I prezzi delle carte restano sui dati di oggi (D128). Gli indici invece si calcolano **per intero** con motore e indici (v1.4, gruppi D136 e D142) sulle vendite con lo storico lungo (`SLABWISE_TC_HISTORY=1`), dal primo paniere abbastanza pieno a oggi: nessun incastro con l'indice di oggi (il problema di H4 in §27). Base comune come in D121, sulla serie con lo storico.

**Paniere minimo (regola).** Come §27: una serie parte dalla prima revisione con almeno 5 voci (era, set, Giappone) o 15 (generale).

| # | Criterio | Soglia |
|---|---|---|
| J1 | Mercato simulato: l'algoritmo è quello del §7 (superato: quota 1,02, correlazione 0,807) e del §27 H1 sui dati scarsi (superato: 0,945 e 0,747) | già superato, si riporta |
| J2 | Vendite vere ripetute dello stesso cert (archivio delle case d'asta), coppie consecutive nello stesso voto, **in tutto il periodo** coperto dall'indice d'era della carta: retta Δlog prezzo su Δlog indice | pendenza tra 0,70 e 1,30, intervallo al 95% (bootstrap per carta) sopra 0,30 |
| J3 | Stesse coppie: errore quadratico di Δlog prezzo corretto con l'indice contro senza | almeno il 10% in meno |
| J4 | Coppie con la prima vendita dopo la base dell'indice pubblicato oggi (almeno 30 coppie, altrimenti non superato): errore quadratico corretto con l'indice storico contro quello pubblicato | non più del 5% sopra |

Se J1–J4 passano, il sito prende gli indici (generale, ere, set, Giappone) dal calcolo con lo storico e lo dice nella pagina dell'indice; i prezzi delle carte non cambiano. Se no, gli indici restano quelli di oggi e si dice quale criterio non passa.

**Esito §29 (3 novembre 2026): superato, gli indici del sito si calcolano con lo storico lungo.** J1 sì (riportato). J2 sì: 717 coppie di rivendite dello stesso cert su 29 carte, pendenza 1,21, intervallo al 95% 1,02–1,35. J3 sì: errore quadratico −41,4%. J4 sì: 117 coppie dopo la base dell'indice pubblicato, errore con l'indice storico 0,98 volte quello con l'indice pubblicato. Indici con storia: Wizards of the Coast, EX, Spada e Scudo, Sole e Luna, XY dal 6 gennaio 2023; Nero e Bianco dall'aprile 2023; Scarlatto e Violetto e Giappone dall'ottobre 2023; Mega Evoluzione dal gennaio 2026. Risultati in `results/index_full_history/summary.json`.

## 30. v1.17: salti di prezzo riconosciuti quando più vendite recenti concordano (registrato il 4 novembre 2026, prima del codice; D155)

**Problema (diagnosi del 4 novembre sulle 23 carte fermate dal controllo d'ingresso).** Non è la scala dei voti: per quasi tutte il gradino 10→9 atteso coincide con quello stimato dalle vendite. In ottobre molte carte dell'era di mezzo e della classica hanno cambiato prezzo di 2–5 volte in poche settimane, con vendite coerenti tra loro (Gyarados Call of Legends PSA 9 da 600–800 $ a 3.200–4.600 $; Gengar Legend Maker PSA 9 da circa 1.100 $ a 3.000–4.200 $; Giratina LV.X DP38 PSA 9 da 2.000–4.200 $ a 19.000–35.000 $). La deriva del livello è lenta (`q_L`), quindi le vendite nuove ricevono credibilità bassa e la stima resta indietro: E2r le ferma (giusto) e il motore pubblicherebbe prezzi 2–3 volte sotto il mercato.

**Modifica (v1.17, `jump` = vero).** A ogni nuovo calcolo di una carta, le sue vendite delle ultime 4 settimane si confrontano con la previsione della stima precedente (stesso voto, stessa sede, stessa lingua, fattore d'era applicato). Se sono almeno 3, la mediana degli scarti in log è oltre ±0,35 (×1,42) e almeno il 75% degli scarti ha lo stesso segno e almeno metà di quella mediana, si registra un **salto** per la carta: alla data della prima di quelle vendite, con varianza J = mediana². Il salto resta registrato. Nel modello (GLS esatto della passeggiata casuale) le vendite precedenti il salto ricevono J in più nella varianza e nella parte condivisa tra loro: restano informative sulla scala dei voti (le differenze tra voti), ma non tengono più fermo il livello di oggi. Parametri fissati qui: 4 settimane, 3 vendite, 0,35, 75%.

| # | Criterio (regole del §18) | Soglia |
|---|---|---|
| T1 | R1 su `sales_all` di oggi (catalogo) | 0 voci |
| T2 | E2r sullo stesso insieme | non più voci della v1.15 |
| T3 | Fase R su `sales_tc`: v1.17 meno v1.15 | estremo superiore dell'intervallo al 95% ≤ +0,2 punti |
| T4 | Copertura R4 su `sales_tc` | tra 75% e 85% |
| T5 | Mercato simulato: le 23 prove del §5 contro la v1.15 | N1–N6 |
| T6 | Prova prospettica: T1, T3 e T4 sulle vendite dopo il 4 novembre, appena sono almeno 2.000 | come sopra |

Solo riportato: quante delle 23 carte fermate il 4 novembre passano il controllo d'ingresso con la v1.17. Se T1–T5 passano, la v1.17 si adotta e T6 diventa obbligatoria come S6 per la v1.15. Se no, la v1.15 resta e le carte in forte rialzo aspettano.

**Esito §30 (4 novembre 2026): T2 non superato, la v1.17 non si adotta.** T1 sì: R1 0 voci su 908 con entrambe le versioni (`sales_all` ricostruito oggi). **T2 no**: E2r 3 voci con la v1.17 contro 1 con la v1.15 (in più dp5-98 PSA 9, stima 22.055 $ contro 12.100 $ delle vendite recenti; hgss3-10 PSA 10, 110.225 $ contro 50.400 $): su due carte del catalogo il salto porta la stima oltre il mercato. T3 sì: fase R su `sales_tc` (15.471 vendite) v1.17 meno v1.15 −0,01 punti [−0,04; +0,04]. T4 sì: copertura R4 80,4%. T5 interrotto dopo 12 lavori su 23 (inutile dopo T2). Solo riportato: delle 23 carte fermate il 4 novembre, con la v1.17 ne passano 5 invece di 2 (in più dp2-17, ex12-5, ex4-94). Diagnosi del poco effetto: i salti vengono riconosciuti (es. col1-SL10 alla settimana 191, J = 0,27), ma in molte carte è salito soprattutto il PSA 9 rispetto agli altri voti (Rayquaza Call of Legends: PSA 9 da circa 3 a circa 8 volte il PSA 8), e il salto di livello non cambia la scala dei voti. Il codice resta, spento (`jump=False`); un nuovo tentativo si registra solo con un'idea nuova.

## 31. Quante voci nel paniere: 10, 15 o 20 per era, 30 o 60 per il generale (registrato il 4 novembre 2026, prima del codice; D167)

**Domanda (Oscar).** "Non è un po' riduttivo contare solo 10 carte per indice? Cosa succederebbe raddoppiandole?" Il 4 novembre ogni era ha almeno 28 combinazioni carta e voto con 6 o più vendite in 13 settimane (Vintage 171, Contemporanea 157, Classica 140, Moderna 92, Di mezzo 73, Giappone 28); la 20ª voce ne ha almeno 20.

**Varianti.** Stesso algoritmo (§29: peso uguale, concatenato, ribilanciamento ogni 13 settimane, almeno 6 vendite credibili, tutto lo storico); cambia solo il numero massimo di voci: K = 10 (oggi), 15, 20 per gli indici d'era e Giappone; 30 (oggi) e 60 per il generale. Indici di set invariati (10).

**Misure** (coppie di rivendite dello stesso cert, stesso voto, come J2–J3 del §29; per il generale tutte le coppie inglesi contro l'indice generale):
- Q1: riduzione dell'errore quadratico sulle coppie (J3);
- Q2: pendenza (J2) e intervallo al 95% per carta;
- Q3: rumore: mediana di |variazione settimanale in log| dell'indice, media sulle ere.

| # | Criterio, per una variante contro l'attuale (10 o 30) | Soglia |
|---|---|---|
| Q1 | riduzione dell'errore | non più bassa di quella attuale meno 0,01 |
| Q2 | pendenza | tra 0,70 e 1,30, estremo inferiore dell'intervallo oltre 0,30 |
| Q3 | rumore | non oltre quello attuale più 10% |

Si adotta la K più grande che passa Q1–Q3 (prima 20, poi 15; per il generale 60). Se nessuna passa, resta 10 (30). Lo script è `scripts/index_k_test.py`, che gira sul workflow `prova-indici.yml`; risultati in `results/index_k/summary.json`.

**Esito §31 (5 novembre 2026): superata, si adottano 20 voci per era e 60 per il generale.** Su 717 coppie di rivendite (indici d'era): riduzione dell'errore Q1 0.332 con 10 voci, 0.333 con 15, 0.370 con 20; pendenza Q2 1.27, 1.25, 1.29 (intervallo con 20: 1.07–1.51); rumore Q3 0.0180, 0.0176, 0.0178. Generale, 630 coppie: Q1 0.344 con 30 voci, 0.366 con 60; pendenza 1.01 e 1.03; rumore 0.0143 e 0.0121. Passano K15, K20 e G60; per la regola si prende la più grande.

**Esito L8 della v1.14 (5 novembre 2026): non superata.** Vendite pulite dopo il 30 ottobre: 2.021 (2.020 valutate in fase R, stimatori addestrati sui dati precedenti). L1 **no**: R1 5 voci su 1.003 (base1-8, col1-15, dc1-6, hgssp-HGSS03, neo1-9/1st, tutte PSA 10). L4 sì: v1.14 meno v1.10 −0,20 punti [−0,42; −0,02]. L5 **no**: copertura 66,7% (v1.10: 65,6%). Confronto riportato, sugli stessi dati: la v1.10 ha R1 85 voci su 1.003; la v1.15, che il sito usa dal 2 novembre, R1 0 voci su 1.058, fase R −0,80 punti [−1,26; −0,42] contro la v1.10, copertura 68,1%. La regola di D103 ("se L8 non passa, il sito torna alla v1.10") era scritta quando la v1.14 era il motore del sito; oggi tornare alla v1.10 peggiorerebbe molto i prezzi (85 voci R1 contro 0). Il ritorno è sospeso e la scelta passa a Oscar (D171). La copertura sotto il 75% riguarda tutte le versioni: nel rialzo di ottobre le forchette sono troppo strette; la prova S6 della v1.15 (vendite dopo il 2 novembre, oggi 630) lo misurerà di nuovo.
