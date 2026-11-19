"""Build the saga one-page public summary (tracker/designs/saga/index.html).

    python tracker/designs/saga/build.py

Every number is computed from tracker/data/runs_top5.csv and tracker/queries.txt.
"""
from __future__ import annotations

import csv
import html
from collections import defaultdict
from datetime import date
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACKER = HERE.parent.parent
DATA = TRACKER / "data"
OUT = HERE / "index.html"

DASHBOARD_URL = "../../dashboard/"
METHODOLOGY_URL = "https://github.com/biddy1618/ai-homogenization/blob/main/tracker/README.md"
REPO_URL = "https://github.com/biddy1618/ai-homogenization"

e = html.escape


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def load():
    queries = []
    for line in (TRACKER / "queries.txt").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            cat, q = (s.strip() for s in line.split("|", 1))
            queries.append((cat, q))
    categories = list(dict.fromkeys(cat for cat, _ in queries))

    rows = list(csv.DictReader(open(DATA / "runs_top5.csv")))
    by_date = defaultdict(list)
    for r in rows:
        by_date[r["date"]].append(r)
    dates = sorted(by_date)
    latest = dates[-1]
    latest_rows = {r["query"]: r for r in by_date[latest]}

    series = []
    for d in dates:
        rs = by_date[d]
        series.append({"date": d, "sim": mean([float(r["mean_pairwise_cosine"]) for r in rs])})

    ranked = sorted(by_date[latest], key=lambda r: float(r["mean_pairwise_cosine"]))

    def question(r):
        return {
            "query": r["query"],
            "category": r["category"],
            "sim": float(r["mean_pairwise_cosine"]),
            "distinct": float(r["vendi"]),
        }

    domains = []
    for cat in categories:
        items = []
        sims = []
        for c, q in queries:
            if c != cat:
                continue
            r = latest_rows.get(q)
            if r:
                sim = float(r["mean_pairwise_cosine"])
                sims.append(sim)
                items.append({"query": q, "sim": sim})
            else:
                items.append({"query": q, "sim": None})
        domains.append({"name": cat, "sim": mean(sims), "items": items})

    return {
        "series": series,
        "latest": latest,
        "previous": series[-2]["date"] if len(series) > 1 else None,
        "change": series[-1]["sim"] - series[-2]["sim"] if len(series) > 1 else None,
        "week": len(dates),
        "sim": series[-1]["sim"],
        "distinct": mean([float(r["vendi"]) for r in by_date[latest]]),
        "most": question(ranked[-1]),
        "least": question(ranked[0]),
        "n_queries": len(queries),
        "n_read": len(by_date[latest]),
        "domains": domains,
        "first": dates[0],
    }


def fmt_day(d):
    dt = date.fromisoformat(d)
    return f"{dt.day:02d} {dt.strftime('%b')}"


def fmt_long(d):
    dt = date.fromisoformat(d)
    return f"{dt.day} {dt.strftime('%b')} {dt.year}"


def chart_points(series):
    """Plot geometry in the 1280×720 frame. First point sits after an Einstein-width gap."""
    x0, x1 = 300, 1210
    y0, y1 = 302, 616
    n = len(series)
    pts = []
    for i, p in enumerate(series):
        x = x0 + (i / max(n - 1, 1)) * (x1 - x0)
        y = y1 - p["sim"] * (y1 - y0)
        pts.append({"x": round(x, 1), "y": round(y, 1), "date": p["date"], "sim": p["sim"]})
    return {"x0": x0, "x1": x1, "y0": y0, "y1": y1, "points": pts, "first": series[0]["date"]}


