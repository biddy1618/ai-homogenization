"""Build the tracker dashboard (tracker/dashboard/index.html) from the tracker data.

Methodology v2 (from 2026-10-26; the earlier runs are recomputed the same way): for each question,
the first 5 readable pages in Google rank order (``runs_top5.csv``). Two measures per question:

* similarity - mean pairwise cosine similarity of the 5 pages' whole-text embeddings, the same
  measure as the study (higher = Google's top pages are more alike);
* distinct pages out of 5 - the Vendi score of the 5 pages (5 = all different, 1 = all the same).

"Core 45" = the original questions, tracked since 2026-10-04 (one continuous series); the panel grew
to 100 questions on 2026-10-26. The v1 headline (% distinct over a varying number of pages,
``runs_fullpage.csv``) is kept as an archived chart. Data is embedded in the HTML, so it renders on
GitHub Pages and by opening the file. Stdlib only, so it runs in CI.

Usage:
    python tracker/dashboard/build.py
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

TOP5 = Path("tracker/data/runs_top5.csv")
LEGACY = Path("tracker/data/runs_fullpage.csv")
META = Path("tracker/data/_runs_meta.csv")
SERP_LOG = Path("tracker/data/serp_log.csv")
RAW = Path("tracker/data/raw")
OUT = Path("tracker/dashboard/index.html")
K = 5

# Source groups for the "where results come from" panel: (label, domain rules). A rule starting with
# "." matches a domain ending; otherwise it matches the domain or any of its subdomains.
SOURCES = [
    ("Reddit & Q&A forums", ["reddit.com", "quora.com", "stackexchange.com", "stackoverflow.com"]),
    ("Wikipedia & encyclopedias", ["wikipedia.org", "britannica.com"]),
    ("Government & universities", [".gov", ".edu", ".mil", ".gov.uk", ".ac.uk", ".gc.ca", ".gov.au",
                                   "who.int", "europa.eu", "nhs.uk"]),
    ("Health sites", ["mayoclinic.org", "clevelandclinic.org", "webmd.com", "healthline.com",
                      "hopkinsmedicine.org", "heart.org", "medicalnewstoday.com",
                      "verywellhealth.com", "health.harvard.edu", "medlineplus.gov"]),
    ("Finance & legal publishers", ["investopedia.com", "nerdwallet.com", "bankrate.com",
                                    "fidelity.com", "vanguard.com", "schwab.com", "forbes.com",
                                    "experian.com", "myfico.com", "equifax.com", "nolo.com",
                                    "findlaw.com", "justia.com", "legalzoom.com", "lawhelp.org"]),
    ("Tech companies & publishers", ["ibm.com", "microsoft.com", "amazon.com", "cloudflare.com",
                                     "google.com", "cisco.com", "kaspersky.com", "norton.com",
                                     "techtarget.com", "geeksforgeeks.org", "mozilla.org",
                                     "nvidia.com", "oracle.com"]),
    ("News & magazines", ["nytimes.com", "bbc.com", "bbc.co.uk", "cnn.com", "theguardian.com",
                          "washingtonpost.com", "npr.org", "reuters.com", "apnews.com", "cnbc.com",
                          "nationalgeographic.com", "scientificamerican.com", "time.com",
                          "theconversation.com", "livescience.com", "space.com"]),
]
OTHER = "Other sites"


def source_group(domain: str) -> str:
    host = domain.lower()
    host = host[4:] if host.startswith("www.") else host
    for label, rules in SOURCES:
        for r in rules:
            if (r.startswith(".") and host.endswith(r)) or host == r or host.endswith("." + r):
                return label
    return OTHER


def _providers() -> dict[str, str]:
    """run_date -> Google-results provider name, from _runs_meta.csv 'engine'."""
    if not META.exists():
        return {}
    return {r["run_date"]: "Serper.dev" if r["engine"].startswith("serper") else "SerpAPI"
            for r in csv.DictReader(META.open(encoding="utf-8"))}


def _rows(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8"))) if path.exists() else []


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(mean(xs), 4) if xs else None


def build_payload() -> dict:
    rows = _rows(TOP5)
    for r in rows:
        r["cos"] = float(r["mean_pairwise_cosine"])
        r["vendi"] = float(r["vendi"])
    serp = _rows(SERP_LOG)
    dates = sorted({r["date"] for r in serp} | {r["date"] for r in rows})
    first = dates[0]
    core = {r["query"] for r in serp if r["date"] == first}
    searched = Counter(r["date"] for r in serp)
    cats = sorted({r["category"] for r in serp})
    latest = dates[-1]

    by = defaultdict(list)
    for r in rows:
        by[r["date"]].append(r)

    def series(sel, field):
        return [_mean([r[field] for r in by[d] if sel(r)]) for d in dates]

    expanded = next((i for i, d in enumerate(dates) if searched[d] > len(core)), None)
    sim = {"core": series(lambda r: r["query"] in core, "cos"),
           "all": [v if expanded is not None and i >= expanded else None
                   for i, v in enumerate(series(lambda r: True, "cos"))]}
    ven = {"core": series(lambda r: r["query"] in core, "vendi"),
           "all": [v if expanded is not None and i >= expanded else None
                   for i, v in enumerate(series(lambda r: True, "vendi"))]}
    sim_cat = {c: series(lambda r, c=c: r["category"] == c, "cos") for c in cats}

    prov = _providers()
    markers = [{"index": i, "label": f"Search provider: {prov[dates[i-1]]} \u2192 {prov[dates[i]]}"}
               for i in range(1, len(dates))
               if prov.get(dates[i]) and prov.get(dates[i-1]) and prov[dates[i]] != prov[dates[i-1]]]
    if expanded:
        markers.append({"index": expanded, "label": f"Panel: {len(core)} \u2192 {searched[dates[expanded]]} questions"})

    latest_rows = sorted(by[latest], key=lambda r: -r["cos"])
    domains = [{"cat": c, "cos": _mean([r["cos"] for r in latest_rows if r["category"] == c]),
                "vendi": _mean([r["vendi"] for r in latest_rows if r["category"] == c])} for c in cats]
    domains.sort(key=lambda d: -(d["cos"] or 0))

    groups = [g for g, _ in SOURCES] + [OTHER]
    mix = {g: [] for g in groups}
    for d in dates:
        cnt = Counter()
        for r in serp:
            if r["date"] != d or r["query"] not in core:
                continue
            from_slug = RAW / d / f"{_slug(r['query'])}.json"
            if from_slug.exists():
                for res in json.loads(from_slug.read_text(encoding="utf-8")):
                    cnt[source_group(res.get("domain", ""))] += 1
        tot = sum(cnt.values()) or 1
        for g in groups:
            mix[g].append(round(100 * cnt[g] / tot, 1))

    legacy = _rows(LEGACY)
    leg_dates = sorted({r["date"] for r in legacy})
    leg = [_mean([100 * float(r["distinct_ratio"]) for r in legacy if r["date"] == d]) for d in leg_dates]

    return {
        "dates": dates, "latest": latest, "k": K, "cats": cats, "markers": markers,
        "n_core": len(core), "n_searched": searched[latest], "n_analysed": len(by[latest]),
        "sim": sim, "ven": ven, "sim_cat": sim_cat, "domains": domains,
        "leaderboard": [{"query": r["query"], "category": r["category"], "cos": round(r["cos"], 3),
                         "vendi": round(r["vendi"], 2)} for r in latest_rows],
        "latest_sim": _mean([r["cos"] for r in by[latest]]),
        "latest_vendi": _mean([r["vendi"] for r in by[latest]]),
        "mix": {"groups": groups, "values": mix},
        "legacy": {"dates": leg_dates, "pct": leg},
    }


def _slug(text: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "query"


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
  details.card summary { cursor:pointer; font-size:16px; font-weight:bold; }
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
  <div class="card">
    <p style="margin:0">Every Monday we take Google's top results for a fixed panel of informational
    questions in five domains, read the first 5 pages that can be read in full, and measure how alike
    they are. <b>Similarity</b> is the average cosine similarity between the pages' text embeddings
    &mdash; the same measure as the accompanying study of Stack Exchange and research abstracts
    (higher = the top pages say more of the same). <b>Distinct pages out of 5</b> (Vendi score) counts
    how many genuinely different pages there are: 5 = all different, 1 = all the same.</p>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="card">
    <h2>How alike are Google's top 5 pages? (over time)</h2>
    <p>Average similarity per run. The white line follows the original 45 questions through every run;
       the dashed line covers all questions once the panel grew. Read trends only after several weeks
       from the same search provider.</p>
    <canvas id="sim"></canvas>
  </div>

  <div class="card">
    <h2>Distinct pages out of 5 (over time)</h2>
    <p>Vendi score of the top 5 pages, averaged over questions. Lower = more repetition.</p>
    <canvas id="ven"></canvas>
  </div>

  <div class="card">
    <h2>By domain, latest run</h2>
    <p>Average similarity of the top 5 pages for the questions in each domain. Higher = more alike.</p>
    <canvas id="domains"></canvas>
  </div>

  <div class="card">
    <h2>Where do Google's results come from?</h2>
    <p>Share of all returned results (top 10, videos excluded) by type of source, original 45
       questions. Shifts here show which sources Google favours over time.</p>
    <canvas id="mix"></canvas>
  </div>

  <div class="card">
    <h2>By question, latest run</h2>
    <p>Similarity of the top 5 pages per question, most alike first; coloured by domain.</p>
    <div id="lbwrap" style="position:relative"><canvas id="leaderboard"></canvas></div>
  </div>

  <details class="card">
    <summary>Archive: methodology v1 (4&ndash;19 Oct 2026)</summary>
    <p style="margin-top:10px">The first headline: Vendi score divided by however many pages could be
       read (5&ndash;9 per question), shown as "% distinct". It fell whenever more pages were read, so
       runs were not comparable; replaced on 2026-10-26 by the fixed top-5 measures above, which were
       also recomputed for these runs.</p>
    <canvas id="legacy"></canvas>
  </details>
</div>
<footer>
  Google's top results via __PROVIDERS__; each page's main text (first ~1000 words) via ScrapingRobot;
  MiniLM whole-text embeddings. Video results and unreadable pages excluded.
  Code and data: <a href="https://github.com/biddy1618/ai-homogenization/tree/main/tracker">github.com/biddy1618/ai-homogenization</a>.
</footer>

<script>
const DATA = __DATA__;
const PALETTE = ["#5aa9e6","#e6a15a","#7ac77a","#c77ab0","#e6d15a","#5ae6c1","#e65a5a","#9a8ae6"];
const catColor = {}; DATA.cats.forEach((c,i)=> catColor[c] = PALETTE[i % PALETTE.length]);
const grid = {color:"#262a33"}, tick = {color:"#9aa0aa"};

document.getElementById("sub").textContent =
  `Latest run ${DATA.latest} · ${DATA.n_searched} questions searched, ${DATA.n_analysed} with ${DATA.k} readable pages · ${DATA.dates.length} run(s)`;

const lb = DATA.leaderboard;
const kpis = [
  ["Average similarity", DATA.latest_sim==null ? "–" : DATA.latest_sim.toFixed(2), `top ${DATA.k} pages, latest run`],
  ["Distinct pages", DATA.latest_vendi==null ? "–" : DATA.latest_vendi.toFixed(2), `out of ${DATA.k}, latest run`],
  ["Most alike", lb.length ? lb[0].query : "–", lb.length ? `similarity ${lb[0].cos}` : ""],
  ["Most varied", lb.length ? lb[lb.length-1].query : "–", lb.length ? `similarity ${lb[lb.length-1].cos}` : ""],
];
document.getElementById("kpis").innerHTML = kpis.map(k =>
  `<div class="kpi"><div class="label">${k[0]}</div><div class="value">${k[1]} <small>${k[2]}</small></div></div>`).join("");

const markerPlugin = { id:"markers", afterDatasetsDraw(chart) {
  const {ctx, chartArea:a, scales:{x}} = chart;
  DATA.markers.forEach((m, j) => {
    const xp = (x.getPixelForValue(m.index - 1) + x.getPixelForValue(m.index)) / 2;
    ctx.save(); ctx.strokeStyle = "#9aa0aa"; ctx.setLineDash([4,4]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(xp, a.top); ctx.lineTo(xp, a.bottom); ctx.stroke();
    ctx.setLineDash([]); ctx.fillStyle = "#9aa0aa"; ctx.font = "11px sans-serif"; ctx.textAlign = "center";
    ctx.fillText(m.label, xp, a.top + 12 + 14 * j); ctx.restore();
  });
}};

function timeChart(id, s, label, cats, ratio) {
  const ds = [
    {label:`Original ${DATA.n_core} questions`, data:s.core, borderColor:"#fff", backgroundColor:"#fff",
     borderWidth:3, tension:0, pointRadius:3},
    {label:"All questions", data:s.all, borderColor:"#fff", backgroundColor:"#fff", borderDash:[6,4],
     borderWidth:2, tension:0, pointRadius:3, spanGaps:false},
  ];
  if (cats) ds.push(...DATA.cats.map(c => ({label:c, data:cats[c], borderColor:catColor[c],
     backgroundColor:catColor[c], borderWidth:1.5, tension:0, pointRadius:2})));
  new Chart(document.getElementById(id), { type:"line", data:{labels:DATA.dates, datasets:ds},
    plugins:[markerPlugin],
    options:{ aspectRatio:ratio, plugins:{legend:{labels:{color:"#e8eaed",boxWidth:12,font:{size:11}}}},
      scales:{x:{grid, ticks:tick}, y:{grid, ticks:tick, title:{display:true, text:label, color:"#9aa0aa"}}}}});
}
timeChart("sim", DATA.sim, "average similarity", DATA.sim_cat, 2.4);
timeChart("ven", DATA.ven, `distinct pages out of ${DATA.k}`, null, 3.2);

new Chart(document.getElementById("domains"), { type:"bar",
  data:{ labels:DATA.domains.map(d=>d.cat), datasets:[{ data:DATA.domains.map(d=>d.cos),
    backgroundColor:DATA.domains.map(d=>catColor[d.cat]) }] },
  options:{ aspectRatio:3.4, plugins:{legend:{display:false}, tooltip:{callbacks:{afterLabel:(c)=>
      `distinct pages: ${DATA.domains[c.dataIndex].vendi} of ${DATA.k}`}}},
    scales:{ x:{grid:{display:false}, ticks:{color:"#e8eaed"}},
      y:{grid, ticks:tick, title:{display:true, text:"average similarity", color:"#9aa0aa"}} } } });

const MIXCOL = ["#e65a5a","#e6d15a","#5aa9e6","#7ac77a","#e6a15a","#9a8ae6","#c77ab0","#6b7280"];
new Chart(document.getElementById("mix"), { type:"bar",
  data:{ labels:DATA.dates, datasets:DATA.mix.groups.map((g,i)=>({ label:g, data:DATA.mix.values[g],
    backgroundColor:MIXCOL[i % MIXCOL.length] })) },
  plugins:[markerPlugin],
  options:{ aspectRatio:2.6, plugins:{legend:{labels:{color:"#e8eaed",boxWidth:12,font:{size:11}}}},
    scales:{ x:{stacked:true, grid:{display:false}, ticks:tick},
      y:{stacked:true, max:100, grid, ticks:tick, title:{display:true, text:"% of results", color:"#9aa0aa"}} } } });

const lbCanvas = document.getElementById("leaderboard");
document.getElementById("lbwrap").style.height = Math.max(300, 16 * lb.length + 70) + "px";
new Chart(lbCanvas, { type:"bar",
  data:{ labels:lb.map(d=>d.query), datasets:[{ label:"similarity", data:lb.map(d=>d.cos),
    backgroundColor:lb.map(d=>catColor[d.category]) }] },
  options:{ indexAxis:"y", maintainAspectRatio:false,
    plugins:{ legend:{ display:true, position:"top", align:"end",
        labels:{ color:"#e8eaed", boxWidth:12, font:{size:11},
          generateLabels:() => DATA.cats.map(c => ({ text:c, fillStyle:catColor[c], strokeStyle:catColor[c],
            fontColor:"#e8eaed", lineWidth:0, hidden:false })) }, onClick:() => {} },
      tooltip:{ callbacks:{ afterLabel:(c)=> `${lb[c.dataIndex].category} · distinct pages ${lb[c.dataIndex].vendi} of ${DATA.k}` } } },
    scales:{ x:{grid, ticks:tick}, y:{grid:{display:false}, ticks:{color:"#e8eaed", font:{size:10}}} } } });

new Chart(document.getElementById("legacy"), { type:"line",
  data:{ labels:DATA.legacy.dates, datasets:[{ label:"% distinct (v1)", data:DATA.legacy.pct,
    borderColor:"#9aa0aa", backgroundColor:"#9aa0aa", borderWidth:2, pointRadius:3 }] },
  options:{ aspectRatio:3.4, plugins:{legend:{labels:{color:"#e8eaed"}}},
    scales:{ x:{grid, ticks:tick}, y:{grid, ticks:tick, title:{display:true, text:"% distinct", color:"#9aa0aa"}} } } });
</script>
</body>
</html>
"""


def provider_summary(dates: list[str]) -> str:
    prov = _providers()
    spans: list[list] = []
    for d in dates:
        p = prov.get(d, "unknown provider")
        if spans and spans[-1][0] == p:
            spans[-1][2] = d
        else:
            spans.append([p, d, d])
    return ", ".join(f"{p} ({a}" + (f" to {b})" if b != a else ")") for p, a, b in spans)


def main() -> None:
    payload = build_payload()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = TEMPLATE.replace("__PROVIDERS__", provider_summary(payload["dates"]))
    OUT.write_text(html.replace("__DATA__", json.dumps(payload)), encoding="utf-8")
    print(f"Wrote {OUT} ({len(payload['dates'])} run(s), latest {payload['latest']}: "
          f"{payload['n_analysed']}/{payload['n_searched']} questions with {K} readable pages).")


if __name__ == "__main__":
    main()
