# Reel dai copioni nuovi: scene nuove nel Reel Studio
Stato: finita (27/11/2026; approvata da Oscar lo stesso giorno: "Aggiungine un altro, va bene euro")

## Perché
Oscar, 24–25/11: i copioni nuovi gli piacciono, "ovviamente non si riesce a scrivere sti pipponi in un reel": vuole vedere il risultato finale. La prova a mano (https://claude.ai/artifact/EWqUmxfooWrf5eN4T188Qf) mostra la forma: nel video frasi brevi e numeri grandi, il copione intero come voce o didascalia.

## Cosa deve fare
- Il motore scrive ogni settimana le storie nuove nei dati del sito (accanto a quelle di oggi): giapponese contro inglese, quota di PSA 10 per era, offerta contro prezzo, salto o caduta verificati, nuovo massimo storico (una carta che con le vendite della settimana supera il suo massimo di sempre, con almeno due anni di storia); ordinate per quanto sono sorprendenti, al massimo 6.
- Ogni storia porta il copione intero (gancio, numeri, perché conta, chiusura) e la scaletta delle scene con i testi brevi.
- Il Reel Studio impara cinque scene: frase con numero grande, due carte affiancate, barre, prima e dopo (due colonne di variazioni), domanda finale. Sceglie le scene dalla scaletta della storia.
- Nello studio: scegli la storia, guardi il reel, copi il testo della voce, registri il video come oggi.
- Una storia con un salto anomalo (come il Rayquaza) esce con l'avviso "da controllare a mano" e non va nel reel finché Oscar non la sblocca.

## Cosa non fa
- Non genera la voce né il montaggio audio: il testo è pronto da leggere o da incollare in didascalia.
- Non tocca i modelli di reel di oggi (andamento, occasione, PSA 10): restano come sono.
- Niente nomi di fonti o piattaforme nei reel (D108).

## Finito quando
- [ ] Nei dati del sito ci sono le storie nuove della settimana, con copione e scaletta, calcolate dal motore (non a mano).
- [ ] Per ognuno dei 5 tipi esiste almeno una storia vera della settimana, oppure la scheda dice perché quella settimana non c'è.
- [ ] Il Reel Studio mostra le 5 scene nuove e registra un reel di 15–20 secondi per ogni storia.
- [ ] Nei reel i prezzi sono in euro, al cambio del giorno come nel resto dello studio; convertiti, sono gli stessi della pagina della carta (controllo automatico su tutte le storie).
- [ ] Nomi sempre in inglese con "giapponese" accanto; nessun nome in katakana nei ganci.
- [ ] METHOD descrive come si scelgono e si ordinano le storie; test verdi.

## Decisioni da Oscar
- Valuta: euro (Oscar, 27/11). Il copione dice "euro" e la didascalia porta la data del cambio.
- Tipi: i 4 più "nuovo massimo storico" (Oscar, 27/11).
- Storie a settimana: al massimo 6 (proposta, Oscar non ha obiettato).

## Verifica (a lavoro chiuso)
Fatta il 27/11 sul Sito 45989039664 (success) e sui dati pubblicati (asof 26/11, cambio 0,9112).
- [x] Storie dal motore: il build scrive "storie per i reel (D347): high, high, twin, twin, era_share, jump"; nei dati del sito `pulse.reels` ha 6 storie con copione e scaletta.
- [x] Tipi: 4 su 5 presenti. "Offerta contro prezzo" questa settimana non c'è: nessuna carta ha passato insieme +8% di PSA 10 in un mese e −10% di prezzo con l'ultima lettura delle popolazioni (22/11) e il cambio di vendite del 26/11 (in locale, con i dati del 23/11, c'era Mega Gengar ex).
- [x] Scene e reel: le 5 scene montate e registrate in locale con lo studio costruito da `social/reel-studio/build.py` sui dati veri (immagine inviata a Oscar il 27/11); lo studio online chiede l'accesso da creator, quindi non l'ho aperto io: la lista va guardata da Oscar.
- [x] Numeri: Magikarp PSA 10 giapponese 184 € e inglese 3.226 € = Slabprice della pagina × 0,9112 (184,3 e 3.226,1); Typhlosion giapponese 1.462 € = 1.461,9. Per costruzione i prezzi delle storie vengono dagli stessi valori della pagina.
- [x] Niente katakana: nessun carattere giapponese in ganci e numeri delle 6 storie; i set giapponesi senza nome latino diventano "set giapponese".
- [x] METHOD 8c scritta; test verdi (41 passati).
- Correzione dopo la verifica: Scyther ex PSA 10 (3,8 volte il vecchio massimo) e Typhlosion (+297% in 30 giorni) erano usciti senza avviso. Ora l'avviso "da controllare" c'è sempre oltre il doppio del vecchio massimo e per variazioni del 100% o più (METHOD 8c); le storie di questa settimana si ricalcolano alla prossima ricostruzione.
