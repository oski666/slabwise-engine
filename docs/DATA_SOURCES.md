# Fonti di dati: cosa è gratis, cosa costa, cosa è vietato

**Aggiornato al 23 ottobre 2026.** Verificato sulle pagine ufficiali (documentazione PokemonPriceTracker letta nel browser, pagine Scrydex, PSA, eBay Developers). Le condizioni cambiano: ricontrollare prima di pagare.

## Cosa serve al nostro metodo

Il Modello a Valore Latente lavora meglio con le **singole vendite** (prezzo, data, voto, piattaforma, idealmente cert e titolo). Funziona anche con **aggregati giornalieri** (media e numero di vendite per voto e per giorno), trattando ogni giorno come una misura pesata per il numero di vendite. Si perde però parte del filtro sulle singole vendite anomale.

## Il quadro

| Fonte | Cosa dà per i graded | Costo | Licenza | Uso per noi |
|---|---|---|---|---|
| **PokemonPriceTracker Free** | prezzo per voto + storico giornaliero (media, numero di vendite) degli **ultimi 3 giorni**; 100 crediti al giorno | 0 € | personale, hobby e sviluppo pre-lancio | raccolta giornaliera nostra di ~30 carte, da subito |
| **PokemonPriceTracker API** | come sopra con **6 mesi** di storico giornaliero; 20.000 crediti al giorno | $9,99 al mese | personale, hobby e sviluppo pre-lancio | **backtest su dati reali in un mese** |
| **PokemonPriceTracker Business** | **vendite singole eBay** (id annuncio, titolo, prezzo, data, asta/BIN, Best Offer accettata, spedizione), vendite **Fanatics Collect**, popolazioni PSA, storico illimitato, CSV giornalieri | $99 al mese | uso commerciale ammesso; vietato rivendere i dati | backtest completo e poi il sito |
| Scrydex | dati graded solo dai piani Growth ($99) in su; fonti non dichiarate | da $29 al mese | non dichiarata nella FAQ | nessun vantaggio rispetto a PPT Business |
| PSA Public API | solo verifica del cert | 0 € (token personale) | accordo d'uso PSA | livello di identità |
| PSA Auction Prices Realized | risultati d'asta con voto da eBay, Goldin e altri, consultabili sul sito | consultazione libera | accesso automatico non previsto | solo controlli manuali a campione |
| eBay Marketplace Insights (vendite concluse) | vendite eBay degli ultimi 90 giorni | gratis se concessa | API **privata**: la documentazione è dietro login e serve l'approvazione di eBay; la licenza eBay limita l'uso dei dati per modellare prezzi | da richiedere, ma non contarci |
| Fanatics Collect, Goldin, Alt | risultati sui loro siti | — | nessuna API pubblica; esistono solo scraper di terzi | possibile con scraper di terzi (D26), con i rischi annotati |

## Da dove prende i dati tcgcharts

Dalla loro metodologia: vendite eBay (96%), Fanatics Collect (3,6%), Goldin, Rare Candy e Alt (0,1%). Il gestore dice di usare Scrydex più Fanatics "direttamente" e altre fonti pubbliche. Fanatics e Goldin non hanno API pubbliche, quindi si tratta di accordi o raccolta dai siti, (dal 23 ottobre P18 è rimosso, D26: valutiamo anche gli scraper).

## Costruirci i dati da soli? (verificato il 23 ottobre 2026)

**Dall'API ufficiale di eBay, no.** La licenza delle API eBay ([API License Agreement](https://www.edp.ebay.com/join/api-license-agreement)) vieta proprio quello che faremmo:
- §9.5: vietato usare i contenuti eBay, da soli o insieme ad altri dati, per suggerire o modellare prezzi;
- §8.1(d): serve il permesso scritto di eBay per ricavare prezzi medi di vendita;
- §8.1(b)(1) e §8.1(c): i dati vanno cancellati quando spariscono da eBay, e quelli mostrati non possono essere più vecchi di 6–24 ore, quindi niente storico;
- §9.10: vietato usarli per addestrare algoritmi.

L'API Browse mostra solo annunci attivi: le vendite concluse sono riservate a Marketplace Insights, che richiede l'approvazione di eBay. Raccogliere le pagine di eBay o di Fanatics, Goldin o Heritage senza un accordo va contro i loro termini: dopo D26 è un rischio accettato da Oscar, non più un divieto del progetto.