def plot_line_html(series):
    x0, x1, y0, y1 = 300, 1210, 302, 616
    n = len(series)
    pts = []
    for i, p in enumerate(series):
        x = x0 + (i / max(n - 1, 1)) * (x1 - x0)
        y = y1 - p["sim"] * (y1 - y0)
        pts.append((x, y))
    segs = []
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        length = math.hypot(xb - xa, yb - ya)
        angle = math.degrees(math.atan2(yb - ya, xb - xa))
        segs.append(
            f'<i class="seg" style="left:{xa / 1280 * 100:.3f}%;top:{ya / 720 * 100:.3f}%;'
            f'width:{length / 1280 * 100:.3f}%;transform:rotate({angle:.3f}deg)"></i>'
        )
    dots = "".join(
        f'<i class="dot" style="left:{x / 1280 * 100:.3f}%;top:{y / 720 * 100:.3f}%"></i>'
        for x, y in pts
    )
    return "".join(segs) + dots


def render(data):
    series = data["series"]
    change = data["change"]
    change_txt = f"{change:+.2f}" if change is not None else "—"
    since = fmt_day(data["previous"]) if data["previous"] else "last run"
    sim = data["sim"]
    latest = data["latest"]
    first = data["first"]
    most, least = data["most"], data["least"]

    crawl_lines = [
        f"Week {data['week']}. The tracker asked Google the same {data['n_queries']} everyday questions "
        f"and read the first five pages behind each answer.",
        f"This week the pages add up to {data['distinct']:.2f} distinct answers out of 5, "
        f"and a mean similarity of {sim:.2f} on a 0 to 1 scale.",
        f"The weekly change is {change_txt} since {since}. "
        f"Movement week to week is still small, and the series is young.",
        f"The panel grew from 45 to 100 questions on 26 Oct. "
        f"This week {data['n_read']} of {data['n_queries']} questions were readable.",
        f"Most alike: “{most['query']}” at {most['sim']:.2f}. "
        f"Least alike: “{least['query']}” at {least['sim']:.2f}.",
    ]
    crawl_html = "".join(f"<p>{e(line)}</p>" for line in crawl_lines)

    domain_html = []
    for block in data["domains"]:
        rows = []
        for it in block["items"]:
            if it["sim"] is None:
                rows.append(
                    f'<li><span class="q">{e(it["query"])}</span>'
                    f'<span class="v muted">Not read this week</span></li>'
                )
            else:
                rows.append(
                    f'<li><span class="q">{e(it["query"])}</span>'
                    f'<span class="bar" style="--v:{it["sim"]:.3f}"></span>'
                    f'<span class="v scan">{it["sim"]:.2f}</span></li>'
                )
        domain_html.append(
            f'<section class="domain" aria-labelledby="d-{e(block["name"])}">'
            f'<h3 id="d-{e(block["name"])}"><span>{e(block["name"].title())}</span>'
            f'<span class="v">{block["sim"]:.2f}</span></h3>'
            f'<ol>{"".join(rows)}</ol></section>'
        )

    line_markup = plot_line_html(series)
    series_text = "; ".join(f'{fmt_day(p["date"])}: {p["sim"]:.2f}' for p in series)
    chart_label = (
        f"Line chart on a 0 to 1 scale of how alike Google's top 5 answers are, "
        f"weekly from {fmt_day(series[0]['date'])} to {fmt_day(series[-1]['date'])}: {series_text}. "
        f"0 means distinct voices, 1 means identical copies."
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI-driven homogenization of expression — real-time tracker</title>
<meta name="description" content="Every week the tracker asks Google the same {data['n_queries']} everyday questions and measures how alike the top 5 answers are. This week: {sim:.2f} on a 0 to 1 scale.">
<meta property="og:title" content="AI-driven homogenization of expression — real-time tracker">
<meta property="og:description" content="Google's top 5 answers to everyday questions now add up to {data['distinct']:.2f} distinct answers out of 5. Measured weekly.">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0e1014">
<style>
@font-face {{ font-family: 'Passero One'; src: url(fonts/PasseroOne-Regular.ttf) format('truetype'); font-weight: 400; font-display: swap; }}
@font-face {{ font-family: 'Saira'; src: url(fonts/Saira-variable.ttf) format('truetype'); font-weight: 100 900; font-display: swap; }}
@font-face {{ font-family: 'Saira Semi Condensed'; src: url(fonts/SairaSemiCondensed-500.ttf) format('truetype'); font-weight: 500; font-display: swap; }}
@font-face {{ font-family: 'Saira Semi Condensed'; src: url(fonts/SairaSemiCondensed-700.ttf) format('truetype'); font-weight: 700; font-display: swap; }}
@font-face {{ font-family: 'Share Tech Mono'; src: url(fonts/ShareTechMono-Regular.ttf) format('truetype'); font-weight: 400; font-display: swap; }}
:root {{
  --void: #0e1014;
  --horizon: #30271a;
  --ember: #4c2f1d;
  --bone: #dbd8cf;
  --amber: #e18f2a;
  --amber-hot: #f0a84a;
  --navy: #1a2740;
  --steel: #a8b0bc;
  --font-display: 'Passero One', 'Saira Semi Condensed', system-ui, sans-serif;
  --font-figure: 'Saira', 'Saira Semi Condensed', system-ui, sans-serif;
  --font-ui: 'Saira Semi Condensed', system-ui, sans-serif;
  --font-readout: 'Share Tech Mono', ui-monospace, monospace;
  color-scheme: dark;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ background: var(--void); color: var(--bone); }}
body {{ font-family: var(--font-ui); font-weight: 500; line-height: 1.45; overflow-x: hidden; }}
::selection {{ background: var(--amber); color: var(--void); }}
.scan {{
  background-image: repeating-linear-gradient(0deg, transparent 0 2px, rgb(0 0 0 / .28) 2px 3px);
  background-size: 100% 3px;
}}
a {{ color: inherit; }}
a:hover {{ color: var(--amber-hot); }}
:focus-visible {{ outline: 3px solid var(--amber); outline-offset: 3px; }}
img {{ display: block; max-width: 100%; height: auto; }}
.sr {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }}

