# Metodo · Modello a Valore Latente (LVM)

**Versione 1.14 · 30 ottobre 2026** (v1.14 = v1.10 più la scala dei voti a gradini con priore informata dalle popolazioni PSA, D101–D103, protocollo §20, risultati in `results/v1.14/`; adottata prima della prova prospettica L8, che può riportarla alla v1.10; v1.10 = v1.9 più una quota di 15 osservazioni per voto nella finestra di ogni carta, D78–D82, protocollo §15, risultati in `results/v1.10/`; v1.9 = v1.8 più scarti di sede per carta e gerarchici, D70–D71, protocollo §14, risultati in `results/v1.9/`; v1.2 adottata con D32; v1.5 = v1.2 più fasce di fiducia e limite allo spostamento senza vendite, D49, protocollo §8; v1.8 = v1.5 più un terzo punto di partenza della stima dai voti della carta, D67–D68, protocollo §13; la v1.1 è in `results/v1.1/`, la v1.5 in `results/v1.5/`, la v1.8 in `results/v1.8/`) · Codice: `slabwise/model.py`, `slabwise/calibrate.py`, `slabwise/backtest.py` (deal)

Questo documento descrive *esattamente* ciò che fa il codice. Se divergono, ha ragione questo documento e il codice va corretto (pilastro P20).

## 1. L'idea in una frase

Ogni carta ha un **valore latente** che nessuno osserva direttamente. Ogni vendita è una misura rumorosa di quel valore, deformata da voto, copia, piattaforma e tempo, e a volte non è proprio una misura (contaminazione). Il fair value è la stima migliore del valore latente oggi, data *tutta* l'evidenza, con l'incertezza che ne deriva.

I concorrenti costruiscono il prezzo con una pila di regole: finestre, soglie, recinti, pesi e aggiustamenti, ognuno con parametri scelti a mano. Noi scriviamo un solo modello e tutte quelle regole ne diventano conseguenze, con parametri stimati dai dati.

## 2. Il modello

Per una carta *c* della sua era *e*, una vendita pulita *i* di voto *g*, in lingua *l*, nella settimana *tᵢ*, su una piattaforma *v*, di una copia con cert *k*:

```
yᵢ = L_c + d_cg + λ_cl + q_k + o_v − β_c · (F_e(oggi) − F_e(tᵢ)) + εᵢ          (y = log del prezzo)
```

Una **carta** è una stampa precisa: set, numero, edizione (1st Edition, Shadowless, Unlimited) e, per giapponese, coreano e cinese, la stampa asiatica, che è una carta a sé del catalogo (D28).

| Termine | Significato | Come si stima |
|---|---|---|
| `L_c` | log del valore del voto di riferimento (10) **oggi** | dalle vendite |
| `d_cg` | distanza del voto *g* dal 10 per questa carta (`d_c10 = 0`) | dalle vendite. Dalla v1.14 (D101) la priore è sui tre **gradini** 10→9, 9→8, 8→7, indipendenti `N(m_k + b_k·(x_ck − x̄_k), s_k²)`, e le distanze sono le loro somme (quindi correlate: una carta con gradini alti piatti ha anche la PSA 7 vicina); `x_ck` = log(popolazione PSA del voto basso / del voto alto) da tcgcharts, assente se la popolazione manca. Fino alla v1.10: priore comune `N(μ_g, s_g²)` su ogni distanza |
| `λ_cl` | scarto della lingua europea *l* (tedesco, francese, italiano, spagnolo, portoghese, olandese) rispetto all'inglese (`λ_c,en = 0`) | dalle vendite in quella lingua, con priore comune a tutte le carte `N(λ̄_l, s_λl²)`; senza vendite nella lingua vale lo scarto comune con la sua dispersione |
| `q_k` | qualità della singola copia (centratura, estetica) | solo per i cert venduti più di una volta (vendite ripetute); altrimenti è parte del rumore |
| `o_v` | scarto di ogni sede (asta, prezzo fisso) rispetto a eBay | dalla v1.9 (D71) **per carta e gerarchico** come le lingue (`venue_gaps=True`, già provato come v1.6b, D53): ogni carta ha il suo scarto con priore comune `N(μ_v, s_v²)`, e `μ_v`, `s_v` si imparano dalle carte che fissano bene il proprio. Fino alla v1.8 era la media mobile dei residui (D27), che con le vendite eBay di Alt dava −0,122 per le aste contro −0,059 del confronto diretto (D70). La sede "prezzo fisso" (D51) resta senza vendite |
| `F_e` | fattore di mercato dell'era (l'indice dell'era) | ogni settimana, da tutte le carte dell'era |
| `β_c` | quanto la carta segue la sua era | dalle vendite, priore `N(1, 0,3²)` |
| `εᵢ` | rumore della transazione | varianza `σ_v²` per piattaforma |

