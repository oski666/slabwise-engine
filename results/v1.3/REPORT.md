# Report del backtest · fase S (mercato simulato)

Semi: [1, 2, 3, 4, 5] · contaminazione base 15% · modalità A (stesso livello di identità per tutti). Valori = mediana tra i semi. Errore = mediana di |log(stima/valore vero)|, circa uguale all'errore percentuale.

> Risultati su dati simulati (P14): dicono quale formula è migliore a parità di condizioni note, non quanto sarà preciso il sito sui dati reali.

## Criteri pre-registrati

| # | Criterio | Risultato | Esito |
|---|---|---|---|
| S1 | EV totale ≥ 20% sotto il miglior concorrente | 0.0570 vs 0.0910 (PriceCharting (media pesata per età)): 37% in meno | ✅ |
| S2 | EV mai peggiore per fascia | fasce peggiori: nessuna | ✅ |
| S3 | Rumore il più basso | 0.0172 vs 0.0164 (PriceCharting (media pesata per età)) | ❌ |
| S4 | Calibrazione 75–85% | 79.0% | ✅ |
| S5 | EV al 35% di contaminazione ≤ 1,5 × EV base | 0.0598 vs 0.0570 | ✅ |
| S6 | Precisione deal ≥ 80% | 87% | ✅ |
| S7 | Errore post-crollo il più basso | 0.0637 vs 0.1232 (Card Ladder (ultima vendita × indice)) | ✅ |
| I1 | Indice d'era: quota dei movimenti veri catturata ≥ 0,80 | 0.65 | ❌ |

## Errore sul valore vero

| Metodo | Totale | Alta | Media | Bassa | Rarissima | Vendita successiva | Rumore | Post-crollo | Inondazione falsi |
|---|---|---|---|---|---|---|---|---|---|
| Ultima vendita | 10.5% | 8.2% | 8.6% | 9.6% | 12.1% | 12.4% | 1.8% | 19.0% | 68.0% |
| tcgcharts (mediana a fasce) | 9.3% | 4.2% | 6.6% | 8.8% | 12.1% | 10.0% | 1.9% | 16.1% | 178.9% |
| PriceCharting (media pesata per età) | 9.1% | 5.3% | 6.4% | 8.3% | 11.8% | 10.4% | 1.6% | 25.7% | 41.6% |
| Card Ladder (ultima vendita × indice) | 10.0% | 8.2% | 8.6% | 9.5% | 11.3% | 12.3% | 2.1% | 12.3% | 68.0% |
| Slabwise v0 (regole, tipo TCGBerg) | 9.4% | 4.0% | 5.3% | 8.1% | 13.9% | 9.8% | 1.7% | 25.7% | 17.1% |
| Slabwise LVM | 5.7% | 2.5% | 3.6% | 5.0% | 8.2% | 8.3% | 1.7% | 6.4% | 1.8% |

Fasce di liquidità: alta ≥ 1 vendita/settimana, media ≥ 1/mese, bassa ≥ 1/trimestre, rarissima meno.

## Forchetta all'80% (solo LVM)

Copertura: 79.0% · per fascia: alta 80.7%, media 79.4%, bassa 78.7%, rarissima 77.8%

## Deal

| Metodo | Segnalati | Precisione | Richiamo |
|---|---|---|---|
| Ultima vendita | 2474 | 25.7% | 41.4% |
| tcgcharts (mediana a fasce) | 2228 | 27.4% | 38.8% |
| PriceCharting (media pesata per età) | 2482 | 30.0% | 47.9% |
| Card Ladder (ultima vendita × indice) | 2445 | 26.1% | 42.3% |
| Slabwise v0 (regole, tipo TCGBerg) | 2231 | 28.6% | 40.6% |
| Slabwise LVM | 377 | 87.0% | 20.8% |

Tutti i metodi hanno lo stesso controllo del cert sugli annunci. Concorrenti: segnalato se la stima è almeno 20% sopra il prezzo. LVM: probabilità di deal ≥ 0,80 (`docs/METHOD.md` §7).

## Robustezza alla contaminazione (semi 1–3)

| Contaminazione | Ultima vendita | tcgcharts (mediana a fasce) | PriceCharting (media pesata per età) | Card Ladder (ultima vendita × indice) | Slabwise v0 (regole, tipo TCGBerg) | Slabwise LVM |
|---|---|---|---|---|---|---|
| 0% | 9.6% | 8.6% | 7.7% | 9.0% | 9.0% | 5.3% |
| 10% | 10.2% | 9.2% | 8.7% | 9.9% | 9.2% | 5.6% |
| 15% | 10.5% | 9.3% | 9.1% | 10.2% | 9.4% | 5.8% |
| 35% | 12.5% | 11.1% | 11.9% | 12.9% | 10.4% | 6.0% |
| 50% | 15.4% | 13.4% | 15.6% | 17.7% | 11.3% | 6.0% |

## Modalità B (filiera completa: i concorrenti senza verifica del cert)

| Metodo | Errore totale | Precisione deal |
|---|---|---|
| Ultima vendita | 10.8% | 25.8% |
| tcgcharts (mediana a fasce) | 9.7% | 27.1% |
| PriceCharting (media pesata per età) | 9.4% | 29.9% |
| Card Ladder (ultima vendita × indice) | 10.5% | 26.0% |
| Slabwise v0 (regole, tipo TCGBerg) | 9.6% | 28.8% |
| Slabwise LVM | 5.8% | 87.0% |

## Scenario sfavorevole (modello fuori dalle sue ipotesi)

Picchi da evento sul 30% delle carte, rumore di vendita 0,13 invece di 0,09, 30% delle carte con l'era sbagliata. Semi: [1, 2, 3].

| Metodo | Errore totale | Rarissima | Vendita successiva | Precisione deal |
|---|---|---|---|---|
| Ultima vendita | 12.3% | 14.1% | 15.3% | 24.8% |
| tcgcharts (mediana a fasce) | 10.9% | 13.7% | 12.5% | 26.7% |
| PriceCharting (media pesata per età) | 10.3% | 13.6% | 12.2% | 29.5% |
| Card Ladder (ultima vendita × indice) | 12.4% | 14.2% | 15.4% | 24.8% |
| Slabwise v0 (regole, tipo TCGBerg) | 10.3% | 15.5% | 11.5% | 27.8% |
| Slabwise LVM | 6.8% | 10.0% | 10.4% | 84.9% |

Copertura della forchetta LVM: 77.0%


## Parametri stimati (P7)

- q_L=0.0002838155625813746, q_d=2e-05, σ_e=0.0833814048198117, σ_q=0.07, τ_f=0.01
- q_L=0.0006978791604270691, q_d=0.0, σ_e=0.0701652817300401, σ_q=0.09, τ_f=0.01
- q_L=0.00036798160680303254, q_d=0.0001, σ_e=0.08527531600059533, σ_q=0.07, τ_f=0.02
- q_L=0.00024116035145666518, q_d=2e-05, σ_e=0.08887508630108723, σ_q=0.07, τ_f=0.02
- q_L=0.000536587789084841, q_d=2e-05, σ_e=0.0733957221100492, σ_q=0.07, τ_f=0.01
