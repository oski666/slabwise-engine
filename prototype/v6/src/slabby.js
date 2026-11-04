/* Slabby: la guida di Slabwise (docs/DESIGN.md §3.6). Pose dal character sheet in prototype/character/slabby/ (sostituibile).
   Regole: non copre i contenuti, un fumetto alla volta, si chiude da solo, si zittisce con un clic,
   con "riduci movimento" non si muove. */
(function () {
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Poses come from the character sheet (prototype/character/slabby/poses.svg, injected by build.py):
  // a symbol "slabby-<pose>" for each pose. Replacing the character = replacing that file (see its README).
  const POSES = ["smug", "drool", "sleep", "laugh", "shock", "bliss", "peek"];
  const POSE = {};
  for (const p of POSES) {
    const sym = document.getElementById("slabby-" + p);
    const vb = sym ? sym.getAttribute("viewBox") : "0 0 200 200";
    POSE[p] = `<svg viewBox="${vb}" aria-hidden="true"><use href="#slabby-${p}"/></svg>`;
  }

  const TOUR = {
    mercato: {pose: "smug", text: "Qui trovi tutti gli slab. Guarda la barra blu: più è corta, più siamo sicuri del valore.", target: "[data-tour=grid] .fork"},
    card: {pose: "bliss", text: "Questo è il valore di oggi. La barra è la forchetta: 8 volte su 10 il valore vero sta lì dentro.", target: "[data-tour=fork]", next: {text: "I puntini rosa nel grafico sono vendite che non mi convincono. Passaci sopra!", target: "[data-tour=chart]"}},
    settimana: {pose: "laugh", text: "Le 5 storie della settimana: ognuna è già un reel. Copia, incolla nel Reel Studio, fatto.", target: "[data-tour=story]"},
    deal: {pose: "drool", text: "Affari calcolati in euro, con spedizione, IVA e dogana. L'anello è la probabilità che sia un affare vero.", target: "[data-tour=dealfilters]"},
    metodo: {pose: "smug", text: "Qui ti spiego come facciamo i conti. Nessuna magia, solo un modello onesto.", target: null},
  };
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem("slabby-" + k)); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem("slabby-" + k, JSON.stringify(v)); } catch (e) {} },
  };
  const seen = new Set(store.get("seen") || []);      // a section's tip appears once, ever; the menu replays them

  const root = document.createElement("div");
  root.className = "slabby";
  root.innerHTML = `<div class="sb-bubble" role="status" aria-live="polite" hidden></div>
    <button class="sb-char" aria-label="Slabby, la tua guida: apri il menu" aria-expanded="false"></button>`;
  document.body.appendChild(root);
  const charBtn = root.querySelector(".sb-char"), bubble = root.querySelector(".sb-bubble");
  let pose = "smug", muted = !!store.get("muted"), hideT, idleT, poseT;

  function setPose(p, ms) {
    clearTimeout(poseT);
    pose = p;
    charBtn.innerHTML = POSE[p];
    charBtn.dataset.pose = p;
    if (ms) poseT = setTimeout(() => setPose(muted ? "peek" : "smug"), ms);
  }
  function say(text, opts = {}) {
    if (muted && !opts.force) return;
    clearTimeout(hideT);
    bubble.innerHTML = `<p>${text}</p>${opts.actions ? `<div class="sb-actions">${opts.actions}</div>` : ""}<button class="sb-x" aria-label="Chiudi">×</button>`;
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
    setPose(on ? "peek" : "laugh", on ? 0 : 1600);
  }
  function menu() {
    if (muted) { mute(false); say("Eccomi di nuovo! Clicca su di me quando vuoi una mano.", {ms: 4000}); return; }
    say("Cosa ti mostro?", {sticky: true, menu: true, actions:
      `<button data-sb="fork">Cos'è la forchetta?</button><button data-sb="deal">Portami agli affari</button><button data-sb="week">Le storie della settimana</button><button data-sb="mute" class="ghost">Fammi stare zitto</button>`});
  }
  charBtn.addEventListener("click", () => charBtn.getAttribute("aria-expanded") === "true" ? hush() : menu());
  bubble.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.classList.contains("sb-x")) return hush();
    const a = b.dataset.sb;
    if (a === "mute") return mute(true);
    if (a === "deal") { location.hash = "deal"; return; }
    if (a === "week") { location.hash = "settimana"; return; }
    if (a === "fork") {
      if (!location.hash.startsWith("#c-")) location.hash = "c-swsh7-215";
      setTimeout(() => { say(TOUR.card.text, {ms: 9000}); spot("[data-tour=fork]"); }, 350);
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
      say(t.text, {ms: 8000, actions: t.target ? `<button data-sb-spot="${t.target}">Mostrami</button>` : ""});
      if (t.next) setTimeout(() => { if (!muted && location.hash.startsWith("#c-")) { say(t.next.text, {ms: 7000, actions: `<button data-sb-spot="${t.next.target}">Mostrami</button>`}); } }, 9500);
    }, 600);
  });
  bubble.addEventListener("click", e => { const b = e.target.closest("[data-sb-spot]"); if (b) { spot(b.dataset.sbSpot); hush(); } });

  // reactions to what you look at (rate-limited, never while muted)
  let lastReact = 0;
  function react(p, text) {
    const now = Date.now(); if (muted || now - lastReact < 6000) return;
    lastReact = now; setPose(p, 2600); if (text) say(text, {ms: 4000});
  }
  document.addEventListener("pointerover", e => {
    const t = e.target;
    if (t.closest && t.closest("circle.s.bad")) react("shock", "Questa vendita puzza! Per questo pesa quasi zero.");
    else if (t.closest && t.closest(".deal.top")) react("drool", "Questo sì che è un affare…");
    else if (t.closest && t.closest(".deal.sus")) react("shock", "Troppo bello per essere vero. Occhio!");
  });

  // falls asleep when you leave it alone, wakes up laughing
  function wake() {
    clearTimeout(idleT);
    if (pose === "sleep") setPose("laugh", 1500);
    idleT = setTimeout(() => { if (!muted) { hush(); setPose("sleep"); } }, 45000);
  }
  ["pointermove", "keydown", "scroll"].forEach(ev => addEventListener(ev, wake, {passive: true}));

  root.classList.toggle("muted", muted);
  setPose(muted ? "peek" : "smug");
  wake();
  if (!muted && !store.get("greeted")) {
    store.set("greeted", true);
    setTimeout(() => { setPose("laugh", 2500); say("Ciao! Sono Slabby. Ti faccio vedere come si legge il valore di uno slab: clicca su di me quando vuoi.", {ms: 9000}); }, 900);
  }
  window.Slabby = {say, setPose, mute};
})();