**Dinamica.** `L_c` e ogni `d_cg` seguono un cammino casuale (varianze settimanali `q_c`, `q_d`). Il codice prevede una deriva **propria di ogni carta**, `q_c = q_L · κ_c`, ma nella v1.2 è **spenta** (`card_drift=False`, quindi `κ_c = 1` e `q_c = q_L`) perché peggiorava l'errore nel controllo sul seme 1 (D30). Quando è accesa:, dove `κ_c` = (52·q_L + Σ(rᵢ² − parte non dovuta alla deriva)) / (52 + Σ settimane coperte) ÷ q_L, calcolato sugli errori di previsione delle vendite nuove della carta con probabilità genuina > 0,8, limitato a [0,5; 8]. Le 52 settimane sono la forza del priore: senza evidenza `κ_c = 1` (D29). Gli scarti di lingua non hanno deriva. Due vendite vicine nel tempo condividono quasi tutta la deviazione dal valore di oggi, quindi gli errori **non sono indipendenti**: la covarianza tra le vendite *i* e *j* è `q_c · min(etàᵢ, etàⱼ)` (più `q_d · min(…)` se hanno lo stesso voto). Il calcolo usa questa covarianza esatta (minimi quadrati generalizzati). È matematicamente il valore "oggi" di un filtro di Kalman con smoother, ed è ciò che rende le forchette oneste.

**Conseguenze che i concorrenti ottengono con regole a mano:**

- *Memoria*: una vendita vecchia pesa meno perché da allora il valore si è potuto muovere. Una carta che vende spesso ha memoria corta, una carta rara ha memoria lunga. Nessun peso fisso per età; per il calcolo però ogni carta usa solo le osservazioni delle ultime 156 settimane (`window`) e al massimo le ultime 80 (`max_obs`). Dalla v1.10 (D82) la finestra tiene in più le ultime 15 osservazioni di ogni voto (`grade_keep=15`): senza, con molte vendite recenti restavano quasi solo PSA 10 e 9 e i voti bassi tornavano al valore comune delle distanze (D78).
- *Prestito dalle carte simili*: il fattore d'era sposta anche le carte ferme, con un'incertezza che cresce col tempo.
- *Scala dei voti*: tutti i voti di una carta si stimano insieme. Una vendita di PSA 9 informa il PSA 10 attraverso `d_c9`, con la sua incertezza.
- *Vendite ripetute*: quando lo stesso slab torna sul mercato, la sua qualità individuale si cancella, come negli indici immobiliari ibridi (Case & Quigley).

## 3. Vendite anomale: probabilità, non soglie

Ogni vendita è genuina oppure contaminata. La contaminazione è a due lati, con densità piatte sul residuo `r = y − previsione`:

```
P(genuina) = (1−a−b)·N(r; 0, varᵢ) / [ (1−a−b)·N(r; 0, varᵢ) + a·U_basso(r) + b·U_alto(r) ]
U_basso uniforme su (−4, 0), U_alto uniforme su (0, 2) in unità di log
```

