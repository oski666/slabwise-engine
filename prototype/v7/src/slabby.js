/* Slabby: la guida di Slabwise (docs/DESIGN.md §3.6). Pose dal character sheet in prototype/character/slabby/ (sostituibile).
   Regole: non copre i contenuti, un fumetto alla volta, si chiude da solo, si zittisce con un clic,
   con "riduci movimento" non si muove. */
(function () {
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  // D344: with GSAP Slabby has weight: he squashes before a hop, stretches in the air, wobbles when he lands,
  // and can be grabbed and thrown. Without GSAP or with "reduce motion" he behaves as before.
  const G = !RM && window.gsap ? window.gsap : null;
  if (G && window.Draggable) G.registerPlugin(window.Draggable, ...(window.InertiaPlugin ? [window.InertiaPlugin] : []));
  // Poses come from the character sheet (prototype/character/slabby/poses.svg, injected by build.py):
  // a symbol "slabby-<pose>" for each pose. Replacing the character = replacing that file (see its README).
  const POSES = ["smug", "drool", "sleep", "laugh", "shock", "bliss", "peek"];
  // optional poses for the antics (D44): taken from the folder when present, otherwise a required pose stands in
  const EXTRA = {run: "laugh", cling: "peek", sit: "smug", tongue: "laugh", wave: "bliss", peek_top: "peek", peek_side: "smug", teacher: "smug", side: "peek"};   // teacher (D108): glasses and pointer, for the card's scorecard
  const POSE = {};
  for (const p of POSES.concat(Object.keys(EXTRA))) {
    const id = document.getElementById("slabby-" + p) ? p : EXTRA[p];
    const sym = document.getElementById("slabby-" + id);
    const vb = sym ? sym.getAttribute("viewBox") : "0 0 200 200";
    POSE[p] = `<svg viewBox="${vb}" aria-hidden="true"><use href="#slabby-${id}"/></svg>`;
  }

  // Italian / English (D62): the page's language is <html lang>; every text is a pair [it, en]
  const EN = () => document.documentElement.lang === "en";
  const tr = (it, en) => EN() ? en : it;
  const TOUR = {
    mercato: {pose: "smug", text: ["Qui trovi tutte le carte gradate. Guarda la barra blu: più è corta, più il valore è affidabile.", "Here are all the graded cards. Look at the blue bar: the shorter it is, the more reliable the value."], target: "[data-tour=grid] .fork"},
    card: {pose: "bliss", text: ["Questo è lo Slabprice di oggi. La barra è lo SlabRange: 8 vendite su 10 finiscono lì dentro.", "This is today's Slabprice. The bar is the SlabRange: 8 sales in 10 land inside it."], target: "[data-tour=fork]", next: {text: ["I puntini rosa nel grafico sono vendite che non mi convincono. Passaci sopra!", "The pink dots in the chart are sales I don't believe. Hover them!"], target: "[data-tour=chart]"}},
    settimana: {pose: "laugh", text: ["Le storie della settimana: ognuna è già un reel. Copia, incolla nel Reel Studio, fatto.", "The stories of the week: each one is already a reel. Copy, paste into the Reel Studio, done."], target: "[data-tour=story]"},
    deal: {pose: "drool", text: ["Occasioni calcolate in euro, con spedizione, IVA e dogana. L'anello è la probabilità che sia un'occasione vera.", "Deals worked out in euros, with shipping, VAT and customs. The ring is the probability that it is a real deal."], target: "[data-tour=dealfilters]"},
    metodo: {pose: "smug", text: ["Qui ti spiego come facciamo i conti. Nessuna magia, solo un modello onesto.", "Here I explain how we do the maths. No magic, just an honest model."], target: null},
  };
  const T = p => tr(p[0], p[1]);
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem("slabby-" + k)); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem("slabby-" + k, JSON.stringify(v)); } catch (e) {} },
  };
  const seen = new Set(store.get("seen") || []);      // a section's tip appears once, ever; the menu replays them

  const root = document.createElement("div");
  root.className = "slabby";
  root.innerHTML = `<div class="sb-bubble" role="status" aria-live="polite" hidden></div>
    <button class="sb-char" aria-expanded="false"></button>`;
  document.body.appendChild(root);
  const charBtn = root.querySelector(".sb-char"), bubble = root.querySelector(".sb-bubble");
  const label = () => charBtn.setAttribute("aria-label", tr("Slabby, la tua guida: apri il menu", "Slabby, your guide: open the menu"));
  label(); window.addEventListener("slabwise:lang", () => { label(); hush(); });
  let pose = "smug", muted = !!store.get("muted"), hideT, idleT, poseT;

  function setPose(p, ms) {
    clearTimeout(poseT);
    const changed = p !== pose;
    pose = p;
    charBtn.innerHTML = G ? `<span class="sb-sq">${POSE[p]}</span>` : POSE[p];
    charBtn.dataset.pose = p;
    if (G && changed) {               // a new pose lands with a squash and a little wobble, feet on the ground
      const svg = charBtn.querySelector(".sb-sq");   // a wrapper: the CSS breathing stays on the svg inside
      G.fromTo(svg, {scaleX: 1.14, scaleY: .84, transformOrigin: "50% 100%"}, {scaleX: 1, scaleY: 1, duration: .7, ease: "elastic.out(1, .38)"});
    }
    if (ms) poseT = setTimeout(() => setPose(muted ? "peek" : "smug"), ms);
  }
  function say(text, opts = {}) {
    if (muted && !opts.force) return;
    if (!opts.menu && !opts.force && !bubble.hidden && charBtn.getAttribute("aria-expanded") === "true") return;   // a menu or request the visitor opened stays
    clearTimeout(hideT);
    bubble.innerHTML = `<p>${text}</p>${opts.actions ? `<div class="sb-actions">${opts.actions}</div>` : ""}<button class="sb-x" aria-label="${tr("Chiudi", "Close")}">×</button>`;
    bubble.hidden = false;
    charBtn.setAttribute("aria-expanded", opts.menu ? "true" : "false");
    bubble.classList.remove("in"); void bubble.offsetWidth; bubble.classList.add("in");
    if (!opts.sticky) hideT = setTimeout(hush, opts.ms || 7000);
  }
  function hush() { bubble.hidden = true; charBtn.setAttribute("aria-expanded", "false"); }
  function spot(sel) {
    const el = sel && document.querySelector(sel);
    if (!el) return;
    el.scrollIntoView({behavior: RM ? "auto" : "smooth", block: "center"});
    el.classList.remove("sb-spot"); void el.offsetWidth; el.classList.add("sb-spot");
    setTimeout(() => el.classList.remove("sb-spot"), 2600);
  }
  function mute(on) {
    muted = on; store.set("muted", on);
    root.classList.toggle("muted", on);
    hush();
    if (on) { stopAntics(); setPose("tongue"); poseT = setTimeout(() => setPose("peek"), 1300); }
    else setPose("laugh", 1600);
  }
  function menu() {
    if (muted) { mute(false); say(tr("Eccomi di nuovo! Clicca su di me quando vuoi una mano.", "I'm back! Click me whenever you need a hand."), {ms: 4000}); return; }
    say(tr("Cosa ti mostro?", "What shall I show you?"), {sticky: true, menu: true, actions:
      `<button data-sb="fork">${tr("Cos'è lo SlabRange?", "What is the SlabRange?")}</button><button data-sb="deal">${tr("Portami alle occasioni", "Take me to the deals")}</button><button data-sb="week">${tr("Le storie della settimana", "The stories of the week")}</button><button data-sb="req">${tr("Chiedimi una carta che manca", "Ask me for a missing card")}</button><button data-sb="mute" class="ghost">${tr("Fammi stare zitto", "Be quiet")}</button>`});
  }
  /* card requests through Slabby (D100): he searches, asks and reports back */
  const escS = x => String(x ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
  let reqLang = "en";
  function reqForm(q = "", note = "") {
    say(`${note || tr("Dimmi che carta cerchi e la chiedo io. Ogni giorno controllo se ci sono abbastanza vendite PSA per stimarla bene.", "Tell me which card you want and I'll ask for it. Every day I check whether there are enough PSA sales to value it well.")}`,
      {sticky: true, menu: true, actions: `<form class="sb-req"><input name="q" value="${escS(q)}" placeholder="${tr("es. Umbreon VMAX", "e.g. Umbreon VMAX")}" aria-label="${tr("Nome della carta", "Card name")}">
        <span class="sb-lang"><button type="button" data-sb-lang="en" aria-pressed="${reqLang === "en"}">EN</button><button type="button" data-sb-lang="ja" aria-pressed="${reqLang === "ja"}">JP</button></span>
        <button type="submit">${tr("Cerca", "Search")}</button></form><button data-sb="reqlist" class="ghost">${tr("Vedi tutte le richieste", "See all requests")}</button>`});
    const f = bubble.querySelector(".sb-req input"); if (f && !q) setTimeout(() => f.focus(), 50);
  }
  async function reqSearch(q) {
    if (!window.SWReq || q.length < 2) return;
    setPose("peek", 3000);
    say(tr("Cerco…", "Searching…"), {sticky: true, menu: true});
    let hits = [];
    try { hits = await window.SWReq.search(q, reqLang); } catch (e) {}
    if (!hits.length) return reqForm(q, tr("Non la trovo con questo nome. Prova a scriverlo come sulla carta (in inglese).", "I can't find it with that name. Try writing it as printed on the card (in English)."));
    say(tr("Quale di queste? Scegli la stampa esatta.", "Which one? Pick the exact printing."), {sticky: true, menu: true, actions:
      `<div class="sb-hits">${hits.slice(0, 8).map(h => { const k = window.SWReq.have(h.id, reqLang);
        if (!k && window.SWReq.soon && window.SWReq.soon(h.id, reqLang)) return `<span class="sb-hit" title="${escS(h.name)} · ${escS(h.id)}">${h.image ? `<img src="${escS(h.image)}/low.webp" alt="">` : ""}<small>${tr("In arrivo", "Coming")}</small></span>`;
        return k ? `<a href="#c-${escS(k)}" class="sb-hit" title="${escS(h.name)} · ${escS(h.id)}">${h.image ? `<img src="${escS(h.image)}/low.webp" alt="">` : ""}<small>${tr("Già qui", "Here")}</small></a>`
          : `<button class="sb-hit" data-sb-req="${escS(h.id)}" data-sb-name="${escS(h.name)}" title="${escS(h.name)} · ${escS(h.id)}">${h.image ? `<img src="${escS(h.image)}/low.webp" alt="">` : ""}<small>${escS(h.id)}</small></button>`; }).join("")}</div>
       <button data-sb="req" class="ghost">${tr("Cerca un'altra", "Search another")}</button>`});
  }
  async function reqSend(id, name) {
    setPose("peek", 2500);
    say(tr("La segno…", "Noting it down…"), {sticky: true, menu: true});
    const j = window.SWReq ? await window.SWReq.send(id, name, reqLang) : {ok: false};
    if (j.ok) { setPose("laugh", 2600); say(tr(`Fatto! ${escS(name)} (${escS(id)}) ora ha ${j.n} ${j.n === 1 ? "richiesta" : "richieste"}. Se ci sono abbastanza vendite coerenti la aggiungo, altrimenti la tengo in attesa e la ricontrollo ogni settimana.`,
      `Done! ${escS(name)} (${escS(id)}) now has ${j.n} ${j.n === 1 ? "request" : "requests"}. If there are enough consistent sales I'll add it, otherwise I'll keep it on hold and check again every week.`), {sticky: true, menu: true, actions: `<button data-sb="reqlist">${tr("Vedi le richieste", "See the requests")}</button><button data-sb="req" class="ghost">${tr("Chiedine un'altra", "Ask for another")}</button>`}); }
    else say(j.error === "limit" ? tr("Per oggi hai già chiesto 10 carte: riprova domani!", "You already asked for 10 cards today: try again tomorrow!")
      : j.error === "inactive" ? tr("Le richieste non sono ancora attive, scusa!", "Requests aren't active yet, sorry!") : tr("Qualcosa non è andato, riprova tra poco.", "Something went wrong, try again shortly."), {ms: 6000, menu: true});
  }
  function offerRequest(q) {
    if (muted || (!bubble.hidden && charBtn.getAttribute("aria-expanded") === "true")) return;   // never interrupt a flow the visitor opened
    setPose("peek", 2500);
    say(tr(`"${escS(q)}" non ce l'ho ancora. Vuoi che la chieda io?`, `I don't have "${escS(q)}" yet. Shall I ask for it?`), {ms: 9000, actions: `<button data-sb-reqq="${escS(q)}">${tr("Sì, cercala", "Yes, find it")}</button>`});
  }
  bubble.addEventListener("submit", e => { if (e.target.closest(".sb-req")) { e.preventDefault(); reqSearch((e.target.q.value || "").trim()); } });
  bubble.addEventListener("click", e => {
    const b = e.target.closest("[data-sb-lang],[data-sb-req],[data-sb-reqq]"); if (!b) return;
    e.stopPropagation();
    if (b.dataset.sbLang) { reqLang = b.dataset.sbLang; bubble.querySelectorAll("[data-sb-lang]").forEach(x => x.setAttribute("aria-pressed", x.dataset.sbLang === reqLang)); }
    else if (b.dataset.sbReqq !== undefined) { const q = b.dataset.sbReqq; reqForm(q); reqSearch(q); }
    else reqSend(b.dataset.sbReq, b.dataset.sbName);
  }, true);

  charBtn.addEventListener("click", () => charBtn.getAttribute("aria-expanded") === "true" ? hush() : menu());
  bubble.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.classList.contains("sb-x")) return hush();
    const a = b.dataset.sb;
    if (a === "mute") return mute(true);
    if (a === "deal") { location.hash = "deal"; return; }
    if (a === "week") { location.hash = "settimana"; return; }
    if (a === "req") return reqForm();
    if (a === "reqlist") { location.hash = "richieste"; hush(); return; }
    if (a === "fork") {
      if (!location.hash.startsWith("#c-")) location.hash = "c-swsh7-215";
      setTimeout(() => { say(T(TOUR.card.text), {ms: 9000}); spot("[data-tour=fork]"); }, 350);
    }
  });

  // tour: one tip the first time each section is opened in this visit
  window.addEventListener("slabwise:view", e => {
    const v = e.detail; wake();
    if (muted || seen.has(v)) return;
    seen.add(v); store.set("seen", [...seen]);
    const t = TOUR[v]; if (!t) return;
    setTimeout(() => {
      setPose(t.pose, 3500);
      const show = tr("Mostrami", "Show me");
      say(T(t.text), {ms: 8000, actions: t.target ? `<button data-sb-spot="${t.target}">${show}</button>` : ""});
      if (t.next) setTimeout(() => { if (!muted && location.hash.startsWith("#c-")) { say(T(t.next.text), {ms: 7000, actions: `<button data-sb-spot="${t.next.target}">${tr("Mostrami", "Show me")}</button>`}); } }, 9500);
    }, 600);
  });
  bubble.addEventListener("click", e => { const b = e.target.closest("[data-sb-spot]"); if (b) { spot(b.dataset.sbSpot); hush(); } });
  /* the teacher (D108): when a card's scorecard comes into view, Slabby puts on his glasses and explains the mark */
  let teachIO = null, teachT = 0;
  window.addEventListener("slabwise:view", e => {
    clearTimeout(teachT);
    if (teachIO) { teachIO.disconnect(); teachIO = null; }
    if (e.detail !== "card") return;
    teachT = setTimeout(() => {
      const el = document.querySelector("[data-tour=score]"); if (!el || !("IntersectionObserver" in window)) return;
      const io = teachIO = new IntersectionObserver(ents => {
        if (!ents.some(x => x.isIntersecting)) return;
        io.disconnect(); if (teachIO === io) teachIO = null;
        return;                                                  // D201: the teacher now taps the price when a card opens (app.html)
        if (muted || store.get("teacher") >= 3) return;
        store.set("teacher", (store.get("teacher") || 0) + 1);
        setPose("teacher", 6000);
        say(tr("Ecco la pagella! Ogni pallino è una vendita vera: verde se era vicina al prezzo che avevamo scritto prima, rosa se no. Così vedi quanto fidarti di noi.",
               "Here's the report card! Each dot is a real sale: green if it was close to the price we wrote before, pink if not. That's how much you can trust us."), {ms: 9000});
      }, {threshold: .4});
      teachIO.observe(el);
    }, 1500);
  });

  // reactions to what you look at (rate-limited, never while muted)
  let lastReact = 0;
  function react(p, text) {
    const now = Date.now(); if (muted || now - lastReact < 6000) return;
    lastReact = now; setPose(p, 2600); if (text) say(text, {ms: 4000});
  }
  document.addEventListener("pointerover", e => {
    const t = e.target;
    if (t.closest && t.closest("circle.s.bad")) react("shock", tr("Questa vendita puzza! Per questo pesa quasi zero.", "This sale smells fishy! That's why it weighs almost nothing."));
    else if (t.closest && t.closest(".deal.top")) react("drool", tr("Questa sì che è un'occasione…", "Now that's a deal…"));
    else if (t.closest && t.closest(".deal.sus")) react("shock", tr("Troppo bello per essere vero. Occhio!", "Too good to be true. Careful!"));
  });

  // falls asleep when you leave it alone, wakes up laughing
  function wake() {
    clearTimeout(idleT);
    if (pose === "sleep") setPose("laugh", 1500);
    idleT = setTimeout(() => { if (!muted) { hush(); setPose("sleep"); } }, 45000);
  }
  ["pointermove", "keydown", "scroll"].forEach(ev => addEventListener(ev, wake, {passive: true}));

  // D344: grab him and throw him: he flies with real physics (gravity, bounces off the screen edges), then walks home
  // with a squash and has something to say. Our own small physics, so the throw follows the finger on phones too.
  if (G && window.Draggable) {
    let thrown = false, trail = [], flying = null;
    charBtn.style.transition = "none";            // the CSS transition on transform would drag behind the pointer
    charBtn.style.touchAction = "none";
    // 23 Nov: in flight Slabby curls into a ball and rolls (a light vector drawing, nothing to decode mid-throw);
    // on landing he stops rolling, uncurls with a squash and walks home
    const BALL = '<span class="sb-sq sb-ball"><svg viewBox="0 0 208 208"><g fill="#111014" stroke="#111014" stroke-linejoin="round" stroke-linecap="round" stroke-width="5"><path d="M54.3 137.6 Q36.7 132.4 20.2 123.5 L44.3 110.3Z"/><path d="M44.0 105.0 Q28.0 91.8 15.1 73.6 L49.6 78.6Z"/><path d="M51.0 75.8 Q41.9 53.5 38.2 28.7 L70.4 54.3Z"/><path d="M73.1 52.6 Q76.2 31.1 85.5 9.8 L98.8 44.2Z"/><path d="M101.9 44.0 Q116.9 24.0 137.0 7.5 L130.3 50.1Z"/><path d="M133.1 51.5 Q152.6 44.3 174.8 42.2 L153.1 69.6Z"/><path d="M156.0 74.0 Q173.1 77.6 190.3 87.0 L163.7 97.7Z"/><path d="M164.0 103.0 Q174.5 112.8 182.5 127.8 L160.0 125.5Z"/><circle cx="104" cy="104" r="60"/></g><path d="M56 120 Q104 172 156 116 Q156 150 120 162 Q78 168 56 120Z" fill="#D9D2E9"/><path d="M60 94 Q80 58 106 88 Q84 76 64 100Z" fill="#FF6A2B" stroke="#111014" stroke-width="3" stroke-linejoin="round"/><path d="M154 92 Q134 56 110 86 Q132 74 150 98Z" fill="#FF6A2B" stroke="#111014" stroke-width="3" stroke-linejoin="round"/><path d="M78 108 Q108 138 140 106 Q110 120 78 108Z" fill="#FFFFFF" stroke="#111014" stroke-width="3" stroke-linejoin="round"/></svg></span>';
    const setX = G.quickSetter(charBtn, "x", "px"), setY = G.quickSetter(charBtn, "y", "px"), setR = G.quickSetter(charBtn, "rotation", "deg");
    const home = () => {
      const r = G.getProperty(charBtn, "rotation"), up = Math.round(r / 360) * 360;
      G.timeline()
        .to(charBtn, {rotation: up, duration: .25, ease: "power2.out"})
        .add(() => { G.set(charBtn, {rotation: 0}); charBtn.classList.remove("fly"); root.style.zIndex = ""; setPose("laugh", 2200);
          const sq = charBtn.querySelector(".sb-sq");
          sq && G.fromTo(sq, {scaleX: 1.25, scaleY: .72, transformOrigin: "50% 100%"}, {scaleX: 1, scaleY: 1, duration: .7, ease: "elastic.out(1, .35)"}); })
        .to(charBtn, {x: 0, y: 0, duration: .8, ease: "power2.inOut", onComplete: () => say(pick(LINES.thrown), {ms: 3200, force: false})}, "+=.35");
    };
    const fly = (vx, vy) => {
      charBtn.classList.add("fly"); root.style.zIndex = 90; charBtn.innerHTML = BALL; charBtn.dataset.pose = "ball";
      const r0 = charBtn.getBoundingClientRect(), ox = r0.left - G.getProperty(charBtn, "x"), oy = r0.top - G.getProperty(charBtn, "y");
      const minX = -ox, maxX = innerWidth - r0.width - ox, minY = -oy, maxY = innerHeight - r0.height - oy;
      const rad = Math.max(20, r0.width * .42);
      let x = G.getProperty(charBtn, "x"), y = G.getProperty(charBtn, "y"), t = 0, rot = 0;
      const GRAV = 2600, BOUNCE = .6, AIR = .996;
      flying = (time, dt) => {
        dt = Math.min(dt, 34) / 1000; t += dt;
        vy += GRAV * dt; vx *= AIR; x += vx * dt; y += vy * dt;
        if (x < minX) { x = minX; vx = -vx * BOUNCE; } if (x > maxX) { x = maxX; vx = -vx * BOUNCE; }
        if (y < minY) { y = minY; vy = -vy * BOUNCE; }
        if (y > maxY) { y = maxY; vy = -vy * BOUNCE; vx *= .85; if (Math.abs(vy) < 160) vy = 0; }
        rot += vx * dt / rad * 57.3;                       // rolls like a ball: the turn follows the distance travelled
        setX(x); setY(y); setR(rot);
        if (t > 2.6 || (y >= maxY && !vy && Math.abs(vx) < 40)) { G.ticker.remove(flying); flying = null; home(); }
      };
      G.ticker.add(flying);
    };
    // decode the poses used by the throw once, while idle, so grabbing him does not stall on a big image
    const warm = () => { const w = document.createElement("div"); w.style.cssText = "position:fixed;left:-300px;top:0;width:84px;height:78px;opacity:.01;pointer-events:none";
      w.innerHTML = POSE.shock + POSE.laugh; document.body.appendChild(w); setTimeout(() => w.remove(), 4000); };
    setTimeout(() => (window.requestIdleCallback || (f => f()))(warm), 2500);
    window.Draggable.create(charBtn, {type: "x,y", dragClickables: true, minimumMovement: 6, allowContextMenu: true,
      onPress() { if (flying) { G.ticker.remove(flying); flying = null; } G.killTweensOf(charBtn); trail = []; charBtn.style.willChange = "transform"; },
      onDragStart() { thrown = true; hush(); setPose("shock"); },
      onDrag() { const n = performance.now(); trail.push([n, this.x, this.y]); trail = trail.filter(p => n - p[0] < 90); setR(Math.max(-25, Math.min(25, (this.deltaX || 0) * 1.5))); },
      onDragEnd() {
        const a = trail[0], b = trail[trail.length - 1], dt = a && b && b[0] > a[0] ? (b[0] - a[0]) / 1000 : 0;
        const vx = dt ? (b[1] - a[1]) / dt : 0, vy = dt ? (b[2] - a[2]) / dt : 0, cap = v => Math.max(-3200, Math.min(3200, v));
        fly(cap(vx), cap(vy));
      }});
    charBtn.addEventListener("click", e => { if (thrown) { e.stopImmediatePropagation(); e.preventDefault(); thrown = false; } }, true);
  }
  root.classList.toggle("muted", muted);
  setPose(muted ? "peek" : "smug");
  wake();
  if (!muted && !store.get("greeted")) {
    store.set("greeted", true);
    setTimeout(() => { setPose("laugh", 2500); say(tr("Ciao! Sono Slabby. Ti faccio vedere come si legge il valore di una carta gradata: clicca su di me quando vuoi.", "Hi! I'm Slabby. I'll show you how to read the value of a graded card: click me whenever you like."), {ms: 9000}); }, 900);
  }
  /* ---- antics (D44): Slabby is a nuisance on purpose. He runs across the screen, pops up from behind
     the slab when you open a card, clings to the top when you scroll too fast, sits on section titles
     and butts in when you search. Never while muted, never with "reduce motion", one at a time, at
     most one every ~25 s, and he never sits on a control for more than a few seconds. ---- */
  const LINES = {
    thrown: [["Ehi! Non sono una carta da lanciare!", "Ancora! Ancora!", "Mi sono rovinato il grading…", "Atterraggio da PSA 10!"],
      ["Hey! I'm not a card to throw!", "Again! Again!", "There goes my grade…", "PSA 10 landing!"]],
    run: [["Scusa, passavo di qua!", "Non mi hai visto.", "Corro a controllare un prezzo!", "Più veloce del mercato!"],
      ["Sorry, just passing through!", "You didn't see me.", "Off to check a price!", "Faster than the market!"]],
    card: [["Bella eh? È mia.", "Non toccarla, l'ho vista prima io!", "Psst… guarda lo SlabRange.", "Questa la voglio in PSA 10."],
      ["Nice, huh? It's mine.", "Hands off, I saw it first!", "Psst… look at the value range.", "I want this one in PSA 10."]],
    side: [["Bu!", "Ancora qui?", "Ti tengo d'occhio."], ["Boo!", "Still here?", "I'm watching you."]],
    cling: [["Piano! Mi gira la testa!", "Ehi, dove corri?", "Aspettami!"], ["Slow down! I'm dizzy!", "Hey, where are you rushing?", "Wait for me!"]],
    sit: [["Mi siedo un attimo.", "Bel titolo, eh?", "Che vista da quassù."], ["Just sitting for a sec.", "Nice title, huh?", "What a view from up here."]],
    search: [["Cerchi qualcosa? Io punterei sul Charizard.", "Scrivi, scrivi… ti guardo.", "Dimmi che cerchi una carta rara!"],
      ["Looking for something? I'd go for the Charizard.", "Type away… I'm watching.", "Tell me you're after a rare card!"]],
  };
  const pick = a => { if (Array.isArray(a[0])) a = a[EN() ? 1 : 0]; return a[Math.floor(Math.random() * a.length)]; };
  const NO = () => muted || RM;
  let busy = false, lastAntic = Date.now(), live = [];
  function sprite(cls, pose, text, flip) {
    const el = document.createElement("div");
    el.className = "sb-act " + cls + (flip ? " flip" : "");
    el.setAttribute("aria-hidden", "true");
    // peeking poses hug the edge they come out of: bottom for peek_top, left for peek_side
    const fit = pose === "peek_side" ? "xMinYMax meet" : pose === "peek_top" ? "xMidYMax meet" : "";
    const svg = fit ? POSE[pose].replace("<svg ", `<svg preserveAspectRatio="${fit}" `) : POSE[pose];
    el.innerHTML = `<div class="sb-body">${svg}</div>${text ? `<span class="sb-pop">${text}</span>` : ""}`;
    live.push(el);
    return el;
  }
  function drop(el, ms) { setTimeout(() => { el.remove(); live = live.filter(x => x !== el); }, ms); }
  function stopAntics() { live.forEach(el => el.remove()); live = []; busy = false; root.classList.remove("away"); }
  function begin() { if (NO() || busy) return false; busy = true; lastAntic = Date.now(); hush(); return true; }
  function end(ms) { setTimeout(() => { busy = false; root.classList.remove("away"); }, ms); }

  // 1. runs across the screen, stops in the middle to look at you, runs off; click him and he flees
  function run() {
    if (!begin()) return;
    root.classList.add("away");
    const ltr = Math.random() < .5, W = innerWidth, y = 30 + Math.random() * 40;
    const el = sprite("sb-run" + (G ? " gs" : ""), "run", pick(LINES.run), !ltr);
    el.style.top = y + "vh";
    document.body.appendChild(el);
    const from = ltr ? -220 : W + 40, mid = W * (ltr ? .44 : .5), to = ltr ? W + 40 : -220;
    if (G) {                          // D344: he hops as he runs, brakes with a squash, looks at you, sprints off
      const body = el.querySelector(".sb-body");
      const hop = G.to(body, {y: -14, duration: .17, ease: "power1.out", yoyo: true, repeat: -1});
      const tl = G.timeline({onComplete: () => { hop.kill(); el.remove(); live = live.filter(x => x !== el); end(0); }});
      tl.set(el, {x: from})
        .to(el, {x: mid, duration: 2.4, ease: "power1.inOut"})
        .call(() => hop.pause())
        .to(body, {y: 0, scaleX: 1.18, scaleY: .8, transformOrigin: "50% 100%", duration: .12, ease: "power2.out"})
        .to(body, {scaleX: 1, scaleY: 1, duration: .6, ease: "elastic.out(1, .35)"})
        .to({}, {duration: 1})
        .to(body, {scaleX: .85, scaleY: 1.15, duration: .12})
        .call(() => hop.play())
        .to(el, {x: to, duration: 1.4, ease: "power2.in"});
      el.addEventListener("pointerdown", () => { tl.timeScale(4); hop.timeScale(3); el.classList.add("hit"); el.querySelector(".sb-pop") && (el.querySelector(".sb-pop").textContent = tr("Ahi!", "Ouch!")); });
      return;
    }
    const anim = el.animate([{transform: `translateX(${from}px)`}, {transform: `translateX(${mid}px)`, offset: .4},
      {transform: `translateX(${mid}px)`, offset: .66}, {transform: `translateX(${to}px)`}], {duration: 6200, easing: "linear"});
    el.addEventListener("pointerdown", () => { anim.playbackRate = 4; el.classList.add("hit"); el.querySelector(".sb-pop") && (el.querySelector(".sb-pop").textContent = tr("Ahi!", "Ouch!")); });
    anim.onfinish = () => { el.remove(); live = live.filter(x => x !== el); end(0); };
  }
  // 2. card page: pops up from behind the card, then now and then from its side when you hover it
  function cardPeek(side) {
    const stage = document.querySelector("#app .stage"), slab = stage && stage.querySelector(".slab");
    if (!slab || !begin()) return;
    let el;
    if (side) {   // a window glued to the slab's right edge: whatever is left of it is hidden, so he seems to come out from behind
      const r = slab.getBoundingClientRect();
      if (innerWidth - r.right < r.height * .42 * .8 + 40) { busy = false; return; }   // no room on the right (phones): skip
      el = sprite("sb-sidewin", "peek_side", pick(LINES.side));
      el.style.setProperty("--sh", Math.round(r.height * .42) + "px");
      // inside the card's own box: the card column is sticky, so a sprite placed on the page would drift away on scroll
      stage.classList.add("sb-host");
      el.style.left = (slab.offsetLeft + slab.offsetWidth - 2) + "px"; el.style.top = (slab.offsetTop + r.height * .3 - 44) + "px";
      stage.appendChild(el);
    } else {
      stage.classList.add("sb-host");
      el = sprite("sb-behind", "peek_top", pick(LINES.card));
      el.style.left = (slab.offsetLeft + slab.offsetWidth / 2) + "px";
      el.style.top = slab.offsetTop + "px";
      el.style.setProperty("--sw", slab.offsetWidth + "px");
      stage.insertBefore(el, stage.firstChild);
    }
    el.addEventListener("pointerdown", () => el.classList.add("hit"));
    drop(el, side ? 3200 : 5200); end(side ? 3200 : 5200);
  }
  // 3. scrolling too fast: he drops from the top edge and hangs there
  let lastY = scrollY, lastT = performance.now(), jumpT = 0;     // jumps caused by changing page do not count
  addEventListener("hashchange", () => { jumpT = performance.now(); });
  document.addEventListener("click", e => { if (e.target.closest("a[href^='#'],[data-sec]")) jumpT = performance.now(); }, true);
  addEventListener("scroll", () => {
    const now = performance.now(), v = Math.abs(scrollY - lastY) / Math.max(1, now - lastT) * 1000;
    lastY = scrollY; lastT = now;
    if (v > 4200 && now - jumpT > 1200 && Date.now() - lastAntic > 15000 && begin()) {
      const el = sprite("sb-cling" + (document.getElementById("slabby-cling") ? "" : " upside"), "cling", pick(LINES.cling));
      el.style.left = (25 + Math.random() * 50) + "%";
      document.body.appendChild(el); drop(el, 2600); end(2600);
    }
  }, {passive: true});
  // 4. sits on the title of a section you are looking at; hop off when you point at him
  function sit() {
    const hs = [...document.querySelectorAll("#app .boxtitle h2, #app .sechead h2")].filter(h => { const r = h.getBoundingClientRect(); return r.top > 80 && r.bottom < innerHeight - 80; });
    if (!hs.length || !begin()) return;
    const h = hs[0]; h.classList.add("sb-host");
    const el = sprite("sb-sit", "sit", pick(LINES.sit));
    h.appendChild(el);
    el.addEventListener("pointerenter", () => { el.classList.add("hit"); drop(el, 450); });
    drop(el, 6000); end(6000);
  }
  // 5. butts in when you start a search
  const q = document.getElementById("q");
  if (q) q.addEventListener("focus", () => {
    if (store.get("searchjoke") || !begin()) return;
    store.set("searchjoke", true);
    const box = q.closest(".search") || q.parentElement; box.classList.add("sb-host");
    const el = sprite("sb-search", "wave", pick(LINES.search));
    box.appendChild(el); drop(el, 3600); end(3600);
  });
  addEventListener("hashchange", () => { stopAntics(); });
  window.addEventListener("slabwise:view", e => {
    if (e.detail === "card") setTimeout(() => { if (!NO()) { busy = false; cardPeek(false); } }, 1400);
  });
  document.addEventListener("pointerenter", e => {
    if (e.target.closest && e.target.closest("#app .stage .slab") && location.hash.startsWith("#c-") && Math.random() < .35 && Date.now() - lastAntic > 9000) cardPeek(true);
  }, true);
  // the scheduler: something every 22–40 s while the page is in view
  (function tick() {
    setTimeout(() => {
      if (!NO() && !busy && document.visibilityState === "visible" && bubble.hidden && pose !== "sleep") {
        const opts = [run, run, sit];
        pick(opts)();
      }
      tick();
    }, 22000 + Math.random() * 18000);
  })();

  // which file fills each pose slot (the pose sheet in the preview, #pose, reads this)
  const SLOTS = POSES.concat(Object.keys(EXTRA)).map(p => ({pose: p, own: !!document.getElementById("slabby-" + p),
    uses: document.getElementById("slabby-" + p) ? p : EXTRA[p], svg: POSE[p]}));
  window.Slabby = {say, setPose, mute, run, sit, cardPeek, SLOTS, offerRequest, reqForm};
})();
