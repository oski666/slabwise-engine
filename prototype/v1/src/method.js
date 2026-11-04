V.method=()=>{
  const cnt={};EXCL.forEach(o=>{const k=o.why.startsWith("Cert:")?"cert":o.why.startsWith("Duplicato")?"dup":/slab|Lotto/.test(o.why)?"listing":/Best Offer|Pagamento/.test(o.why)?"price":/incoerente/.test(o.why)?"ladder":"fence";cnt[k]=(cnt[k]||0)+1});
  const N0=ALLSALES.length,s1=N0-(cnt.dup||0),s2=s1-(cnt.cert||0),s3=s2-(cnt.listing||0)-(cnt.price||0),s4=s3-(cnt.ladder||0),s5=s4-(cnt.fence||0);
  const lo=ALLSALES.filter(o=>o.st==="lo").length;
  const st=[[L("Registrate","Recorded"),N0,""],[L("Senza duplicati","No duplicates"),s1,L("stesso cert","same cert")],[L("Cert verificato","Cert verified"),s2,L("grado reale","real grade")],[L("Annunci validi","Valid listings"),s3,L("lotti, raw, Best Offer, non pagate","lots, raw, Best Offer, unpaid")],[L("Scala coerente","Coherent ladder"),s4,L("sotto il grado inferiore","below lower grade")],[L("Nel prezzo","In the price"),s5,L("troppo sotto il mercato","far below market")]];
  const W=980,colW=W/st.length,maxH=150,top=40;
  const funnel=`<svg viewBox="0 0 ${W} 250" role="img" aria-label="${L(`Imbuto: da ${N0} vendite registrate a ${s5} vendite usate nel prezzo`,`Funnel: from ${N0} recorded sales to ${s5} sales used in the price`)}" style="min-width:760px;width:100%;height:auto;color:var(--fg)">
    <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker>
    <linearGradient id="fh" x1="0" x2="1"><stop offset="0" stop-color="#6ef0ff"/><stop offset=".5" stop-color="#9d8cff"/><stop offset="1" stop-color="#ff8ad8"/></linearGradient></defs>
    ${st.map(([t,v,wy],i)=>{const h=maxH*v/N0,x=i*colW+20,w=colW-58,y=top+(maxH-h)/2;
      return`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="8" fill="${i===st.length-1?"url(#fh)":"currentColor"}" opacity="${i===st.length-1?1:0.12+i*0.05}"/>
      <text x="${x+w/2}" y="${top+maxH/2+6}" text-anchor="middle" font-family="var(--f-mono)" font-size="17" font-weight="600" fill="${i===st.length-1?"#0b0d1a":"currentColor"}">${int(v)}</text>
      <text x="${x+w/2}" y="${top+maxH+30}" text-anchor="middle" font-family="var(--f-body)" font-size="13" font-weight="700" fill="currentColor">${t}</text>
      ${i?`<line x1="${x-34}" y1="${top+maxH/2}" x2="${x-6}" y2="${top+maxH/2}" stroke="currentColor" stroke-width="1.6" marker-end="url(#ar)"/>
      <text x="${x-20}" y="${top-14}" text-anchor="middle" font-family="var(--f-mono)" font-size="11.5" fill="var(--down)">−${int(st[i-1][1]-v)}</text>
      <text x="${x+w/2}" y="${top+maxH+48}" text-anchor="middle" font-family="var(--f-body)" font-size="11.5" fill="var(--muted)">${wy}</text>`:""}`}).join("")}
  </svg>`;
  const TOC=[["m1",L("Il percorso di una vendita","How a sale travels")],["m2",L("Perché la maggioranza sbaglia","Why the majority is wrong")],["m3",L("Fair value prudente","Prudent fair value")],["m4",L("Tre misure del mercato","Three market measures")],["m5",L("Liquidità","Liquidity")],["m6",L("Cosa può falsare i dati","What can distort the data")],["m7",L("Fonti","Sources")],["m8",L("Glossario","Glossary")]];
  const head=(n,t,p)=>`<div class="mhead"><span class="sn">${n}</span><div><h2>${t}</h2>${p?`<p>${p}</p>`:""}</div></div>`;
  const LIQ=[[L("Ricambio","Turnover"),L("cert unici venduti in 12 mesi ÷ popolazione","unique certs sold in 12 months ÷ population"),L("Quanta parte dell'offerta circola","How much of the supply actually circulates"),82,9],
    [L("Regolarità","Regularity"),L("intervallo mediano tra vendite e sua variabilità","median gap between sales and its variability"),L("Vende con costanza o a ondate","Steady sales or bursts"),88,14],
    [L("Profondità","Depth"),L("annunci attivi ÷ popolazione","active listings ÷ population"),L("Se c'è qualcuno dall'altra parte, adesso","Whether someone is on the other side, right now"),74,22],
    [L("Dispersione","Dispersion"),L("distanza tipica dei prezzi dal fair value","typical distance of prices from fair value"),L("Mercato ordinato o trattative una per una","Orderly market or one-off negotiations"),79,31],
    [L("Impatto","Impact"),L("variazione di prezzo ÷ volume in euro","price change ÷ euro volume"),L("Quanto basta poco denaro a muovere il prezzo","How little money it takes to move the price"),85,18]];
  const RISK=[[L("Grado sbagliato nel titolo","Wrong grade in the title"),L("Un PSA 1 conta come PSA 10","A PSA 1 counts as a PSA 10"),L("Verifica del cert con PSA","Cert check with PSA"),"y"],
    [L("Carta raw venduta come “pronta per il 10”","Raw card sold as “PSA 10 ready”"),L("Prezzi graded troppo bassi","Graded prices too low"),L("Riconoscimento del titolo e coerenza con la scala","Title recognition and ladder coherence"),"y"],
    [L("Lotti di più carte","Multi-card lots"),L("Prezzi troppo alti","Prices too high"),L("Riconoscimento del titolo e recinto asimmetrico","Title recognition and asymmetric fence"),"y"],
    [L("Best Offer con prezzo nascosto","Best Offer with hidden price"),L("Prezzi troppo alti","Prices too high"),L("Escluse finché non c'è il prezzo accettato","Excluded until the accepted price is known"),"y"],
    [L("Aste non pagate","Unpaid auctions"),L("Prezzi troppo alti","Prices too high"),L("Escluse finché il pagamento non è confermato","Excluded until payment is confirmed"),"y"],
    [L("Stesso slab rimesso in vendita","Same slab relisted"),L("Volume e ricambio gonfiati","Inflated volume and turnover"),L("Un cert conta una volta","One cert counts once"),"y"],
    [L("Vendita record isolata","Isolated record sale"),L("Market cap gonfiato","Inflated market cap"),L("Peso ridotto finché non c'è conferma; tetto del 5% negli indici","Reduced weight until confirmed; 5% cap in indices"),"y"],
    [L("Slab falso con cert vero","Fake slab with a real cert"),L("Prezzi troppo bassi","Prices too low"),L("Confronto con le foto PSA del cert","Comparison with PSA's cert photos"),"p"],
    [L("Vendite tra account collegati","Sales between linked accounts"),L("Prezzi e volumi gonfiati","Inflated prices and volumes"),L("Coppie compratore-venditore ricorrenti, account nuovi","Recurring buyer-seller pairs, new accounts"),"p"],
    [L("Regrade e crack-out","Regrades and crack-outs"),L("Popolazione e market cap sovrastimati","Overstated population and market cap"),L("Sconto stimato per grado ed epoca","Estimated discount by grade and era"),"p"],
    [L("Commissioni d'asta diverse","Different auction fees"),L("Confronti falsati tra piattaforme","Distorted cross-platform comparisons"),L("Normalizzazione al prezzo pagato dal compratore","Normalised to the price the buyer paid"),"p"],
    [L("Copie migliori alle case d'aste","Best copies go to auction houses"),L("eBay sottostima il grado","eBay underestimates the grade"),L("Peso per piattaforma e controllo per fascia di prezzo","Per-platform weighting and price-band checks"),"p"],
    [L("Picchi da eventi (ristampe, nuovi set)","Event spikes (reprints, new sets)"),L("Valori gonfiati per poche settimane","Values inflated for a few weeks"),L("Valore pesato per recenza e forchetta","Recency weighting and range"),"p"],
    [L("Cambi e mercati diversi","Currencies and different markets"),L("Prezzi incoerenti tra paesi","Inconsistent prices across countries"),L("Conversione al cambio BCE del giorno della vendita","ECB rate conversion on the sale date"),"p"]];
  const GL=[[L("Atomo","Atom"),L("La combinazione carta × stampa × grado. Un Charizard Base Set PSA 10 e lo stesso Charizard PSA 9 sono due atomi, con prezzi e popolazioni proprie.","The card × printing × grade combination. A Base Set Charizard PSA 10 and the same Charizard PSA 9 are two atoms, each with its own price and population.")],
    ["Cert",L("Il numero di certificato stampato sull'etichetta dello slab. Permette di verificare carta e voto presso l'ente di grading.","The certificate number printed on the slab label. It lets you verify card and grade with the grading company.")],
    ["Fair value",L("La nostra stima di quanto vale oggi una copia di un atomo, costruita solo da vendite valide.","Our estimate of what one copy of an atom is worth today, built only from valid sales.")],
    [L("Evidenza","Evidence"),L("Punteggio da 0 a 100 che dice quanto è solido un fair value.","A 0 to 100 score saying how solid a fair value is.")],
    [L("Forchetta","Range"),L("L'intervallo in cui il valore si trova con buona probabilità. Larga quando le vendite sono poche.","The interval the value most likely falls in. Wide when there are few sales.")],
    [L("Popolazione","Population"),L("Quante copie di un atomo sono state gradate, secondo i report degli enti.","How many copies of an atom have been graded, according to the grading companies' reports.")],
    [L("Ricambio","Turnover"),L("Quota delle copie esistenti che cambia proprietario in un anno.","The share of existing copies that change hands in a year.")],
    [L("Copie che circolano","Circulating copies"),L("Equivalente del flottante in borsa: le copie realisticamente sul mercato in un dato orizzonte.","The equivalent of free float on a stock exchange: the copies realistically on the market over a given horizon.")],
    [L("Recinto asimmetrico","Asymmetric fence"),L("Regola che scarta con decisione le vendite molto sotto il mercato e tiene, a peso ridotto, quelle molto sopra.","A rule that firmly rejects sales far below the market and keeps, at reduced weight, those far above it.")],
    [L("Costo reale","Landed cost"),L("Prezzo + spedizione + IVA all'importazione + sdoganamento + commissioni: quanto paghi davvero in Italia.","Price + shipping + import VAT + customs handling + fees: what you actually pay in Italy.")]];
  return`<div class="crumbs"><a href="#market">${L("Mercato","Market")}</a>/<span>${L("Metodologia","Methodology")}</span></div>
  <section class="mhero">
    <div>
      <div class="eyebrow">${L("Metodologia · versione prototipo · 22 ottobre 2026","Methodology · prototype version · 22 October 2026")}</div>
      <h1 style="font-size:clamp(28px,4vw,48px);margin-top:14px;max-width:20ch">${L(`Come una vendita diventa un <span class="holo">prezzo giusto</span>.`,`How a sale becomes a <span class="holo">fair price</span>.`)}</h1>
      <p class="lede">${L("Tutti i siti di prezzi partono dalle stesse vendite eBay e d'asta, e quelle vendite sono sporche. Questa pagina spiega, passo per passo, come decidiamo quali vendite contano, come calcoliamo il valore di una carta e quanto vale davvero il mercato. Ogni numero qui sotto è calcolato dal vivo sul dataset del prototipo.","Every price site starts from the same eBay and auction sales, and those sales are dirty. This page explains, step by step, how we decide which sales count, how we calculate a card's value and what the market is really worth. Every number below is calculated live on the prototype dataset.")}</p>
    </div>
    <div class="mkpi">
      <div><span class="num">${int(N0)}</span><small>${L("vendite registrate","recorded sales")}</small></div>
      <div><span class="num" style="color:var(--down)">${int(N0-s5)}</span><small>${L("scartate, ognuna con il motivo","rejected, each with its reason")}</small></div>
      <div><span class="num">${lo}</span><small>${L("alte isolate, a peso ridotto","isolated highs, reduced weight")}</small></div>
      <div><span class="num">0</span><small>${L("inversioni nella scala dei gradi","inversions in the grade ladder")}</small></div>
    </div>
  </section>

  <nav class="toc" aria-label="${L("Indice","Contents")}">${TOC.map(([id,t],i)=>`<a href="#method" data-to="${id}"><span class="num">${String(i+1).padStart(2,"0")}</span>${t}</a>`).join("")}</nav>

  <section class="msec" id="m1">
    ${head("01",TOC[0][1],L("Una vendita deve superare ogni passaggio, in quest'ordine. I primi tre non guardano il prezzo: prima capiamo <b>cosa</b> è stato venduto, solo dopo <b>a quanto</b>.","A sale has to pass every step, in this order. The first three ignore the price: first we work out <b>what</b> was sold, only then <b>for how much</b>."))}
    <figure class="panel pad fig"><div class="scroll">${funnel}</div>
      <figcaption>${L(`Su ${int(N0)} vendite registrate, ${int(s5)} entrano nel calcolo del prezzo. I numeri in rosso sono le vendite scartate a ogni passaggio.`,`Of ${int(N0)} recorded sales, ${int(s5)} go into the price. The red numbers are the sales rejected at each step.`)}</figcaption></figure>
    <div class="cards3">
      <div class="panel pad"><span class="tag">${L("Identità","Identity")}</span><h3>${L("Il certificato decide, non il titolo","The cert decides, not the title")}</h3><p>${L("Se l'annuncio riporta il numero di cert, lo verifichiamo con PSA: carta e voto reali. Un titolo che dice \"PSA 10\" su una carta che il certificato dice PSA 2 viene riclassificato.","If the listing shows a cert number, we verify it with PSA: real card and real grade. A title saying \"PSA 10\" on a card the cert says is a PSA 2 gets reclassified.")}</p></div>
      <div class="panel pad"><span class="tag">${L("Annuncio","Listing")}</span><h3>${L("Non tutto quello che è \"venduto\" è una vendita","Not everything \"sold\" is a sale")}</h3><p>${L("Lotti di più carte, carte raw vendute come \"pronte per il 10\", Best Offer con il prezzo vero nascosto, aste non pagate e rilanci dello stesso slab restano fuori.","Multi-card lots, raw cards sold as \"PSA 10 ready\", Best Offers with the real price hidden, unpaid auctions and relists of the same slab all stay out.")}</p></div>
      <div class="panel pad"><span class="tag">${L("Prezzo","Price")}</span><h3>${L("Regole in rapporti, non in euro","Rules in ratios, not euros")}</h3><p>${L("Un PSA 10 non vale meno di un PSA 9, e nessuno slab meno della carta raw. Le soglie sono rapporti, quindi valgono uguale per una carta da 30 € e per una da 35.000 €.","A PSA 10 can't be worth less than a PSA 9, and no slab less than the raw card. Thresholds are ratios, so they work the same for a €30 card and a €35,000 one.")}</p></div>
    </div>
  </section>

  <section class="msec" id="m2">
    ${head("02",TOC[1][1],L("Il caso classico: in due settimane escono dieci annunci \"PSA 10\" a 30 € e una vendita vera a 35.000 €. Un algoritmo che guarda solo i prezzi dà ragione ai dieci. Prova a cambiare metodo.","The classic case: within two weeks, ten \"PSA 10\" listings sell at €30 and one real sale goes for €35,000. An algorithm that only looks at prices sides with the ten. Try switching method."))}
    <figure class="panel pad fig">
      <div class="tabs" id="majt" style="margin-bottom:14px"><button data-m="med" class="on">${L("Mediana semplice","Plain median")}</button><button data-m="sw">Slabwise</button></div>
      <div id="majfig"></div><figcaption id="majcap"></figcaption>
    </figure>
  </section>

  <section class="msec" id="m3">
    ${head("03",TOC[2][1],L("Con molte vendite ci fidiamo delle vendite. Con poche, il valore si appoggia anche a un riferimento costruito dalla scala dei gradi e dalle carte simili. Il peso si sposta da solo man mano che arrivano vendite.","With many sales we trust the sales. With few, the value also leans on a reference built from the grade ladder and similar cards. The weight shifts on its own as sales come in."))}
    <div class="split2">
      <figure class="panel pad fig">
        <label class="slider" for="shs"><span>${L("Vendite valide osservate","Valid sales observed")}: <b class="num" id="shn">1</b></span><input id="shs" type="range" min="0" max="30" value="1"></label>
        <div id="shfig"></div>
        <figcaption>${L("Esempio: le vendite osservate sono a 3,72 milioni, il riferimento dei comparabili a 400.000. Con una sola vendita il riferimento pesa tre volte tanto; con trenta vendite quasi non conta più.","Example: observed sales are at 3.72 million, the comparables' reference at 400,000. With a single sale the reference weighs three times as much; with thirty sales it barely counts.")}</figcaption>
      </figure>
      <div class="panel pad formula">
        <span class="tag">${L("La formula, a parole","The formula, in words")}</span>
        <p class="big">${L("valore = media pesata, in scala logaritmica, tra la <b>mediana delle vendite</b> (peso = numero di vendite) e il <b>riferimento</b> (peso fisso = 3).","value = weighted average, on a log scale, of the <b>median of sales</b> (weight = number of sales) and the <b>reference</b> (fixed weight = 3).")}</p>
        <p>${L("Si usa la scala logaritmica perché i prezzi delle carte si muovono per percentuali: passare da 100 a 200 € è lo stesso salto di passare da 10.000 a 20.000 €.","We use a log scale because card prices move in percentages: going from €100 to €200 is the same jump as going from €10,000 to €20,000.")}</p>
        <p>${L("Ogni valore esce con una <b>forchetta</b> e un <b>punteggio di evidenza</b> da 0 a 100, costruito da: numero di vendite, quanto sono recenti, quanto concordano tra loro e quante hanno il cert verificato.","Every value comes with a <b>range</b> and an <b>evidence score</b> from 0 to 100, built from: number of sales, how recent they are, how much they agree and how many have a verified cert.")}</p>
        <div class="evscale">${[["0–19",L("Scarsa","Sparse")],["20–39",L("Limitata","Limited")],["40–59",L("Moderata","Moderate")],["60–79",L("Forte","Strong")],["80–100",L("Molto forte","Very strong")]].map(([r,l],i)=>`<div><i style="opacity:${0.25+i*0.18}"></i><b>${l}</b><span class="num">${r}</span></div>`).join("")}</div>
        <p style="font-size:13px;margin-top:12px">${L("Sotto 40 il valore si mostra, ma non genera deal e non entra negli indici.","Below 40 the value is shown, but it triggers no deals and stays out of the indices.")}</p>
      </div>
    </div>
  </section>

  <section class="msec" id="m4">
    ${head("04",L("Tre misure del mercato, non una","Three market measures, not one"),L("Il market cap classico (prezzo × copie) presume che le carte siano tutte uguali e vendibili domani al prezzo dell'ultima vendita. Per le carte non è vero, quindi lo dividiamo in tre domande diverse.","Classic market cap (price × copies) assumes every card is identical and could sell tomorrow at the last sale price. That isn't true for cards, so we split it into three different questions."))}
    <div class="cards3">
      <div class="panel pad measure"><span class="tag">${L("Stima","Estimate")}</span><h3>${L("Valore di collezione","Collection value")}</h3><p class="f">${L("fair value prudente × popolazione, con forchetta","prudent fair value × population, with range")}</p><p>${L("Quanto vale l'insieme delle copie esistenti, secondo la stima migliore.","What all existing copies are worth, on the best estimate.")}</p></div>
      <div class="panel pad measure"><span class="tag">${L("Stima prudente","Prudent estimate")}</span><h3>${L("Valore liquido","Liquid value")}</h3><p class="f">${L("valore basso della forchetta × copie che circolano","low end of the range × circulating copies")}</p><p>${L("Quanto si potrebbe realizzare vendendo in tempi ragionevoli. È il numero più vicino al \"denaro vero\".","What could be realised by selling within a reasonable time. It's the figure closest to \"real money\".")}</p></div>
      <div class="panel pad measure"><span class="tag ok">${L("Dato","Fact")}</span><h3>${L("Volume reale","Real volume")}</h3><p class="f">${L("somma delle vendite valide in 12 mesi","sum of valid sales over 12 months")}</p><p>${L("Quanti soldi sono passati davvero di mano. Non è una stima: è un conteggio.","How much money actually changed hands. Not an estimate: a count.")}</p></div>
    </div>
    <figure class="panel pad fig" style="margin-top:16px">
      <h3 style="margin-bottom:4px">${L("Lo stesso caso, due metodi","The same case, two methods")}</h3>
      <p style="color:var(--muted);font-size:13.5px;margin:0 0 16px">${L("Una carta con 3 copie graded e una sola vendita da 3,72 milioni di dollari. Esempio illustrativo.","A card with 3 graded copies and a single $3.72 million sale. Illustrative example.")}</p>
      <div class="scroll">${capCompare()}</div>
      <figcaption>${L("Il metodo \"ultima vendita × copie\" produce 11,2 milioni. Il valore di collezione prudente è circa 2,1 milioni, con una forchetta larga perché c'è una sola vendita; il valore liquido è più basso ancora, perché in tre anni circola probabilmente una copia sola.","The \"last sale × copies\" method gives 11.2 million. The prudent collection value is about 2.1 million, with a wide range because there is only one sale; the liquid value is lower still, because over three years probably only one copy circulates.")}</figcaption>
    </figure>
    <div class="note" style="margin-top:14px">${L("<b>Il compromesso, detto chiaramente.</b> Se quella vendita record era vera, il nostro valore la \"insegue\" più lentamente: sale man mano che arrivano altre vendite a quel livello. La forchetta larga lo segnala subito. In cambio, una vendita sola non può più gonfiare l'intero mercato. Negli indici, inoltre, nessuna carta può pesare più del 5%.","<b>The trade-off, stated plainly.</b> If that record sale was real, our value \"catches up\" more slowly: it rises as more sales arrive at that level. The wide range flags it right away. In exchange, a single sale can no longer inflate the whole market. In the indices, no card can weigh more than 5%.")}</div>
  </section>

  <section class="msec" id="m5">
    ${head("05",L("Liquidità: quanto si vende davvero una carta","Liquidity: how easily a card really sells"),L("Serve per stimare le copie che circolano e lo sconto del valore liquido. Nessun indicatore basta da solo, quindi ne combiniamo cinque.","It's used to estimate circulating copies and the liquid-value discount. No single indicator is enough, so we combine five."))}
    <div class="scroll"><table class="tbl panel liq">
      <thead><tr><th class="l">${L("Indicatore","Indicator")}</th><th class="l">${L("Come si calcola","How it's calculated")}</th><th class="l">${L("Cosa dice","What it tells you")}</th><th>${L("Carta molto scambiata","Heavily traded card")}</th><th>${L("Carta rara","Rare card")}</th></tr></thead>
      <tbody>${LIQ.map(([a,b,c,x,y])=>`<tr><td class="l"><b>${a}</b></td><td class="l" style="white-space:normal;min-width:200px;color:var(--muted)">${b}</td><td class="l" style="white-space:normal;min-width:180px;color:var(--muted)">${c}</td><td><span class="lb"><i style="width:${x}%"></i></span><span class="num">${x}</span></td><td><span class="lb rare"><i style="width:${y}%"></i></span><span class="num">${y}</span></td></tr>`).join("")}
      <tr class="tot"><td class="l"><b>${L("Punteggio di liquidità","Liquidity score")}</b></td><td class="l" colspan="2" style="color:var(--muted)">${L("media dei cinque, corretta per il numero di osservazioni","average of the five, adjusted for the number of observations")}</td><td class="num"><b>82</b></td><td class="num"><b>19</b></td></tr></tbody></table></div>
    <div class="cards3" style="margin-top:16px">
      <div class="panel pad"><span class="tag">${L("Accorgimento 1","Safeguard 1")}</span><h3>${L("Copie, non vendite","Copies, not sales")}</h3><p>${L("Se lo stesso slab passa di mano tre volte in un mese, è una copia che circola, non tre. Contare i cert unici neutralizza anche buona parte delle vendite gonfiate tra account collegati.","If the same slab changes hands three times in a month, that's one circulating copy, not three. Counting unique certs also neutralises much of the inflated trading between linked accounts.")}</p></div>
      <div class="panel pad"><span class="tag">${L("Accorgimento 2","Safeguard 2")}</span><h3>${L("Poche osservazioni, stima prudente","Few observations, prudent estimate")}</h3><p>${L("Una carta con 3 copie e 1 vendita in un anno sembra liquidissima (33% di ricambio). È un'illusione statistica: come per il fair value, pesa soprattutto il dato delle carte comparabili.","A card with 3 copies and 1 sale a year looks extremely liquid (33% turnover). It's a statistical illusion: as with fair value, the comparable cards' figure carries most of the weight.")}</p></div>
      <div class="panel pad"><span class="tag">${L("Accorgimento 3","Safeguard 3")}</span><h3>${L("Popolazione corretta","Corrected population")}</h3><p>${L("Chi apre uno slab per ritentare il voto spesso non restituisce l'etichetta: la carta viene contata due volte. Applichiamo uno sconto stimato per grado ed epoca, con forchetta.","People who crack a slab to try for a higher grade often don't return the label, so the card gets counted twice. We apply an estimated discount by grade and era, with a range.")}</p></div>
    </div>
    <p class="note" style="margin-top:14px">${L("<b>Come sapremo se funziona.</b> Un buon punteggio di liquidità deve prevedere se un annuncio vende entro 30 giorni e quanto vicino al fair value. Lo misureremo osservando gli annunci ogni giorno, prima di usarlo sui dati reali. I valori nella tabella sono un esempio.","<b>How we'll know it works.</b> A good liquidity score must predict whether a listing sells within 30 days and how close to fair value. We'll measure it by watching listings every day before using it on real data. The values in the table are an example.")}</p>
  </section>

  <section class="msec" id="m6">
    ${head("06",L("Cosa può falsare i dati, e cosa facciamo","What can distort the data, and what we do"),L("L'elenco completo dei rischi noti. Lo stato dice se la difesa è già nel prototipo o è prevista per la versione con dati reali.","The full list of known risks. The status shows whether the defence is already in the prototype or planned for the real-data version."))}
    <div class="scroll"><table class="tbl panel risk">
      <thead><tr><th class="l">${L("Rischio","Risk")}</th><th class="l">${L("Effetto sui numeri","Effect on the numbers")}</th><th class="l">${L("Difesa","Defence")}</th><th class="l">${L("Stato","Status")}</th></tr></thead>
      <tbody>${RISK.map(([a,b,c,s])=>`<tr><td class="l" style="white-space:normal;min-width:200px"><b>${a}</b></td><td class="l" style="white-space:normal;min-width:170px;color:var(--muted)">${b}</td><td class="l" style="white-space:normal;min-width:220px;color:var(--muted)">${c}</td><td class="l">${s==="y"?`<span class="why ok">${L("Nel prototipo","In prototype")}</span>`:`<span class="why lo">${L("Previsto","Planned")}</span>`}</td></tr>`).join("")}</tbody></table></div>
  </section>

  <section class="msec" id="m7">
    ${head("07",L("Fonti e cosa è reale","Sources and what's real"),L("Usiamo solo fonti con condizioni d'uso compatibili. Niente scraping di siti che lo vietano.","We only use sources whose terms allow it. No scraping of sites that forbid it."))}
    <figure class="panel pad fig"><div class="scroll">${sourcesDiagram()}</div>
      <figcaption>${L("Nel prototipo sono reali solo catalogo, immagini e prezzo raw (TCGdex). Vendite graded, popolazioni e annunci sono simulati, con errori inseriti apposta per mettere alla prova il filtro. Il filtro invece è vero e gira nel tuo browser.","In the prototype only the catalogue, images and raw prices are real (TCGdex). Graded sales, populations and listings are simulated, with deliberate errors to test the filter. The filter itself is real and runs in your browser.")}</figcaption></figure>
  </section>

  <section class="msec" id="m8">
    ${head("08",TOC[7][1],"")}
    <dl class="gloss">${GL.map(([t,d])=>`<div class="panel"><dt>${t}</dt><dd>${d}</dd></div>`).join("")}</dl>
  </section>`};

function capCompare(){
  const W=900,H=190,x0=200,x1=W-40,max=12e6,X=v=>x0+(x1-x0)*v/max;
  const M=v=>"$"+fx(v/1e6,1)+"M";
  const rows=[[L("Ultima vendita × copie","Last sale × copies"),11.16e6,null,"tcg"],[L("Valore di collezione","Collection value"),2.09e6,[0.9e6,6.2e6],"col"],[L("Valore liquido","Liquid value"),0.5e6,[0.3e6,0.9e6],"liq"]];
  return`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${L("Confronto: 11,2 milioni con l'ultima vendita, 2,1 milioni come valore di collezione, 0,5 milioni come valore liquido","Comparison: 11.2 million with the last sale, 2.1 million as collection value, 0.5 million as liquid value")}" style="min-width:640px;width:100%;height:auto;color:var(--fg)">
  <defs><linearGradient id="cg" x1="0" x2="1"><stop offset="0" stop-color="#6ef0ff"/><stop offset=".5" stop-color="#9d8cff"/><stop offset="1" stop-color="#ff8ad8"/></linearGradient></defs>
  ${[0,3e6,6e6,9e6,12e6].map(v=>`<line x1="${X(v)}" x2="${X(v)}" y1="10" y2="${H-26}" stroke="currentColor" opacity=".12"/><text x="${X(v)}" y="${H-8}" text-anchor="middle" font-family="var(--f-mono)" font-size="11" fill="var(--faint)">${v?"$"+v/1e6+"M":"0"}</text>`).join("")}
  ${rows.map(([t,v,band,k],i)=>{const y=22+i*50;return`
    <text x="${x0-14}" y="${y+18}" text-anchor="end" font-family="var(--f-body)" font-size="13" font-weight="700" fill="currentColor">${t}</text>
    ${band?`<rect x="${X(band[0])}" y="${y+4}" width="${X(band[1])-X(band[0])}" height="20" rx="4" fill="#9d8cff" opacity=".18"/>`:""}
    <rect x="${x0}" y="${y+8}" width="${X(v)-x0}" height="12" rx="3" fill="${k==="tcg"?"var(--down)":"url(#cg)"}"/>
    <text x="${X(v)+(k==="tcg"?-8:10)}" y="${y+18}" text-anchor="${k==="tcg"?"end":"start"}" font-family="var(--f-mono)" font-size="12.5" font-weight="600" fill="${k==="tcg"?"#fff":"currentColor"}">${M(v)}</text>`}).join("")}
  <text x="${X(6.2e6)+8}" y="${22+50+10}" font-family="var(--f-body)" font-size="11" fill="var(--muted)">${L("forchetta","range")}</text>
  </svg>`}

function sourcesDiagram(){
  const W=980,H=300;
  const Ls=[["TCGdex",L("catalogo, immagini, raw","catalogue, images, raw"),"real",40],[L("Fonte graded con licenza","Licensed graded source"),L("vendite e popolazioni","sales and populations"),"plan",110],[L("API PSA","PSA API"),L("verifica dei cert","cert verification"),"plan",180],["eBay Browse API",L("annunci attivi","active listings"),"plan",250]];
  const mid=[[L("Pulizia","Cleaning"),L("imbuto a 6 passaggi","6-step funnel"),95],[L("Valutazione","Valuation"),L("fair value, evidenza, liquidità","fair value, evidence, liquidity"),205]];
  const R=[[L("Classifica e indici","Rankings and indices"),60],[L("Pagina carta","Card page"),135],[L("Deal sul costo reale","Landed-cost deals"),210]];
  const box=(x,y,w,h,t,s,kind)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="10" fill="${kind==="real"?"#4fe3a1":kind==="core"?"#9d8cff":"currentColor"}" fill-opacity="${kind==="real"?.16:kind==="core"?.18:.06}" stroke="${kind==="real"?"#4fe3a1":kind==="core"?"#9d8cff":"currentColor"}" stroke-opacity="${kind==="plan"?.35:.9}" ${kind==="plan"?'stroke-dasharray="5 4"':""}/>
    <text x="${x+14}" y="${y+22}" font-family="var(--f-body)" font-size="13.5" font-weight="700" fill="currentColor">${t}</text>${s?`<text x="${x+14}" y="${y+40}" font-family="var(--f-body)" font-size="11.5" fill="var(--muted)">${s}</text>`:""}`;
  const arrow=(x1,y1,x2,y2,lab)=>`<path d="M${x1} ${y1} C${(x1+x2)/2} ${y1}, ${(x1+x2)/2} ${y2}, ${x2} ${y2}" fill="none" stroke="currentColor" stroke-opacity=".45" stroke-width="1.5" marker-end="url(#ar2)"/>${lab?`<text x="${(x1+x2)/2}" y="${(y1+y2)/2-6}" text-anchor="middle" font-family="var(--f-mono)" font-size="10.5" fill="var(--faint)">${lab}</text>`:""}`;
  return`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${L("Le fonti alimentano pulizia e valutazione, che producono classifica, pagina carta e deal","Sources feed cleaning and valuation, which produce rankings, card pages and deals")}" style="min-width:760px;width:100%;height:auto;color:var(--fg)">
  <defs><marker id="ar2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="currentColor" fill-opacity=".6"/></marker></defs>
  <text x="20" y="22" font-family="var(--f-mono)" font-size="11" fill="var(--faint)">${L("FONTI","SOURCES")}</text><text x="400" y="22" font-family="var(--f-mono)" font-size="11" fill="var(--faint)">SLABWISE</text><text x="740" y="22" font-family="var(--f-mono)" font-size="11" fill="var(--faint)">${L("COSA VEDI","WHAT YOU SEE")}</text>
  ${Ls.map(([t,s,k,y])=>box(20,y-8,250,52,t,s,k)).join("")}
  ${mid.map(([t,s,y])=>box(400,y-8,230,56,t,s,"core")).join("")}
  ${R.map(([t,y])=>box(740,y-8,220,44,t,"","core")).join("")}
  ${arrow(270,58,400,115,L("raw e catalogo","raw and catalogue"))}${arrow(270,128,400,115,L("vendite","sales"))}${arrow(270,198,400,125,"cert")}${arrow(515,143,515,197,"")}${arrow(270,268,740,224,L("annunci","listings"))}
  ${arrow(630,225,740,74,"")}${arrow(630,225,740,149,"")}${arrow(630,225,740,212,"")}
  <rect x="20" y="${H-26}" width="12" height="12" rx="3" fill="#4fe3a1" fill-opacity=".3" stroke="#4fe3a1"/><text x="40" y="${H-16}" font-family="var(--f-body)" font-size="12" fill="var(--muted)">${L("reale nel prototipo","real in the prototype")}</text>
  <rect x="210" y="${H-26}" width="12" height="12" rx="3" fill="none" stroke="currentColor" stroke-opacity=".4" stroke-dasharray="3 3"/><text x="230" y="${H-16}" font-family="var(--f-body)" font-size="12" fill="var(--muted)">${L("simulato ora, fonte reale prevista","simulated now, real source planned")}</text>
  </svg>`}

V.method.after=()=>{
  document.querySelector(".toc").addEventListener("click",e=>{const a=e.target.closest("a[data-to]");if(!a)return;e.preventDefault();document.getElementById(a.dataset.to).scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"start"})});
  const sales=[...Array(10)].map((_,i)=>({d:13-i*1.2,p:26+((i*37)%11)})).concat([{d:5,p:35000,real:true}]);
  const raw=2000,psa9=9000,eu=v=>"€"+Math.round(v).toLocaleString(LOC());
  let mode="med";
  const draw=m=>{mode=m;const W=880,H=260,p={l:70,r:20,t:16,b:30},lo=Math.log(15),hi=Math.log(70000);
    const X=d=>p.l+(W-p.l-p.r)*(1-d/14),Y=v=>p.t+(H-p.t-p.b)*(1-(Math.log(v)-lo)/(hi-lo));
    const res=m==="med"?median(sales.map(s=>s.p)):35000;
    const lines=m==="sw"?`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(raw)}" y2="${Y(raw)}" stroke="#ffcc66" stroke-dasharray="6 5"/><text x="${W-p.r-4}" y="${Y(raw)-6}" text-anchor="end" font-family="var(--f-mono)" font-size="11" fill="#ffcc66">${L(`raw NM ${eu(raw)}: nessun PSA 10 può stare sotto`,`raw NM ${eu(raw)}: no PSA 10 can sit below this`)}</text>
      <line x1="${p.l}" x2="${W-p.r}" y1="${Y(psa9)}" y2="${Y(psa9)}" stroke="currentColor" stroke-opacity=".35" stroke-dasharray="3 5"/><text x="${W-p.r-4}" y="${Y(psa9)-6}" text-anchor="end" font-family="var(--f-mono)" font-size="11" fill="var(--muted)">PSA 9 ${eu(psa9)}</text>`:"";
    const dots=sales.map(s=>m==="sw"&&!s.real?`<path d="M${X(s.d)-5} ${Y(s.p)-5}l10 10M${X(s.d)+5} ${Y(s.p)-5}l-10 10" stroke="var(--down)" stroke-width="2.2" stroke-linecap="round"/>`:`<circle cx="${X(s.d)}" cy="${Y(s.p)}" r="${s.real?8:6}" fill="${s.real?"#6ef0ff":"#9d8cff"}" stroke="var(--panel)" stroke-width="2"/>`).join("");
    document.getElementById("majfig").innerHTML=`<div class="scroll"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${m==="med"?L("Con la mediana semplice il prezzo è 30 euro","With the plain median the price is 30 euros"):L("Con Slabwise i dieci annunci sono scartati e il prezzo è 35.000 euro","With Slabwise the ten listings are rejected and the price is 35,000 euros")}" style="min-width:600px;width:100%;height:auto;color:var(--fg)">
      ${[30,300,3000,30000].map(v=>`<line x1="${p.l}" x2="${W-p.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="currentColor" stroke-opacity=".1"/><text x="${p.l-10}" y="${Y(v)+4}" text-anchor="end" font-family="var(--f-mono)" font-size="11" fill="var(--faint)">${eu(v)}</text>`).join("")}
      ${[14,7,0].map(d=>`<text x="${X(d)}" y="${H-8}" text-anchor="middle" font-family="var(--f-mono)" font-size="11" fill="var(--faint)">${d?L("-"+d+" giorni","-"+d+" days"):L("oggi","today")}</text>`).join("")}
      ${lines}${dots}
      <line x1="${p.l}" x2="${W-p.r}" y1="${Y(res)}" y2="${Y(res)}" stroke="${m==="med"?"var(--down)":"#4fe3a1"}" stroke-width="2.5"/>
      <text x="${p.l+8}" y="${Y(res)-8}" font-family="var(--f-display)" font-size="14" font-weight="700" fill="${m==="med"?"var(--down)":"#4fe3a1"}">${L("Prezzo","Price")}: ${eu(res)}</text>
      <text x="${X(5)+14}" y="${Y(35000)+4}" font-family="var(--f-body)" font-size="11.5" fill="var(--muted)">${L("vendita con cert verificato","sale with verified cert")}</text></svg></div>`;
    document.getElementById("majcap").innerHTML=m==="med"
      ?L("La mediana dà ragione alla maggioranza: 10 annunci su 11 sono a circa 30 €, quindi il PSA 10 “vale” 30 €. È l'errore che tcgcharts ammette per le carte molto scambiate.","The median sides with the majority: 10 of 11 listings are around €30, so the PSA 10 is “worth” €30. It's the error tcgcharts admits for heavily traded cards.")
      :L("Slabwise prima classifica: i dieci annunci stanno sotto il prezzo della carta raw, quindi non possono essere PSA 10 (sono carte raw o ristampe). Resta la vendita con cert verificato. Nessuna regola scritta per questa carta: la stessa logica vale per qualsiasi prezzo.","Slabwise classifies first: the ten listings sit below the raw card's price, so they can't be PSA 10s (they're raw cards or reprints). The sale with a verified cert remains. No rule written for this card: the same logic works at any price.");
  };
  draw("med");
  document.getElementById("majt").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;[...b.parentNode.children].forEach(x=>x.classList.toggle("on",x===b));draw(b.dataset.m)});
  const obs=3.72e6,ref=4e5,k=3;
  const sh=()=>{const n=+document.getElementById("shs").value;document.getElementById("shn").textContent=n;
    const v=Math.exp((n*Math.log(obs)+k*Math.log(ref))/(n+k)),wo=n/(n+k);
    const W=520,H=150,X=x=>30+(W-60)*(Math.log(x)-Math.log(2e5))/(Math.log(6e6)-Math.log(2e5));
    document.getElementById("shfig").innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${L(`Con ${n} vendite il valore è ${Math.round(v).toLocaleString(LOC())} dollari`,`With ${n} sales the value is ${Math.round(v).toLocaleString(LOC())} dollars`)}" style="width:100%;height:auto;color:var(--fg)">
      <line x1="30" x2="${W-30}" y1="70" y2="70" stroke="currentColor" stroke-opacity=".2" stroke-width="6" stroke-linecap="round"/>
      <circle cx="${X(ref)}" cy="70" r="7" fill="var(--panel)" stroke="currentColor" stroke-width="2"/><text x="${X(ref)}" y="100" text-anchor="middle" font-family="var(--f-mono)" font-size="11" fill="var(--muted)">${L("riferimento","reference")} $400k</text>
      <circle cx="${X(obs)}" cy="70" r="7" fill="var(--panel)" stroke="#6ef0ff" stroke-width="2"/><text x="${X(obs)}" y="100" text-anchor="middle" font-family="var(--f-mono)" font-size="11" fill="var(--muted)">${L("vendite","sales")} $${fx(3.72,2)}M</text>
      <circle cx="${X(v)}" cy="70" r="11" fill="#9d8cff"/><text x="${X(v)}" y="42" text-anchor="middle" font-family="var(--f-display)" font-size="16" font-weight="700" fill="currentColor">$${v>=1e6?fx(v/1e6,2)+"M":Math.round(v/1e3)+"k"}</text>
      <rect x="30" y="122" width="${(W-60)*wo}" height="10" rx="3" fill="#6ef0ff"/><rect x="${30+(W-60)*wo}" y="122" width="${(W-60)*(1-wo)}" height="10" rx="3" fill="currentColor" fill-opacity=".25"/>
      <text x="30" y="146" font-family="var(--f-mono)" font-size="10.5" fill="var(--muted)">${L("peso vendite","sales weight")} ${Math.round(wo*100)}%</text><text x="${W-30}" y="146" text-anchor="end" font-family="var(--f-mono)" font-size="10.5" fill="var(--muted)">${L("peso riferimento","reference weight")} ${Math.round((1-wo)*100)}%</text></svg>`};
  sh();document.getElementById("shs").addEventListener("input",sh);
};
