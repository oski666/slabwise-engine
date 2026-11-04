# v1.5: fasce di fiducia e limite allo spostamento (protocollo §8, D47)

Rifatti tutti i 23 lavori del protocollo con i parametri calibrati della v1.2 e il limite ±log 3 acceso (`scripts/run_v15.py`).

## Limite allo spostamento (L)

Il limite non è mai scattato (0 stime toccate in tutti i lavori): nel mercato simulato nessuna carta si sposta di più di 3 volte con la sua era tra due vendite. Tutte le metriche sono identiche alla v1.2 (differenza massima 0 su EV, ES, RC e CA), quindi N1–N6 valgono come per la v1.2. Il limite è una protezione per i dati reali, dove un fattore d'era stimato su poche vendite può scappare.

## Fasce di fiducia (T1, T2)

| Seme | Errore mediano fresche | Stimato | Poco sicuro | Ordine | Copertura 80% (fresche / stimato / poco sicuro) | Stime per fascia |
|---|---|---|---|---|---|---|
| 1 | 3.6% | 7.7% | 22.8% | sì | 76% / 71% / 81% | 37296 / 94670 / 19742 |
| 2 | 3.7% | 7.9% | 23.4% | sì | 82% / 77% / 79% | 41027 / 97518 / 16023 |
| 3 | 3.6% | 7.1% | 23.3% | sì | 82% / 80% / 82% | 43249 / 97358 / 12413 |
| 4 | 3.5% | 7.2% | 24.4% | sì | 81% / 80% / 78% | 44322 / 93635 / 14951 |
| 5 | 3.7% | 7.5% | 18.9% | sì | 80% / 77% / 86% | 42456 / 96622 / 13182 |

**T1 superato in tutti e 5 i semi**: chi legge "Vendite fresche" ha un errore tipico intorno al 3,6%, "Stimato" intorno al 7,5%, "Poco sicuro" intorno al 23%. La forchetta all'80% resta calibrata in ogni fascia (T2, solo riportato). Errori in log, sul valore vero simulato (mercato simulato, P14).
