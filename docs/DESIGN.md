# Design · identità di Slabwise

**Versione 2.0 · 23 ottobre 2026** (v1.1 → v2.0: "Riso pop" e Slabby, decisioni D23–D24; storico nel registro) · Vale per sito, reel e materiali. Come i pilastri, si cambia solo con una voce in `DECISIONS.md`.

## 1. Il panorama (studiato il 23 ottobre 2026)

| Sito | Aspetto | Idea di fondo | Cosa fa bene | Dove è debole |
|---|---|---|---|---|
| tcgcharts | bianco, tabellone stile CoinMarketCap, riquadri numerici, "Fear & Greed" | le carte come criptovalute | classifica densa, pagina carta con grafico e vendite | un numero solo, nessuna incertezza visibile; linguaggio da borsa crypto |
| TCGBerg | crema e arancione, ricerca gigante, ticker che scorre | "il vero valore" | pagina carta ricchissima: fascia di fiducia, evidenza, scala dei voti, deal sotto il fair value | la spiegazione di come nasce il prezzo è a pagamento (Pro); deal = sconto in %, quindi la "maledizione del vincitore" |
| Card Ladder | bianco e verde, titoli in maiuscolo | database di vendite | completezza | sito di marketing, nessuna personalità sul dato |
| PokemonPriceTracker | grigio e rosso, condensato maiuscolo | API e strumenti | quantità di dati | aspetto da prodotto tecnico |
| Collectr | nero con bagliore turchese | app per il portafoglio | atmosfera | poco dato sul web |
| Alt | nero, slab grandi in vetrina | negozio e aste | lo slab come oggetto prezioso | è un negozio, non un riferimento di prezzo |

**Cosa li accomuna tutti:**

- un solo numero presentato come verità, con l'incertezza nascosta o ridotta a un'etichetta;
- il prezzo trattato come un titolo di borsa (verde/rosso, "momentum") oppure come una vetrina;
- nessuno parla a chi compra in Europa: prezzi in dollari, nessun costo d'importazione.

## 2. La nostra posizione

**"Il valore ha un intervallo, e te lo mostriamo."** Slabwise è il perito, non la borsa né il negozio: uno strumento calmo e preciso che dice quanto vale una carta gradata, quanto ne è sicuro e se conviene comprarlo dall'Italia.

## 3. Cinque principi di design

1. **Lo slab è l'interfaccia.** Ogni carta compare come slab con la nostra etichetta (perla, striscia viola, voto grande), come nei reel. Lo slab è l'unico elemento che si muove: si inclina, il riflesso olografico lo attraversa.
2. **Ogni valore ha il suo intervallo.** La firma grafica di Slabwise è la *barra dell'intervallo di valore*: un tratto orizzontale con il valore centrale marcato. Compare ovunque compaia un prezzo: classifica, pagina carta, deal. Più la barra è corta, più il valore è sicuro. Niente punteggi inventati.
3. **Il perché è gratis.** La sezione "Perché questo prezzo" è aperta a tutti: ogni vendita compare con la sua probabilità di essere genuina e il motivo, se pesa poco. È la nostra differenza più visibile rispetto a TCGBerg Pro.
4. **I deal sono probabilità, in euro, a casa tua.** Un deal mostra la probabilità che sia davvero un affare e il costo finale in Italia (spedizione, IVA, sdoganamento). Uno sconto "troppo bello" si vede come sospetto, non come premio.
5. **Pulito e vivo.** Fondo bianco e tanto spazio, come i migliori prodotti per ragazzi (Duolingo: colori vivaci su bianco, forme tonde, il minimo di dettagli). La vita la danno il personaggio e le piccole reazioni al passaggio, non contorni pesanti. I dati restano esatti: nessuna animazione cambia un numero.
6. **Slabby ti accompagna, e ti disturba apposta.** Il personaggio di Slabwise vive in un angolo, ti accoglie, ti mostra le sezioni quando ci entri e reagisce a quello che guardi. In più è invadente per scelta (D44): ogni tanto corre attraverso lo schermo, spunta da dietro lo slab quando apri una carta, si aggrappa in alto se scorri troppo veloce, si siede sui titoli e si intromette quando cerchi. Regole che non cambiano: un dispetto alla volta e al massimo uno ogni 20–40 secondi, nessuno resta sopra un comando per più di qualche secondo, si scaccia con un clic, "Fammi stare zitto" li spegne tutti e con "riduci movimento" non succede nulla.

*(Storico: v1.0 "calma professionale", v1.1 "giocattolo preciso" in stile neo-brutalista, superato su richiesta di Oscar.)*

## 3b. Le parole del sito (D62)

Il sito è in italiano e in inglese (pulsante IT/EN in alto, scelta ricordata nel browser; la prima volta segue la lingua del browser). Nomi e set delle carte giapponesi restano sempre come sono stampati. I termini stanno in un'unica tabella, `GLOSSARY` in `prototype/v7/src/app.html` (Slabby: coppie italiano/inglese in `slabby.js`): si cambiano lì.

