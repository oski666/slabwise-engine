// Full tcgcharts sale history of some cards (D80, D123), run INSIDE the owner's logged-in tcgcharts tab: the token never
// leaves the page. Usage (by Claude, through the browser pane): set TODO = [[card id, tcgcharts id], ...] and DB, run,
// poll window.SWH; then export with the second snippet and merge with scripts/tc_history_merge.py.
// One request every 3 seconds (permission from tcgcharts, 27 Oct 2026). Progress survives a reload (IndexedDB).
const TODO = [];
const DB = "swhist";
const KEYS = ["platform", "sale_id", "title", "grading_service", "grade", "price_cents", "sold_date", "source",
              "is_excluded", "exclusion_reason", "payment_pending", "payment_held"];
const auth = () => ({authorization: "Bearer " + localStorage.getItem("auth_token")});
const db = await new Promise((ok, ko) => { const r = indexedDB.open(DB, 1); r.onupgradeneeded = () => r.result.createObjectStore("done"); r.onsuccess = () => ok(r.result); r.onerror = ko; });
const get = k => new Promise(ok => { const r = db.transaction("done").objectStore("done").get(k); r.onsuccess = () => ok(r.result); });
const put = (k, v) => new Promise(ok => { const t = db.transaction("done", "readwrite"); t.objectStore("done").put(v, k); t.oncomplete = ok; });
window.SWH = {state: "running", done: 0, total: TODO.length * 4, rows: 0, err: []};
(async () => {
  for (const [cid, tc] of TODO) for (const g of [10, 9, 8, 7]) {
    const k = cid + "|" + g;
    if (await get(k)) { SWH.done++; continue; }
    const out = [];
    try {
      for (let page = 1; ; page++) {
        const q = new URLSearchParams({cardId: tc, cardType: "base", sort: "sold_date", order: "DESC", page, limit: 100, company: "PSA", grade: g});
        const r = await fetch("/api/card-sales?" + q, {headers: auth()});
        if (!r.ok) throw new Error(r.status);
        const d = (await r.json()).data;
        for (const s of d.sales) { const o = {card: cid, tc_grade: g}; for (const x of KEYS) o[x] = s[x] ?? null; out.push(o); }
        await new Promise(z => setTimeout(z, 3000));
        if (!d.pagination.has_next) break;
      }
      await put(k, out); SWH.done++; SWH.rows += out.length;
    } catch (e) { SWH.err.push(k + " " + e.message); await new Promise(z => setTimeout(z, 10000)); }
  }
  SWH.state = "finished";
})();

/* export (second snippet): every stored card/grade as one JSON file in the owner's Downloads
const all = await new Promise(ok => { const out = []; const c = db.transaction("done").objectStore("done").openCursor();
  c.onsuccess = e => { const k = e.target.result; if (k) { out.push(...k.value); k.continue(); } else ok(out); }; });
const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(all)], {type: "application/json"}));
a.download = "slabwise_hist.json"; document.body.appendChild(a); a.click(); a.remove();
*/
