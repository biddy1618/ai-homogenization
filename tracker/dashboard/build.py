"""Build a self-contained dashboard (tracker/dashboard/index.html) from the tracker data.

All metrics are FULL-PAGE (``runs_fullpage.csv``). The headline is the DISTINCT RATIO = Vendi / pages
analysed, shown as "% of pages that are effectively distinct": raw Vendi is capped by how many pages
could be fetched, so it would drop whenever coverage drops. Data is embedded in the HTML, so it
renders on GitHub Pages and by simply opening the file. Stdlib only -> runs in CI.

Usage:
    python tracker/dashboard/build.py
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

FULL = Path("tracker/data/runs_fullpage.csv")
META = Path("tracker/data/_runs_meta.csv")
OUT = Path("tracker/dashboard/index.html")


def _providers() -> dict[str, str]:
    """run_date -> Google-results provider name, from _runs_meta.csv 'engine'."""
    if not META.exists():
        return {}
    return {r["run_date"]: "Serper.dev" if r["engine"].startswith("serper") else "SerpAPI"
            for r in csv.DictReader(META.open(encoding="utf-8"))}


def provider_switches(dates: list[str]) -> list[dict]:
    """Indices where the Google-results provider changed."""
    prov = _providers()
    seq = [prov.get(d) for d in dates]
    return [{"index": i, "label": f"{seq[i-1]} \u2192 {seq[i]}"}
            for i in range(1, len(seq)) if seq[i] and seq[i-1] and seq[i] != seq[i-1]]


def provider_summary(dates: list[str]) -> str:
    """e.g. 'SerpAPI 2026-10-04 to 2026-10-12, Serper.dev from 2026-10-19'."""
    prov = _providers()
    spans: list[list] = []
    for d in dates:
        p = prov.get(d, "unknown provider")
        if spans and spans[-1][0] == p:
            spans[-1][2] = d
        else:
            spans.append([p, d, d])
    if len(spans) == 1:
        return f"via {spans[0][0]}"
    parts = [f"{p} {a}" + (f" to {b}" if b != a else "") for p, a, b in spans[:-1]]
    return "via " + ", ".join(parts + [f"{spans[-1][0]} from {spans[-1][1]}"])


def load(path: Path) -> list[dict]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    for r in rows:
        r["vendi"] = float(r["vendi"])
        r["pct"] = 100 * float(r["distinct_ratio"])
        r["n_results"] = int(r["n_results"])
        r["n_serp"] = int(r["n_serp"])
    return rows


def overall_by_date(rows: list[dict], dates: list[str]) -> list:
    by = defaultdict(list)
    for r in rows:
        by[r["date"]].append(r["pct"])
    return [round(mean(by[d]), 1) if by.get(d) else None for d in dates]


def build_payload() -> dict:
    primary = load(FULL)

    dates = sorted({r["date"] for r in primary})
    latest = dates[-1]
    latest_rows = [r for r in primary if r["date"] == latest]
    cats = sorted({r["category"] for r in primary})

    leaderboard = sorted(latest_rows, key=lambda r: r["pct"])
    by_date_cat = defaultdict(list)
    for r in primary:
        by_date_cat[(r["date"], r["category"])].append(r["pct"])
    series = {c: [round(mean(by_date_cat[(d, c)]), 1) if by_date_cat[(d, c)] else None for d in dates]
              for c in cats}

    served = sum(r["n_serp"] for r in latest_rows)
    cov = round(sum(r["n_results"] for r in latest_rows) / served, 3) if served else None

    dom = defaultdict(list)
    for r in latest_rows:
        dom[r["category"]].append(r["pct"])
    domains = [{"cat": c, "pct": round(mean(dom[c]), 1)} for c in sorted(dom, key=lambda c: mean(dom[c]))]

    return {
        "dates": dates, "latest": latest, "n_queries": len(latest_rows),
        "switches": provider_switches(dates),
        "cats": cats, "overall": overall_by_date(primary, dates),
        "series": series, "coverage": cov,
        "primary_mean": round(mean([r["pct"] for r in latest_rows]), 1),
        "domains": domains,
        "leaderboard": [{"query": r["query"], "category": r["category"], "pct": round(r["pct"], 1),
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
    <p>Share of each domain's result pages that are effectively distinct (Vendi score ÷ pages
       analysed), latest run. Lower = the top results repeat each other more.</p>
    <canvas id="domains" height="200"></canvas>
  </div>

  <div class="card">
    <h2>How repetitive are the top results, by query</h2>
    <p>% of the analysed pages that are effectively distinct, per question, latest run, colored by
       domain. Lower = more homogeneous.</p>
    <canvas id="leaderboard" height="560"></canvas>
  </div>

  <div class="card">
    <h2>Diversity over time</h2>
    <p>Mean % distinct per run — overall (white) and by domain. Week-to-week movement per
       query is still large; read trends only once several weeks have accumulated.</p>
    <canvas id="timeseries" height="320"></canvas>
    <p id="switchnote" style="margin-top:10px"></p>
  </div>
</div>
<footer>
  Full-page content: Google's top results (__PROVIDERS__), each
  page's main text (first ~1000 words) via ScrapingRobot, MiniLM embeddings. Video results and
  unfetchable pages excluded. Forward-looking companion to the AI-homogenization study.
</footer>

<script>
const DATA = __DATA__;
const PALETTE = ["#5aa9e6","#e6a15a","#7ac77a","#c77ab0","#e6d15a","#5ae6c1","#e65a5a","#9a8ae6",
                 "#8ae65a","#e68a5a","#5a7ae6","#b0b0b0"];
const catColor = {};
DATA.cats.forEach((c,i)=> catColor[c] = PALETTE[i % PALETTE.length]);

document.getElementById("sub").textContent =
  `Latest run ${DATA.latest} · ${DATA.n_queries} queries · full-page`
  + (DATA.coverage!=null ? ` · ${Math.round(DATA.coverage*100)}% of result pages analysed` : "")
  + ` · ${DATA.dates.length} run(s)`;

const lb = DATA.leaderboard;
const mostHom = lb[0], mostDiv = lb[lb.length-1];
const kpis = [
  ["Most homogeneous", mostHom.query, `${mostHom.pct}% distinct (Vendi ${mostHom.vendi} of ${mostHom.n} pages)`],
  ["Most diverse", mostDiv.query, `${mostDiv.pct}% distinct (Vendi ${mostDiv.vendi} of ${mostDiv.n} pages)`],
  ["Mean % distinct", `${DATA.primary_mean}%`, `across ${DATA.n_queries} questions`],
];
document.getElementById("kpis").innerHTML = kpis.map(k =>
  `<div class="kpi"><div class="label">${k[0]}</div>
   <div class="value">${k[1]} <small>${k[2]}</small></div></div>`).join("");

new Chart(document.getElementById("domains"), {
  type: "bar",
  data: { labels: DATA.domains.map(d=>d.cat),
    datasets: [{ data: DATA.domains.map(d=>d.pct),
      backgroundColor: DATA.domains.map(d=>catColor[d.cat]) }] },
  options: { plugins:{legend:{display:false}},
    scales:{ x:{grid:{display:false},ticks:{color:"#e8eaed"}},
      y:{beginAtZero:true,grid:{color:"#262a33"},ticks:{color:"#9aa0aa"},title:{display:true,text:"% distinct",color:"#9aa0aa"}} } },
});

new Chart(document.getElementById("leaderboard"), {
  type: "bar",
  data: { labels: lb.map(d=>d.query),
    datasets: [{ label:"% distinct", data: lb.map(d=>d.pct), backgroundColor: lb.map(d=>catColor[d.category]) }] },
  options: { indexAxis:"y",
    plugins:{
      legend:{ display:true, position:"top", align:"end",
        labels:{ color:"#e8eaed", boxWidth:12, font:{size:11},
          generateLabels: () => DATA.cats.map(c => ({ text:c, fillStyle:catColor[c],
            strokeStyle:catColor[c], fontColor:"#e8eaed", lineWidth:0, hidden:false })) },
        onClick: () => {} },
      tooltip:{ callbacks:{ afterLabel:(c)=> lb[c.dataIndex].category } } },
    scales:{ x:{beginAtZero:true,grid:{color:"#262a33"},ticks:{color:"#9aa0aa"}},
      y:{grid:{display:false},ticks:{color:"#e8eaed",font:{size:10}}} } },
});

const crossesSwitch = (i) => DATA.switches.some(s => s.index === i + 1);
const switchSegment = { borderDash: ctx => crossesSwitch(ctx.p0DataIndex) ? [2,5] : undefined };
const tsDatasets = [{
  label:"Overall", data:DATA.overall, borderColor:"#ffffff", backgroundColor:"#ffffff",
  borderWidth:3, tension:.25, pointRadius:3, segment:switchSegment,
}];
tsDatasets.push(...DATA.cats.map(c => ({
  label:c, data:DATA.series[c], borderColor:catColor[c], backgroundColor:catColor[c],
  borderWidth:1.5, tension:.25, pointRadius:2, segment:switchSegment })));

// Vertical dashed marker midway between the last run of one provider and the first of the next.
const switchMarker = { id:"switchMarker", afterDatasetsDraw(chart) {
  const {ctx, chartArea:a, scales:{x}} = chart;
  DATA.switches.forEach(s => {
    const xp = (x.getPixelForValue(s.index - 1) + x.getPixelForValue(s.index)) / 2;
    ctx.save(); ctx.strokeStyle = "#9aa0aa"; ctx.setLineDash([4,4]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(xp, a.top); ctx.lineTo(xp, a.bottom); ctx.stroke();
    ctx.setLineDash([]); ctx.fillStyle = "#9aa0aa"; ctx.font = "11px sans-serif";
    ctx.textAlign = "center"; ctx.fillText("Search provider: " + s.label, xp, a.top + 12);
    ctx.restore();
  });
}};
if (DATA.switches.length)
  document.getElementById("switchnote").textContent =
    "Dotted segments cross a change of Google-results provider (" +
    DATA.switches.map(s => s.label).join(", ") + "). Both return Google's top results, but for " +
    "the same query they can surface different pages, so the step across the marker is not a " +
    "like-for-like comparison.";
new Chart(document.getElementById("timeseries"), {
  type:"line", data:{ labels:DATA.dates, datasets:tsDatasets }, plugins:[switchMarker],
  options:{ plugins:{legend:{labels:{color:"#e8eaed",boxWidth:12,font:{size:11}}}},
    scales:{ x:{grid:{color:"#262a33"},ticks:{color:"#9aa0aa"}},
      y:{grid:{color:"#262a33"},ticks:{color:"#9aa0aa"},title:{display:true,text:"mean % distinct",color:"#9aa0aa"}} } },
});
</script>
</body>
</html>
"""


def main() -> None:
    payload = build_payload()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = TEMPLATE.replace("__PROVIDERS__", provider_summary(payload["dates"]))
    OUT.write_text(html.replace("__DATA__", json.dumps(payload)), encoding="utf-8")
    print(f"Wrote {OUT} ({len(payload['dates'])} run(s), "
          f"{payload['n_queries']} queries, coverage={payload['coverage']}).")


if __name__ == "__main__":
    main()
