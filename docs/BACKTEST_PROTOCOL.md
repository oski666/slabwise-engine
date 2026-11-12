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

**S6 annullata (9 novembre 2026, D240):** la v1.15 è stata sostituita dalla v1.20 (D210) prima che le vendite dopo il 2 novembre bastassero; vale la verifica prospettica Y7 del §37.

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

## 32. Due bande: il valore (blu) e il mercato (rosa) (registrato il 6 novembre 2026, prima del codice; D173)

**Domanda (Oscar).** Forchette troppo larghe renderebbero i grafici poco leggibili; meglio tenere il fair value nella sua banda e "avvertire con una seconda forchetta dell'alta volatilità in corso". Dopo il 30 ottobre la copertura delle vendite è 66–68% (D171–D172).

**Modifica.** La banda **blu** resta quella di oggi (valore stimato ± incertezza della stima, 80%). Nuova banda **rosa**: dove cadono le vendite. Per ogni vendita, scarto standardizzato z = (log prezzo − stima della settimana prima con lo scarto di sede) / s, con s² = sd² + (σ² della sede + σ_q²)·κ (la banda del controllo R4). Per ogni era (e Giappone): v_e(t) = media esponenziale di z² con emivita 4 settimane fino alla settimana precedente; v0_e(t) = media di z² di tutta la storia dell'era fino alla settimana precedente; fattore f_e(t) = √max(1, v_e/v0_e). Correzione automatica della copertura (adaptive conformal inference): moltiplicatore c, all'inizio 1, ogni settimana c ← c·exp(0,5·(quota di vendite fuori dalla rosa la settimana prima − 0,20)), tra 0,8 e 3. Rosa = stima ± 1,2816·s·f_e·c. **Avviso "mercato agitato"** quando f_e ≥ 1,5. Parametri fissati qui: emivita 4, γ 0,5, limiti 0,8–3, soglia 1,5.

| # | Criterio (vendite di `sales_all` con tcgcharts del 5 novembre, fase R) | Soglia |
|---|---|---|
| V1 | copertura della rosa sulle vendite dopo il 30 ottobre | tra 75% e 85% |
| V2 | copertura della rosa su tutto il periodo | tra 75% e 85% |
| V3 | per ogni era, copertura su tutto il periodo | tra 70% e 90% |
| V4 | mercati calmi (settimane ed ere con f_e ≤ 1,1): mediana di f_e·c | non oltre 1,10 |

Solo riportato: quota di settimane ed ere con avviso, copertura della banda di oggi. Se V1–V4 passano, la rosa e l'avviso vanno sul sito (grafici e schede) e la promessa dell'80% si riferisce alla rosa; la blu resta il fair value. Script `scripts/band_test.py` sulle righe della fase R (`PHASE_R_ROWS`).

**Esito §32 (6 novembre 2026): non superata, la rosa così non si adotta.** Fase R della v1.15 su 56.191 vendite. V1 sì: copertura dopo il 30 ottobre 77.6% (oggi 68.9%). **V2 no**: 73.9% su tutto il periodo (oggi 74.5%). **V3 no**: Classica 51%, Contemporanea 81%, Di mezzo 42%, Giappone 65%, Moderna 62%, Vintage 68%. V4 sì: 0.96. Avvisi: 0% delle settimane ed ere. Diagnosi: il fattore di volatilità quasi non scatta (la media di lungo periodo comprende già i periodi agitati), e il moltiplicatore unico c segue la Contemporanea, che ha metà delle vendite; le ere con meno vendite (Classica, Di mezzo) restano scoperte tutto il tempo, non solo a ottobre. Il problema principale non è la volatilità del momento ma una banda tarata male per era.

## 33. Banda rosa tarata per era (registrato il 6 novembre 2026, dopo l'esito del §32 e prima di questa prova; D175)

**Trasparenza.** Questa variante nasce dalla diagnosi del §32, quindi dopo aver visto quei dati: per questo, oltre a V1–V4 sugli stessi dati, serve una prova sul futuro (V5) prima di considerarla confermata.

**Modifica rispetto al §32.** Tutto uguale (z, f_e, emivita 4, avviso a 1,5), ma il moltiplicatore della correzione automatica è **uno per era** (c_e, Giappone compreso), aggiornato solo con le vendite di quell'era: c_e ← c_e·exp(0,5·(quota fuori la settimana prima − 0,20)), tra 0,8 e 3.

| # | Criterio | Soglia |
|---|---|---|
| V1–V4 | come §32, sugli stessi dati | come §32 |
| V5 | V1 e V3 sulle vendite dopo il 6 novembre, appena sono almeno 2.000 | come sopra |

Se V1–V4 passano, la rosa e l'avviso vanno sul sito subito, con la nota che la prova sul futuro è in corso; se V5 non passa, si tolgono.

**Esito §33 (6 novembre 2026): non superata.** V1 sì (78.2%), V2 sì (75.1%), **V3 no** (Classica 66%, Contemporanea 78%, Di mezzo 61%, Giappone 73%, Moderna 70%, Vintage 74%), V4 sì (0.94). Moltiplicatori finali per era: Classica 2.21, Contemporanea 0.97, Di mezzo 2.93, Giappone 1.47, Moderna 1.68, Vintage 1.40; quello della Di mezzo arriva quasi al limite di 3. Lettura: la banda di partenza è troppo stretta proprio nelle ere con meno vendite, in modo stabile; una correzione a valle insegue il problema senza risolverlo. La causa sta nel motore: il rumore delle singole vendite (σ della sede) è stimato uguale per tutte le ere. Non si fanno altri ritocchi a questa famiglia di prove; il prossimo passo è un rumore delle vendite per era nel motore, da registrare come nuova versione.

## 34. v1.18: rumore delle vendite per era (registrato il 6 novembre 2026, prima del codice; D177)

**Problema (§32–§33, D176).** Le forchette coprono bene la Contemporanea (78–81%) e male le ere con meno vendite (Classica 51–66%, Di mezzo 42–61%), in modo stabile nel tempo. Il motore usa un solo rumore delle vendite (σ di eBay e delle aste, per un fattore κ unico) per tutte le carte.

**Modifica (v1.18, `era_noise` = vero).** Un fattore di rumore per ogni era del motore, κ_e, all'inizio 1. Ogni settimana, per ogni era con almeno 10 vendite credibili (probabilità di essere buone > 0,8): rapporto ρ_e = mediana(r²/var)/0,455 (come la v1.12, ma per era); κ_e ← κ_e·ρ_e^λ con λ = 1 − 0,5^(1/26) (emivita 26 settimane), tra 0,25 e 4. La varianza del rumore di ogni vendita (e della copia singola) è moltiplicata per κ·κ_e della sua era. La banda R4 usa lo stesso fattore. Parametri fissati qui: 10 vendite, emivita 26, limiti 0,25–4.

| # | Criterio (regole del §18) | Soglia |
|---|---|---|
| W1 | R1 su `sales_all` con tcgcharts del 5 novembre | 0 voci |
| W2 | E2r sullo stesso insieme | non più voci della v1.15 (3) |
| W3 | Fase R sullo stesso insieme: v1.18 meno v1.15 | estremo superiore dell'intervallo al 95% ≤ +0,2 punti |
| W4 | Copertura R4 sullo stesso insieme | tra 75% e 85% |
| W5 | Copertura R4 per era del sito (Vintage, Classica, Di mezzo, Moderna, Contemporanea, Giappone) | ognuna tra 70% e 90% |
| W6 | Mercato simulato: le 23 prove del §5 contro la v1.15 | N1–N6 |
| W7 | Prova prospettica: W1, W3, W4, W5 sulle vendite dopo il 6 novembre, appena sono almeno 2.000 | come sopra |

Se W1–W6 passano, la v1.18 si adotta e W7 diventa obbligatoria. Il mercato simulato gira sul workflow `prova-motore.yml`.

**Esito §34 (6 novembre 2026): non superata, la v1.18 non si adotta.** W1 sì (R1 0 voci su 1.058). W2 sì (E2r 1 voce, la v1.15 ne ha 3). W3 sì: v1.18 meno v1.15 −0,02 punti [−0,06; +0,01] su 56.191 vendite. **W4 no**: copertura 74,4% (dopo il 30 ottobre 69,7%). **W5 no**: Classica 58,5%, Di mezzo 47,2%, Moderna 60,0%, Giappone 62,4% (Vintage 77,1%, Contemporanea 79,7%); con la v1.15: 50,4%, 41,9%, 61,6%, 65,4%, 69,3%, 81,9%. W6 interrotta (inutile dopo W4–W5). Lettura: il rumore per era migliora la Classica, la Di mezzo e il Vintage di 6–8 punti ma non basta; le ere del motore (wotc, ex_dp, bw_xy, sm_swsh, sv) non coincidono con quelle del sito, e nelle ere scoperte gli scarti sono soprattutto da una parte (il motore in ritardo, D172), che un rumore più grande non corregge. Codice spento (`era_noise=False`).