**Strade lecite per costruire qualcosa di nostro:**
1. **Chiedere i permessi**: richiesta a eBay per Marketplace Insights o per un permesso scritto; richiesta di licenza dati ad aste come Heritage e Fanatics Collect. Non costa nulla chiedere.
2. **Vendite inviate dagli utenti**: chi compra o vende uno slab lo registra con cert e prezzo. Sono dati suoi, quindi possiamo usarli; il motore li tratta come una fonte in più (il cert si verifica con l'API PSA).
3. **Archivio storico curato a mano** per le carte simbolo: vendite record pubblicate in comunicati e articoli (un fatto con data, prezzo, voto e casa d'aste). Serve per lo storico lungo, 2015–2020, non per la valutazione di tutti i giorni.

**Cosa conta davvero per il motore:** servono le vendite **singole**, anche sporche, perché il modello è costruito per riconoscere doppioni, lotti, falsi e Best Offer. I dati aggregati o "già puliti" lo rendono inutile. Per stimare il valore di oggi bastano 12–24 mesi di vendite; lo storico lontano è un contenuto da mostrare, non una necessità del calcolo.

## Prova dal vivo della PSA Public API (23 ottobre 2026)

Con il token personale di Oscar la verifica del cert risponde **403: "Access to this API is limited to approved customers."** Il token non basta: PSA concede l'accesso solo ai clienti approvati. Da chiedere a PSA prima di contare su questa fonte. La documentazione pubblica elenca solo la verifica del cert: niente prezzi.

## Apify (verificato il 23 ottobre 2026)

Piattaforma dove terzi pubblicano scraper ("actor"). Piano gratuito: 5 $ di utilizzo al mese; poi Starter 19 $/mese. Gli actor sono della comunità: affidabilità da provare su pochi risultati.

| Actor | Cosa dà | Costo | Note |
|---|---|---|---|
| [datasteady/ebay-sold-listings](https://apify.com/datasteady/ebay-sold-listings) | vendite eBay singole: id, titolo, prezzo, spedizione, data di fine, asta/BIN, offerte, **flag Best Offer accettata** (non l'importo), venditore; anche ebay.it/.de/.co.uk | da 1,49 $ ogni 1.000 risultati | solo gli ultimi ~90 giorni (quanto mostra eBay); pochissimi utenti, nessuna esecuzione riuscita registrata |
| [khadinakbar/ebay-sold-comps-analytics-scraper](https://apify.com/khadinakbar/ebay-sold-comps-analytics-scraper) | vendite eBay singole (stessi campi, senza flag Best Offer) più statistiche | da 5 $ ogni 1.000 vendite | massimo 90 giorni |
| [lexis-solutions/psacard-com-scraper](https://apify.com/lexis-solutions/psacard-com-scraper) | PSA Auction Prices Realized: casa d'aste, tipo, data, voto, prezzo, **numero di cert** | 35 $/mese più utilizzo | l'unica strada per lo storico lungo (anni) e multi-casa; nessun utente attivo, esempio fittizio |
| Fanatics (fanatics.com) | abbigliamento, non Fanatics Collect | — | inutile |
| [jungle_synthesizer/goldin-auctions-marketplace-scraper](https://apify.com/jungle_synthesizer/goldin-auctions-marketplace-scraper) | Goldin: archivio aste passate (`past_auctions`), filtro Pokemon e grader, prezzo finale con commissione, offerte, riserva raggiunta, data di vendita | 0,0015 $ a record (~3.300 record con i 5 $ gratuiti) | 61 utenti, ~93% esecuzioni riuscite negli ultimi 30 giorni; profondità dello storico da verificare |
| [jungle_synthesizer/fanaticscollect-weekly-auction-scraper](https://apify.com/jungle_synthesizer/fanaticscollect-weekly-auction-scraper) | Fanatics Collect (ex PWCC): archivio aste passate, filtro Pokemon, prezzo finale con commissione, offerte, **numero di cert** | 0,002 $ a record + 0,10 $ ad avvio (~2.400 record gratis) | 80 utenti, ~99% esecuzioni riuscite; profondità dello storico da verificare |

**Prima prova (23 ottobre 2026, 200 vendite Pokémon PSA per actor, 0,90 $ del credito gratuito):**
- Fanatics Collect: 200 vendite concluse, **199 con numero di cert**, prezzo finale, offerte, voto. Date dal 2023 al 2026 (il grosso nel 2026). Il prezzo con commissione è ricavato dall'actor ("derived").
- Goldin: 200 vendite concluse, tutte del 2023 (l'archivio non è ordinato per data), senza cert; voto e prezzo con commissione presenti. Qualche lotto multiplo e prodotto sigillato, da scartare.
- Profondità dello storico: Goldin non restituisce nessuna vendita Charizard PSA prima del 2021 (filtro `soldBefore`); le vendite trovate vanno da gennaio 2023 a oggi. Fanatics: dal 2023. **Lo storico 2015–2020 non arriva da qui.**

**Raccolta mirata (23 ottobre 2026, 1,95 $, totale del mese 2,85 $ su 5 $ gratuiti):** ricerche per nome sulle nostre 23 carte (Goldin, 40 lotti ciascuna) e su 6 carte (Fanatics, 60 lotti). Dopo il riconoscimento dei titoli (`slabwise/sources/auction_titles.py`): 419 vendite PSA 7–10 delle nostre carte, 203 con cert. Scartate: voti fuori 7–10 o senza voto (554), lingue diverse, lotti, buste sigillate, firmate, ristampe (320), altre carte (172). Le ricerche per nome di Goldin sono rumorose: su 40 lotti di "Base Set Charizard" solo 6–8 sono la carta giusta.

Dati sensibili: i nomi dei venditori non servono al motore e non si salvano. Eccezione (D93): i venditori professionali (case d'asta, consegnatari, account con molte vendite) per il confronto tra venditori, solo da una fonte registrata qui prima della raccolta; i privati mai.

## eBay "venduti" in proprio e mercati giapponesi (23 ottobre 2026)

**eBay, filtro "Oggetti venduti" + "Inserzioni completate"**: è esattamente la pagina che legge l'actor eBay di Apify (`LH_Sold=1&LH_Complete=1`). Chiamata direttamente dai nostri server risponde **403** (eBay blocca le richieste automatiche dai data center); aggirare il blocco non è un'opzione. Mostra solo gli ultimi 90 giorni. Strada pratica: l'actor Apify (`caffein.dev/ebay-sold-listings`), 0,004 $ a vendita sul piano gratuito.

**Mercari Japan**: le vendite concluse sono visibili (filtro 売り切れ, `status=sold_out`), ma la pagina carica gli oggetti con un'API protetta: dai nostri server l'HTML non contiene annunci e l'API risponde 403. Actor Apify affidabili: `fatihtahta/mercari-japan-scraper` (≈31.800 esecuzioni, 0 fallite, 0,004 $ a annuncio) e `logiover/mercari-japan-scraper` (≈4.900, 2 fallite, 0,0035 $), con filtro venduti. Limiti: prezzo in yen; il prezzo mostrato è quello finale (si compra al prezzo esposto, le trattative avvengono prima nei commenti); la data di vendita è approssimata dall'ultimo aggiornamento; molti annunci sono raw o lotti; titoli in giapponese.

**SNKRDUNK** (verificato il 25 ottobre 2026): è la fonte giapponese di Pikawu, ma i suoi termini vietano espressamente di accedere o raccogliere informazioni "con crawling, scraping o mezzi simili" (art. 7.1.xiii) e l'unico actor Apify che lo copre dà solo il prezzo minimo in vendita, senza le vendite concluse né il voto. Non lo usiamo.

**Altre fonti giapponesi** per gli slab: Yahoo! Auctions (aste chiuse, actor dedicati ai prezzi di aggiudicazione) e SNKRDUNK (storico scambi per voto PSA, pochi actor e poco usati).

**Prerequisito per tutte le fonti giapponesi**: le carte giapponesi sono stampe diverse (set e numeri propri, D28), quindi servono voci nel catalogo con i nomi giapponesi (es. ブラッキーVMAX SA, S6a 095/069) e un riconoscitore dei titoli in giapponese.

## Fanatics Collect: archivio pubblico delle vendite (D46, D50)

| Cosa | Dettaglio |
|---|---|
| Indirizzo | `https://sales-history-api.services.fanaticscollect.com/api/v1/pub/sales?title=<parole>&page=<n>&size=50`, lo stesso archivio che usa la pagina pubblica "Sales History" di Fanatics Collect (circa 5,5 milioni di vendite) |
| Costo | gratis, senza chiave e senza Apify |
| Cosa dà | titolo, voto e grader, cert, prezzo pagato (commissione compresa, uguale a quello che avevamo da Apify), data, tipo di vendita (asta settimanale, Premier, prezzo fisso) e **stato del pagamento** |
| Limiti | circa 1.000 risultati per ricerca (20 pagine); lo stato del pagamento è registrato solo da dicembre 2025 (D50); le vendite a prezzo fisso non entrano nel modello, compaiono solo nella storia delle copie (D63) |
| Storia delle copie (D63) | il cert (`serial`) di ogni vendita PSA delle carte del catalogo, aste e prezzo fisso, con lo stato del pagamento: `prototype/data/certs.json`. Non teniamo foto né venditore |
| Rischi | API non documentata, usata dalla loro pagina pubblica: può cambiare o chiudere senza preavviso; i termini d'uso di Fanatics non la menzionano. robots.txt non la vieta. Richieste lente (una ogni 1,5 s, nuovi tentativi distanziati), copia locale di ogni risposta in `data/raw/fanatics_history/` |
| Script | `scripts/fanatics_history.py` (scarica), `scripts/apify_to_csv.py … data/raw/fanatics_history` (unisce e applica il flag), `scripts/cert_history.py data/raw/fanatics_history prototype/data/certs.json` (storia delle copie per cert) |

## Immagini delle carte (D45)

| Fonte | Cosa prendiamo | Provenienza | Rischi |
|---|---|---|---|
| **TCGdex** (assets.tcgdex.net, api.tcgdex.net) | immagini e dati del catalogo, inglese e giapponese | progetto aperto; immagini di proprietà di The Pokémon Company | alcune carte mancano (es. promo SVP 085, varie stampe giapponesi); copyright delle immagini da chiarire prima del lancio |
| **Pokémon TCG API, CDN immagini** (images.pokemontcg.io) | immagini delle carte inglesi che TCGdex non ha (oggi: Pikachu with Grey Felt Hat, SVP 085) | servizio gratuito della comunità | stesso copyright; nessuna garanzia di disponibilità |
| **Database ufficiale giapponese** (www.pokemon-card.com, ricerca e scheda carta) | immagini delle stampe giapponesi che TCGdex non ha (oggi: メガリザードンXex M2 110/080, scheda 48516) | sito ufficiale di The Pokémon Company | il database elenca una scheda per testo di carta: alcune illustrazioni alternative non ci sono (ブラッキーVMAX S6a 095/069: immagine da tcgcharts, con il permesso D76, dal 1° novembre); uso delle immagini da chiarire prima del lancio |

Le immagini si scaricano una volta (`scripts/fetch_missing_images.py`) e finiscono nella pagina come dati incorporati; nessuna spesa.

## Piano consigliato (da approvare: P19)

| Fase | Spesa | Cosa facciamo | Cosa impariamo |
|---|---|---|---|
| 0 | 0 € | Chiave gratuita PPT; raccolta giornaliera automatica di ~30 slab (aggregati degli ultimi 3 giorni) | La filiera reale funziona; si comincia a costruire uno storico nostro |
| 1 | ~10 € una tantum (1 mese di piano API, poi disdetta) | Scarichiamo 6 mesi di storico giornaliero per qualche centinaio di slab; backtest fase R sulla vendita successiva contro i metodi dei concorrenti | Se il modello batte i concorrenti anche su dati reali |
| 2 | ~92 € una tantum (1 mese di Business, solo se la fase 1 va bene) | Vendite singole con titolo e Best Offer: filtro completo, popolazioni, market cap | Il metodo completo su dati reali; base per il sito |

**Totale massimo per sapere se il metodo vale: circa 100 €, in due passi, il secondo solo se il primo convince.**

## Collectoon API (developers.collectoon.it; letta il 26 ottobre 2026, non adottata)

| Cosa | Dettaglio |
|---|---|
| Chi | app italiana per collezionisti: collezione, prezzi, scansione, mercato tra privati al 3%, assistente AI |
| Cosa dà | catalogo di 10 giochi e **prezzi aggregati** per carta (valore stimato, prezzo in vendita o di transazione, con minimo e massimo e data), da CardMarket, TCGplayer, eBay, JustTCG, PokeTrace e Collectoon, in euro; filtro `graded`; storico per giorno, settimana o mese. **Nessuna vendita singola** |
| Costo | Free 100 richieste al giorno, storico 7 giorni, **solo uso personale e non commerciale**; Pro 12,99 €/mese (stesso limite d'uso); API Developer 24,99 €/mese e Business 79,99 €/mese con uso commerciale "entro le licenze delle fonti" |
| Termini (§6.1) | vietato ridistribuire i dati, usarli per un servizio concorrente e usarli per addestrare o **valutare** modelli; chiavi solo su server propri |
| Giudizio | non serve al modello: il metodo vuole vendite singole concluse (P3, P4), non prezzi già aggregati da altri. Al massimo un confronto a campione, ma i termini vietano di usarli per valutare modelli. Da seguire due nomi tra le loro fonti: **PokeTrace** e **JustTCG** |

## PokeTrace e JustTCG (fonti di Collectoon; lette il 26 ottobre 2026, non adottate)

| | PokeTrace (poketrace.com) | JustTCG (justtcg.com) |
|---|---|---|
| Cosa dà | prezzi aggregati (media, minimo, massimo, numero di vendite) da eBay venduti, TCGplayer e CardMarket, raw e **graded** (15 enti, voti 1–10), storico 7 g / 30 g / 90 g / 1 anno / tutto. Con il piano Scale anche le **vendite eBay singole** (`/cards/:id/listings`: titolo, id dell'oggetto, prezzo, data, ente e voto, link, segnale di anomalia) | prezzi aggregati per condizione da negozi partner e mercati; graded (PSA, BGS, CGC, SGC…) **in beta**, come prezzi aggregati; nessuna vendita singola dichiarata |
| Costo | Free 250 richieste/giorno solo raw e non commerciale; Pro 19,99 $/mese (graded, storico, uso commerciale); Growth 49,99 $; **Scale 98 $/mese** (vendite singole, 20 per pagina, 30 richieste ogni 30 s) | Free 100/giorno non commerciale; 19 $, 49 $, 149 $/mese con licenza commerciale |
| Termini | vietato creare un servizio concorrente o rivendere/ridistribuire i dati senza permesso scritto | uso commerciale, conservazione e combinazione con altre fonti ammessi; vietato rivendere i dati grezzi o fare un'API di prezzi concorrente |
| Limiti per noi | profondità dello storico delle vendite singole non dichiarata; i dati vengono da eBay, quindi la provenienza resta quella di eBay | dati aggregati: il modello vuole vendite singole (P3, P4) |
| Giudizio | l'unica delle tre con vendite singole graded, ma a 98 $/mese come PokemonPriceTracker Business (99 $/mese), che in più dà Fanatics, popolazioni PSA e storico illimitato. Da confrontare con PPT prima di qualsiasi spesa (P19) | non serve al modello |

## Alt (alt.xyz): vendite recenti dal sito pubblico, con permesso (D64)

| Cosa | Dettaglio |
|---|---|
| Permesso | email di Alt Team a Oscar del 27 ottobre 2026: non hanno ancora un'API; ci invitano a leggere i dati dal sito "senza essere troppo aggressivi" e "con un numero ragionevole di richieste al giorno"; sostengono questo tipo di progetti |
| Cosa dà | la pagina "Sold listings" di ogni ricerca: titolo normalizzato (anno, set, variante, soggetto, numero), voto, prezzo, tipo di vendita (asta, compralo subito, best offer), data, mercato (eBay, Fanatics Collect, Goldin, Heritage, Pristine, Alt, CardHobby) e, per eBay, l'id dell'annuncio |
| Limiti | ai visitatori Alt mostra **solo la prima pagina** (15 vendite) di ogni ricerca; le pagine successive chiedono di registrarsi e non le apriamo. Lo storico pubblico arriva a circa 90 giorni. Per questo una ricerca per carta e voto ogni giorno, che accumula |
| Regole | browser vero come un visitatore, nessuna chiave interna, al massimo 150 pagine al giorno, una ogni 8 s o più; niente foto né venditori |
| Doppioni | Fanatics Collect scartata qui (presa dall'archivio con il flag di pagamento); eBay riconosciuta dall'id e tenuta una volta sola |
| Best Offer | il prezzo mostrato entra solo se passa il controllo B1 (D64); altrimenti scartato come "Best Offer senza prezzo accettato" |
| Script | `scripts/alt_sold.py data/raw/alt` (raccolta del giorno), poi `scripts/apify_to_csv.py … --alt=data/raw/alt` (unione). I dati grezzi stanno in `data/raw/alt/` nel repository privato `slabwise-data` (D163), non in quello pubblico |

## eBay Browse API: annunci attivi per le occasioni (D72)

| Cosa | Dettaglio |
|---|---|
| Accesso | account eBay Developers di Oscar, keyset di produzione, token "application" (client credentials, scope `https://api.ebay.com/oauth/api_scope`); chiavi in `~/.slabwise/ebay_client_id` e `~/.slabwise/ebay_client_secret`, mai nel repository |
| Cosa usiamo | `GET /buy/browse/v1/item_summary/search` su EBAY_US, EBAY_IT, EBAY_DE, categoria carte singole, con `X-EBAY-C-ENDUSERCTX: affiliateCampaignId=5339232565,contextualLocation=country%3DIT` (spedizione verso l'Italia e link affiliati); `GET /item/{id}` solo per gli annunci candidati, per leggere il cert |
| Limiti | 5.000 chiamate al giorno (limite base); al massimo 10.000 risultati per ricerca |
| Licenza | §9.5 (niente prezzi modellati senza permesso scritto): rischio accettato con D72; §8.1 annunci mostrati non più vecchi di 6 ore e cancellati quando chiudono |
| Conteggio per la Slabvalve (D225) | quante copie di ogni carta e voto sono in vendita nel giorno, dagli stessi risultati di ricerca; si salva solo il numero nella pagina, nessun annuncio oltre le 6 ore (§8.1); con più di 200 risultati il numero è un minimo |
| Script | `scripts/ebay_listings.py` (raccolta) e calcolo in `slabwise/deals.py` |

## tcgcharts (tcgcharts.com): vendite singole e popolazioni, con permesso (D76)

| Cosa | Dettaglio |
|---|---|
| Permesso | email di Marek (tcgcharts) a Oscar del 27 ottobre 2026: possiamo navigare il sito e raccogliere dati come preferiamo, gratis, finché siamo in prova |
| Cosa dà (letto dal file HAR della visita di Oscar del 20 ottobre) | `/api/pokemon/card-detail/<set>/<carta>`: scheda con **popolazioni PSA per voto** (`psa10Count`…`psa1Count`, anche CGC e BGS), `marketCapUsd`, id interni; `/api/card-sales?cardId=…&cardType=base\|variant&page=…&limit=…`: **vendite singole** con piattaforma, id della vendita (per eBay l'id dell'oggetto), titolo, ente e voto, prezzo, data, fonte a monte (Scrydex, PokeData, Fanatics), esclusione e motivo, flag di pagamento in attesa o trattenuto |
| Provenienza a monte | aggregatore: eBay (via Scrydex e PokeData), Fanatics Collect, Alt, PriceCharting. Le vendite eBay possono essere doppioni di quelle che abbiamo da Apify e Alt (si riconoscono dall'id dell'oggetto), quelle Fanatics doppioni dell'archivio (si riconoscono dall'id del lotto) |
| Rischi | API non documentata, il sito è nuovo e cambia spesso; il permesso vale per la fase di prova; dati aggregati (prezzi medi, capitalizzazioni) non entrano nel modello (P3, P4) |
| Regole | raccolta giornaliera della pagina più recente e completa il lunedì (D89); ritmo basso (una richiesta ogni 3 s o più), copia locale di ogni risposta in `data/raw/tcgcharts/`, nessun dato di venditori |
| Vendite d'asta (D121, D124) | dal 2 novembre entrano nei prezzi anche le vendite Fanatics Collect, Goldin e Alt lette da tcgcharts, perché le nostre raccolte da quelle case si sono fermate il 23 ottobre; una vendita già nei nostri file (stessa carta e voto, entro 3 giorni e 2% di prezzo) non si conta due volte; quelle in attesa di pagamento restano fuori |
| Storico lungo (D80, D123) | con l'account di Oscar, dal suo browser (`scripts/browser/tc_history.js`): il token resta nella pagina; serve all'ultima vendita nota, non ai prezzi (D86) |
| Stampe giapponesi (D134) | carte collegate (`relatedCards` del dettaglio) e ricerca, per trovare le stampe giapponesi delle carte del catalogo; l'illustratore del dettaglio deve coincidere con quello della carta inglese; id, nome giapponese e immagine vengono da TCGdex (ja) |

## Messaggi dal modulo Contatti (D129)

| | |
|---|---|
| Cosa | testo del messaggio e, se scritta, l'email per la risposta; data |
| Dove | Cloudflare KV legato al sito (`REQUESTS`, chiavi `msg:`), scadenza 365 giorni; letti e cancellati su `/studio/messaggi` (password dello studio) |
| Dati personali | l'email, solo se la persona la lascia; impronta (hash) della connessione con la data per limitare gli invii, scade in 24 ore |
| Rischi | spam (limite di 5 al giorno per connessione); dati sensibili scritti nel messaggio: si cancellano su richiesta |

## Statistiche anonime dei visitatori (D133)

| | |
|---|---|
| Cosa | quante persone seguono o possiedono ogni carta per voto (+1/−1 quando aggiungono o tolgono), quante volte si apre ogni scheda per giorno; visite al sito con Cloudflare Web Analytics (pagine, paesi, provenienza) |
| Dove | Cloudflare D1 legato al sito (`STATS`); letti su `/studio/statistiche` (password dello studio). Web Analytics nel pannello Cloudflare |
| Dati personali | nessuno salvato: niente identificativi, cookie, prezzi pagati o cert. Il browser del visitatore può spegnere il conteggio dalla pagina `#mie`; le visite di chi ha il cookie dello studio non si contano |
| Rischi | conteggi gonfiabili (limite di 120 eventi ogni 10 minuti per connessione, in memoria): indicativi, mai usati nei prezzi; lettori con blocco dei tracciatori non contano |

## Richieste degli utenti (D97)

| | |
|---|---|
| Cosa | carte richieste dai visitatori: identificativo TCGdex, nome, set, lingua, numero di richieste, data della prima e dell'ultima |
| Dove | Cloudflare KV legato al sito (`REQUESTS`), letto ogni giorno dal controllo automatico; stato pubblicato in `prototype/data/requests_status.json` |
| Dati personali | nessuno: niente account, email o nomi. Per limitare l'abuso si salva un'impronta (hash) dell'indirizzo di rete con la data del giorno, che scade dopo 24 ore |
| Ricerca | il browser del visitatore interroga direttamente l'API pubblica di TCGdex (api.tcgdex.net) |
| Rischi | richieste ripetute per gonfiare una carta (limitate a 10 al giorno per connessione); l'ammissione dipende comunque dai dati, non dal numero di richieste |

## Fonti giapponesi valutate (D144) — non attive

Ricerca del 3 novembre 2026 per il mercato giapponese (D142). Nessuna è collegata: serve l'ok di Oscar sulla spesa (P19) e una prova di riconoscimento dei titoli registrata prima.

| Fonte | Cosa darebbe | Come | Costo | Rischi |
|---|---|---|---|---|
| Yahoo! Auctions (ヤフオク), aste chiuse | prezzo finale in yen, data di fine, titolo, numero di offerte, venditore | attore Apify `datalab-jp/yahoo-auctions-sold-scraper` (pagine pubbliche delle aste chiuse, nessun login) | da 4 $ ogni 1.000 risultati | termini d'uso di Yahoo Japan sulla raccolta automatica da verificare; titoli in giapponese ("PSA10", "201/165") da riconoscere; profondità storica non dichiarata |
| Mercari Japan, venduti | prezzo in yen dei venduti | attori Apify (`datalab-jp/mercari-scraper`, filtro "sold_out") | da 4 $ ogni 1.000 risultati | **nessuna data di vendita** (solo creazione/aggiornamento dell'annuncio): debole per una serie nel tempo; termini d'uso da verificare |
| Aucfan | archivio dei venduti di Yahoo! Auctions, Mercari, Rakuma e altri, con data di fine | attore Apify `jungle_synthesizer/aucfan-...` | per evento, da verificare | rivende dati di altri; limiti di frequenza aggressivi; lo storico lungo è a pagamento sul sito |
| SNKRDUNK (スニダン) | mercato giapponese con slab PSA e storico delle transazioni per carta | nessuna API pubblica nota | — | da studiare: termini d'uso, possibilità di accordo |

**Proposta (D144):** partire da Yahoo! Auctions (aste chiuse con data, stesso fornitore dei dati eBay) su poche carte giapponesi del catalogo, misurare la quota di titoli riconosciuti con le regole di D97, e solo dopo decidere; Mercari solo come controllo dei prezzi, non come serie.

## Marketplace in cassaforte e aggregatori (D146) — non attivi

Ricerca del 3 novembre 2026 (Oscar ha segnalato Traded).

| Fonte | Cosa darebbe | Come | Costo | Rischi |
|---|---|---|---|---|
| Courtyard (vendite concluse) | vendite di slab PSA, CGC e BGS custoditi in cassaforte: prezzo in USDC, data, **numero di cert, voto e titolo nei metadati** del token | catena Polygon, contratto ERC-721 `0x251be3a17af4892035c37ebf5890f4a4d889dcad`, dati pubblici (nodo RPC o esploratore con chiave gratuita); in alternativa attori Apify (es. `trev0n/courtyard-io-scraper`, da 1 $ ogni 1.000) | gratis via catena; pochi dollari via Apify | non ogni trasferimento è una vendita (pacchetti "gacha" con riacquisto istantaneo, spostamenti tra portafogli): vanno tenute solo le vendite di mercato; prezzo senza spedizione né tasse (lo slab resta in cassaforte); va misurata la sovrapposizione con le nostre vendite per cert |
| Traded (traded.gg) | annunci in vendita di eBay, Fanatics e marketplace in cassaforte (Courtyard, Collector Crypt, Renaiss, Beezie, DYLI), con un'identità unica per carta | API in sviluppo, annunciata anche come MCP; oggi nessuna documentazione, condizioni d'uso o prezzi pubblici | da chiedere | solo annunci (P3: mai nei prezzi, utili alle occasioni); i link eBay non porterebbero la nostra affiliazione; è anche un sito di occasioni (D108: non si nomina sul sito) |

**Esito (D147):** Courtyard e i marketplace in cassaforte o a pacchetti (DOPA e simili) **esclusi** dalle fonti dei prezzi. **Proposta originale (D146):** (1) Oscar chiede a Traded condizioni e accesso anticipato all'API; (2) prova registrata sulle vendite Courtyard delle carte del catalogo: quante vendite di mercato in 90 giorni, quota riconosciuta, scarto dal nostro valore, sovrapposizione per cert; solo dopo l'eventuale ingresso nei prezzi, come le altre case.

## Pokecolor (pokecolor.com): vendite concluse, con permesso (D180)

| Cosa | Dettaglio |
|---|---|
| Permesso | email di Lian (team Pokecolor) a Oscar del 6 novembre 2026: non hanno un'API, ma la storia delle vendite è pubblica; possiamo interrogare i loro endpoint "in a timely manner" e usare i dati di vendita pubblici per il nostro sito |
| Chi sono | marketplace di Hong Kong (aste, acquisto diretto, cassaforte) con carte giapponesi, inglesi, cinesi e coreane; un ufficio nuovo negli Stati Uniti |
| Cosa dà | la lista pubblica della pagina "Sales History" (`/api/overseas/trade/sellorder/?status_filter=sold_finish`, filtri per gioco ed ente) e il dettaglio di ogni vendita: titolo, data di chiusura, prezzo in HKD, prezzo in dollari e cambio della vendita, ente e voto, asta o prezzo fisso, numero di offerte; nel dettaglio la carta strutturata (nome, numero, rarità, anno, lingua, codice e nome del set). Alcuni titoli contengono il numero di cert PSA |
| Prima prova (6 novembre 2026) | 290 vendite PSA di carte Pokémon dal 21 giugno al 1 novembre 2026 (circa 70 al mese), 251 giapponesi; 13 su 7 carte del nostro catalogo giapponese |
| Da scartare | carte firmate (签绘), lotti di più carte (连号, ×N), lingue diverse dalla carta (il titolo e la lingua del dettaglio lo dicono); il prezzo è quello di aggiudicazione, la commissione del compratore va verificata |
| Rischi | endpoint non documentati, che possono cambiare; volume piccolo; doppioni possibili con eBay per i lotti venduti anche lì (si riconoscono dal cert) |
| Regole | raccolta giornaliera (`raccolta-pokecolor.yml`), una richiesta ogni 4 s, si ferma alla prima pagina già nota; nessun dato di compratori o venditori; dati grezzi in `data/raw/pokecolor/` nel repository privato `slabwise-data` (D163); nei prezzi solo dopo un controllo registrato prima (D180) |
| Script | `scripts/pokecolor_sold.py data/raw/pokecolor` |

## GemRate (gemrate.com): popolazioni e gradazioni nel tempo, con permesso (D189)

| Cosa | Dettaglio |
|---|---|
| Permesso | email di Ryan (fondatore di GemRate) a Oscar: non offre una licenza API, ma possiamo raccogliere i dati dal sito e usarne le analisi, purché non peggioriamo l'esperienza degli altri utenti |
| Cosa dà | report di popolazione unificato (PSA, Beckett, SGC, CGC), gradazioni giornaliere, settimanali e mensili, carte e set con più gradazioni nella settimana (gradate l'ultima settimana e quella prima), pagine "Population Trend" per carta e per set |
| Accesso | il sito usa una verifica Cloudflare (Turnstile): niente raccolta da GitHub né dal nostro server; solo dal browser integrato di Oscar, dopo che lui ha fatto la verifica, una richiesta ogni 5 s o più |
| Rischi | pagine e formati non documentati; il permesso è informale; il report conta le gradazioni, non le copie (rinvii e sbustamenti contano due volte, come già per PSA, D109) |
| Copertura | dal D261 tutti i set del catalogo che hanno una pagina (160 set, anche giapponesi; promo divise per anno); `scripts/gemrate_merge.py` unisce le letture in `sets.json` |
| Regole | solo popolazioni e gradazioni, solo PSA per i nostri calcoli (D165); dati grezzi in `data/raw/gemrate/` nel repository privato `slabwise-data`; sul sito la fonte non si nomina |

## PokeAPI (github.com/PokeAPI/pokeapi): nomi delle specie in giapponese (D237) — non attiva (§47 non superato)

| Cosa | Dettaglio |
|---|---|
| Licenza | BSD a 3 clausole ("Copyright © 2013–2023 Paul Hallett and PokéAPI contributors"); la licenza stessa ricorda che "Pokémon and Pokémon character names are trademarks of Nintendo" |
| Cosa usiamo | solo il file `data/v2/csv/pokemon_species_names.csv`: per ogni specie il nome inglese e il nome giapponese in katakana (lingua `ja-hrkt`) e in giapponese (`ja`). Niente immagini: le sprite dello stesso progetto restano fuori (diritti di Nintendo, Game Freak, The Pokémon Company) |
| Come | scaricato una volta (8 novembre 2026, commit `6ea97b5`) con `scripts/species_ja.py`, che scrive `data/species_ja.json` (katakana → nome inglese) con l'avviso di licenza; nessuna richiesta continua, nessuna spesa |
| A cosa serve | leggere i titoli delle vendite giapponesi che scrivono il nome in katakana ("リザードン", "ピカチュウ"): il motore aggiunge al titolo il nome inglese prima del riconoscimento (D237, protocollo §47) |
| Rischi | errori o nomi mancanti nel file (le specie nuove arrivano con qualche ritardo); un nome giapponese contenuto in un altro ("ミュウ" in "ミュウツー"): si sceglie sempre il nome più lungo; i nomi sono marchi di Nintendo, usati solo per riconoscere i titoli e non pubblicati come contenuto |

## Dove stanno i dati grezzi (D163)

Il repository `slabwise-engine` è pubblico. I dati grezzi delle fonti (tcgcharts: vendite, schede, storico, popolazioni; Alt; Pokecolor; base delle vendite; cert delle aste) non si redistribuiscono e stanno nel repository privato `slabwise-data`, con gli stessi percorsi; l'elenco è in `.github/private-paths.txt`. Le corse li scaricano e li salvano con `.github/actions/private-data`.
