"""Build a self-contained dashboard (tracker/dashboard/index.html) from the tracker data.

Full-page metrics (``runs_fullpage.csv``) are the PRIMARY series; snippet metrics (``runs.csv``) are
shown as a secondary comparison baseline ("snippets overstate homogeneity"). Data is embedded in the
HTML, so it renders on GitHub Pages and by simply opening the file. Stdlib only -> runs in CI.

Usage:
    python tracker/dashboard/build.py
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

SNIP = Path("tracker/data/runs.csv")
FULL = Path("tracker/data/runs_fullpage.csv")
OUT = Path("tracker/dashboard/index.html")


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    for r in rows:
        r["vendi"] = float(r["vendi"])
        r["n_results"] = int(r["n_results"])
        if "n_fullpage" in r and r["n_fullpage"] != "":
            r["n_fullpage"] = int(r["n_fullpage"])
    return rows


def overall_by_date(rows: list[dict], dates: list[str]) -> list:
    by = defaultdict(list)
    for r in rows:
        by[r["date"]].append(r["vendi"])
    return [round(mean(by[d]), 3) if by.get(d) else None for d in dates]


def build_payload() -> dict:
    full, snip = load(FULL), load(SNIP)
    primary = full if full else snip
    mode = "full-page" if full else "snippet"

    dates = sorted({r["date"] for r in primary})
    latest = dates[-1]
    latest_rows = [r for r in primary if r["date"] == latest]
    cats = sorted({r["category"] for r in primary})

    leaderboard = sorted(latest_rows, key=lambda r: r["vendi"])
    by_date_cat = defaultdict(list)
    for r in primary:
        by_date_cat[(r["date"], r["category"])].append(r["vendi"])
    series = {c: [round(mean(by_date_cat[(d, c)]), 3) if by_date_cat[(d, c)] else None for d in dates]
              for c in cats}

    cov = None
    if full:
        t = sum(r["n_results"] for r in full)
        f = sum(r["n_fullpage"] for r in full)
        cov = round(f / t, 3) if t else None
    snip_overall = overall_by_date(snip, dates) if (full and snip) else None
    snip_latest = None
    if full and snip:
        sl = [r["vendi"] for r in snip if r["date"] == latest]
        snip_latest = round(mean(sl), 2) if sl else None

    dom = defaultdict(list)
    for r in latest_rows:
        dom[r["category"]].append(r["vendi"])
    domains = [{"cat": c, "vendi": round(mean(dom[c]), 2)} for c in sorted(dom, key=lambda c: mean(dom[c]))]

    return {
        "mode": mode, "dates": dates, "latest": latest, "n_queries": len(latest_rows),
        "cats": cats, "overall": overall_by_date(primary, dates), "snip_overall": snip_overall,
        "series": series, "coverage": cov,
        "primary_mean": round(mean([r["vendi"] for r in latest_rows]), 2), "snippet_mean": snip_latest,
        "domains": domains,
        "leaderboard": [{"query": r["query"], "category": r["category"],
                         "vendi": round(r["vendi"], 2), "n": r["n_results"]} for r in leaderboard],
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
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .wrap { max-width:1000px; margin:0 auto; padding:0 16px 48px; }
  header { padding:24px 16px 8px; max-width:1000px; margin:0 auto; }
  h1 { margin:0 0 4px; font-size:22px; }
  .sub { color:var(--muted); font-size:14px; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; margin:16px 0; }
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
<header>
  <h1>Homogenization Tracker</h1>
  <div class="sub" id="sub"></div>
</header>
<div class="wrap">
  <div class="kpis" id="kpis"></div>

  <div class="card">
    <h2>Homogeneity by domain</h2>
    <p>Mean Vendi (effective number of distinct results) per knowledge domain — latest run,
       full-page. Lower = results repeat each other more.</p>
    <canvas id="domains" height="200"></canvas>
  </div>

  <div class="card">
    <h2>How repetitive are the top results, by query</h2>
    <p>Full-page Vendi per query, latest run, colored by domain. Lower = more homogeneous.</p>
    <canvas id="leaderboard" height="560"></canvas>
  </div>

  <div class="card">
    <h2>Diversity over time</h2>
    <p>Mean Vendi per run — full-page (solid white) vs snippet (dashed yellow) and by domain.
       Full-page sits higher: snippets overstate homogeneity. Populates as runs accumulate.</p>
    <canvas id="timeseries" height="320"></canvas>
  </div>
</div>
<footer>
  Full-page content (Google top results via SerpAPI, pages via ScrapingRobot, MiniLM embeddings).
  Video results excluded. Forward-looking companion to the AI-homogenization study.
</footer>

<script>
const DATA = __DATA__;
const PALETTE = ["#5aa9e6","#e6a15a","#7ac77a","#c77ab0","#e6d15a","#5ae6c1","#e65a5a","#9a8ae6",
                 "#8ae65a","#e68a5a","#5a7ae6","#b0b0b0"];
const catColor = {};
DATA.cats.forEach((c,i)=> catColor[c] = PALETTE[i % PALETTE.length]);

document.getElementById("sub").textContent =
  `Latest run ${DATA.latest} · ${DATA.n_queries} queries · ${DATA.mode}`
  + (DATA.coverage!=null ? ` · ${Math.round(DATA.coverage*100)}% page coverage` : "")
  + ` · ${DATA.dates.length} run(s)`;

const lb = DATA.leaderboard;
const mostHom = lb[0], mostDiv = lb[lb.length-1];
const kpis = [
  ["Most homogeneous", mostHom.query, `Vendi ${mostHom.vendi} of ${mostHom.n}`],
  ["Most diverse", mostDiv.query, `Vendi ${mostDiv.vendi} of ${mostDiv.n}`],
  ["Mean Vendi (full-page)", DATA.primary_mean.toFixed(2), `across ${DATA.n_queries} queries`],
];
if (DATA.snippet_mean!=null)
  kpis.push(["Full-page vs snippet", `${DATA.primary_mean} vs ${DATA.snippet_mean}`,
             "snippets overstate homogeneity"]);
document.getElementById("kpis").innerHTML = kpis.map(k =>
  `<div class="kpi"><div class="label">${k[0]}</div>
   <div class="value">${k[1]} <small>${k[2]}</small></div></div>`).join("");

new Chart(document.getElementById("domains"), {
  type: "bar",
  data: { labels: DATA.domains.map(d=>d.cat),
    datasets: [{ data: DATA.domains.map(d=>d.vendi),
      backgroundColor: DATA.domains.map(d=>catColor[d.cat]) }] },
  options: { plugins:{legend:{display:false}},
    scales:{ x:{grid:{display:false},ticks:{color:"#e8eaed"}},
      y:{beginAtZero:true,grid:{color:"#262a33"},ticks:{color:"#9aa0aa"},title:{display:true,text:"mean Vendi",color:"#9aa0aa"}} } },
});

new Chart(document.getElementById("leaderboard"), {
  type: "bar",
  data: { labels: lb.map(d=>d.query),
    datasets: [{ label:"Vendi", data: lb.map(d=>d.vendi), backgroundColor: lb.map(d=>catColor[d.category]) }] },
  options: { indexAxis:"y",
    plugins:{ legend:{display:false},
      tooltip:{ callbacks:{ afterLabel:(c)=> lb[c.dataIndex].category } } },
    scales:{ x:{beginAtZero:true,grid:{color:"#262a33"},ticks:{color:"#9aa0aa"}},
      y:{grid:{display:false},ticks:{color:"#e8eaed",font:{size:10}}} } },
});

const tsDatasets = [{
  label:"Overall (full-page)", data:DATA.overall, borderColor:"#ffffff", backgroundColor:"#ffffff",
  borderWidth:3, tension:.25, pointRadius:3,
}];
if (DATA.snip_overall)
  tsDatasets.push({ label:"Overall (snippet)", data:DATA.snip_overall, borderColor:"#ffd166",
    backgroundColor:"#ffd166", borderWidth:2, borderDash:[6,4], tension:.25, pointRadius:2 });
tsDatasets.push(...DATA.cats.map(c => ({
  label:c, data:DATA.series[c], borderColor:catColor[c], backgroundColor:catColor[c],
  borderWidth:1.5, tension:.25, pointRadius:2 })));
new Chart(document.getElementById("timeseries"), {
  type:"line", data:{ labels:DATA.dates, datasets:tsDatasets },
  options:{ plugins:{legend:{labels:{color:"#e8eaed",boxWidth:12,font:{size:11}}}},
    scales:{ x:{grid:{color:"#262a33"},ticks:{color:"#9aa0aa"}},
      y:{grid:{color:"#262a33"},ticks:{color:"#9aa0aa"},title:{display:true,text:"mean Vendi",color:"#9aa0aa"}} } },
});
</script>
</body>
</html>
"""


def main() -> None:
    payload = build_payload()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(TEMPLATE.replace("__DATA__", json.dumps(payload)), encoding="utf-8")
    print(f"Wrote {OUT} (mode={payload['mode']}, {len(payload['dates'])} run(s), "
          f"{payload['n_queries']} queries, coverage={payload['coverage']}).")


if __name__ == "__main__":
    main()