/* First viewport: establishing shot at 1280×720 proportions. */
.viewport {{
  position: relative;
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  aspect-ratio: 1280 / 720;
  overflow: hidden;
  background: var(--void);
  container-type: inline-size;
}}
.backdrop {{
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover; object-position: center 60%;
  z-index: 0;
}}
.scrim {{
  position: absolute; inset: 0; z-index: 1; pointer-events: none;
  background:
    linear-gradient(180deg, rgb(14 16 20 / .72) 0%, rgb(14 16 20 / .28) 22%, rgb(14 16 20 / .15) 48%, rgb(14 16 20 / .55) 100%),
    linear-gradient(90deg, rgb(14 16 20 / .35) 0%, transparent 28%, transparent 72%, rgb(14 16 20 / .2) 100%);
}}
.layer {{ position: absolute; z-index: 2; }}
.brand {{
  left: 1.56%; top: 1.94%; width: 19.53%; height: 3.61%;
  display: flex; align-items: center;
  font-size: calc(19 * 100cqw / 1280); letter-spacing: .08em; text-transform: uppercase;
  color: var(--amber); font-weight: 500; white-space: nowrap;
}}
.week {{
  left: 23.44%; top: 1.94%; width: 20%; height: 3.61%;
  display: flex; align-items: center;
  font-size: calc(18 * 100cqw / 1280); letter-spacing: .08em; text-transform: uppercase;
  color: var(--bone); font-weight: 500; white-space: nowrap;
}}
.link-method, .link-dash {{
  top: 1.94%; height: 3.89%;
  display: flex; align-items: center;
  font-size: clamp(10px, 1.1cqw, 13px); letter-spacing: .02em; font-weight: 500;
  color: var(--bone); text-decoration: underline; text-underline-offset: .22em; white-space: nowrap;
}}
.link-method {{ left: 72.5%; width: 13.44%; }}
.link-dash {{ left: 88.28%; width: 9.22%; }}
.rule {{
  left: 0; top: 6.11%; width: 100%; height: calc(6 * 100cqw / 1280);
  background: #c9883a;
}}
.title {{
  left: 2.2%; top: 8.2%; width: 95%;
  font-family: var(--font-display); font-weight: 400;
  font-size: clamp(18px, 3.55cqw, 46px); line-height: 1.05;
  letter-spacing: .01em; color: var(--bone); white-space: nowrap;
  text-shadow: 0 1px 18px rgb(14 16 20 / .75);
}}
.figure {{
  left: 2.97%; top: 18.33%; width: 22.97%; height: 16.11%;
  font-family: var(--font-figure); font-weight: 700;
  font-size: clamp(56px, 11cqw, 140px); line-height: .92;
  color: var(--amber); letter-spacing: .02em;
  font-variant-numeric: tabular-nums;
  
}}
.figure-label {{
  left: 2.97%; top: 35.28%; width: 40.94%; height: 3.89%;
  display: flex; align-items: center;
  font-size: clamp(12px, 1.55cqw, 18px); color: var(--bone); letter-spacing: .03em; font-weight: 500;
  white-space: nowrap; overflow: hidden;
}}
.change-box {{
  left: 29.22%; top: 17.78%; width: 17.03%; height: 16.67%;
  border: 2px solid rgb(225 143 42 / .85);
  background: rgb(14 16 20 / .55); z-index: 3;
}}
.change-value {{
  left: 31.56%; top: 20.56%; width: 12.34%; height: 7.5%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-figure); font-weight: 700;
  font-size: calc(48 * 100cqw / 1280); line-height: 1;
  color: var(--amber); font-variant-numeric: tabular-nums; z-index: 4;
}}
.change-since {{
  left: 32.34%; top: 28.61%; width: 10.78%; height: 3.89%;
  display: flex; align-items: center; justify-content: center;
  font-size: calc(22 * 100cqw / 1280); color: var(--bone); letter-spacing: .06em; font-weight: 500; z-index: 4;
}}
.formation {{
  left: 66.9%; top: 16.4%; width: 32%; height: 24%;
  object-fit: contain; object-position: right center;
  filter: drop-shadow(0 8px 18px rgb(0 0 0 / .55));
}}
.formation-label {{
  left: 80.94%; top: 38.61%; width: 13.75%; height: 3.33%;
  font-size: clamp(11px, 1.4cqw, 17px); color: var(--amber); letter-spacing: .04em; white-space: nowrap; font-weight: 500;
}}
.einstein {{
  left: 5.9%; top: 53.9%; width: 17.3%; height: 33%;
  object-fit: contain; object-position: bottom center;
  filter: drop-shadow(0 6px 14px rgb(0 0 0 / .55));
}}
.einstein-label {{
  left: 8.28%; top: 82.22%; width: 9.84%; height: 3.33%;
  display: flex; align-items: center;
  font-size: calc(20 * 100cqw / 1280); color: var(--amber); letter-spacing: .04em; white-space: nowrap; font-weight: 700;
}}
.chart-wrap {{
  left: 0; top: 0; width: 100%; height: 100%;
  z-index: 2; pointer-events: none;
}}
.plot-line {{ position: absolute; inset: 0; }}
.plot-line .seg {{
  position: absolute; height: 3.5px; background: var(--amber); transform-origin: 0 50%;
  border-radius: 2px; 
}}
.plot-line .dot {{
  position: absolute; width: 10px; height: 10px; margin: -5px 0 0 -5px;
  border-radius: 50%; background: var(--amber); border: 2px solid var(--void);
}}
.yticks {{
  left: 3.44%; top: 41.11%; width: 3.75%; height: 46.39%;
  display: flex; flex-direction: column; justify-content: space-between; align-items: flex-end;
  font-size: clamp(10px, 1.2cqw, 15px); color: var(--bone); letter-spacing: .04em;
  font-variant-numeric: tabular-nums; z-index: 3;
}}
.xticks {{
  left: 6.09%; top: 87.5%; width: 90.94%; height: 3.61%;
  display: flex; justify-content: space-between; align-items: flex-start;
  font-size: clamp(10px, 1.2cqw, 15px); color: var(--bone); letter-spacing: .06em; z-index: 3;
}}
.gap-label {{
  left: 27.97%; top: 76.94%; width: 8.28%; height: 6.39%;
  font-size: calc(19 * 100cqw / 1280); line-height: 1.15; color: var(--bone); z-index: 3; font-weight: 500;
}}
.y-axis {{ left: 7.19%; top: 41.67%; width: calc(4 * 100cqw / 1280); height: 45.28%; background: #e18f2a; z-index: 2; }}
.baseline {{ left: 7.19%; top: 85.56%; width: 88.44%; height: calc(4 * 100cqw / 1280); background: #e18f2a; z-index: 2; }}
.frame-right {{ left: 94.69%; top: 41.67%; width: calc(4 * 100cqw / 1280); height: 45.28%; background: #e18f2a; z-index: 2; }}
.gridline {{ height: 2px; background: repeating-linear-gradient(90deg, #9a968c 0 4px, transparent 4px 11px); z-index: 2; }}
.grid-1 {{ left: 7.81%; top: 41.94%; width: 86.88%; }}
.grid-mid {{ left: 23.44%; top: 62.5%; width: 71.25%; }}
.grid-low {{ left: 23.44%; top: 73.33%; width: 71.25%; }}
.gap-hatch {{
  left: 21.09%; top: 73.61%; width: 6.41%; height: 12.78%; z-index: 2;
  background: repeating-linear-gradient(-28deg, rgb(225 143 42 / .55) 0 2px, transparent 2px 8px);
  border: 1px solid rgb(225 143 42 / .35);
}}

/* Below the fold */
.below {{
  max-width: 1100px; margin: 0 auto;
  padding: clamp(40px, 7vw, 88px) clamp(16px, 4vw, 40px) clamp(64px, 10vw, 120px);
}}
.wipe {{ margin: 0 0 clamp(28px, 5vw, 56px); transform-origin: center; }}
.wipe-h {{ height: 3px; background: linear-gradient(90deg, transparent, var(--amber), transparent); }}
.wipe-d {{
  height: 28px; background:
    linear-gradient(135deg, transparent 46%, var(--amber) 46%, var(--amber) 54%, transparent 54%);
  opacity: .85;
}}
.wipe-iris {{
  height: 36px;
  background: radial-gradient(ellipse at 50% 50%, transparent 28%, var(--amber) 28%, var(--amber) 32%, transparent 32%);
  opacity: .7;
}}
.crawl {{
  perspective: 480px; overflow: hidden;
  max-height: 280px; margin-bottom: clamp(40px, 7vw, 72px);
  mask-image: linear-gradient(180deg, transparent, #000 18%, #000 78%, transparent);
}}
.crawl-inner {{
  transform: rotateX(28deg) translateY(12%);
  transform-origin: 50% 0;
  text-align: center; color: var(--bone);
  font-family: var(--font-ui); font-weight: 500;
  font-size: clamp(1.05rem, 2.2vw, 1.35rem); line-height: 1.55;
  letter-spacing: .02em;
}}
.crawl-inner p {{ margin: 0 auto 1.1em; max-width: 42ch; }}
.band {{ margin-top: clamp(36px, 6vw, 72px); padding-top: clamp(28px, 4vw, 40px); border-top: 1px solid rgb(219 216 207 / .14); }}
.band h2 {{
  font-family: var(--font-display); font-weight: 400;
  font-size: clamp(1.6rem, 3.4vw, 2.6rem); line-height: 1.05;
  color: var(--bone); margin-bottom: .6em;
}}
.facts {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }}
.fact {{
  padding: 1rem 1rem 1.1rem; background: rgb(26 39 64 / .55);
  border: 1px solid rgb(219 216 207 / .18);
  box-shadow: inset 0 0 0 1px rgb(225 143 42 / .12);
  position: relative;
}}
.fact::before {{
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
  background: repeating-linear-gradient(180deg, var(--amber) 0 6px, #1a2740 6px 12px);
}}
.fact b {{
  display: block; font-family: var(--font-figure); font-weight: 700;
  font-size: clamp(1.8rem, 3.5vw, 2.6rem); color: var(--amber);
  font-variant-numeric: tabular-nums; line-height: 1;
}}
.fact span {{ display: block; margin-top: .45em; color: var(--bone); font-size: .95rem; max-width: 22ch; }}
.extremes {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.2rem; }}
.extreme {{
  padding: 1rem 1.1rem 1.15rem; border: 1px solid rgb(225 143 42 / .45);
  background: linear-gradient(180deg, rgb(26 39 64 / .55), rgb(14 16 20 / .7));
  box-shadow: inset 0 0 0 1px rgb(219 216 207 / .08);
}}
.extreme .k {{ color: var(--amber); font-size: .8rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700; }}
.extreme .q {{ margin-top: .45em; font-size: clamp(1.1rem, 2.2vw, 1.45rem); color: var(--bone); text-wrap: balance; }}
.extreme .n {{ margin-top: .5em; color: var(--steel); font-size: .95rem; }}
.domains {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr)); gap: 1.5rem 2rem; }}
.domain h3 {{
  display: flex; justify-content: space-between; gap: 1em;
  font-size: 1.15rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  color: var(--amber); border-bottom: 1px solid rgb(225 143 42 / .35); padding-bottom: .35em; margin-bottom: .55em;
}}
.domain ol {{ list-style: none; }}
.domain li {{
  display: grid; grid-template-columns: 1fr 4.5em 2.6ch; align-items: center; gap: .55em;
  padding: .22em 0; font-size: .92rem;
}}
.domain .bar {{
  height: .45em;
  background: linear-gradient(90deg, var(--amber) calc(var(--v) * 100%), rgb(219 216 207 / .12) 0);
}}
.domain .v {{ color: var(--amber); text-align: right; font-variant-numeric: tabular-nums; font-family: var(--font-readout); }}
.domain .muted {{ color: var(--steel); grid-column: 2 / 4; white-space: nowrap; }}
.domain .q {{ min-width: 0; overflow-wrap: anywhere; }}
.how {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 2rem; }}
.how p {{ max-width: 58ch; font-size: 1.05rem; margin-bottom: .9em; color: var(--bone); }}
.links {{ list-style: none; display: grid; gap: .55em; align-content: start; }}
.links a {{
  display: inline-block; padding: .55em .9em;
  background: var(--amber); color: var(--void); font-weight: 700;
  letter-spacing: .06em; text-transform: uppercase; text-decoration: none;
  font-size: .85rem;
}}
.links a:hover {{ background: var(--bone); color: var(--void); }}
.colophon {{ margin-top: 2rem; color: var(--steel); font-size: .9rem; }}

@media (prefers-reduced-motion: no-preference) {{
  .wipe-h, .wipe-d, .wipe-iris {{ animation: wipeIn .7s cubic-bezier(.16,1,.3,1) both; }}
  .crawl-inner {{ animation: crawl 48s linear infinite; }}
  @keyframes wipeIn {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
  @keyframes crawl {{ from {{ transform: rotateX(28deg) translateY(28%); }} to {{ transform: rotateX(28deg) translateY(-70%); }} }}
}}
@media (prefers-reduced-motion: reduce) {{
  .crawl {{ max-height: none; mask-image: none; perspective: none; }}
  .crawl-inner {{ transform: none; }}
}}

@container (max-width: 760px) {{
  .viewport {{ aspect-ratio: auto; min-height: 0; display: flex; flex-direction: column; gap: 10px; padding: 12px 14px 8px; overflow: visible; }}
  .backdrop {{ position: absolute; inset: 0; opacity: .55; }}
  .scrim {{ background: linear-gradient(180deg, rgb(14 16 20 / .7), rgb(14 16 20 / .92)); }}
  .layer {{ position: relative; left: auto !important; top: auto !important; right: auto !important; width: auto !important; height: auto !important; }}
  .brand, .week, .link-method, .link-dash {{ order: 0; }}
  .rule {{ order: 1; height: 1px; width: 100%; }}
  .title {{ order: 2; white-space: normal; font-size: clamp(1.35rem, 7vw, 1.85rem); line-height: 1.1; width: 100%; }}
  .figure {{ order: 3; font-size: 4.2rem; }}
  .figure-label {{ order: 4; width: 100%; }}
  .change-box, .change-value, .change-since {{ order: 5; position: relative !important; width: auto !important; height: auto !important; left: auto !important; top: auto !important; }}
  .change-box {{ display: none; }}
  .yticks, .xticks, .y-axis, .baseline, .frame-right, .gridline, .gap-hatch {{ display: none; }}
  .gap-label {{ order: 6; position: relative !important; left: auto !important; top: auto !important; }}
  .chart-wrap {{ order: 6; position: relative; width: calc(100% + 28px); margin: 8px -14px 0; aspect-ratio: 5 / 4; height: auto; pointer-events: auto; }}
  .formation {{ order: 0; position: absolute !important; left: auto !important; right: 2% !important; top: 8% !important; width: 42% !important; height: auto !important; z-index: 3; }}
  .formation-label {{ position: absolute !important; right: 4% !important; top: 2% !important; left: auto !important; z-index: 4; }}
  .einstein {{ position: absolute !important; left: 6% !important; bottom: 14% !important; top: auto !important; width: 28% !important; height: auto !important; z-index: 3; }}
  .einstein-label {{ position: absolute !important; left: 6% !important; bottom: 8% !important; top: auto !important; z-index: 4; }}
}}
@media (max-width: 760px) {{
  .facts, .extremes, .how {{ grid-template-columns: 1fr; }}
  .domain li {{ grid-template-columns: 1fr auto; }}
  .domain .bar {{ display: none; }}
}}
@media (max-width: 420px) {{
  .header {{ font-size: 11px; letter-spacing: .08em; }}
  .title {{ font-size: 1.25rem; }}
}}
</style>
</head>
<body>
<main class="viewport" id="top" aria-labelledby="title">
  <img class="backdrop" src="assets/plates/backdrop.jpg" alt="" width="1920" height="1080" decoding="async">
  <div class="scrim" aria-hidden="true"></div>
  <p class="layer brand scan">HOMOGENIZATION TRACKER</p>
  <p class="layer week scan">WEEK {data['week']} · RUN OF {fmt_long(latest).upper()}</p>
  <a class="layer link-method" href="{METHODOLOGY_URL}">Methodology and data</a>
  <a class="layer link-dash" href="{DASHBOARD_URL}">Full dashboard</a>
  <div class="layer rule" aria-hidden="true"></div>
  <h1 id="title" class="layer title">AI-driven homogenization of expression — real-time tracker</h1>
  <p class="layer figure" aria-hidden="true">{sim:.2f}</p>
  <p class="layer figure-label">how alike Google's top 5 answers are this week, 0 to 1</p>
  <div class="layer change-box" aria-hidden="true"></div>
  <p class="layer change-value scan">{change_txt}</p>
  <p class="layer change-since">since {since}</p>
  <img class="layer formation" src="assets/plates/formation.png" width="1107" height="507"
       alt="Identical armoured troopers in navy and matte grey with hazard-yellow markings: where we're heading">
  <p class="layer formation-label" aria-hidden="true">where we're heading</p>
  <div class="layer y-axis" aria-hidden="true"></div>
  <div class="layer baseline" aria-hidden="true"></div>
  <div class="layer frame-right" aria-hidden="true"></div>
  <div class="layer gridline grid-1" aria-hidden="true"></div>
  <div class="layer gridline grid-mid" aria-hidden="true"></div>
  <div class="layer gridline grid-low" aria-hidden="true"></div>
  <div class="layer gap-hatch" aria-hidden="true"></div>
  <p class="layer gap-label" aria-hidden="true">no data<br>before {fmt_day(first)}</p>
  <div class="layer yticks scan" aria-hidden="true"><span>1</span><span>0.75</span><span>0.50</span><span>0.25</span><span>0</span></div>
  <div class="layer chart-wrap" role="img" aria-label="{e(chart_label)}">
    <div class="plot-line" aria-hidden="true">{line_markup}</div>
  </div>
  <div class="layer xticks scan" aria-hidden="true">{''.join(f'<span>{fmt_day(p["date"])}</span>' for p in series)}</div>
  <img class="layer einstein" src="assets/plates/einstein.png" width="560" height="596"
       alt="Albert Einstein: distinct voices">
  <p class="layer einstein-label" aria-hidden="true">distinct voices</p>
</main>

<div class="below">
  <div class="wipe wipe-h" aria-hidden="true"></div>
  <section class="crawl" aria-label="This week's story">
    <div class="crawl-inner">{crawl_html}</div>
  </section>

  <div class="wipe wipe-d" aria-hidden="true"></div>
  <section class="band" id="this-week" aria-labelledby="this-week-h">
    <h2 id="this-week-h">This week</h2>
    <div class="facts">
      <p class="fact"><b>{sim:.2f}</b><span>How alike the top 5 answers are, 0 to 1</span></p>
      <p class="fact"><b>{change_txt}</b><span>Change since {since}</span></p>
      <p class="fact"><b>{data['distinct']:.2f}</b><span>Distinct answers out of 5</span></p>
      <p class="fact"><b>{data['n_read']}</b><span>Of {data['n_queries']} questions readable this week</span></p>
    </div>
    <div class="extremes">
      <article class="extreme">
        <p class="k">Most alike this week</p>
        <p class="q">{e(most['query'])}</p>
        <p class="n">{most['sim']:.2f} alike · {most['distinct']:.2f} distinct out of 5 · {e(most['category'])}</p>
      </article>
      <article class="extreme">
        <p class="k">Least alike this week</p>
        <p class="q">{e(least['query'])}</p>
        <p class="n">{least['sim']:.2f} alike · {least['distinct']:.2f} distinct out of 5 · {e(least['category'])}</p>
      </article>
    </div>
  </section>

  <div class="wipe wipe-iris" aria-hidden="true"></div>
  <section class="band" id="questions" aria-labelledby="questions-h">
    <h2 id="questions-h">All {data['n_queries']} questions</h2>
    <p style="margin:-.2em 0 1.2em;color:var(--steel)">Latest run · higher means the top 5 answers say more of the same thing</p>
    <div class="domains">{''.join(domain_html)}</div>
  </section>

  <div class="wipe wipe-h" aria-hidden="true"></div>
  <section class="band" id="how" aria-labelledby="how-h">
    <h2 id="how-h">How it's measured</h2>
    <div class="how">
      <div>
        <p>Every week the tracker asks Google the same {data['n_queries']} everyday questions, twenty each in finance, health, law, science and tech. It reads the first five pages that answer each one and compares what they say, by meaning rather than exact wording.</p>
        <p>The score runs from 0, where the five pages share nothing, to 1, where they say the same thing. The line is the average across the questions readable that week. The first 45 questions have been tracked since 04 Oct; the panel grew to 100 on 26 Oct. Movement week to week is still small, and the series is young.</p>
      </div>
      <ul class="links">
        <li><a href="{METHODOLOGY_URL}">Methodology and data</a></li>
        <li><a href="{DASHBOARD_URL}">Full dashboard</a></li>
        <li><a href="{REPO_URL}">Source code</a></li>
      </ul>
    </div>
    <p class="colophon">Updated weekly · last run {fmt_long(latest)} · {data['week']} runs since {fmt_long(first)}</p>
  </section>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(render(load()))
    print(f"wrote {OUT.relative_to(TRACKER.parent)}")