## 35. Lo storico lungo nei prezzi, con il motore v1.15 (registrato il 6 novembre 2026, prima della prova; D188)

**Problema.** Su 289 carte, 64 voti non mostrano un valore (nessuna vendita propria nei dati dei prezzi, o stima in revisione), tra cui 22 PSA 10, e 46 PSA 10 sono "Stimato". Molte di queste carte passano di mano poche volte l'anno: nei prezzi entrano solo i 90 giorni di tcgcharts più le aste (D77, D121), mentre lo storico lungo (dal 2017, D80, D123) serve agli indici e all'ultima vendita nota. Lo storico è stato provato solo con la v1.10 (D83–D86: H3 mancato di 0,02 punti, H4 copertura 87,9%); da allora il motore è la v1.15 (forchetta tarata sulla copertura, D110, D124).

**Modifica.** Nei prezzi entrano anche le vendite dello storico tcgcharts dal 1° luglio 2022 (D85), con le stesse regole delle altre vendite tcgcharts (titolo riconosciuto dal nostro abbinamento, doppioni per id, pagamenti in attesa fuori). Motore invariato (v1.15, parametri adottati).

| # | Criterio | Soglia |
|---|---|---|
| X1 | R1 sulle vendite con lo storico | 0 voci |
| X2 | E2r sulle stesse | al massimo 3 voci (come la v1.15 oggi) |
| X3 | Fase R sulle vendite valutate in entrambe le corse (stesso id): errore medio \|log\| con lo scarto di sede, con storico meno senza | estremo superiore dell'intervallo al 95% (bootstrap per carta) ≤ +0,2 punti |
| X4 | Copertura della forchetta all'80% sulle stesse vendite | con storico ≥ senza − 1 punto, e ≤ 85% |
| X5 | Build del sito con e senza storico | meno voti senza valore e meno PSA 10 "Stimato" |
| X6 | Voti con almeno 5 vendite in 90 giorni e valore a più di 0,5 in log dalla loro mediana | non più che senza storico |
| X7 | Prova prospettica: X1, X3, X4 sulle vendite dopo il 6 novembre, appena sono almeno 2.000 | come sopra |

Se X1–X6 passano, il sito usa lo storico nei prezzi e X7 diventa obbligatoria. Script `scripts/history_test.py`, workflow `prova-storico.yml`; risultati in `results/history/summary.json`.

**Esito §35 (6 novembre 2026): non superata, lo storico lungo resta fuori dai prezzi.** X1 sì (R1 0 voci). **X2 no**: E2r 4 voci (soglia 3). X3 sì: con lo storico l'errore scende di 0,37 punti [−0,52; −0,24] su 57.267 vendite valutate in entrambe le corse (13,63% → 13,27%). X4 sì: copertura della forchetta all'80% dal 74,2% all'83,6%. **X5 no**: i voti senza valore scendono da 64 a 45, ma i PSA 10 "Stimato" salgono da 46 a 53. X6 sì (8 voci lontane dalla mediana recente, come senza storico). Risultati in `results/history/summary.json`.

## 36. Storico lungo nei prezzi con revisione sulle vendite recenti, con e senza deriva per carta (registrato il 6 novembre 2026, prima del codice; D204)

**Problema (dopo il §35, D193).** Con lo storico lungo nei prezzi i voti "in revisione" salgono da 22 a 32 e E2r ha 4 voci. Due cause diverse: (1) carte salite di 2–4 volte in poche settimane, dove la stima segue le vendite di oggi ma la regola D98 la confronta con la mediana di 13 settimane, che resta indietro; (2) carte con poche vendite, dove il cammino casuale comune a tutte le carte (`q_L` tarato su tutte) tiene il livello vicino ai prezzi vecchi.

**Modifiche.**
- **Braccio A**: storico tcgcharts dal 1° luglio 2022 nei prezzi (come il §35) e regola di revisione D98 con il riferimento recente di E2r (§23): mediana delle vendite del voto negli ultimi 30 giorni se sono almeno 5, altrimenti delle ultime 5 vendite delle 13 settimane (tutte, se sono meno di 5). Soglia invariata: più di 2 volte. Motore v1.15.
- **Braccio B**: A più la deriva propria per carta (`card_drift` = vero, D29: `q_c = q_L · κ_c`, κ dagli errori di previsione della carta, priore di 52 settimane, limiti 0,5–8; codice invariato).
- **Riferimento**: il sito di oggi, senza storico, v1.15, D98 a 13 settimane.

| # | Criterio (ogni braccio contro il riferimento) | Soglia |
|---|---|---|
| Y1 | R1 sulle vendite con lo storico | 0 voci |
| Y2 | E2r sulle stesse | al massimo 3 voci |
| Y3 | Fase R sulle vendite valutate in entrambe le corse (stesso id): errore medio \|log\| con lo scarto di sede, braccio meno riferimento | estremo superiore dell'intervallo al 95% (bootstrap per carta) ≤ +0,2 punti |
| Y4 | Copertura della forchetta all'80% sulle stesse vendite | ≥ riferimento − 1 punto, e ≤ 85% |
| Y5 | Build del sito: voti senza valore (nessuna vendita o in revisione) + PSA 10 "Stimato" | meno del riferimento |
| Y6 | Voti con almeno 5 vendite in 90 giorni e valore a più di 0,5 in log dalla loro mediana | non più del riferimento |
| Y7 | Prova prospettica: Y1–Y4 sulle vendite dopo il 6 novembre, appena sono almeno 2.000 | come sopra |

Se passano entrambi, si adotta quello con l'errore Y3 più basso; se ne passa uno, quello; se nessuno, il sito resta com'è. Il braccio adottato rende Y7 obbligatoria (il criterio Y5 è stato pensato dopo aver visto i dati del §35). Solo riportati: voti in revisione, voti senza vendite, PSA 10 "Stimato" separatamente. Script `scripts/forget_test.py`, workflow `prova-dimenticare.yml`; risultati in `results/forget/summary.json`.

**Esito (6 novembre 2026, D205).** Nessun braccio adottato. A: Y1 0 voci; Y2 **4 voci** (soglia 3) → non passa; Y3 −0,28 punti [−0,39; −0,18]; Y4 73,9% → 83,4%; Y5 111 → 83; Y6 33 → 3. B: Y1 1 voce, Y2 12 voci, Y5 130 → non passa. Y7 non si applica.

## 37. Salti di un singolo voto (registrato il 6 novembre 2026, prima di eseguirla; D206)

**Problema.** Nel braccio A del §36, 3 delle 4 voci E2r sono voti saliti di 2–3 volte in poche settimane (Snorlax Jungle 1st PSA 9, Kyogre EX Double Crisis PSA 9, Lugia Aquapolis PSA 10). Il salto per carta (§30) non basta quando sale un solo voto.