| Concetto | Italiano | English | Non usare |
|---|---|---|---|
| intervallo all'80% del valore | intervallo di valore, intervallo all'80% | value range, 80% range | forchetta |
| la carta nella custodia del grader | carta gradata | graded card | slab (resta solo nel marchio Slabwise e in Slabby) |
| elenco delle carte seguite | Catalogo | Catalogue | Collezione |
| annuncio che conviene | occasione, Occasioni | deal, Deals | Deal, affare |
| fascia di fiducia (D47) | Affidabilità alta / media / bassa | High / Medium / Low confidence | Vendite fresche, Stimato, Poco sicuro (restano solo come nomi interni del motore) |
| vendita giudicata anomala | vendita anomala, poco credibile | outlier sale, implausible sale | smascherata |
| vendita con probabilità alta di essere genuina | vendita attendibile | genuine / reliable sale | vendita vera |

## 4. Sistema visivo · "Riso pop"

**Atmosfera:** una stampa risograph su carta bianca. I colori sono quelli di Slabby; la firma grafica è il *fuori registro*: titoli e tessere hanno un leggero doppio ciano e magenta sfasato, che al passaggio del mouse torna a registro.

| Ruolo | Chiaro | Notte |
|---|---|---|
| Fondo | `#ffffff` | `#0b1240` |
| Superficie | `#ffffff` con bordo `#e3e6f7` | `#121b58` |
| Testo | `#0E1A5C` blu notte | `#f2f4ff` |
| Testo secondario | `#4a5390` | `#aeb5e6` |
| Blu inchiostro (marchio, azioni, forchetta) | `#1D3FD1` | `#6f86ff` |
| Magenta (fuori registro, attenzione) | `#FF2E93` (testo: `#c8106a`) | `#ff5ca9` |
| Ciano (fuori registro, informazione) | `#2EE6FF` | `#2EE6FF` |
| Giallo (perno della forchetta, evidenza) | `#FFC93C` | `#FFC93C` |
| Menta (su, affare) | `#39F2A6` (testo: `#0a8a58`) | `#39F2A6` |

**Caratteri:** Mochiy Pop One per titoli e grandi numeri (lo stesso del character sheet), M PLUS Rounded 1c per il testo, JetBrains Mono solo per piccole etichette.

**Movimento:** morbido (`cubic-bezier(.22,1,.36,1)`), 200–400 ms, solo `transform`, `opacity` e ombre. Con "riduci movimento" tutto si ferma, Slabby compreso.

**Componenti chiave:**

- `Slab`: lo slab con etichetta Slabwise e immagine TCGdex della carta.
- `Forchetta`: barra con estremi all'80% e centro marcato; testo "€3.180 · da €2.950 a €3.420".
- `Vendite`: punti sul grafico colorati per probabilità genuina (pieno = genuina, vuoto = poco credibile, ambra = sospetta).
- `Probabilità deal`: anello con la percentuale, accanto allo scontrino del costo in Italia.
- `Scontrino`: righe prezzo, spedizione, IVA, sdoganamento, totale, in monospazio.

## 5. Esperienza

- La pagina carta risponde a tre domande, in quest'ordine: **quanto vale** (intervallo di valore), **quanto ne siamo sicuri** (perché, vendite), **conviene comprarla ora dall'Italia** (deal e costo finale).
- La ricerca è sempre raggiungibile (tasto `/`).
- Mobile prima: la pagina carta si legge in una colonna con lo slab in alto.
- Dati dimostrativi sempre segnalati da un'etichetta visibile (P14).

## Prova v5 "Promo TCG" (D25, da confermare)

In prova sopra la v2.0: fondo cielo ciano con scintille bianche e griglia leggera; titoli in M PLUS 1 Black (gotico squadrato, come il volantino) gialli, inclinati in avanti con contorno blu notte e anello bianco; etichette come nastri rossi inclinati; pannelli bianchi con doppio bordo (bianco dentro, blu notte fuori); bottoni lucidi giallo-arancio con riflesso al passaggio; adesivi a stella. Corpo del testo in M PLUS 1 Bold; prezzi, date e nastri in M PLUS 1 Black inclinato. I numeri restano leggibili (niente effetti sui dati), il movimento rispetta `prefers-reduced-motion`, Slabby resta la guida. Si riprende solo il linguaggio grafico, mai personaggi o marchi altrui.

## Prova v6 "Trainer Pop" (D31, da confermare)

- **Testata illustrata a strati**: cielo pastello con raggiera, nuvole, slab che fluttuano, scintille, Slabby grande al centro con il suo fumetto. Gli strati si spostano a velocità diverse con il mouse e lo scorrimento; con "riduci movimento" restano fermi.
- **Barra in alto scura** con il logo su una linguetta bianca tagliata in diagonale e la ricerca a pillola.
- **Titoli di sezione** gialli con bordo scuro, inclinati; dietro, una parola inglese gigante solo contornata (ERAS, SLABS, WEEKLY, DEALS, METHOD).
- **Schede** quasi quadrate con una striscia colorata in alto che dice l'era: Wizards rosso, Spada e Scudo blu, Scarlatto e Violetto viola, Mega Evoluzione verde.
- **Filtri** come linguette con la riga sotto; **pulsanti** neri a pillola con il cerchio giallo e la freccia.
- **Carattere**: M PLUS 1, gotico giapponese squadrato, dal medio al nerissimo.

## Slabby sostituibile

Slabby vive in `prototype/character/slabby/character.json`, unica fonte (D37): colori, carattere dei fumetti e 7 pose (SVG interno o immagini nella cartella). Per ridisegnarlo si cambia quel file seguendo il README della cartella.

