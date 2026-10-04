"""Build a self-contained dashboard (tracker/dashboard/index.html) from the tracker data.

Reads ``tracker/data/runs.csv`` and writes a single static HTML file with the data **embedded**
(so it renders on GitHub Pages and by simply opening the file — no fetch/CORS needed). Charts are
drawn client-side with Chart.js from a CDN. Regenerated after each weekly run by the workflow.

Stdlib only (csv/json) so it runs in CI without extra dependencies.

Usage:
    python tracker/dashboard/build.py
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

DATA = Path("tracker/data/runs.csv")
FULL = Path("tracker/data/runs_fullpage.csv")
OUT = Path("tracker/dashboard/index.html")


def load_rows() -> list[dict]:
    rows = list(csv.DictReader(DATA.open(encoding="utf-8")))
    for r in rows:
        r["vendi"] = float(r["vendi"])
        r["mean_pairwise_cosine"] = float(r["mean_pairwise_cosine"])
        r["mean_marginal_novelty"] = float(r["mean_marginal_novelty"])
        r["n_results"] = int(r["n_results"])
    return rows


def build_payload(rows: list[dict], full_rows: list[dict]) -> dict:
    dates = sorted({r["date"] for r in rows})
    latest = dates[-1]
    latest_rows = [r for r in rows if r["date"] == latest]
    cats = sorted({r["category"] for r in rows})

    leaderboard = sorted(latest_rows, key=lambda r: r["vendi"])
    by_date_cat = defaultdict(list)
    by_date = defaultdict(list)
    for r in rows:
        by_date_cat[(r["date"], r["category"])].append(r["vendi"])
        by_date[r["date"]].append(r["vendi"])

    series = {
        c: [round(mean(by_date_cat[(d, c)]), 3) if by_date_cat[(d, c)] else None for d in dates]
        for c in cats
    }
    overall = [round(mean(by_date[d]), 3) for d in dates]

    fp_by_date = defaultdict(list)
    fp_cov_n = fp_cov_d = 0
    for r in full_rows:
        fp_by_date[r["date"]].append(float(r["vendi"]))
        fp_cov_n += int(r.get("n_fullpage", 0))
        fp_cov_d += int(r["n_results"])
    fp_overall = [round(mean(fp_by_date[d]), 3) if fp_by_date.get(d) else None for d in dates]
    fp_with = [d for d in dates if fp_by_date.get(d)]
    fp_mean_latest = round(mean(fp_by_date[fp_with[-1]]), 2) if fp_with else None
    snip_mean_matched = round(mean(by_date[fp_with[-1]]), 2) if fp_with else None

    return {
        "dates": dates,
        "latest": latest,
        "n_queries": len(latest_rows),
        "cats": cats,
        "overall": overall,
        "series": series,
        "leaderboard": [
            {"query": r["query"], "category": r["category"],
             "vendi": round(r["vendi"], 2), "n": r["n_results"]}
            for r in leaderboard
        ],
        "has_fullpage": bool(full_rows),
        "fullpage_overall": fp_overall,
        "fullpage_coverage": round(fp_cov_n / fp_cov_d, 3) if fp_cov_d else None,
        "fullpage_mean_latest": fp_mean_latest,
        "snippet_mean_matched": snip_mean_matched,
    }


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Homogenization Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root { --bg:#0f1115; --card:#181b22; --fg:#e8eaed; --muted:#9aa0aa; --accent:#5aa9e6; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--fg);
         font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  header { padding:24px 20px 8px; }
  h1 { margin:0 0 4px; font-size:22px; }
  .sub { color:var(--muted); font-size:14px; }
  .wrap { max-width:1000px; margin:0 auto; padding:0 16px 48px; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin:16px 0; }
  .kpi { background:var(--card); border-radius:12px; padding:14px 16px; }
  .kpi .label { color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
  .kpi .value { font-size:20px; margin-top:4px; }
  .kpi .value small { color:var(--muted); font-size:13px; }
  .card { background:var(--card); border-radius:12px; padding:16px; margin:16px 0; }
  .card h2 { margin:0 0 4px; font-size:16px; }
  .card p { margin:0 0 12px; color:var(--muted); font-size:13px; }
  footer { color:var(--muted); font-size:12px; text-align:center; padding:16px; }
  a { color:var(--accent); }
</style>
</head>
<body>
<header class="wrap">
  <h1>Homogenization Tracker</h1>
  <div class="sub" id="sub"></div>
</header>
<div class="wrap">
  <div class="kpis" id="kpis"></div>

  <div class="card">
    <h2>How repetitive are the top results, by query</h2>
    <p>Vendi score = the effective number of <em>distinct</em> results among the top ~10.
       Lower = more homogeneous. Latest run.</p>
    <canvas id="leaderboard" height="520"></canvas>
  </div>

  <div class="card">
    <h2>Diversity over time</h2>
    <p>Mean Vendi per run — overall (snippet = solid white; full-page = dashed yellow) and by
       category. Full-page sits higher: snippets overstate homogeneity. Populates as runs accumulate.</p>
    <canvas id="timeseries" height="320"></canvas>
  </div>
</div>
<footer>
  Generated from <code>tracker/data/runs.csv</code>. Snippet-level (Google top-10 via SerpAPI),
  MiniLM embeddings. Forward-looking companion to the AI-homogenization study.
</footer>

<script>
const DATA = __DATA__;

const PALETTE = ["#5aa9e6","#e6a15a","#7ac77a","#c77ab0","#e6d15a","#5ae6c1","#e65a5a","#9a8ae6",
                 "#8ae65a","#e68a5a","#5a7ae6","#b0b0b0"];
const catColor = {};
DATA.cats.forEach((c,i)=> catColor[c] = PALETTE[i % PALETTE.length]);

// --- subtitle + KPIs
document.getElementById("sub").textContent =
  `Latest run ${DATA.latest} · ${DATA.n_queries} queries · ${DATA.dates.length} run(s) to date`;

const lb = DATA.leaderboard;
const mostHom = lb[0], mostDiv = lb[lb.length-1];
const overallLatest = DATA.overall[DATA.overall.length-1];
const kpis = [
  ["Most homogeneous", `${mostHom.query}`, `Vendi ${mostHom.vendi} of ${mostHom.n}`],
  ["Most diverse", `${mostDiv.query}`, `Vendi ${mostDiv.vendi} of ${mostDiv.n}`],
  ["Mean Vendi (latest)", overallLatest.toFixed(2), `snippet-level, ${DATA.n_queries} queries`],
];
if (DATA.has_fullpage) {
  kpis.push(["Full-page vs snippet",
    `${DATA.fullpage_mean_latest} vs ${DATA.snippet_mean_matched}`,
    `full-page higher · ${Math.round(DATA.fullpage_coverage*100)}% page coverage`]);
}
document.getElementById("kpis").innerHTML = kpis.map(k =>
  `<div class="kpi"><div class="label">${k[0]}</div>
   <div class="value">${k[1]} <small>${k[2]}</small></div></div>`).join("");

// --- leaderboard (horizontal bar, sorted most→least homogeneous)
new Chart(document.getElementById("leaderboard"), {
  type: "bar",
  data: {
    labels: lb.map(d => d.query),
    datasets: [{
      label: "Vendi (effective distinct results)",
      data: lb.map(d => d.vendi),
      backgroundColor: lb.map(d => catColor[d.category]),
    }],
  },
  options: {
    indexAxis: "y",
    plugins: { legend: { display:false },
      tooltip: { callbacks: { afterLabel: (c)=> DATA.leaderboard[c.dataIndex].category } } },
    scales: {
      x: { beginAtZero:true, grid:{color:"#262a33"}, ticks:{color:"#9aa0aa"} },
      y: { grid:{display:false}, ticks:{color:"#e8eaed", font:{size:11}} },
    },
  },
});

// --- time series (overall + per category)
const tsDatasets = [{
  label: "Overall (snippet)", data: DATA.overall, borderColor:"#ffffff", backgroundColor:"#ffffff",
  borderWidth:3, tension:.25, pointRadius:3,
}];
if (DATA.has_fullpage) {
  tsDatasets.push({
    label: "Overall (full-page)", data: DATA.fullpage_overall, borderColor:"#ffd166",
    backgroundColor:"#ffd166", borderWidth:3, borderDash:[6,4], tension:.25, pointRadius:3,
  });
}
tsDatasets.push(...DATA.cats.map(c => ({
  label: c, data: DATA.series[c], borderColor: catColor[c], backgroundColor: catColor[c],
  borderWidth:1.5, tension:.25, pointRadius:2,
})));
new Chart(document.getElementById("timeseries"), {
  type: "line",
  data: { labels: DATA.dates, datasets: tsDatasets },
  options: {
    plugins: { legend: { labels:{color:"#e8eaed", boxWidth:12, font:{size:11}} } },
    scales: {
      x: { grid:{color:"#262a33"}, ticks:{color:"#9aa0aa"} },
      y: { grid:{color:"#262a33"}, ticks:{color:"#9aa0aa"}, title:{display:true,text:"mean Vendi",color:"#9aa0aa"} },
    },
  },
});
</script>
</body>
</html>
"""


def main() -> None:
    rows = load_rows()
    full_rows = list(csv.DictReader(FULL.open(encoding="utf-8"))) if FULL.exists() else []
    payload = build_payload(rows, full_rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(TEMPLATE.replace("__DATA__", json.dumps(payload)), encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} rows, {len(payload['dates'])} run(s), "
          f"{payload['n_queries']} queries in latest).")


if __name__ == "__main__":
    main()