**Modifica (braccio C, `grade_jump` = vero).** Braccio A del §36 (storico nei prezzi, revisione sulle vendite recenti, motore v1.15) più: a ogni nuovo calcolo di una carta, per ogni voto, le vendite di quel voto delle ultime 4 settimane (dopo l'ultimo salto dello stesso voto) si confrontano con la previsione della stima precedente; se sono almeno 3, la mediana degli scarti in log è oltre ±0,35 e almeno il 75% ha lo stesso segno e almeno metà di quella mediana, si registra un salto del voto alla data della prima di quelle vendite, con varianza J = mediana². Le vendite **di quel voto** precedenti il salto ricevono J in più nella varianza e nella parte condivisa tra loro; le vendite degli altri voti no. Soglie di D155, non ritoccate. Il salto per carta resta spento.

**Criteri.** Y1–Y6 del §36, identici, braccio C contro lo stesso riferimento (sito di oggi). Si adotta C solo se li passa tutti; poi Y7 (prospettica, dopo almeno 2.000 vendite nuove) è obbligatoria. Il braccio A si riesegue solo come confronto e non si può adottare. Script `scripts/grade_jump_test.py`, workflow `prova-salti-voto.yml`; risultati in `results/gradejump/summary.json`.

**Esito (6 novembre 2026, D210).** Braccio C adottato come v1.20. C: Y1 0 voci; Y2 0 voci; Y3 −0,28 punti [−0,40; −0,18]; Y4 73,9% → 83,5%; Y5 111 → 82; Y6 33 → 0. A (solo confronto): come nel §36, Y2 4 voci. Y7 (prospettica) da eseguire appena ci sono almeno 2.000 vendite dopo il 6 novembre. Da D241 (9 novembre 2026, prima di Y7): se Y7 non passa la v1.20 resta e si corregge con una nuova prova registrata, senza ritorno alla v1.15.

## 38. Titoli giapponesi: sigla e nome giapponese del set, trattini e apostrofi (registrato il 7 novembre 2026, prima del codice; D214)

**Domanda.** Le tre regole nuove del riconoscitore dei titoli giapponesi (D214) fanno riconoscere più vendite della carta giusta senza attribuire vendite alla carta sbagliata?

**Modifica.** Nel riconoscitore (`slabwise/sources/auction_titles.py`, voci del catalogo giapponese): (1) il set vale anche se il titolo contiene la sigla del nostro codice (`ja:m3-086` → "m3", `ja:sv11b-169` → "sv11b", `ja:sv-p-288` → "sv-p"), come parola intera; le sigle dei set con nome (vintage) non si usano; (2) il set vale anche se il titolo contiene il nome giapponese del set della nostra scheda; (3) nel titolo un trattino prima di gx, ex, v, vmax, vstar vale uno spazio e gli apostrofi si ignorano, anche nel nome della carta. Numero e nome restano obbligatori come oggi.

**Criteri** (tutti, altrimenti non si adotta).
- **T1, nessuna carta sbagliata**: su tutti i titoli giapponesi delle vendite del sito (`sales_all` costruito come nel build) e sui titoli delle 10 carte della diagnosi, 0 titoli che passano da una carta del catalogo a un'altra; i titoli "ambigui" non aumentano.
- **T2, lettura a mano**: leggo tutti i titoli distinti riconosciuti in più sulle 10 carte della diagnosi; se anche uno solo descrive un'altra carta (altra stampa, altro numero, altra lingua, lotto), non si adotta.
- **T3, prezzi delle giapponesi già sul sito**: con le vendite riconosciute in più, il controllo del motore del sito (`real_r1.py --adopted --v120`, D213) non dà voci R1 o E2r nuove sulle giapponesi.

Le carte con l'abbinamento sbagliato (D214 a) escono dalla coda in ogni caso: non dipende da questa prova.

**Esito (7 novembre 2026, D214).** Adottate. T1: su 14.252 titoli giapponesi distinti (vendite tcgcharts e storico, più le 10 carte della diagnosi, con 105 stampe nel riconoscitore) 0 titoli passano da una carta a un'altra, ambigui 1 → 1, nessun titolo perso; 462 titoli riconosciuti in più, uno solo su una carta diversa da quella di tcgcharts (un "SV2a Japanese #168 Charmander" che tcgcharts ha messo sulla Charmander inglese: il titolo è giapponese, il nostro riconoscimento è giusto e nel build quella vendita resta fuori). T2: letti tutti i titoli distinti in più delle 10 carte (Clefairy M3, Victini SV-P, Zekrom SV11B, Mewtwo GX Shining Legends, Kyogre EX Double Crisis): tutti della carta giusta; letto anche un campione dei titoli in più delle giapponesi già sul sito, tutti giusti. T3: vendite giapponesi del sito 43.620 → 44.765; `real_r1.py --adopted --v120` R1 0 e E2r 0 sia prima sia dopo.

## 39. Titoli inglesi: trattini, tag team a tre, sottoinsiemi, promo senza prefisso (registrato il 7 novembre 2026, prima del codice; D216)

**Domanda.** Le quattro regole nuove del riconoscitore inglese (D216) fanno riconoscere più vendite della carta giusta senza attribuire vendite alla carta sbagliata?

**Modifica.** In `slabwise/sources/auction_titles.py` (titoli inglesi) e `scripts/card_requests.py` (nomi delle candidate): le regole (1)–(5) di D216 (la (5), anno d'inizio della serie per i Black Star Promo, aggiunta il 7 novembre prima di lanciare la prova), accese da `SLABWISE_EN_RULES` ("1", default; "0" per la prova). Nome, set e numero restano obbligatori come oggi; gli anni anche.

**Criteri** (tutti, altrimenti non si adotta).
- **T1, nessuna carta sbagliata**: su tutti i titoli inglesi delle vendite tcgcharts e dello storico, con nel riconoscitore tutte le carte del catalogo più le 14 candidate della diagnosi, 0 titoli che passano da una carta a un'altra; i titoli "ambigui" non aumentano.
- **T2, lettura a mano**: leggo un campione di 10 titoli distinti riconosciuti in più per ognuna delle 14 candidate (tutti, se sono meno di 10) e un campione di 40 titoli riconosciuti in più sulle carte del catalogo; se anche uno solo descrive un'altra carta (altro numero, altra stampa, altra lingua, lotto), non si adotta.
- **T3, prezzi del sito**: con le vendite riconosciute in più, `real_r1.py --adopted --v120` non dà voci R1 o E2r nuove.

**Esito (7 novembre 2026, D216).** Non adottate: passano T1 e T2, non T3. T1: su 126.763 titoli inglesi distinti (vendite tcgcharts e storico, 290 carte nel riconoscitore) 0 cambi di carta, ambigui 72 → 72, nessun titolo perso, 628 riconosciuti in più, nessuno su una carta diversa da quella di tcgcharts. T2: letti 10 titoli in più per ognuna delle 14 candidate (meno dove erano meno) e 40 sulle carte del catalogo: tutti della carta giusta (nota a parte: un titolo "PSA 8 OC", voto con riserva, conta come PSA 8 anche con il riconoscitore di oggi; da trattare per conto suo). T3: vendite del sito 416.673 → 422.338; `real_r1.py --adopted --v120` passa da R1 0 / E2r 0 a **R1 1 / E2r 1, entrambi su dc1-6** (Team Aqua's Kyogre-EX, Double Crisis): le 213 vendite in più sono sue e vere (lo storico 2022-2025, quando il PSA 9 valeva circa 200 $ contro i 10.000-20.000 $ di oggi), e con loro il motore non tiene il valore del PSA 9 vicino alle vendite recenti (169 contro 66 nelle unità del controllo). Le regole restano nel codice spente (`SLABWISE_EN_RULES=0`). Il difetto è del motore davanti a un rialzo di circa 80 volte nello storico lungo: va corretto lì, con una prova sua, prima di riprovare queste regole.

## 40. Salto di un voto sulle sue ultime vendite; scalini con code più larghe (registrato il 7 novembre 2026, prima del codice; D220)

**Domanda.** Un motore che legge il salto di un voto sulle sue ultime vendite (D) e, in più, accetta scalini tra voti più estremi (E) dà prezzi almeno buoni quanto quelli della v1.20, e regge le vendite in più delle regole dei titoli di D216?

**Riferimento.** R = il motore del sito (v1.20: storico lungo, revisione sulle vendite recenti, salto di voto su 4 settimane), sulle vendite di oggi con lo storico, regole D216 spente.

**Bracci.** D = R con il salto di voto cercato sulle ultime vendite del voto (fino a 5, tra le ultime 13 settimane, almeno 3, tutte dopo l'ultimo salto di quel voto; soglie D155: |mediana| > 0,35, accordo 75%). E = D con il prior Student-t sugli scalini a 2 gradi di libertà invece di 4.

**Criteri per braccio** (tutti):
- Y1: R1 = 0.
- Y2: E2r ≤ 3 e non più di R.
- Y3: differenza dell'errore medio |log| sulle vendite valutate in entrambi, estremo alto dell'intervallo al 95% (bootstrap per carta) ≤ +0,2 punti.
- Y4: copertura della banda all'80% ≥ quella di R meno 1 punto, e ≤ 85%.
- Y5: voti nascosti sul sito (senza vendite proprie, in revisione, PSA 10 "Stimato") non più di R.
- Y6: voti con ≥ 5 vendite in 90 giorni e |log valore − log mediana| > 0,5 non più di R.

**Adozione.** Tra i bracci che passano tutto, quello con l'errore Y3 più basso, come v1.21. Prova a valle: con la v1.21 si rifà il T3 del §39 (vendite con `SLABWISE_EN_RULES=1`): **Y8**, R1 = 0 e nessuna voce E2r in più rispetto alla v1.21 senza le regole; se passa, D216 si adotta. Se nessun braccio passa, resta la v1.20 e D216 resta spento. Il controllo a venire Y7 (§37, dal 14 novembre) vale anche per la v1.21.

**Esito §40 (7 novembre 2026, D229): nessun braccio adottato, resta la v1.20 e D216 resta spento.** R: R1 0, E2r 2 voci (col1-4 PSA 10, dp3-15 PSA 7), Y5 109. **D**: Y1 sì; **Y2 no** (E2r 4 voci, in più ecard3-149 PSA 9 e ex7-105 PSA 9); Y3 sì (−0,03 punti [−0,04; −0,02]); **Y4 no** (copertura 87,7%, sopra il tetto dell'85%; R 87,6%); **Y5 no** (110 contro 109); **Y6 no** (4 voci lontani contro 2). **E**: Y1 sì; **Y2 no** (stesse 4 voci); Y3 sì (−0,02 punti [−0,04; −0,01]); **Y4 no** (87,7%); Y5 sì (108); **Y6 no** (4 contro 2). Y8 non eseguito (nessun braccio adottato). Solo riportato: la copertura all'80% della v1.20 sulle vendite di oggi è già 87,6%, sopra il tetto di Y4; la banda del motore risulta larga, da guardare con una prova registrata a parte.

## 41. Titoli delle promo giapponesi e carte solo giapponesi (registrato il 7 novembre 2026, prima del codice; D231)

**Domanda.** La regola nuova sui numeri delle promo giapponesi ("207/XY-P") e sui nomi dei set promo cambia il riconoscimento delle carte già nel catalogo?

**Dati.** Tutti i titoli delle vendite tcgcharts che abbiamo (vendite recenti e storico lungo), con il catalogo giapponese di oggi.

**Criteri** (tutti):
- U1: nessun titolo che oggi va a una carta del catalogo cambia carta con la regola nuova.
- U2: nessun titolo che oggi va a una carta del catalogo diventa "ambiguo" o non riconosciuto.
- U3: i titoli in più riconosciuti per le carte del catalogo sono letti a mano su un campione di 20 (o tutti, se meno): nessuno di un'altra carta.

**Adozione.** Se U1–U3 passano, la regola si accende e le carte solo giapponesi entrano in coda; ognuna passa poi i controlli di sempre (D97: vendite, titoli ≥ 60%, motore R1/E2r sul lotto, D213). Se una cade, la regola resta spenta e le carte solo giapponesi entrano in coda solo con i titoli "#numero" di oggi.

**Esito §41 (7 novembre 2026): superato, la regola si accende.** 24.404 titoli giapponesi (vendite recenti e storico lungo). U1 sì: 0 titoli cambiano carta. U2 sì: 0 titoli persi o ambigui. U3 sì: 42 titoli in più riconosciuti per le carte del catalogo, tutti di Victini 288/SV-P ("288/SV-P" senza "#"); letti a mano i 20 del campione, tutti di quella carta. Risultati in `results/d231/titles.json`.

## 42. "Box" nei titoli giapponesi (registrato l'8 novembre 2026, prima del codice; D232)

**Domanda.** Se "box" non scarta più il titolo quando è "Special/Stamp/Gift/Premium/Collection/Golden Box", cambia la lettura delle carte già nel catalogo?

**Dati e criteri.** Gli stessi del §41 (tutti i titoli giapponesi delle vendite tcgcharts, catalogo di oggi). V1: nessun titolo che oggi va a una carta del catalogo cambia carta; V2: nessuno diventa ambiguo o non riconosciuto; V3: i titoli in più riconosciuti per le carte del catalogo, campione di 20 letto a mano, sono tutti della carta giusta e nessuno è un prodotto sigillato.

**Adozione.** Se V1–V3 passano la regola si accende; altrimenti resta spenta.

**Esito §42 (8 novembre 2026): superato, la regola si accende.** 26.604 titoli giapponesi. V1 sì (0 titoli cambiano carta), V2 sì (0 persi o ambigui), V3 sì: nessun titolo in più per le carte del catalogo (i titoli "Stamp Box", "Special Box", "Gift Box" riguardano promo non ancora nel catalogo). Prova a mano su titoli reali: "S-P PROMO POKEMON STAMP BOX #227 … PSA 10" va a Pikachu 227/S-P, "Special Box Promo Poncho Wearing Pikachu #207 PSA 10" a Poncho 207, "Stamp Box sealed" e "227/S-P Japanese box PSA 10" restano scartati. Risultati in `results/d232/titles.json`.

## 43. Promo giapponesi dal numero di promo (registrato l'8 novembre 2026, prima del codice; D233)

**Domanda.** Se un titolo giapponese con il numero di promo esatto ("207/XY-P") va alla carta anche senza il nome inglese, cambia la lettura delle carte già nel catalogo, e i titoli in più sono della carta giusta?

**Dati e criteri.** Gli stessi del §41 e §42 (tutti i titoli giapponesi delle vendite tcgcharts e dello storico lungo, catalogo di oggi). W1: nessun titolo che oggi va a una carta del catalogo cambia carta; W2: nessuno diventa ambiguo o non riconosciuto; W3: i titoli in più riconosciuti per le carte del catalogo, campione di 20 letto a mano, sono tutti della carta giusta e nessuno è un prodotto sigillato o un'altra carta. In più, per le 4 Poncho rimaste fuori (207, 208, 230, 231) si rimisura l'ammissione con le regole D232 invariate.

**Adozione.** Se W1–W3 passano la regola si accende; altrimenti resta spenta.

**Esito §43 (8 novembre 2026): superato, la regola si accende.** 26.604 titoli giapponesi. W1 sì (0 titoli cambiano carta), W2 sì (0 persi o ambigui), W3 sì: 16 titoli in più, tutti letti a mano e tutti della carta giusta (Rayquaza 232/XY-P "レックウザ", le Eeveelution 063–070/SV-P "シャワーズ", "サンダース", "エーフィ", "リーフィア", "グレイシア", "ニンフィア"). Rimisura delle Poncho con D232 invariato: nessun cambiamento (207: 17 su 30; 208: 20 su 30; 230: 38 su 64; 231: 42 su 73), perché nei loro titoli "ピカチュウ" è il nome di un'altra carta del catalogo (Pikachu) e la regola li tratta come ambigui. Risultati in `results/d233/titles.json` e `results/d233/poncho.json`.

## 44. Il nome di un'altra carta contenuto nel nome della carta (registrato l'8 novembre 2026, prima del codice; D234)

**Domanda.** Nella regola §43, se il nome di un'altra carta trovato nel titolo non conta come conflitto quando è già contenuto nel nome della carta del numero di promo ("Pikachu" in "Poncho-wearing Pikachu"), cambia la lettura delle carte del catalogo, e i titoli in più sono della carta giusta?

**Dati e criteri.** Gli stessi del §43 (W1–W3), confrontando la regola §44 con la §43 accesa. Si rimisurano le 4 Poncho con D232 invariato; il risultato si riporta qualunque sia.

**Adozione.** Se W1–W3 passano la variante si accende; altrimenti resta la §43.

**Esito §44 (8 novembre 2026): superato, la variante si accende.** 26.604 titoli giapponesi. W1 sì (0 titoli cambiano carta), W2 sì (0 persi o ambigui), W3 sì: 37 titoli in più per le carte del catalogo; letti a mano i 20 del campione, tutti della carta giusta (per esempio "ピカチュウ #272/S-P" → Pikachu 272/S-P, "リザードン #143/S-P" → Charizard 143/S-P, "桜アフロのピカチュウ #211/SM-P" → Pikachu afro 211/SM-P, "イーブイ #287/SM-P" → Eevee). Rimisura delle Poncho con D232 invariato: 207 27 su 30, 208 29 su 30, 230 59 su 64, 231 64 su 73: tutte pronte. Risultati in `results/d234/titles.json` e `results/d234/poncho.json`.

## 45. Quattro correzioni dei titoli inglesi (registrato l'8 novembre 2026, prima del codice; D235)

**Domanda.** Con le correzioni D235 ("Mega Evolutions", promo delle Elite Trainer Box, anni delle promo per serie, anno fra parentesi), cambia la lettura delle carte del catalogo, e i titoli in più sono della carta giusta?

**Dati e criteri.** Tutti i titoli inglesi delle vendite tcgcharts (vendite recenti e storico lungo), catalogo di oggi. X1: nessun titolo che oggi va a una carta del catalogo cambia carta; X2: nessuno diventa ambiguo o non riconosciuto; X3: dei titoli in più riconosciuti per le carte del catalogo, campione di 20 letto a mano, tutti della carta giusta, nessun prodotto sigillato, nessuna versione in metallo, nessuna ristampa XY Evolutions. Si riporta anche quanti titoli in più per ciascuna delle quattro correzioni.

**Adozione.** Se X1–X3 passano le correzioni si accendono; altrimenti restano spente.

**Esito §45 (8 novembre 2026): superato, le correzioni si accendono.** 200.629 titoli inglesi. X1 sì (0 titoli cambiano carta), X2 sì (0 persi o ambigui), X3 sì: 1.709 titoli in più (anni delle promo 931, anno fra parentesi 370, Elite Trainer Box 240, Mega Evolutions 168); letti a mano i 20 del campione, tutti della carta giusta (Pikachu SM162 e Mimikyu SM163 "Team Up", Charizard SM226 "Collector Chest", Charizard V SWSH050 "Champion's Path Elite Trainer Box", Latias ex 239 "Surging Sparks (2024)"), nessun sigillato, metallo o ristampa Evolutions. Risultati in `results/d235/titles.json`.

## 46. Numero senza # né / nei titoli inglesi (registrato l'8 novembre 2026, prima del codice; D236)

**Domanda.** Se in un titolo inglese senza numeri con # o / vale anche il numero scritto da solo (esclusi voto, anni, popolazione), cambia la lettura delle carte del catalogo, e i titoli in più sono della carta giusta?

**Dati e criteri.** Gli stessi del §45, con le correzioni D235 accese in tutti e due i casi. Y1: nessun titolo che oggi va a una carta del catalogo cambia carta; Y2: nessuno diventa ambiguo o non riconosciuto; Y3: dei titoli in più, campione di 40 letto a mano (il doppio del solito, perché la regola è più larga), tutti della carta giusta; se anche uno è di un'altra carta o di un'altra stampa, la regola non passa.

**Adozione.** Se Y1–Y3 passano la regola si accende; altrimenti resta spenta.

**Esito §46 (8 novembre 2026): superato, la regola si accende.** 200.629 titoli inglesi. Y1 sì (0 titoli cambiano carta), Y2 sì (0 persi o ambigui), Y3 sì: 12.443 titoli in più; letti a mano i 40 del campione, tutti della carta giusta (per esempio "Team Rocket 4 Dark Charizard Holo", "Evolving Skies 215 Umbreon VMAX", "Pikachu with Grey Felt Hat SVP 085", "Phantasmal Flames 125 Mega Charizard X ex", "Crown Zenith Radiant Charizard 020"). Risultati in `results/d236/titles.json`.

## 47. Nomi giapponesi delle specie nei titoli (registrato l'8 novembre 2026, prima del codice; D237)

**Domanda.** Se nei titoli giapponesi i nomi delle specie in katakana si leggono anche in inglese (dati PokeAPI), cambia la lettura delle carte del catalogo, e i titoli in più sono della carta giusta?

**Dati e criteri.** Gli stessi del §43 (tutti i titoli giapponesi delle vendite tcgcharts e dello storico lungo, catalogo di oggi, regole D233–D234 accese in tutti e due i casi). Z1: nessun titolo che oggi va a una carta del catalogo cambia carta; Z2: nessuno diventa ambiguo o non riconosciuto; Z3: dei titoli in più, campione di 40 letto a mano, tutti della carta giusta; se anche uno è di un'altra carta o di un'altra stampa, la regola non passa.

**Adozione.** Se Z1–Z3 passano la regola si accende; altrimenti resta spenta.

**Esito §47 (8 novembre 2026): non superato, la regola resta spenta.** 27.290 titoli giapponesi. Z1 sì (0 titoli cambiano carta), Z2 no: 44 titoli oggi letti non si leggono più, perché lo spazio aggiunto attorno al nome spezza i nomi giapponesi scritti a mano nel catalogo ("ひかるルギア" diventa "ひかる ルギア lugia"; così anche "カツラのウインディ", "ひかるレックウザ"); Z3 non serve: solo 6 titoli in più (Umbreon 067/SV-P "ブラッキー", Jolteon Jungle "サンダース"). Risultati in `results/d237/titles.json`.

## 48. Titoli giapponesi riconosciuti dalla sigla del set (registrato l'8 novembre 2026, prima del codice; D238 a)

**Domanda.** Se un titolo senza "Japanese" che contiene la sigla di un set giapponese (D238 a) si legge come giapponese, cambia la lettura delle carte del catalogo, inglesi e giapponesi, e i titoli in più sono della carta giusta?

**Dati e criteri.** Tutti i titoli delle vendite tcgcharts e dello storico lungo, inglesi e giapponesi, catalogo di oggi, regole accese fino alla D236. A1: nessun titolo che oggi va a una carta del catalogo cambia carta; A2: nessuno diventa ambiguo o non riconosciuto; A3: dei titoli in più, campione di 40 letto a mano, tutti della carta giusta.

**Adozione.** Se A1–A3 passano la regola si accende; altrimenti resta spenta.

## 49. Numero senza # né / nei titoli giapponesi (registrato l'8 novembre 2026, prima del codice; D238 b)

**Domanda.** Come il §46, per i titoli giapponesi (D238 b), con la regola §48 accesa in tutti e due i casi se ha passato la sua prova.

**Dati e criteri.** Tutti i titoli giapponesi (con la definizione in uso dopo il §48). B1: nessun titolo che oggi va a una carta del catalogo cambia carta; B2: nessuno diventa ambiguo o non riconosciuto; B3: dei titoli in più, campione di 40 letto a mano, tutti della carta giusta.

**Adozione.** Se B1–B3 passano la regola si accende; altrimenti resta spenta.

**Esito §48 (8 novembre 2026): non superato, la regola resta spenta.** 227.919 titoli. A1 no: 48 titoli di carte inglesi del 151 passano alla stampa giapponese (Bulbasaur 166/165, Charmander 168/165, Wartortle 171/165: il 151 inglese e il giapponese SV2a hanno gli stessi numeri e molti venditori di carte inglesi scrivono "SV2a"); A2 no: 18 titoli inglesi persi; 639 titoli in più. Risultati in `results/d238/setcode.json`.

## 48b. Sigla del set giapponese, solo quando il titolo non è di una carta inglese (registrato l'8 novembre 2026, prima del codice; D238 a, variante)

**Domanda.** Come il §48, ma la sigla rende giapponese un titolo solo se il titolo non va a nessuna carta inglese del catalogo, e la sigla SV2a non conta (stessi numeri del 151 inglese).

**Dati e criteri.** Gli stessi del §48 (A1–A3, campione di 40).

**Adozione.** Se A1–A3 passano la variante si accende; altrimenti la regola resta spenta.

**Esito §48b (8 novembre 2026): superato, la variante si accende.** 227.919 titoli. A1 sì (0 titoli cambiano carta), A2 sì (0 persi o ambigui), A3 sì: 569 titoli in più; letti a mano i 40 del campione, tutti della carta giusta e di set solo giapponesi o con numeri diversi dall'inglese (Crimson Haze SV5a, Raging Surf SV3a, Shiny Treasure SV4a, Dream League SM11b, Triplet Beat SV1a, Wild Force SV5K, Inferno X M2, Mega Dream M2a, Nihil Zero M3). Risultati in `results/d238/setcode_b.json`. Visto durante la lettura, fuori dal campione: un titolo coreano con "Kor." o "(KR)", scartato dalla via inglese, per la sigla arriva alla via giapponese, che quelle sigle non le scarta (D239).

## 50. Sigle coreane nei titoli giapponesi (registrato l'8 novembre 2026, prima del codice; D239)

**Domanda.** Se la via giapponese scarta anche le sigle coreane brevi ("Kor", "Kor.", "KR", "(KR)"), quanti titoli oggi letti si perdono, e sono davvero coreani?

**Dati e criteri.** Tutti i titoli letti dalla via giapponese, con le regole accese fino al §48b. K1: nessun titolo cambia carta; K2: tutti i titoli che si perdono, letti a mano (o un campione di 40 se sono di più), sono di carte coreane.

**Adozione.** Se K1 e K2 passano la regola si accende; altrimenti resta spenta.

**Esito §50 (8 novembre 2026): superato, la regola si accende.** 227.919 titoli. K1 sì (0 titoli cambiano carta); K2 sì: si perdono 4 titoli, letti a mano, tutti coreani ("SV5A-Crimson Haze … Greninja ex PSA 9 Kor.", "Mega Dream - M2A KR #199/193 Psyduck", "Inferno X- M2 KR Mega Charizard X ex #094/080"). Risultati in `results/d238/kor.json`.

**Esito §49 (8 novembre 2026): superato, la regola si accende.** 27.290 titoli giapponesi (definizione del §48b). B1 sì (0 titoli cambiano carta), B2 sì (0 persi o ambigui), B3 sì: 1.003 titoli in più; letti a mano i 40 del campione, tutti della carta giusta (per esempio "Japanese Basic 6 Charizard-Holo", "Jungle Snorlax 143", "Gym 2 59 Blaine's Arcanine", "SV4a Charizard ex 349 SAR", "M2a-Mega Dream 199 Psyduck", "Fusion Arts 106 Mew V"; nei set vintage il numero è quello del Pokédex, come nel catalogo). Risultati in `results/d238/bare.json`.

## 51. Indice generale a quote per era (registrato il 9 novembre 2026, prima del codice; D245)

**Domanda.** Un generale con 12 voci per era (cinque ere inglesi, 60 voci) rappresenta il mercato inglese meglio del generale di oggi (le 60 voci più vendute), senza diventare instabile?

**Dati.** Lo stesso passaggio del sito (vendite con lo storico lungo, motore v1.20, `SLABWISE_INDEX_SELF=1`), sulle settimane dalla base comune degli indici (D121) a oggi. Si calcolano: il generale attuale (A), il generale a quote (Q) e la media semplice dei cinque indici d'era pubblicati (M, ogni era pesa uguale). Q usa le stesse regole di idoneità del paniere (D136, D169: almeno 6 vendite genuine nelle 13 settimane, ribilanciamento ogni 13 settimane, una voce per combinazione carta-voto); se un'era ha meno di 12 voci idonee, i posti liberi vanno alle altre ere in proporzione alle loro voci idonee.

**Criteri.**
- **Q1 rappresentanza**: a ogni ribilanciamento ogni era con almeno 12 voci idonee ha **almeno** 12 voci in Q. *(Correzione del 9 novembre 2026, prima della prova sui dati veri: la prima scrittura diceva "12 voci", in contraddizione con la regola dei posti liberi registrata nello stesso paragrafo, che ne dà di più alle ere grandi quando un'era piccola non arriva a 12; trovata provando il codice su un campione di 120 carte, non sui dati della prova.)*
- **Q2 vicinanza al mercato delle ere**: la mediana, su tutte le settimane, di |rendimento a 13 settimane di Q − quello di M| è minore della stessa misura per A.
- **Q3 stabilità**: la volatilità di Q (variazioni settimanali in log, ultime 26 settimane, ×√52) non supera 1,5 volte quella di A.
- **Q4 niente salti**: nessuna variazione settimanale di Q oltre ±15%.

**Adozione.** Se Q1–Q4 passano, il generale del sito diventa Q (stesso nome, stessa base comune; la pagina dell'indice spiega le quote). Altrimenti resta A e il risultato si riporta.

**Esito §51 (9 novembre 2026): non superato, il generale resta com'è.** 150 settimane confrontate (run 42603210249, `results/ix_quota/summary.json`). Q1 sì (all'ultimo ribilanciamento 12 voci per ognuna delle cinque ere, idonee da 149 a 312). Q2 sì: scarto mediano dal mercato delle ere 1,0% per Q contro 11,8% per A. **Q3 no**: volatilità di Q 22,4% contro 8,6% di A (soglia 1,5×, cioè 12,9%). Q4 sì (variazione settimanale massima 8,7%). Solo riportato: nelle ultime 13 settimane A −17,8%, Q +19,0%, media delle ere +19,4%; oggi il paniere di A ha 53 voci Contemporanee e 7 Moderne.

## 52. Generale a quote per era, prova prospettica con la volatilità misurata contro le ere (registrato il 9 novembre 2026, prima dei dati che giudica; D249)

**Perché.** Il §51 non è passato per la volatilità (Q3): il confronto era con il generale di oggi, che è quasi tutto Contemporanea e quindi poco volatile per costruzione. Oscar: "parliamo di carte, è normale avere volatilità alta… proporzionerei l'indice rispetto a questa cosa". Una soglia nuova scelta dopo aver visto il §51 non può decidere sui dati già visti: questa prova giudica solo le settimane che arrivano **dopo il 9 novembre 2026**.

**Bracci.** A: generale di oggi (D169). **Q**: 12 voci per era, pesi uguali (il §51). **R**: 12 voci per era, ma ogni era pesa in proporzione inversa alla volatilità del suo indice nelle 52 settimane prima del ribilanciamento (pesi delle ere che sommano a 1, dentro l'era pesi uguali); con meno di 26 settimane d'indice l'era pesa come in Q. M: la media semplice dei cinque indici d'era, come nel §51.

**Dati.** Lo stesso passaggio del sito; si guardano solo le settimane dal 13 novembre 2026 al 29 gennaio 2027 (12 settimane). Si giudica il 1° febbraio 2027.

**Criteri** (per Q e per R):
- **P1 rappresentanza**: a ogni ribilanciamento ogni era con almeno 12 voci idonee ha almeno 12 voci.
- **P2 vicinanza al mercato delle ere**: mediana di |rendimento a 4 settimane del braccio − quello di M| minore della stessa misura per A.
- **P3 volatilità proporzionata**: volatilità del braccio (variazioni settimanali in log, ×√52) non oltre 1,5 volte quella di M nelle stesse settimane.
- **P4 niente salti**: nessuna variazione settimanale oltre ±15%.

**Adozione.** Tra i bracci che passano P1–P4, quello con P2 più basso diventa il generale del sito. Se nessuno passa, resta A. *Aggiornamento (9 novembre 2026, D250, prima dei dati che giudica): Q è adottato subito per decisione di Oscar; il §52 diventa la sua verifica obbligatoria. Se Q passa resta; se R passa con P2 più basso, si passa a R; se nessuno passa, si corregge con una nuova prova, non si torna ad A.*

## 53. Indice Giappone a quote per era (registrato il 9 novembre 2026, prima del codice; D251)

**Domanda.** Un indice Giappone con posti uguali per era (20 voci divise tra le ere giapponesi presenti nel paniere idoneo) racconta il mercato giapponese meglio dell'indice di oggi (le 20 voci giapponesi più vendute), senza essere più agitato del mercato delle ere giapponesi?

**Dati.** Lo stesso passaggio del sito (vendite con lo storico lungo, motore v1.20). Si calcolano: l'indice Giappone di oggi (A), quello a quote (Q, `EraIndex(quota=…)` con le ere di `series_of` per le carte giapponesi, promo comprese come oggi) e M, la media semplice degli indici delle ere giapponesi (stesse regole, 20 voci per era). Settimane dalla base comune degli indici (D121).

**Criteri.**
- **J1 rappresentanza**: a ogni ribilanciamento ogni era giapponese con almeno 5 voci idonee ne ha almeno 5 in Q.
- **J2 vicinanza al mercato delle ere**: mediana di |rendimento a 13 settimane di Q − quello di M| minore della stessa misura per A.
- **J3 volatilità proporzionata**: volatilità di Q (variazioni settimanali in log, ultime 26 settimane, ×√52) non oltre 1,5 volte quella di M nelle stesse settimane.
- **J4 niente salti**: nessuna variazione settimanale di Q oltre ±15%.

**Adozione.** Se J1–J4 passano, l'indice Giappone del sito diventa Q. Altrimenti resta A e il risultato si riporta.

**Esito §53 (9 novembre 2026): superato, l'indice Giappone diventa a quote per era.** 150 settimane (run 42626137100, `results/ix_ja/summary.json`). J1 sì (all'ultimo ribilanciamento 5 voci per Contemporanea, Moderna, Vintage e Di mezzo, idonee 141, 112, 57 e 13). J2 sì: scarto mediano dal mercato delle ere giapponesi 2,3% per Q contro 9,3% per A. J3 sì: volatilità 13,4% contro 12,7% della media delle ere (soglia 19,1%; A 17,1%). J4 sì (settimana peggiore 10,1%). Solo riportato: ultime 13 settimane A −24,7%, Q −21,8%, media delle ere −13,2%; il paniere di A era tutto Contemporanea.

## 54. La Contemporanea in due ere (registrato il 9 novembre 2026, prima del codice; D253)

**Domanda.** Spada e Scudo (set swsh, cel) e Scarlatto e Violetto con Mega Evoluzione (set sv, me) si muovono come un mercato solo o come due? Se sono due, conviene dividerli, purché ciascuno abbia abbastanza voci e non diventi rumore.

**Dati.** Lo stesso passaggio del sito (motore v1.20, storico lungo). Si calcolano l'indice Contemporanea di oggi (C) e due indici con le stesse regole (20 voci, D169): SS (swsh, cel) e SV (sv, me); promo fuori come oggi. Settimane dalla base comune degli indici (D121).

**Criteri.**
- **E1 mercati diversi**: la correlazione tra le variazioni settimanali (in log) di SS e SV è sotto 0,8.
- **E2 abbastanza voci**: all'ultimo ribilanciamento SS e SV hanno ciascuno almeno 20 voci idonee.
- **E3 niente rumore in più**: la volatilità di SS e quella di SV (ultime 26 settimane, ×√52) non superano 1,5 volte quella di C.
- **E4 niente salti**: nessuna variazione settimanale di SS o SV oltre ±15%.

**Adozione.** Se E1–E4 passano: sei ere sul sito (Vintage, Classica, Di mezzo, Moderna, Spada e Scudo, Scarlatto e Violetto), con indici, riquadri e schede; lo SlabDex con 10 voci per era (stessa regola di D250). Le stampe giapponesi seguono la stessa divisione (s* → Spada e Scudo, sv*/m* → Scarlatto e Violetto). Altrimenti la Contemporanea resta una e il risultato si riporta.

**Esito §54 (9 novembre 2026): non superato, la Contemporanea resta una.** 150 settimane (run 42645338705, `results/era_split/summary.json`). E1 sì: correlazione tra Spada e Scudo e Scarlatto e Violetto 0,68. E2 sì: 91 e 221 voci idonee. **E3 no**: volatilità di Scarlatto e Violetto 15,2% contro la soglia di 14,3% (1,5 × 9,55% della Contemporanea); Spada e Scudo 7,8%. E4 sì (settimana peggiore 10,2%). Solo riportato: ultime 13 settimane Contemporanea −28,3%, Spada e Scudo −14,2%, Scarlatto e Violetto −40,0%.

## 55. Verifica prospettica delle sei ere (registrata il 9 novembre 2026, prima dei dati che giudica; D255)

Le due ere nuove sono in uso da subito (D255, eccezione di P12). Si giudicano solo le settimane dal 13 novembre 2026 al 29 gennaio 2027, il 1° febbraio 2027.
- **V1 mercati diversi**: correlazione tra le variazioni settimanali (in log) di Spada e Scudo e di Scarlatto e Violetto sotto 0,8.
- **V2 abbastanza voci**: a ogni ribilanciamento ciascuna delle due ha almeno 20 voci idonee.
- **V3 niente salti**: nessuna variazione settimanale di una delle due oltre ±15%.
- **V4 volatilità**: la volatilità di Spada e Scudo non oltre 1,5 volte quella della media delle sei ere; per Scarlatto e Violetto, ancora in stampa, solo riportata.

Se V1–V3 passano, restano sei ere. Se non passano, si corregge con una nuova prova (per esempio confini diversi), senza tornare automaticamente a cinque.

## 56. Assegnazione delle fonti salvo contraddizioni (registrato il 10 novembre 2026, prima del codice; D258)

**Domanda.** Se teniamo la carta che i fornitori di tcgcharts assegnano a una vendita, scartandola solo quando il titolo la contraddice, recuperiamo le vendite giuste senza far entrare vendite sbagliate?

**Dati.** Le vendite PSA dell'ultimo anno nello storico privato (`history.json.gz`, non escluse da tcgcharts). Regola di oggi (O): la vendita entra se `match_title` dà la carta assegnata. Regola nuova (N): `accept_assigned(titolo, carta)`.

**Criteri.**
- **A1 errori**: su 100 titoli scelti a caso tra quelli che N tiene e O no, letti a mano, al massimo 5 sono un'altra carta, un'altra stampa (1st Edition, Shadowless, altra lingua) o un lotto.
- **A2 niente perso**: nessuna vendita tenuta da O viene scartata da N.
- **A3 copertura**: N tiene almeno il 95% delle vendite PSA dell'ultimo anno.

**Adozione.** Se A1–A3 passano, N vale per il motore (`tcgcharts_rows`) e per la misura d'ingresso (D232), e la quota di titoli coerenti della misura d'ingresso si calcola con N.

**Esito §56 (10 novembre 2026): superato, si adotta.** 434.399 vendite PSA dell'ultimo anno (`results/d258/`). A3 sì: la regola nuova tiene il 96,9% (oggi 86,5%); 45.540 vendite in più. *Correzione dello stesso giorno, prima dell'adozione: un segno di giapponese ("JPN") su una carta inglese ora scarta la vendita (trovato dal test automatico: "Pokémon GO JPN Radiant Charizard" assegnata alla carta inglese); regola più severa, 90 vendite in meno, A2 e A3 ricalcolati e ancora superati; la lettura A1 resta quella del primo campione, da cui questa correzione può solo togliere.* A2 sì: nessuna vendita tenuta oggi viene scartata. A1 sì: dei 100 titoli letti a mano tra quelli in più, 4 sono sbagliati (n. 1 un set di due carte giapponesi; n. 47 la promo SWSH050 assegnata a Champion's Path 74; n. 76 tre carte Pokémon GO insieme assegnate a Southern Islands 4; n. 88 "Secret Charizard V" assegnata alla Charizard VMAX 74), limite 5. Scartate dalla regola nuova: 5.572 escluse, 2.972 giapponesi senza segno di giapponese, 2.927 con un numero diverso, 1.285 di un'altra carta, 251 ambigue, 210 di un'altra stampa.

## 57. Il motore con le ere del sito (registrato l'11 novembre 2026, prima del codice; D260)

**Domanda.** Se il fattore comune di mercato lavora sulle sei ere del sito invece che su tre gruppi, il valore segue più da vicino le ere che si muovono in fretta, senza peggiorare il resto?

**Bracci.** R: motore del sito (v1.20, tre gruppi). **F**: gruppi = Vintage, Classica, Di mezzo, Moderna, Spada e Scudo, Scarlatto e Violetto (`series_of`; le giapponesi con la loro era, come oggi con i tre gruppi). **G**: come F, ma le giapponesi in due gruppi propri (moderne: sv*, m*, s*, sm*, xy*, bw*; vecchie: le altre). Tutto il resto identico; i parametri si ricalibrano con le stesse regole.

**Dati.** Le vendite con lo storico lungo (come §37, §40); fase R come sempre.

**Criteri** (per F e per G, contro R):
- **Y1** R1 = 0. **Y2** E2r al massimo 3 voci e non più di R. **Y3** errore di fase R: limite superiore dell'intervallo al 95% della differenza ≤ +0,2 punti. **Y4** copertura non sotto quella di R meno 1 punto e non sopra il maggiore tra 85% e la copertura di R. **Y5**, **Y6** come nel §40 (voci nascoste; voci lontane dalla mediana a 90 giorni).
- **Y7 ritardo** (nuovo): sulle vendite di fase R comuni ai due bracci, nelle ultime 26 settimane, per ogni casella (era del sito, settimana) con almeno 30 vendite si prende la mediana di (prezzo − previsione) in log; L = media dei valori assoluti di queste mediane. Si chiede L del braccio ≤ 0,8 × L di R, e che nelle due ere dove R ha L più alto la L dell'era scenda.

**Adozione.** Tra i bracci che passano Y1–Y7, quello con L più basso diventa il motore del sito (v1.22). Se nessuno passa, resta la v1.20 e si riporta tutto.

**Esito (11 novembre 2026, D264): non adottato.** F e G passano Y3, Y5, Y6; non passano Y1 (1 contro 0 richiesto; R ne ha 2), Y2 (E2r 30 e 18; R 30), Y4 (copertura 85,76% e 85,74%, tetto 85,73%) e Y7 (L 0,0328 e 0,0327 contro 0,8 × 0,0367 = 0,0294; nelle due ere peggiori L scende). Resta la v1.20.

## 58. Panieri più grandi: 30 o 40 voci per era (registrato l'11 novembre 2026, prima del codice; D263)

**Domanda (Oscar).** "Dovremmo capire come omogeneizzare questi dati per tutte le ere, la disparità di mole di vendita per i vari indici mi spaventa." L'11 novembre il margine al 95% del rendimento a 4 settimane (1,96 × dev. standard delle variazioni delle voci ÷ √20) va da ±3,1 punti (Spada e Scudo) a ±14,1 (Di mezzo); voci idonee per era tra 166 (Spada e Scudo) e 516 (Giappone).

**Varianti.** Stesso algoritmo e stesse misure del §31 (peso uguale, concatenato, ribilanciamento ogni 13 settimane, almeno 6 vendite credibili, tutto lo storico, motore del sito dopo l'esito del §57); per gli indici d'era e Giappone K = 20 (oggi), 30, 40; generale invariato (60, a quote).

**Misure.** Q1, Q2, Q3 come nel §31 (coppie di rivendite dello stesso cert). In più **Q4 margine**: per ogni era e ogni ribilanciamento delle ultime 52 settimane, 1,96 × dev. standard delle variazioni in log a 4 settimane delle voci del paniere ÷ √voci; si prende il massimo sulle ere della mediana nel tempo.

| # | Criterio, per una variante contro K = 20 | Soglia |
|---|---|---|
| Q1 | riduzione dell'errore | non più bassa di quella di K = 20 meno 0,01 |
| Q2 | pendenza | tra 0,70 e 1,30, estremo inferiore dell'intervallo oltre 0,30 |
| Q3 | rumore | non oltre quello di K = 20 più 10% |
| Q4 | margine massimo sulle ere | più basso di quello di K = 20 |

Si adotta la K più grande che passa Q1–Q4 (prima 40, poi 30). Se nessuna passa, resta 20. Solo riportato: carte diverse per paniere e vendite a 90 giorni dietro ogni paniere, per era. Script `scripts/index_k_test.py` con `VARIANTS=K20:20:60,K30:30:60,K40:40:60`, workflow `prova-indici.yml`; risultati in `results/index_k58/summary.json`.

**Esito (11 novembre 2026, D268): K = 40 adottata.** Corsa 43026175927. Q1 riduzione dell'errore 0,312 (K20), 0,342 (K30), 0,373 (K40); Q2 pendenza 1,02 / 1,08 / 1,15, estremi inferiori 0,87 / 0,91 / 0,95; Q3 rumore 0,0176 / 0,0173 / 0,0174; Q4 margine massimo sulle ere 7,6 / 5,6 / 4,4 punti (Scarlatto e Violetto il più alto in tutte; Di mezzo 5,4 / 4,1 / 3,5). K30 e K40 passano tutto; per regola si adotta la più grande. Carte diverse per paniere con K40: Classica 29, Di mezzo 22, Vintage 34, Moderna 39, Spada e Scudo 40, Scarlatto e Violetto 40, Giappone 36.

## 59. Indici fatti con un voto solo: PSA 10, PSA 9, PSA 8 (registrato l'11 novembre 2026, prima del codice; D266; solo riportato)

**Domanda (Oscar).** "Se invece del PSA 10 basassimo… la gran parte del mercato scambia i PSA 9… vorrei capire se con indici con carte PSA 9 ci fossero degli scostamenti significativi tra gli indici, e me lo aspetto."

**Cosa si calcola.** Per ogni era e per il Giappone, oltre all'indice in uso (voci di ogni voto, D169, D252), tre indici con le stesse regole (20 voci, almeno 6 vendite credibili in 13 settimane, ribilanciamento ogni 13 settimane, pesi uguali, quote giapponesi del D252) ma con le sole voci PSA 10, PSA 9 o PSA 8 (con 40 voci per indice dopo il D268, come l'indice in uso). Motore del sito, storico lungo. Si riportano: rendimento a 13, 26 e 52 settimane di ogni indice; mediana, sulle settimane dal 5 gennaio 2024, della differenza assoluta tra il rendimento a 13 settimane dell'indice PSA 9 e del PSA 10 (e PSA 8 contro PSA 9); correlazione delle variazioni a 4 settimane; posti occupati all'ultimo ribilanciamento.

**Nessuna soglia, nessuna adozione:** è una misura per decidere se registrare una prova vera (per esempio indici per voto pubblicati, o un indice d'era a quote per voto, già provato nel §28 con un catalogo più piccolo). Script `scripts/ix_grade_test.py`, workflow `prova-indici-voto.yml`, risultati in `results/ix_grade/`.

**Esito (11 novembre 2026, D269), solo misura.** I voti si muovono insieme (correlazione delle variazioni a 4 settimane tra PSA 9 e PSA 10 da 0,85 Vintage a 0,97 Spada e Scudo) ma non della stessa misura: differenza mediana dei rendimenti a 13 settimane tra indice PSA 9 e PSA 10 da 4,4 punti (Classica) a 9,8 (Di mezzo) e 9,0 (Scarlatto e Violetto). A 52 settimane: Scarlatto e Violetto PSA 10 −31,7%, PSA 9 +14,7%, PSA 8 +12,4%; Vintage PSA 10 +172%, PSA 9 +104%, PSA 8 +88%; Spada e Scudo PSA 10 +1,3%, PSA 9 +14,4%, PSA 8 +28,0%; Classica PSA 10 +454%, PSA 9 +370%. Posti PSA 10 pieni ovunque tranne Di mezzo (9 su 40) e Vintage (25 su 40): lì il PSA 10 si scambia poco.

## 60. Aggiunta di carte senza ricostruire (registrato l'11 novembre 2026, prima del codice; D270)

**Domanda (Oscar).** "Dobbiamo arrivare al punto in cui la ricostruzione non serve praticamente più perché aggiungiamo solo carte nuove."

**Variante I (incrementale).** Quando entrano carte nuove, il motore riparte dall'ultimo stato salvato (D244) con i fattori d'era e i parametri condivisi fermi, e calcola solo le carte nuove (le loro vendite, il loro storico, i loro voti); le carte già nel catalogo non si ricalcolano. La ricostruzione completa resta una volta al mese e quando il catalogo cresce di un quarto (D265), ed è lei il campione.

**Prova.** Su tre gruppi di carte entrate davvero (quelle del 10 e dell'11 novembre e le prossime 20), si confronta I con la ricostruzione completa sugli stessi dati.

| # | Criterio | Soglia |
|---|---|---|
| I1 | carte già nel catalogo | valori identici a prima dell'aggiunta (per costruzione; si controlla) |
| I2 | carte nuove, errore rispetto alla ricostruzione completa | mediana dello scarto assoluto del valore ≤ 2%, 95° percentile ≤ 10% |
| I3 | carte nuove, SlabRange | copertura delle vendite delle ultime 13 settimane non più bassa di quella della ricostruzione completa meno 2 punti |
| I4 | tempo | sotto i 10 minuti per 20 carte |

Si adotta se I1–I4 passano su tutti e tre i gruppi. Fino ad allora ogni ingresso ricostruisce tutto, con il riavvio dagli stati salvati (D246).


## 61. SlabRange per carta, rumore per carta, fattore per voto, eccezioni dei dati (registrato il 12 novembre 2026, prima del codice; D274)

**Domanda (Oscar).** "Non possiamo (solo dove serve) normalizzare tutto per avere delle comparazioni reali?" Diagnosi nel D274.

**Eccezioni dei dati (si applicano a tutte le varianti, campione compreso, e si riporta il campione con e senza).** Per ogni carta × voto con almeno 6 vendite, le vendite si dividono in due gruppi al salto di prezzo più grande in scala logaritmica; se le mediane dei due gruppi distano più di 5 volte e il gruppo minore ha al massimo il 40% delle vendite, la voce va "in revisione" e le vendite del gruppo minore entrano nel registro delle eccezioni con il motivo "prezzo di un'altra stampa?" e peso zero. Diventano definitive solo quando Oscar le conferma; finché no, il registro le marca come proposte. Si riporta quante voci e quante vendite sono toccate per era.

**Varianti.**

| | Cosa cambia |
|---|---|
| A | campione: il motore in uso (v1.20) |
| B | SlabRange per carta × voto: deviazione degli scarti tra vendita e valore della settimana prima sulle vendite delle 52 settimane precedenti, ristretta verso quella della sua era × fascia di voto con peso n/(n+10); il valore non cambia |
| C | B, e il rumore delle vendite nel modello per carta × voto con la stessa stima ristretta, al posto del solo rumore d'era |
| D | C, e il fattore d'era diviso per fascia di voto: PSA 10, PSA 9, PSA 8 e sotto, ciascuno legato a quello dell'era con la stessa forza del legame tra ere |

Tutte le stime usano solo dati fino al giorno del valore (P11). Il 10 di n/(n+10) è fissato qui e non si tocca dopo i risultati.

**Prova.** Motore del sito, storico lungo, vendite reali con la metrica della vendita successiva; valutazione sulle vendite dal 1º novembre 2025 con probabilità di essere genuine ≥ 0,5. Fasce di volatilità: terzili della deviazione stimata al momento della vendita.

| # | Criterio | Soglia |
|---|---|---|
| S1 | copertura dello SlabRange, in totale | tra 78% e 82% |
| S2 | copertura per terzile di volatilità | ogni terzile tra 75% e 85% |
| S3 | la forchetta segue la carta | correlazione di rango tra larghezza della forchetta e scarto assoluto della vendita ≥ campione + 0,10 |
| S4 | errore sulla vendita successiva | mediana dell'errore assoluto non più alta del campione di oltre l'1% relativo, in totale e in ogni fascia di liquidità (P12) |
| S5 | distorsione per era × voto | media sulle celle era × fascia di voto (con almeno 200 vendite) del valore assoluto dello scarto mediano ≤ 75% di quella del campione (solo C e D) |
| S6 | ritardo | ritardo misurato come nel §57 non peggiore del campione |

B entra se passa S1–S4 e S6; C e D se passano anche S5. Tra le varianti che passano si adotta la più semplice che passa tutto; D solo se batte C su S5 di almeno 10 punti relativi. Per il D265 l'adozione vuole due giri di fila; il primo giro è questo, il secondo il giro mensile successivo con il catalogo cresciuto. Se nessuna passa, la frase del Metodo che dice che la forchetta si stringe con molte vendite concordi va corretta.
