// Slabwise clock (D116): GitHub's own schedules arrive hours late or not at all, so a Cloudflare Worker with cron
// triggers starts the workflows on time. Secret GITHUB_TOKEN: fine-grained token, this repository only, Actions read/write.
// The site build and the site check follow the collection by themselves (workflow_run), so they are not here.
const REPO = "oski666/slabwise-engine";
const JOBS = {
  "11 4 * * *": "raccolta-tcgcharts.yml",       // 05:11 in Italy (winter)
  "23 11,17,23 * * *": "occasioni.yml",
  "41 * * * *": ["misura-occasioni.yml",         // the measurement stops by itself after 9 November
                 "richieste.yml"],              // D117; since 4 Nov only every 3 hours (EVERY_3H below)
};

export default {
  async scheduled(event, env) {
    const errors = [];
    // 4 Nov (GitHub minutes): the hourly trigger stays as configured in Cloudflare, but runs only every third hour
    if (event.cron === "41 * * * *" && new Date(event.scheduledTime).getUTCHours() % 3 !== 0) return;
    for (const wf of [].concat(JOBS[event.cron] || [])) {
      const r = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${wf}/dispatches`, {
      method: "POST",
      headers: {authorization: `Bearer ${env.GITHUB_TOKEN}`, accept: "application/vnd.github+json",
                "user-agent": "slabwise-orologio", "x-github-api-version": "2022-11-28"},
        body: JSON.stringify({ref: "main"}),
      });
      if (!r.ok) errors.push(`${wf}: ${r.status} ${(await r.text()).slice(0, 200)}`);
    }
    if (errors.length) throw new Error(errors.join("; "));
  },
};
