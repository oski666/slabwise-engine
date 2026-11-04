/* Slabby: la guida di Slabwise (docs/DESIGN.md §3.6). Pose tratte dal character sheet in social/slabby/.
   Regole: non copre i contenuti, un fumetto alla volta, si chiude da solo, si zittisce con un clic,
   con "riduci movimento" non si muove. */
(function () {
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DEFS = `<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<filter id="ppFuzz" x="-20%" y="-20%" width="140%" height="140%"><feTurbulence type="fractalNoise" baseFrequency="0.11" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="9" xChannelSelector="R" yChannelSelector="G"/></filter>
<filter id="ppWob" x="-20%" y="-20%" width="140%" height="140%"><feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="9" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3" xChannelSelector="R" yChannelSelector="G"/></filter>
<g id="pp-trunk"><path d="M100 30 C150 30 172 70 170 120 C168 170 150 196 100 196 C50 196 32 170 30 120 C28 70 50 30 100 30 Z"/><ellipse cx="76" cy="196" rx="20" ry="11"/><ellipse cx="124" cy="196" rx="20" ry="11"/></g>
<g id="pp-horns"><path d="M66 50 Q54 22 72 12 Q80 30 86 44 Z"/><path d="M134 50 Q146 22 128 12 Q120 30 114 44 Z"/></g>
<g id="pp-armsD"><path d="M36 112 Q12 124 20 144 Q32 152 42 138 Z"/><path d="M164 112 Q188 124 180 144 Q168 152 158 138 Z"/></g>
<g id="pp-armsU"><path d="M40 108 Q12 94 16 70 Q28 60 38 76 Q38 94 50 100 Z"/><path d="M160 108 Q188 94 184 70 Q172 60 162 76 Q162 94 150 100 Z"/></g>
<g id="pp-detail" fill="none" stroke-linecap="round"><path d="M62 160 Q100 188 138 160" stroke="#2EE6FF" stroke-width="3.5"/><path d="M24 132 Q30 142 40 134" stroke="#FF2E93" stroke-width="3"/><path d="M176 132 Q170 142 160 134" stroke="#FF2E93" stroke-width="3"/><path d="M70 204 L70 196 M80 205 L80 197 M120 205 L120 197 M130 204 L130 196" stroke="#39F2A6" stroke-width="3"/><path d="M140 52 Q156 66 160 90" stroke="#2EE6FF" stroke-width="3" opacity="0.8"/></g>
<g id="pp-cheeks"><ellipse cx="58" cy="116" rx="11" ry="6" fill="#FF2E93" opacity="0.8"/><ellipse cx="142" cy="116" rx="11" ry="6" fill="#FF2E93" opacity="0.8"/></g>
<g id="pp-smug"><path d="M68 90 L92 96 M132 90 L108 96" stroke="#FF2E93" stroke-width="6" stroke-linecap="round"/><path d="M72 93 Q84 104 90 97 Z M128 93 Q116 104 110 97 Z" fill="#FFC93C"/></g>
<linearGradient id="ppTeeth" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF7D6"/><stop offset="1" stop-color="#F2CF5B"/></linearGradient>
<g id="pp-grin"><path d="M50 110 Q100 138 150 110 Q100 222 50 110 Z" fill="url(#ppTeeth)"/><path d="M52 111 L62 132 L70 120 L78 153 L86 123 L94 163 L102 124 L110 162 L118 122 L126 149 L134 118 L142 125 L148 111" fill="none" stroke="#0E1A5C" stroke-width="2.6"/><path d="M50 110 Q100 138 150 110 Q100 222 50 110 Z" fill="none" stroke="#0E1A5C" stroke-width="3.5" stroke-linejoin="round"/><path d="M52 104 Q100 132 148 104" fill="none" stroke="#2EE6FF" stroke-width="3.5" stroke-linecap="round"/><path d="M60 136 Q100 206 140 136" fill="none" stroke="#FF2E93" stroke-width="3" stroke-linecap="round"/></g>
<g id="pp-open"><path d="M50 108 Q100 132 150 108 Q100 236 50 108 Z" fill="#2A0A3A"/><ellipse cx="100" cy="160" rx="24" ry="9" fill="#FF2E93"/><path d="M50 108 Q100 132 150 108 L142 126 L134 117 L126 133 L118 122 L110 136 L102 124 L94 137 L86 123 L78 133 L70 119 L62 126 L56 111 Z" fill="url(#ppTeeth)" stroke="#0E1A5C" stroke-width="2.2" stroke-linejoin="round"/><path d="M56 122 L68 132 L74 155 L80 148 L86 167 L93 157 L100 172 L107 157 L114 167 L120 148 L126 155 L132 132 L144 122 Q100 222 56 122 Z" fill="url(#ppTeeth)" stroke="#0E1A5C" stroke-width="2.2" stroke-linejoin="round"/><path d="M50 108 Q100 132 150 108 Q100 236 50 108 Z" fill="none" stroke="#0E1A5C" stroke-width="3.5" stroke-linejoin="round"/></g>
</defs></svg>`;
  const body = arms => `<g filter="url(#ppFuzz)"><g transform="translate(-6 4)" fill="#2EE6FF"><use href="#pp-trunk"/><use href="#pp-horns"/><use href="#pp-${arms}"/></g><g transform="translate(6 -3)" fill="#FF2E93"><use href="#pp-trunk"/><use href="#pp-horns"/><use href="#pp-${arms}"/></g><g fill="#1D3FD1"><use href="#pp-trunk"/><use href="#pp-${arms}"/></g><use href="#pp-horns" fill="#FFC93C"/></g>`;
  const POSE = {
    smug: `<svg viewBox="-30 -10 260 240">${body("armsU")}<g filter="url(#ppWob)"><path d="M62 160 Q100 188 138 160" fill="none" stroke="#2EE6FF" stroke-width="3.5" stroke-linecap="round"/><use href="#pp-cheeks"/><use href="#pp-smug"/><use href="#pp-grin"/><path d="M84 70 L96 80 M116 70 L104 80" stroke="#FF2E93" stroke-width="4" stroke-linecap="round"/></g></svg>`,
    drool: `<svg viewBox="-30 -10 260 254">${body("armsD")}<g filter="url(#ppWob)"><use href="#pp-cheeks"/><circle cx="80" cy="94" r="10" fill="#FFC93C" stroke="#FF2E93" stroke-width="3"/><circle cx="120" cy="94" r="10" fill="#FFC93C" stroke="#FF2E93" stroke-width="3"/><circle cx="83" cy="90" r="3" fill="#fff"/><circle cx="123" cy="90" r="3" fill="#fff"/><use href="#pp-open" transform="translate(100 108) scale(0.78) translate(-100 -108)"/><path d="M136 112 Q142 134 137 146 Q131 134 133 114 Z" fill="#2EE6FF"/><g transform="translate(0 18) rotate(-6 100 170)"><rect x="64" y="134" width="72" height="86" rx="6" fill="#0E1A5C" stroke="#2EE6FF" stroke-width="4"/><rect x="70" y="140" width="60" height="18" rx="3" fill="#FFC93C"/><text x="100" y="153" text-anchor="middle" font-family="Mochiy Pop One, sans-serif" font-size="11" fill="#0E1A5C">GEM 10</text><rect x="72" y="164" width="56" height="48" rx="3" fill="#FF2E93" opacity="0.75"/><path d="M88 180 l6 -12 l6 12 l12 4 l-12 4 l-6 12 l-6 -12 l-12 -4 z" fill="#39F2A6"/></g><circle cx="60" cy="192" r="11" fill="#1D3FD1"/><circle cx="142" cy="186" r="11" fill="#1D3FD1"/></g></svg>`,
    sleep: `<svg viewBox="-30 -10 260 240">${body("armsD")}<g filter="url(#ppWob)"><use href="#pp-detail"/><use href="#pp-cheeks"/><path d="M68 98 Q80 108 92 98 M108 98 Q120 108 132 98" fill="none" stroke="#FF2E93" stroke-width="5" stroke-linecap="round"/><ellipse cx="100" cy="132" rx="7" ry="8" fill="#FF2E93"/><circle class="zbub" cx="126" cy="120" r="15" fill="#2EE6FF" fill-opacity="0.25" stroke="#2EE6FF" stroke-width="3"/></g><text x="152" y="22" font-family="Mochiy Pop One, sans-serif" font-size="30" fill="#2EE6FF">Z</text><text x="180" y="2" font-family="Mochiy Pop One, sans-serif" font-size="22" fill="#FF2E93">z</text></svg>`,
    laugh: `<svg viewBox="-30 -10 260 240">${body("armsU")}<g filter="url(#ppWob)"><use href="#pp-cheeks"/><path d="M68 100 Q80 86 92 100 M108 100 Q120 86 132 100" fill="none" stroke="#2EE6FF" stroke-width="5.5" stroke-linecap="round"/><use href="#pp-open"/><path d="M60 100 Q50 112 58 118 Q64 112 60 100 Z M140 100 Q150 112 142 118 Q136 112 140 100 Z" fill="#2EE6FF"/></g></svg>`,
    shock: `<svg viewBox="-30 -10 260 240">${body("armsU")}<g filter="url(#ppWob)"><ellipse cx="80" cy="96" rx="12" ry="15" fill="#FFC93C" stroke="#FF2E93" stroke-width="3"/><ellipse cx="120" cy="96" rx="12" ry="15" fill="#FFC93C" stroke="#FF2E93" stroke-width="3"/><circle cx="80" cy="97" r="2.5" fill="#0E1A5C"/><circle cx="120" cy="97" r="2.5" fill="#0E1A5C"/><use href="#pp-grin" transform="translate(100 118) scale(0.8 0.55) translate(-100 -110)"/><path d="M164 40 Q156 54 164 60 Q172 54 164 40 Z M184 66 Q178 76 184 80 Q190 76 184 66 Z" fill="#2EE6FF"/></g></svg>`,
    bliss: `<svg viewBox="-30 -10 260 240">${body("armsD")}<g filter="url(#ppWob)"><use href="#pp-detail"/><use href="#pp-cheeks"/><path d="M66 100 Q80 86 94 100 M106 100 Q120 86 134 100" fill="none" stroke="#FF2E93" stroke-width="6" stroke-linecap="round"/><use href="#pp-grin"/></g></svg>`,
    peek: `<svg viewBox="-20 0 240 130"><g filter="url(#ppFuzz)"><g transform="translate(-6 4)" fill="#2EE6FF"><use href="#pp-trunk"/><use href="#pp-horns"/></g><g transform="translate(6 -3)" fill="#FF2E93"><use href="#pp-trunk"/><use href="#pp-horns"/></g><use href="#pp-trunk" fill="#1D3FD1"/><use href="#pp-horns" fill="#FFC93C"/></g><g filter="url(#ppWob)"><path d="M68 94 L92 94 M108 94 L132 94" stroke="#FF2E93" stroke-width="6" stroke-linecap="round"/><path d="M78 96 Q83 106 88 96 Z M118 96 Q123 106 128 96 Z" fill="#FFC93C"/></g></svg>`,
  };

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
  root.innerHTML = DEFS + `<div class="sb-bubble" role="status" aria-live="polite" hidden></div>
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
