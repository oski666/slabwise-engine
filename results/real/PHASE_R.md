# Fase R: errore sulla vendita successiva, vendite vere (protocollo §12, D55)

Dati: 3876 vendite vere dopo la calibrazione (65 settimane su 196); eBay, Goldin, Fanatics Collect (aste). Errore = differenza assoluta in log tra la stima della settimana prima e il prezzo, mediana.

| Metodo | Tutte | Alta (≥26 vendite/anno) | Media (6–25) | Bassa (≤5) |
|---|---|---|---|---|
| Ultima vendita | 11.1% | 9.2% | 14.9% | 17.2% |
| tcgcharts (mediana a fasce) | 11.3% | 9.5% | 15.4% | 17.4% |
| PriceCharting (media pesata per età) | 12.8% | 11.8% | 15.1% | 16.5% |
| Card Ladder (ultima vendita × indice) | 11.0% | 9.4% | 14.1% | 16.1% |
| Slabwise v0 (regole, tipo TCGBerg) | 15.3% | 13.6% | 19.9% | 22.6% |
| Slabwise LVM | 10.4% | 9.0% | 14.1% | 19.2% |
| *vendite* | 3876 | 2635 | 1040 | 201 |

- **R2 superato**: LVM 10.4% contro 11.0% del miglior concorrente (Card Ladder (ultima vendita × indice)).
- **R3 non superato**: nelle carte con poche vendite (≤5 in un anno) LVM 19.2% contro 16.1% di Card Ladder. Nelle fasce alta e media LVM è il migliore o alla pari.
- **R4** (solo riportato): 75.9% delle vendite dentro la forchetta predittiva all'80%.

Lettura: sulle carte liquide il modello batte tutte le regole dei concorrenti; sulle carte rare (soprattutto vintage, poche vendite PSA 10 molto sopra il PSA 9) perde, coerente con il problema della scala dei voti (D54, D58). È il prossimo lavoro sul metodo.