- `a` e `b` (quote di contaminazione verso il basso e verso l'alto) **si imparano dai dati** e sono separate per vendite con cert verificato (dove la contaminazione verso il basso è quasi impossibile) e senza.
- Il fit è iterativo: a ogni giro il rumore di ogni vendita viene diviso per la sua probabilità di essere genuina. Le vendite poco credibili pesano poco ma non spariscono (P8), e ognuna conserva la sua probabilità.
- **Cambi di mercato (P9).** Il fit parte da tre punti: la stima precedente, una mediana robusta delle vendite recenti con le distanze tra voti del valore comune, e (v1.8, D67–D68) il livello dalla mediana delle vendite PSA 10 con la distanza di ogni voto che ha almeno 2 vendite presa dalla mediana delle sue vendite. Tiene la soluzione con la verosimiglianza più alta. Il terzo punto serve quando un voto sta lontano dal valore comune (es. PSA 7 delle carte moderne): partendo dagli altri due le sue vendite risultavano tutte anomale e la stima restava bloccata. Se più vendite indipendenti indicano un nuovo livello, la soluzione "il mercato è cambiato" vince da sola. Se invece è una sola vendita, o un gruppo di vendite senza cert in contraddizione con quelle certificate (inondazione di falsi), vince "contaminazione".

## 4. Il fattore d'era (indici)

Ogni settimana, prima di aggiornare le carte, per ogni vendita di una carta già stimata si calcola lo scarto dalla previsione. L'incremento del fattore è la media pesata robusta di questi scarti (peso = probabilità genuina ÷ varianza; scarti tagliati a ±2 deviazioni standard), con un priore `N(0, τ_f²)` sull'incremento settimanale:

```
ΔF_e = Σ wᵢ·β_c·rᵢ / (Σ wᵢ·β_c² + 1/τ_f²)
```

Anche l'incertezza dell'incremento, `1/(Σ wᵢ·β_c² + 1/τ_f²)`, si accumula settimana per settimana (`V_e`). Quando una vendita viene riportata a oggi con l'indice, l'errore dell'indice da quel giorno a oggi entra nella sua varianza, ed è condiviso con le vendite più recenti.

`F_e` serve a spostare le carte che non vendono. **Non è ancora un indice pubblicabile**: nel backtest v1.1 cattura circa metà dei movimenti veri dell'era (es. +30% contro +65% nel rialzo simulato), perché il priore settimanale centrato sullo zero frena i movimenti prolungati. I fair value restano accurati perché ogni carta recupera con le proprie vendite.

**v1.20 (adottata con D210, protocollo §37; verifica prospettica Y7 in sospeso).** v1.15 più tre cose: (1) le vendite con lo storico lungo di tcgcharts entrano nei prezzi; (2) **salti di un singolo voto** (`grade_jump`): a ogni nuovo calcolo di una carta, per ogni voto, le vendite di quel voto delle ultime 4 settimane (dopo l'ultimo salto dello stesso voto) si confrontano con la previsione della stima precedente; se sono almeno 3, la mediana degli scarti in log è oltre ±0,35 e almeno il 75% ha lo stesso segno e almeno metà della mediana, si registra un salto del voto alla data della prima di quelle vendite con varianza J = mediana²; le vendite di quel voto precedenti il salto ricevono J in più nella varianza e nella parte condivisa tra loro, quelle degli altri voti no; (3) la regola di revisione (D98) confronta la stima con la mediana delle vendite del voto degli ultimi 30 giorni se sono almeno 5, altrimenti delle ultime 5 delle 13 settimane (soglia: più di 2 volte). Il salto per carta (v1.17) e la deriva per carta restano spenti.

**v1.3 (provata, non adottata: D36).** L'incremento settimanale del fattore ha un priore centrato sulla **pendenza recente** invece che sullo zero: pendenza `s_e` con cammino casuale smorzato (`s_e ← 0,9 · s_e + ζ`, `ζ ~ N(0, τ_s²)`), incremento `= s_e + η`, `η ~ N(0, τ_f²)`. Ogni settimana un filtro di Kalman combina il priore con l'incremento misurato dalle vendite (media pesata dei residui, varianza 1/Σpesi). Senza vendite il fattore prosegue con la pendenza, che si smorza. `τ_s` si stima con la ricerca a griglia {0; 0,001; 0,003; 0,006}; con `τ_s = 0` il fattore è quello della v1.2. Nel protocollo ha migliorato tutte le metriche ma ha catturato il 65% dei movimenti veri, sotto la soglia dell'80% (I1): il codice resta, spento (`τ_s = 0`), e il metodo in uso è la v1.2.



## 4b. Indice d'era pubblicato (v1.4, D38–D39; base comune da D121, gruppi da D154)

- **Gruppi** (D154, prima D121): le cinque ere in uso nel mercato, le stesse delle schede del sito: **Vintage** (Base, Gym, Neo, Southern Islands, promo Wizards, Best of Game), **Classica** (e-Card, EX, POP, promo Nintendo), **Di mezzo** (Diamante e Perla, Platino, HeartGold SoulSilver, Call of Legends, Pokémon Rumble, Nero e Bianco), **Moderna** (XY, Sole e Luna), **Contemporanea** (Spada e Scudo, Scarlatto e Violetto, Mega Evoluzione); le stampe giapponesi nel gruppo Giappone (D142). Le carte dei set promo (Black Star Promos) restano nel catalogo ma non entrano negli indici d'era e generale (`slabwise/series.is_promo`). Un solo criterio d'ingresso per tutte le ere (D97, D150); la coda non riempie più le ere (D139 superata).
- **Calcolo con lo storico lungo** (D149, protocollo §29; D210): prezzi e indici pubblicati si calcolano con lo stesso passaggio del motore sulle vendite che includono lo storico lungo di tcgcharts (dal 1° luglio 2022); ogni serie d'indice parte dalla prima revisione con almeno 5 voci (15 per il generale). Da D228 è letteralmente un solo passaggio: la costruzione ritaglia i propri indici (`slabwise/index_full.py`) invece di ripetere il calcolo.
- **Riconoscimento del set nei titoli** (D153): `auction_titles.set_re` costruisce l'espressione dal nome del set con parole brevi facoltative ("Call of Legends"), parole composte divisibili ("Fire Red"), le sigle FRLG e HGSS e, per i set Black Star Promos, la sola parola "promo" (il numero con prefisso, es. HGSS03 o DP38, indica già il set). Si usa per le carte che entrano da D153 in poi.
- **Titoli inglesi, correzioni D235** (protocollo §45): "Mega Evolutions" vale come il set Mega Evolution e non scarta il titolo; "box" non scarta dopo "elite trainer" (promo delle Elite Trainer Box); per una promo con numero con prefisso ("SM162", "SWSH050") valgono gli anni dell'intera serie (XY 2013–2016, SM 2017–2020, SWSH 2019–2023, BW 2011–2013, HGSS 2010–2011, DP 2007–2009, SV 2023–2026); un anno fra parentesi ("(2023)") non è una quantità e non scarta il titolo. Numero senza # né / (D236, protocollo §46): se il titolo non ha numeri con # o /, vale anche il numero scritto da solo (1–3 cifre), esclusi il voto (dopo "PSA", "Gem Mint", "Mint", "NM-MT", "Grade"), gli anni e la popolazione ("Pop 66").
- **Titoli giapponesi** (D134, D158, D168, D170, D214): una vendita è di una stampa giapponese del catalogo se il titolo contiene il nome (inglese o giapponese) e numero/totale, oppure il numero e il set. Il set si riconosce dal nome inglese o dagli alias dei set vintage, dalla sigla del nostro codice come parola intera (`ja:m3-086` → "m3", `ja:sv-p-288` → "sv-p"; non per i set con nome) e dal nome giapponese del set della scheda. Un trattino prima di gx/ex/v/vmax/vstar vale uno spazio e gli apostrofi non contano. Esclusi lotti, sigillati, firmate, altri grader, coreane e cinesi, "No Rarity" e, in inglese e in giapponese, i voti con riserva ("PSA 9 OC", MK, ST, PD, MC; D221). Più carte possibili → nessuna. Promo giapponesi (D231): il numero scritto "207/XY-P" vale come numero; il set di una serie promo (XY-P, SM-P, S-P, SV-P, M-P, BW-P, DP-P) si riconosce anche da "XY Promo", "Sun & Moon Promo", "XY-P"…; "Poncho-wearing" vale anche "Poncho Wearing" e "Poncho". Promo dal numero (D233, D234): se il nome non si legge (spesso è scritto in giapponese, "ポンチョを着たピカチュウ #207/XY-P"), il numero di promo con il suo codice basta per la carta con quell'id; il titolo resta ambiguo se nomina un'altra carta del catalogo, salvo che quel nome sia già contenuto nel nome della carta ("Pikachu" in "Poncho-wearing Pikachu"). Sigla del set (D238 a, protocollo §48b): un titolo senza "Japanese" che contiene, come parola intera, la sigla di un set giapponese del catalogo che finisce con una lettera (SV4a, SV5a, M2a, M1S, SM11b…) o "M" e una cifra (M2, M3) va alla via giapponese se nessuna carta inglese del catalogo lo prende; SV2a non conta (stessi numeri del 151 inglese). Sigle coreane brevi (D239): "Kor", "KR" come parola intera scartano il titolo anche nella via giapponese. Numero senza # né / (D238 b, protocollo §49): come per i titoli inglesi (D236), se il titolo non ha numero con #, /, "No." o numero di promo.
- **Ingresso di una carta nuova** (D97, D232): almeno 27 vendite PSA 7–10 riconosciute (il 90% di 30) negli ultimi 365 giorni, su tutte le piattaforme elencate dalla fonte (eBay, aste, marketplace); almeno 5 vendite in almeno 2 voti (1 per una giapponese); almeno il 60% dei titoli riconosciuti; poi il controllo del motore (R1/E2r). Le carte già nel catalogo non cambiano. Nei titoli giapponesi "box" scarta il titolo solo da solo (box sigillato), non in "Special/Stamp/Gift/Premium/Collection/Golden Box" (§42). Sulla pagina, un voto con meno di 5 vendite negli ultimi 90 giorni porta la frase "Poco scambiata: il prezzo segue l'ultima vendita pagata, del …".
- **Carte solo giapponesi** (D231): le giapponesi della classifica per capitalizzazione senza gemella inglese entrano in coda come carte a sé (D28), per le serie promo e per le serie vintage; stessi controlli delle altre. Per una giapponese le 30 vendite riconosciute possono stare in un solo voto (spesso solo PSA 10); i voti senza vendite restano nascosti. Le serie promo giapponesi seguono l'era della serie (XY-P e SM-P Moderna, S-P, SV-P e M-P Contemporanea, BW-P e DP-P Di mezzo) e, come le promo inglesi, restano fuori dagli indici.
- **Stampa giapponese e carta inglese** (D152): il collegamento tra le due serve a cercare le vendite; il sito le presenta come "la stessa carta" solo se TCGdex dà lo stesso Pokémon e l'illustrazione coincide (dHash 16×16 sul riquadro dell'illustrazione, distanza ≤ 80/256; `slabwise/print_match.py`, `scripts/ja_audit.py`). Una riga che è un altro Pokémon esce dalla coda (`scartata`). Se più stampe giapponesi hanno lo stesso numero, si tiene quella con l'illustrazione più vicina (D179).
- **Abbinamento automatico delle stampe giapponesi** (D158, D214, D215, `scripts/ja_complete.py`): per ogni carta inglese si cercano su TCGdex le giapponesi dello stesso Pokémon e illustratore e si confrontano i disegni (distanza ≤ 80/256). Se TCGdex non ha l'immagine, si può usare quella di una pagina tcgcharts con lo stesso numero solo se il set ha lo stesso anno di uscita; lo stesso vale per la pagina vendite. Una stampa giapponese è gemella di una sola carta inglese: se due la reclamano, la tiene quella con il disegno più vicino e l'altra resta "doppione".
- **Giappone a parte** (D142): le stampe giapponesi non entrano negli indici inglesi (generale, ere, set); formano il gruppo "Giappone", con le stesse regole.
- **Tre livelli** (D136): un **indice generale** su tutto il catalogo (paniere di 60 voci, D169; prima 30), gli **indici d'era** e Giappone (20 voci, D169; prima 10) e gli **indici di set** per i set con almeno 8 carte nel catalogo (10 voci). Stesso algoritmo; cambia solo il gruppo.
- **Componenti e statistiche** (D136): per ogni voce del paniere attuale peso (1/n), valore, variazione in 4 settimane del log fair value e contributo (variazione ÷ n, in log: la somma dei contributi è il movimento dell'indice nelle 4 settimane se il paniere non è cambiato); rendimenti a 1, 4, 13, 26 e 52 settimane e da inizio anno; volatilità = deviazione standard delle variazioni settimanali in log nelle ultime 26 settimane × √52; perdita massima dal picco su tutta la serie.
- **Base comune** (D121): un indice si pubblica quando ha almeno 26 settimane; tutti valgono 100 nella stessa settimana, la prima in cui l'ultimo indice pubblicato ha cominciato. Così due ere si confrontano a colpo d'occhio.

Codice: `slabwise/index.py`. Separato dal fattore `F_e` usato per le stime, che non cambia.

- **Paniere**: ogni 13 settimane (dalla 26ª), per ogni era, le combinazioni carta-voto con almeno 6 vendite con probabilità genuina > 0,5 nelle 13 settimane precedenti; al massimo 10, le più vendute. Si usa solo il passato.
- **Pesi uguali**: nessuna carta pesa di più perché costa di più (al contrario degli indici alla Dow Jones come quello di GoCollect).
- **Livello**: concatenato. Ogni settimana l'indice (in log) si muove della media, sulle voci del paniere, della variazione del log fair value tra questa settimana e la precedente. Il concatenamento fa da divisore: l'indice resta continuo quando il paniere cambia. Parte da 0 (cioè 100) quando l'era ha il primo paniere.
- **Verifica** (protocollo §7): segue il 104% dei movimenti veri su 12 settimane (mediana), correlazione 0,81. Nelle ere con poche carte liquide è più rumoroso.

## 5. Parametri: cosa si stima e cosa è un priore

| Parametro | Stima | Come |
|---|---|---|
| `σ_e`, `q_L` | dai dati | **vendite ripetute** dello stesso cert nelle prime 52 settimane: al netto dell'indice, Var(y₂ − y₁) = 2σ_e² + q_L·intervallo; retta robusta (mediane dei quadrati per fasce di intervallo) → intercetta e pendenza. Se le coppie sono meno di 200, si passa alla riga sotto |
| `q_d`, `σ_q`, `τ_f` | dai dati | ricerca a coordinate (2 passate) che massimizza la densità predittiva della vendita successiva sulle prime 52 settimane; poi congelati (P7, P11). Non serve la verità, quindi vale anche sui dati reali |
| `ν` (code dei gradini, v1.15) | priore | 4 gradi di libertà: la priore di ogni gradino è una t di Student con media `m_k + b_k·x` e scala `s_k`; nell'IRLS la precisione del gradino si moltiplica per (ν+1)/(ν+z²) (D124). Le stampe varianti senza popolazioni usano quelle della carta base (`variant_pops`) |
| `m_k`, `b_k`, `s_k` (gradini, v1.14) | dai dati, ricalcolati ogni settimana | per ogni gradino, l'ultima stima di ogni carta che lo misura bene (varianza < metà di `s_k²`): media pesata, pendenza `b_k` con regressione pesata sulle popolazioni (almeno 8 carte con popolazione, pendenza ristretta verso 0), dispersione dai residui meno l'incertezza media, in [0,12; 0,6]. Con meno di 8 carte: media da `μ_g`, dispersione 0,45, nessuna pendenza (`step_prior`, `pop_steps`) |
| `μ_g`, `s_g` (scala dei voti) | dai dati (la variante per era, `era_gaps=True`, è provata e spenta: D55–D58) | media e dispersione correnti delle distanze tra voti delle carte ben misurate; la dispersione somma la varianza delle stime e la loro incertezza media (legge della varianza totale) |
| `o_v` | dai dati | per carta, gerarchico (v1.9, D71); fino alla v1.8 media corrente dei residui delle vendite genuine all'asta (D27) |
| `κ_c` (deriva per carta) | spenta nella v1.2 (D30) | vedi §2, Dinamica |
| `λ̄_l`, `s_λl` (scarti di lingua) | dai dati | come la scala dei voti: carte la cui stima ha varianza < metà di `s_λl²`, dopo 10 carte; iniziali −0,6 e 0,5; dispersione limitata a [0,08; 0,8] |
| `a`, `b` | dai dati | conteggi correnti delle probabilità a posteriori, con oblio dopo ~2.000 vendite |
| `σ_a` | priore | 0,08 (meno rumore all'asta); da stimare quando avremo dati d'asta |
| `μ_g` iniziali | priore debole | −0,8 / −1,35 / −1,7, sostituiti dai dati dopo 30 carte |
| `β` | priore | `N(1, 0,3²)` |
| supporto della contaminazione | scelta di modello | (−4, 0) e (0, 2) in log: copre prezzi da 1/55 a 7 volte il valore |

Calibrazione riusata (D228, solo ingegneria): il risultato della calibrazione si salva con una chiave che riassume le vendite della finestra di addestramento, le opzioni e il codice del motore; a chiave uguale si rilegge, identico, invece di rifare i giri.

Ripartenza da uno stato salvato (D244, solo ingegneria): il ciclo settimanale salva lo stato del motore e degli indici dopo le settimane W−2, W−5, W−9, W−14 e W−27 (al massimo 6 stati). Una ricostruzione riparte dallo stato più recente le cui settimane hanno esattamente le stesse vendite (impronta cumulativa delle vendite pulite settimana per settimana, più catalogo, parametri, versioni e codice del motore) e rifà solo le settimane dopo; con un'impronta diversa, o uno stato illeggibile, rifà tutto. Stesse operazioni nello stesso ordine: il risultato coincide con il calcolo completo.

## 6. Uscite

- **Fair value** di ogni atomo: `exp(L_c + d_cg + β_c·(F_e(oggi) − F_e(ultimo fit)))`, cioè una copia tipica venduta su eBay, in USD. Lo spostamento con l'era dall'ultima stima con vendite, `β_c·(F_e(oggi) − F_e(ultimo fit))`, è limitato a ±log 3 (al massimo ×3 o ÷3; `roll_bound`, D47–D49); l'intervallo non cambia. Nel mercato simulato il limite non scatta mai: protegge i dati reali da un fattore d'era stimato su poche vendite.
- **Forchetta all'80%**: ±1,2816 deviazioni standard a posteriori, comprese la deriva dall'ultimo fit e l'incertezza del fattore. Nel backtest deve contenere il valore vero tra il 75% e l'85% delle volte (P10).
- **Fascia di fiducia** di ogni valore (D47): "Vendite fresche" se il voto ha almeno 3 vendite nelle ultime 13 settimane (passate dal livello di identità) e la mezza forchetta in log (1,2816 · sd) è ≤ 0,20; "Stimato" se ha almeno 1 vendita nelle ultime 13 settimane oppure mezza forchetta ≤ 0,35; altrimenti "Poco sicuro". Sul sito le tre fasce si chiamano "Affidabilità alta / media / bassa" (in inglese "High / Medium / Low confidence", D62). Nel protocollo (§8) l'errore mediano è circa 3,6% / 7,5% / 23% nelle tre fasce. Codice: `tier_of` in `slabwise/backtest.py`.
- **Probabilità genuina** di ogni vendita usata, con il motivo leggibile.
- **Indice per era** `F_e`.

## 7. Deal (P15)

Per un annuncio con prezzo chiesto *A*:

1. **Identità**: se l'annuncio mostra un cert che contraddice carta o voto del titolo, è scartato.
2. **Credibilità dell'annuncio**: stessa miscela a due lati. La dispersione onesta dei prezzi chiesti (`μ_l`, `s_l`) si impara solo dagli annunci con cert verificato, poi si stima la quota di spazzatura negli annunci senza cert (EM non supervisionato, solo sulle settimane di addestramento).
3. **Valore della copia, contro la "maledizione del vincitore"**: anche il prezzo chiesto è un indizio del valore, perché i venditori onesti prezzano vicino al mercato. La stima del valore della copia combina il modello `N(m, sd² + σ_q²)` e il prezzo chiesto `N(A − μ_l, s_l²)`.
4. **Probabilità di deal** = P(annuncio genuino) × P(valore della copia ≥ A × 1,10). Si segnala se è ≥ 0,80. La soglia coincide con la precisione voluta: con probabilità calibrate, 8 segnalazioni su 10 sono giuste.
5. **Copertura degli annunci (D135).** Gli annunci eBay si cercano solo per le prime N carte inglesi del catalogo, in ordine di ingresso (N = 70 fino al 9 novembre, 300 dopo; `slabwise/ebay_budget.py`). Le altre carte e le stampe giapponesi hanno il prezzo ma non le occasioni (`deals_off`), e la scheda lo dice.

Il costo finale in Italia (IVA, dogana, spedizione, cambio BCE) si applica al prezzo chiesto prima del passo 3, in un modulo separato (P5).

## 8. Rollup per set ed era (da implementare dopo la fonte della popolazione)

- **Market cap di collezione** di un gruppo = Σ fair value × popolazione, su tutti gli atomi seguiti.
- **Scomposizione della variazione** tra due date: effetto prezzo = Σ pop₀·(V₁ − V₀); effetto nuovi slab = Σ (pop₁ − pop₀)·V₁.
- **Concentrazione**: quota delle prime 3 carte. **Copertura**: carte seguite ÷ carte del set.
- **Indice d'era** (da costruire, v1.2): regressione robusta a vendite ripetute / effetti temporali sulle vendite pulite, pesate per probabilità genuina; non una somma di market cap, quindi non lo muovono né i nuovi slab né il cambio di composizione.

## 8b. Misure di mercato mostrate sul sito, fuori dai prezzi (D190, D194)

- **Gem Rate a confronto** (pagina della carta; D211): PSA 10 ÷ totale PSA della carta, contro la mediana delle carte della stessa lingua con Gem Rate noto: dello stesso set (almeno 3) e della stessa era (almeno 5); la frase dice quante carte. Era delle stampe giapponesi: quella della stampa inglese (codici sv, m, s → Contemporanea; sm, xy → Moderna; bw → Di mezzo; set con nome, cioè i vintage → Vintage). Se la quota di PSA 10 dalle nostre popolazioni e quella dalle conte di GemRate differiscono di più di 5 punti (D212), la pagina scrive "Gem Rate incerto" con le due quote e la carta non entra nei confronti.
- **Vendite incompatibili tra eBay e aste** (`venue_split`; D226): con almeno 2 vendite eBay e almeno 1 d'asta nelle ultime 13 settimane, se le mediane differiscono di più di 5 volte il voto va in revisione e la pagina mostra le due mediane.
- **Coerenza** (`scripts/coherence_check.py`; D211): controlli C1–C10 su `real.json` dopo ogni costruzione, rapporto in `results/coherence.json`; non blocca la pubblicazione.
- **Gemma nascosta** (`prototype/build_real_data.py`, `rarity_price`; D209): PSA 10 con almeno 3 vendite in 13 settimane, non in revisione; log valore su log popolazione PSA 10, pendenza comune e livello per era e lingua (gruppi ≥ 8); x = e^residuo; gemma se x < 0,5 e popolazione ≤ mediana del gruppo. Il rapporto giapponese/inglese usa la retta unica.
- **Quante vendite ci sono** (`prototype/build_real_data.py`, `sales90`, `disp90`, `in15`; D208, D223): per ogni voto, vendite pulite delle ultime 13 settimane (dopo lo strato d'identità); la pagina mostra "una copia ogni 91/n giorni in media" in colore neutro e, con almeno 5 vendite, la quota di quelle vendite entro il 15% dallo Slabprice (`in15`: |log prezzo − log valore| ≤ log 1,15). `disp90` (mediana di |log prezzo − log valore|) resta nei dati.
- **SlabRange** (`prototype/build_real_data.py`, `slo`, `shi`; D224): dove finiscono le vendite, valore × exp(±1,2816 · √(s² + σe² + σq²)), con s la sd della stima del voto e σe, σq del motore; è la banda della pagella. Misurata il 7 novembre 2026 sulle vendite pulite degli ultimi 30 giorni: dentro 83,3% (68% sotto 50 $, 84% tra 50 e 200 $, 88% tra 200 e 1.000 $, 76% sopra 1.000 $). `lo`, `hi` (intervallo all'80% della stima del valore) restano nel grafico "Quanto ne siamo sicuri?", nei bollini (D47) e nelle occasioni.
- **Se la vendo oggi** (`n30`, `q30`; D223): vendite pulite degli ultimi 30 giorni del voto; con almeno 5, i percentili 10, 25, 75, 90 ("una su dieci sotto", "metà tra", "una su dieci sopra"); con meno, la pagina rimanda allo SlabRange. Nessun prezzo "veloce" o "paziente": tempi di vendita non misurati.
- **Slabvalve** (`scripts/ebay_listings.py`, `scripts/deals_refresh.py`, `on_sale`; D225): copie in vendita adesso = annunci eBay Compralo Subito riconosciuti per carta e voto (EBAY_US, EBAY_IT, EBAY_DE, spedizione verso l'Italia), solo per le carte cercate su tutti e tre i mercati nel giorno (budget D135); "almeno" se una ricerca supera i 200 risultati. Mesi di scorta = in vendita / vendite pulite degli ultimi 30 giorni (`n30`): chiusa < 1, aperta > 3, in equilibrio tra 1 e 3; vendite zero con copie in vendita = aperta; colore neutro. Sostituisce il bollino "Liquida" e il Rubinetto tra i segnali del verdetto.
- **Rubinetto**: abbinamento alle righe GemRate per numero e nome; stampa base = etichetta vuota, Base, Holo, Unlimited o una rarità moderna (D207).
- **Slab-Meter** (`prototype/build_real_data.py`, `slabmeter`): media di quattro punteggi da 0 a 100. (1) Quota di carte inglesi in rialzo tra quelle che si muovono più di ±0,5% in 30 giorni, sul voto con più vendite in 90 giorni tra quelli con variazione mostrata (D161), non in revisione; (2) vendite pulite dell'ultima settimana completa contro la media delle 8 prima: 50 + 50·clip((r − 1)/0,5); (3) carte al massimo contro carte al minimo delle ultime 52 settimane di Slabprice (stesso voto; 50 se nessuna); (4) SlabDex in 4 settimane: 50 + 50·clip(Δ/0,10). Gradi = 33 + 0,09 × punteggio. Stati: ≥80 esplode, 60–80 caldo, 40–60 tiepido, 20–40 freddo, <20 gelo.
- **Rubinetto** (`scripts/gemrate_tap.py`): dalle pagine dei set di GemRate (D189), per ogni carta abbinata per numero, nome e stampa: nuovi PSA 10 negli ultimi 30 giorni (`c10_diff_p1`) contro PSA 10 venduti in 30 giorni nei nostri dati (media delle ultime 13 settimane × 30/7). Rapporto > 1,5 aperto, 0,67–1,5 in equilibrio, < 0,67 chiuso; senza PSA 10 venduti non si calcola. Dal D225 la pagina mostra solo i nuovi PSA 10 del mese e il grafico delle copie gradate a settimana (tutti i voti, ultime 52 settimane), dentro la sezione della Slabvalve; lo stato aperto/chiuso resta nei dati.

## 9. Limiti noti (P17)

- Testato finora solo su un mercato simulato. La fase con dati reali è obbligatoria prima di qualsiasi uso pubblico (P14).
- Un picco da evento su una carta viene inseguito con prudenza: finché non lo confermano più vendite, il modello lo tratta come possibile anomalia.
- **Calibrazione delle forchette**: nella v1.1 sul simulatore la copertura era 78,6% (protocollo completo). La deriva propria per carta (§2) la migliorava sul seme 1 (74,7%) ma peggiorava l'errore, quindi è spenta (D30).
- **Lingue**: lo scarto di lingua è uguale per tutti i voti e non deriva nel tempo. Verificato su un mercato simulato con 4 lingue (test L1, L2); sui dati reali da verificare.
- **Fattore d'era attenuato** (vedi §4): da sostituire con una dinamica a trend locale. Probabilmente migliorerebbe anche il rumore settimanale, l'unico criterio non superato.
- Il fattore è uno per era. Segmenti più fini (fascia di prezzo, tipo di carta) sono un'estensione naturale ma non ancora provata.
- I prezzi esclusi della spedizione e le commissioni delle case d'asta vanno normalizzati dalla fonte prima di entrare (schema dati).
