"""Build the one-page public summary (tracker/designs/casts/index.html) from the tracker CSVs.

    python tracker/designs/casts/build.py

Every number on the page is computed here from tracker/data/runs_top5.csv,
tracker/data/_runs_meta.csv and tracker/queries.txt; nothing is hard-coded.
"""
import csv
import html
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACKER = HERE.parent.parent
DATA = TRACKER / "data"
OUT = HERE / "index.html"

DASHBOARD_URL = "../../dashboard/"
METHODOLOGY_URL = "https://github.com/biddy1618/ai-homogenization/blob/main/tracker/README.md"
REPO_URL = "https://github.com/biddy1618/ai-homogenization"
PAGE_URL = "https://biddy1618.github.io/ai-homogenization/tracker/designs/casts/"

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
    number_of = {q: i + 1 for i, (_, q) in enumerate(queries)}
    categories = list(dict.fromkeys(cat for cat, _ in queries))

    rows = list(csv.DictReader(open(DATA / "runs_top5.csv")))
    by_date = defaultdict(list)
    first_read = {}
    for r in rows:
        by_date[r["date"]].append(r)
        first_read[r["query"]] = min(first_read.get(r["query"], r["date"]), r["date"])
    dates = sorted(by_date)
    latest = dates[-1]
    latest_rows = {r["query"]: r for r in by_date[latest]}

    def summary(pick):
        series = []
        for d in dates:
            rs = [r for r in by_date[d] if pick(r)]
            if rs:
                series.append({"date": d, "sim": mean([float(r["mean_pairwise_cosine"]) for r in rs]), "n": len(rs)})
        lr = [r for r in by_date[latest] if pick(r)]
        return {
            "series": series,
            "sim": series[-1]["sim"],
            "distinct": mean([float(r["vendi"]) for r in lr]),
            "n_read": len(lr),
        }

    overall = summary(lambda r: True)

    def question(r):
        return {"n": number_of.get(r["query"]), "query": r["query"], "category": r["category"],
                "sim": float(r["mean_pairwise_cosine"]), "distinct": float(r["vendi"])}

    ranked = sorted(by_date[latest], key=lambda r: float(r["mean_pairwise_cosine"]))

    domains = []
    for cat in categories:
        s = summary(lambda r, c=cat: r["category"] == c)
        items = []
        for c, q in queries:
            if c != cat:
                continue
            r = latest_rows.get(q)
            items.append({"n": number_of[q], "query": q, "first": first_read.get(q),
                          "sim": float(r["mean_pairwise_cosine"]) if r else None,
                          "distinct": float(r["vendi"]) if r else None})
        domains.append({"name": cat, "sim": s["sim"], "n_read": s["n_read"], "n_total": len(items), "items": items})

    # Panel size per run, from the run log: the first run whose panel is larger than the one before.
    meta = list(csv.DictReader(open(DATA / "_runs_meta.csv")))
    growth = None
    prev = None
    for m in meta:
        n = int(m["n_queries"])
        if prev is not None and n > prev and growth is None:
            growth = {"date": m["run_date"], "from": prev, "to": n}
        prev = n

    latest_sims = [float(r["mean_pairwise_cosine"]) for r in by_date[latest]]
    latest_vendi = [float(r["vendi"]) for r in by_date[latest]]
    series = overall["series"]
    return {
        "series": series,
        "sim": overall["sim"],
        "distinct": overall["distinct"],
        "latest": latest,
        "first": dates[0],
        "previous": series[-2]["date"] if len(series) > 1 else None,
        "change": series[-1]["sim"] - series[-2]["sim"] if len(series) > 1 else None,
        "runs": len(dates),
        "most": question(ranked[-1]),
        "least": question(ranked[0]),
        "n_queries": len(queries),
        "n_read": len(by_date[latest]),
        "share_above_080": sum(v > 0.80 for v in latest_sims) / len(latest_sims),
        "share_below_2": sum(v < 2 for v in latest_vendi) / len(latest_vendi),
        "domains": domains,
        "growth": growth,
    }


def fmt_day(d):
    dt = date.fromisoformat(d)
    return f"{dt.day:02d} {dt.strftime('%b')}"


def fmt_long(d):
    dt = date.fromisoformat(d)
    return f"{dt.day} {dt.strftime('%B')} {dt.year}"


def pct(x):
    return f"{round(x * 100):d}%"


def render(data):
    series = data["series"]
    first, latest = data["first"], data["latest"]
    d0 = date.fromisoformat(first).toordinal()
    span = max(date.fromisoformat(latest).toordinal() - d0, 1)

    def xf(d):
        return (date.fromisoformat(d).toordinal() - d0) / span

    # The line on the honest 0-1 scale, positioned by real date.
    pts = [(xf(p["date"]) * 100, (1 - p["sim"]) * 100) for p in series]
    segs = []
    import math
    # .series is ~890×220 design units; % x/y are not isotropic — correct length for rotate().
    series_h_over_w = 220 / 890
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy * series_h_over_w)
        angle = math.degrees(math.atan2(dy * series_h_over_w, dx))
        segs.append(
            f'<i class="seg" style="left:{x0:.3f}%;top:{y0:.3f}%;width:{length:.3f}%;'
            f'transform:rotate({angle:.3f}deg)"></i>')
    segs_html = "".join(segs)
    runs_html, dates_html = [], []
    last_label_x = -1
    for i, p in enumerate(series):
        x, y = pts[i]
        on = i == len(series) - 1
        runs_html.append(
            f'<button class="run{" on" if on else ""}" type="button" style="left:{x:.3f}%;top:{y:.3f}%" '
            f'data-date="{fmt_day(p["date"])}" data-v="{p["sim"]:.3f}" data-y="{y:.3f}" '
            f'aria-label="{fmt_long(p["date"])}: {p["sim"]:.2f} on the 0 to 1 scale, {p["n"]} questions read"'
            f' aria-pressed="{"true" if on else "false"}"><i></i></button>')
        dates_html.append(f'<span class="date" style="left:{x:.3f}%">{fmt_day(p["date"])}</span>')
        last_label_x = x
    ticks_html = "".join(
        f'<span class="tick{" major" if k % 2 == 0 else ""}" style="top:{100 - k * 10}%">'
        f'{"<b>" + (str(k / 10).rstrip("0").rstrip(".") if k not in (0, 10) else str(k // 10)) + "</b>" if k % 2 == 0 else ""}</span>'
        for k in range(11))
    last = series[-1]
    table_rows = "".join(f"<tr><th scope=\"row\">{fmt_long(p['date'])}</th><td>{p['sim']:.3f}</td><td>{p['n']}</td></tr>"
                         for p in series)
    chart_label = (f"Line chart on the full 0 to 1 scale of how alike Google's top 5 answers are, by run date: "
                   + "; ".join(f"{fmt_day(p['date'])} {p['sim']:.2f}" for p in series)
                   + ". Low end: a carved bust of Einstein, distinct voices. High end: identical helmeted casts, identical copies.")

    change = data["change"]
    change_txt = f"{change:+.3f}".replace("-", "−") if change is not None else "—"
    prev_txt = fmt_day(data["previous"]) if data["previous"] else "the last run"
    g = data["growth"]

    # The calliper: every question read this week, one tick each, by domain.
    strips = []
    for k, dom in enumerate(data["domains"]):
        read = [it for it in dom["items"] if it["sim"] is not None]
        ticks = "".join(
            f'<i style="left:{it["sim"] * 100:.2f}%" data-q="{e(it["query"])}" data-v="{it["sim"]:.2f}" data-n="{it["n"]:03d}"></i>'
            for it in sorted(read, key=lambda it: it["sim"]))
        strips.append(
            f'<div class="strip" data-strip="{k}">'
            f'<p class="strip-name"><span>{e(dom["name"].capitalize())}</span>'
            f'<b>{dom["sim"]:.2f}</b><small>{dom["n_read"]} of {dom["n_total"]} read</small></p>'
            f'<div class="rule" aria-hidden="true">{ticks}<em class="jaw" style="left:{dom["sim"] * 100:.2f}%"></em>'
            f'<output class="reading" hidden></output></div></div>')

    ledger = []
    for dom in data["domains"]:
        rows = ""
        for it in dom["items"]:
            added = (f'<span class="added">first read {fmt_day(it["first"])}</span>'
                     if it["first"] and it["first"] != first else "")
            if it["sim"] is None:
                val = '<span class="val none">not read this week</span>'
            else:
                val = (f'<span class="bar" style="--v:{it["sim"]:.3f}" aria-hidden="true"></span>'
                       f'<span class="val">{it["sim"]:.2f}</span>')
            rows += (f'<li><span class="no">{it["n"]:03d}</span>'
                     f'<span class="q">{e(it["query"])}{added}</span>{val}</li>')
        ledger.append(
            f'<details class="crate"><summary><span class="crate-name">{e(dom["name"].capitalize())}</span>'
            f'<span class="crate-meta">{dom["n_read"]} of {dom["n_total"]} read · average <b>{dom["sim"]:.2f}</b></span></summary>'
            f'<ol>{rows}</ol></details>')

    most, least = data["most"], data["least"]

    def specimen(kind, q, cls):
        return (f'<figure class="specimen {cls}"><figcaption>{kind}</figcaption>'
                f'<p class="specimen-q">“{e(q["query"])}”</p>'
                f'<p class="specimen-n"><b>{q["sim"]:.2f}</b> alike · {q["distinct"]:.2f} distinct pages out of 5 · '
                f'{e(q["category"])} · no. {q["n"]:03d}</p></figure>')

    growth_txt = (f"The panel grew from {g['from']} to {g['to']} questions on {fmt_long(g['date'])}; "
                  f"runs before that read the original {g['from']}." if g else "")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI-driven homogenization of expression — real-time tracker</title>
<meta name="description" content="Every week the tracker asks Google the same everyday questions and measures how alike the top 5 answers are. Latest run, {fmt_long(latest)}: {data['sim']:.2f} on a 0 to 1 scale.">
<meta property="og:title" content="AI-driven homogenization of expression — real-time tracker">
<meta property="og:description" content="How alike Google's top 5 answers are this week: {data['sim']:.2f} on a 0 to 1 scale, {data['distinct']:.2f} distinct pages out of 5. Measured weekly on {data['n_queries']} everyday questions.">
<meta property="og:type" content="website">
<meta property="og:url" content="{PAGE_URL}">
<meta property="og:image" content="{PAGE_URL}assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#131315">
<link rel="preload" href="fonts/BigShouldersStencil-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="fonts/SofiaSansCondensed-var.woff2" as="font" type="font/woff2" crossorigin>
<style>
@font-face {{ font-family: 'Big Shoulders Stencil'; src: url(fonts/BigShouldersStencil-var.woff2) format('woff2'); font-weight: 100 900; font-display: swap; }}
@font-face {{ font-family: 'Sofia Sans Condensed'; src: url(fonts/SofiaSansCondensed-var.woff2) format('woff2'); font-weight: 100 900; font-display: swap; }}
:root {{
  --graphite: #131315; --slate: #1d1e20; --slate-2: #2a2a2b;
  --plaster: #ece6dd; --plaster-dim: #bdb6ac; --chalk: #8f8981;
  --oxblood: #2c0a0a; --oxblood-2: #4a1210; --oxblood-cut: #c94a3a; --oxblood-ink: #e2735d;
  --stencil: 'Big Shoulders Stencil', 'Arial Narrow', sans-serif;
  --text: 'Sofia Sans Condensed', 'Arial Narrow', sans-serif;
  color-scheme: dark;
}}
@property --u {{ syntax: '<length>'; inherits: true; initial-value: 1px; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ background: var(--graphite); color: var(--plaster); scrollbar-color: var(--oxblood-cut) var(--graphite); -webkit-text-size-adjust: 100%; }}
body {{ container-type: inline-size; font-family: var(--text); font-size: 18px; line-height: 1.4; overflow-x: clip; }}
::selection {{ background: var(--oxblood-cut); color: var(--plaster); }}
a {{ color: inherit; text-decoration-color: rgb(236 230 221 / .45); text-underline-offset: .22em; text-decoration-thickness: 1px; }}
a:hover {{ color: #fff; text-decoration-color: var(--oxblood-ink); }}
:focus-visible {{ outline: 2px solid var(--oxblood-ink); outline-offset: 3px; }}
.sr {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }}
img {{ display: block; }}

/* First viewport: the plinth, laid out on the approved 1280 x 720 frame. */
.hero {{ --u: min(100cqw / 1280, 100svh / 720); position: relative; background: var(--graphite); overflow: hidden; }}
.frame {{ position: relative; width: calc(1280 * var(--u)); height: calc(720 * var(--u)); margin: 0 auto; }}
.frame > * {{ position: absolute; }}
.studio {{ left: 0; top: 0; width: 100%; height: calc(628 * var(--u)); }}
.studio img {{ width: 100%; height: 100%; object-fit: cover; }}
.studio::after {{
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: linear-gradient(118deg, transparent 0%, transparent 42%, rgb(236 230 221 / .10) 49%, rgb(236 230 221 / .28) 52%, rgb(236 230 221 / .08) 56%, transparent 64%);
  background-size: 240% 100%; background-position: 100% 0; mix-blend-mode: soft-light;
}}
@media (min-aspect-ratio: 16/9) {{
  .studio {{ -webkit-mask: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent); mask: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent); }}
}}
.title {{ left: calc(20 * var(--u)); top: calc(24 * var(--u)); font-family: var(--stencil); font-weight: 500; font-size: calc(55 * var(--u)); line-height: 1.0; letter-spacing: -0.04em; width: calc(1220 * var(--u)); max-width: calc(1220 * var(--u)); color: var(--plaster); white-space: nowrap; }}
.big {{
  left: calc(40 * var(--u)); top: calc(78 * var(--u)); width: calc(400 * var(--u)); height: calc(230 * var(--u));
  display: flex; align-items: center; justify-content: flex-start;
  font-family: var(--stencil); font-weight: 700; font-size: calc(210 * var(--u));
  line-height: 0.85; letter-spacing: -0.04em; font-variant-numeric: tabular-nums;
  color: #c94a3a;
  text-shadow:
    calc(-1.5 * var(--u)) calc(-1.5 * var(--u)) 0 rgb(236 230 221 / .12),
    calc(2 * var(--u)) calc(3 * var(--u)) calc(8 * var(--u)) rgb(0 0 0 / .7);
}}
.big .sr {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }}
.deck {{ left: calc(408 * var(--u)); top: calc(132 * var(--u)); width: calc(300 * var(--u)); font-size: calc(27 * var(--u)); line-height: 1.32; font-weight: 500; color: var(--plaster); }}
.change {{ left: calc(408 * var(--u)); top: calc(209 * var(--u)); font-size: calc(26 * var(--u)); font-weight: 600; color: var(--plaster-dim); white-space: nowrap; }}
.change b {{ color: #6a2420; font-weight: 700; font-variant-numeric: tabular-nums; text-shadow: 0 0 1px rgb(236 230 221 / .35); }}
.links {{
  left: calc(408 * var(--u)); top: calc(248 * var(--u)); width: calc(360 * var(--u));
  list-style: none; display: flex; flex-wrap: wrap; align-items: baseline; gap: calc(10 * var(--u)) calc(14 * var(--u));
  font-size: calc(22 * var(--u)); font-weight: 600; line-height: 1.2; background: transparent;
}}
.links li {{ position: static; display: inline; }}
.links li + li {{ left: auto; }}
.links li + li::before {{
  content: "|"; margin-right: calc(14 * var(--u)); color: var(--chalk); font-weight: 500;
}}
.links a {{
  color: var(--plaster); text-decoration: underline; text-decoration-color: rgb(236 230 221 / .45);
  text-underline-offset: 0.22em; text-decoration-thickness: 1px; font-size: inherit;
}}
.links a:hover {{ color: #fff; text-decoration-color: var(--oxblood-ink); outline: none; }}

.casts {{ left: calc(716 * var(--u)); top: calc(160 * var(--u)); width: calc(512 * var(--u)); position: absolute; }}
.cast-nos {{ position: absolute; left: calc(744 * var(--u)); top: calc(96 * var(--u)); z-index: 3; width: calc(444 * var(--u)); display: grid; grid-template-columns: repeat(6, 1fr); font-family: var(--stencil); font-weight: 700; font-size: calc(46 * var(--u)); line-height: 1; color: #6a2420; text-align: center; height: calc(48 * var(--u)); text-shadow: calc(-1 * var(--u)) calc(-1 * var(--u)) 0 rgb(236 230 221 / .22), 0 1px 2px rgb(0 0 0 / .8); }}
.cast-row {{
  position: relative; display: grid; grid-template-columns: repeat(6, 1fr); gap: calc(10 * var(--u));
  align-items: end; background: transparent;
}}
.cast-row figure {{ margin: 0; background: transparent; }}
.cast-row img {{ width: 100%; height: auto; display: block; background: transparent; vertical-align: bottom; }}
.cast-row::after {{ content: none; }}
.casts-label {{ left: calc(786 * var(--u)); top: calc(333 * var(--u)); font-size: calc(25 * var(--u)); font-weight: 700; letter-spacing: .02em; color: var(--plaster); white-space: nowrap; }}

.stage, .face {{ position: static; }}
.casts, .casts-label, .chart, .einstein-label {{ position: absolute; }}
.chart {{ left: calc(84 * var(--u)); top: calc(348 * var(--u)); width: calc(1116 * var(--u)); height: calc(220 * var(--u)); container-type: size;
  --eh: calc(222 * var(--u)); --el: 0px; --eg: calc(26 * var(--u)); }}
.axis {{ position: absolute; left: 0; top: 0; bottom: 0; width: 0; border-left: 1.5px solid rgb(236 230 221 / .7); }}
.tick {{ position: absolute; right: 0; width: calc(7 * var(--u)); height: 0; border-top: 1px solid rgb(236 230 221 / .55); }}
.tick.major {{ width: calc(12 * var(--u)); border-top-width: 1.5px; border-top-color: rgb(236 230 221 / .8); }}
.tick b {{ position: absolute; right: calc(18 * var(--u)); top: 0; transform: translateY(-52%); font-size: calc(22 * var(--u)); font-weight: 600; line-height: 1; color: var(--plaster); font-variant-numeric: tabular-nums; }}
.baseline {{ position: absolute; left: 0; right: calc(-14 * var(--u)); bottom: 0; border-top: 1.5px solid rgb(236 230 221 / .6); }}
.jaw {{ position: absolute; left: calc(-9 * var(--u)); width: calc(18 * var(--u)); height: 0; border-top: calc(4 * var(--u)) solid var(--oxblood-ink); transform: translateY(-50%); transition: top .45s cubic-bezier(.16, 1, .3, 1); }}
.einstein {{ position: absolute; left: var(--el); bottom: calc(-6 * var(--u)); width: calc(190 * var(--u)); height: var(--eh); overflow: hidden; background: transparent; }}
.einstein img {{ width: 100%; height: 100%; object-fit: contain; object-position: bottom left; display: block; }}
.einstein-label {{ left: calc(76 * var(--u)); top: calc(574 * var(--u)); width: calc(188 * var(--u)); padding: calc(6 * var(--u)) 0; background: rgb(14 14 15 / .82); box-shadow: 0 calc(2 * var(--u)) calc(6 * var(--u)) rgb(0 0 0 / .5); text-align: center; font-size: calc(22 * var(--u)); font-weight: 700; letter-spacing: .02em; line-height: 1.1; }}
.series {{ position: absolute; left: calc(var(--eh) * 570 / 666 + var(--el) + var(--eg)); right: calc(10 * var(--u)); top: 0; bottom: 0; }}
.series .seg {{ position: absolute; height: 0; border-top: 2px solid var(--plaster); transform-origin: 0 50%; filter: drop-shadow(0 1.5px 1px rgb(0 0 0 / .8)); pointer-events: none; }}
.run {{ position: absolute; width: 30px; height: 30px; margin: -15px 0 0 -15px; border: 0; background: none; cursor: pointer; display: grid; place-items: center; }}
.run i {{ width: calc(9 * var(--u)); height: calc(9 * var(--u)); min-width: 7px; min-height: 7px; border-radius: 50%; background: var(--plaster); box-shadow: 0 1px 2px rgb(0 0 0 / .8); transition: transform .3s cubic-bezier(.16, 1, .3, 1); }}
.run:hover i, .run.on i {{ transform: scale(1.5); background: #fff; box-shadow: 0 0 0 2px var(--oxblood-ink), 0 1px 3px rgb(0 0 0 / .8); }}
.readout {{ position: absolute; transform: translate(-100%, 0); margin-top: calc(14 * var(--u)); white-space: nowrap; font-size: calc(20 * var(--u)); font-weight: 600; color: var(--plaster); transition: left .45s cubic-bezier(.16, 1, .3, 1), top .45s cubic-bezier(.16, 1, .3, 1); pointer-events: none; }}
.readout b {{ color: var(--oxblood-ink); font-weight: 700; font-variant-numeric: tabular-nums; }}
.dates {{ position: absolute; left: 0; right: 0; top: calc(100% + calc(10 * var(--u))); }}
.date {{ position: absolute; transform: translateX(-50%); font-size: calc(17 * var(--u)); font-weight: 600; white-space: nowrap; color: var(--plaster); }}

.band {{ left: 0; top: calc(628 * var(--u)); width: 100%; height: calc(92 * var(--u)); display: grid; place-items: center; }}
.hero::after {{ content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: calc(92 * var(--u)); background: var(--oxblood); z-index: 0; }}
.frame {{ z-index: 1; }}
.band h2 {{ font-family: var(--stencil); font-weight: 650; font-size: calc(54 * var(--u)); line-height: 1; letter-spacing: .01em; color: var(--plaster); }}

@media (prefers-reduced-motion: no-preference) {{
  .studio::after {{ animation: rake 2.8s .4s cubic-bezier(.16, 1, .3, 1) both; }}
  @keyframes rake {{ from {{ background-position: 100% 0; }} to {{ background-position: 0 0; }} }}
  @supports (animation-timeline: scroll()) {{
    .studio::after {{
      animation: rake linear both; animation-timeline: scroll(root); animation-range: 0 80vh;
    }}
  }}
  @supports not (animation-timeline: scroll()) {{
    .studio::after {{
      background-position: calc(100% - (var(--rake, 0) * 100%)) 0;
      animation: none;
    }}
  }}
}}
@media (prefers-reduced-motion: reduce) {{
  .studio::after {{ animation: none; background-position: 0 0; }}
}}

/* Below the first viewport. */
.pull {{ background: var(--oxblood); padding: clamp(28px, 4vw, 56px) clamp(16px, 4vw, 56px) clamp(48px, 6vw, 88px); }}
.wrap {{ max-width: 1240px; margin: 0 auto; }}
.pull-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: clamp(28px, 5vw, 72px); align-items: start; }}
.docket {{ border-top: 2px solid rgb(236 230 221 / .7); }}
.docket div {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 16px; align-items: baseline; padding: 12px 0 11px; border-bottom: 1px dashed rgb(236 230 221 / .32); }}
.docket dt {{ color: #e9d9d3; font-size: 19px; }}
.docket dd {{ font-family: var(--stencil); font-weight: 700; font-size: clamp(30px, 3.2vw, 40px); line-height: 1; font-variant-numeric: tabular-nums; text-align: right; }}
.docket dd small {{ font-family: var(--text); font-size: 17px; font-weight: 500; color: #e9d9d3; margin-left: .3em; }}
.docket-note {{ margin-top: 14px; font-size: 16px; color: #dcc6bf; max-width: 52ch; }}
.specimens {{ display: grid; gap: clamp(18px, 2.4vw, 28px); }}
.specimen {{ position: relative; padding: 18px 20px 20px 22px; background: rgb(19 19 21 / .55); box-shadow: inset 0 0 0 1px rgb(236 230 221 / .14); }}
.specimen::before {{ content: ''; position: absolute; left: 0; top: 12px; bottom: 12px; border-left: 1px dashed rgb(236 230 221 / .5); }}
.specimen figcaption {{ font-family: var(--stencil); font-weight: 700; font-size: 22px; letter-spacing: .04em; text-transform: uppercase; color: var(--oxblood-ink); }}
.specimen-q {{ margin-top: 6px; font-size: clamp(24px, 2.6vw, 32px); line-height: 1.35; font-weight: 600; text-wrap: balance; }}
.specimen-n {{ margin-top: 10px; color: #d9cfc8; font-size: 17px; }}
.specimen-n b {{ color: var(--plaster); font-variant-numeric: tabular-nums; }}

.section {{ padding: clamp(56px, 7vw, 104px) clamp(16px, 4vw, 56px) 0; }}
.section-head {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px clamp(24px, 4vw, 64px); align-items: end; margin-bottom: clamp(28px, 3.5vw, 44px); }}
.section-head h2 {{ font-family: var(--stencil); font-weight: 800; font-size: clamp(40px, 5vw, 66px); line-height: .95; letter-spacing: .005em; text-wrap: balance; }}
.section-head p {{ color: var(--plaster-dim); max-width: 56ch; }}
.seam {{ position: relative; height: 9px; margin: 0 0 clamp(28px, 3.5vw, 44px); border-left: 1px solid rgb(236 230 221 / .38); border-right: 1px solid rgb(236 230 221 / .38); }}
.seam::before {{ content: ''; position: absolute; left: 0; right: 0; top: 4px; border-top: 1px solid rgb(236 230 221 / .38); }}
.seam::after {{ content: ''; position: absolute; left: 50%; top: 0; height: 9px; border-left: 1px solid rgb(236 230 221 / .38); }}

.calliper {{ display: grid; gap: 6px; }}
.scale {{ display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 20px; font-size: 15px; color: var(--chalk); }}
.scale-row {{ position: relative; height: 22px; }}
.scale-row span {{ position: absolute; transform: translateX(-50%); font-variant-numeric: tabular-nums; white-space: nowrap; }}
.scale-row span:first-child {{ transform: none; }}
.scale-row span:last-child {{ transform: translateX(-100%); }}
.strip {{ display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 20px; align-items: center; }}
.strip-name {{ display: grid; grid-template-columns: 1fr auto; column-gap: 10px; align-items: baseline; }}
.strip-name span {{ font-family: var(--stencil); font-weight: 700; font-size: 28px; line-height: 1; }}
.strip-name b {{ font-family: var(--stencil); font-weight: 700; font-size: 28px; color: var(--oxblood-ink); font-variant-numeric: tabular-nums; }}
.strip-name small {{ grid-column: 1 / -1; font-size: 15px; color: var(--chalk); }}
.rule {{ position: relative; height: 64px; background: linear-gradient(90deg, var(--slate), var(--slate-2)); box-shadow: inset 0 1px 0 rgb(236 230 221 / .12), inset 0 -1px 0 rgb(0 0 0 / .6); cursor: crosshair; touch-action: pan-y; }}
.rule i {{ position: absolute; top: 14px; bottom: 14px; width: 2px; margin-left: -1px; background: rgb(236 230 221 / .62); }}
.rule i.hot {{ background: #fff; top: 6px; bottom: 6px; width: 3px; margin-left: -1.5px; }}
.rule .jaw {{ top: 0; bottom: 0; left: auto; width: 0; height: auto; border: 0; transform: none; }}
.rule .jaw::before, .rule .jaw::after {{ content: ''; position: absolute; left: -7px; width: 14px; height: 7px; background: var(--oxblood-ink); }}
.rule .jaw::before {{ top: 0; clip-path: polygon(0 0, 100% 0, 50% 100%); }}
.rule .jaw::after {{ bottom: 0; clip-path: polygon(50% 0, 100% 100%, 0 100%); }}
.reading {{ position: absolute; bottom: calc(100% + 8px); transform: translateX(-50%); width: max-content; max-width: min(340px, 80vw); padding: 8px 11px; background: var(--plaster); color: var(--graphite); font-size: 15px; line-height: 1.25; font-weight: 600; box-shadow: 0 6px 18px rgb(0 0 0 / .5); z-index: 2; pointer-events: none; }}
.reading b {{ color: var(--oxblood-ink); }}
.calliper-note {{ margin-top: 18px; color: var(--chalk); font-size: 16px; }}

.ledger {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 520px), 1fr)); gap: 0 clamp(24px, 4vw, 56px); }}
.crate {{ border-top: 1px solid rgb(236 230 221 / .28); }}
.crate summary {{ list-style: none; cursor: pointer; display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap; padding: 16px 0; }}
.crate summary::-webkit-details-marker {{ display: none; }}
.crate-name {{ font-family: var(--stencil); font-weight: 700; font-size: 30px; line-height: 1; }}
.crate-name::before {{ content: ''; display: inline-block; width: 0.7em; height: 0.7em; margin-right: 0.35em; vertical-align: -0.05em; border: 1.5px solid var(--oxblood-cut); box-shadow: inset 0 0 0 1px rgb(236 230 221 / .12); transform: rotate(0deg); transition: transform .3s cubic-bezier(.16, 1, .3, 1); }}
.crate[open] .crate-name::before {{ transform: rotate(45deg); }}
.crate-meta {{ color: var(--plaster-dim); font-size: 16px; }}
.crate-meta b {{ color: var(--plaster); font-variant-numeric: tabular-nums; }}
.crate summary:hover .crate-name {{ color: #fff; }}
.crate ol {{ list-style: none; padding-bottom: 18px; }}
.crate li {{ display: grid; grid-template-columns: 3.2ch minmax(0, 1fr) 72px 3ch; gap: 12px; align-items: center; padding: 7px 0; border-top: 1px dashed rgb(236 230 221 / .14); font-size: 17px; }}
.no {{ font-family: var(--stencil); font-weight: 600; color: var(--oxblood-ink); font-variant-numeric: tabular-nums; }}
.q {{ min-width: 0; overflow-wrap: anywhere; }}
.added {{ display: block; font-size: 13.5px; color: var(--chalk); }}
.bar {{ height: 6px; background: linear-gradient(90deg, var(--plaster) calc(var(--v) * 100%), rgb(236 230 221 / .14) 0); }}
.val {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
.val.none {{ grid-column: 3 / 5; color: var(--chalk); font-weight: 500; font-size: 15px; }}

.how {{ display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: clamp(28px, 5vw, 72px); }}
.how p {{ max-width: 64ch; color: #ddd6cd; }}
.how p + p {{ margin-top: 1em; }}
.next {{ list-style: none; display: grid; gap: 12px; align-content: start; }}
.next a {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 18px 20px; background: var(--slate); box-shadow: inset 0 0 0 1px rgb(236 230 221 / .16); text-decoration: none; font-family: var(--stencil); font-weight: 700; font-size: 30px; line-height: 1; transition: background .25s ease-out, box-shadow .25s ease-out; }}
.next a svg {{ flex: none; width: 22px; height: 22px; stroke: var(--oxblood-ink); stroke-width: 2; fill: none; transition: transform .3s cubic-bezier(.16, 1, .3, 1); }}
.next a:hover {{ background: var(--oxblood-2); box-shadow: inset 0 0 0 1px rgb(226 115 93 / .6); }}
.next a:hover svg {{ transform: translateX(4px); }}
.next small {{ display: block; margin-top: 6px; font-family: var(--text); font-weight: 500; font-size: 15px; color: var(--plaster-dim); }}
footer {{ margin-top: clamp(64px, 8vw, 112px); padding: 22px clamp(16px, 4vw, 56px) 32px; border-top: 1px solid rgb(236 230 221 / .2); color: var(--chalk); font-size: 15px; }}
footer .wrap {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 24px; }}

/* Narrow screens: the plinth stacks; the chart keeps its full 0-1 scale. */
@container (max-width: 760px) {{
  .frame {{ width: auto; height: auto; padding: 18px 16px 0; display: flex; flex-direction: column; }}
  .frame > * {{ position: relative; left: auto; top: auto; }}
  .studio {{ position: absolute; inset: 0 0 auto 0; height: 430px; width: 100%; overflow: hidden; -webkit-mask: linear-gradient(#000 70%, transparent); mask: linear-gradient(#000 70%, transparent); }}
  .studio img {{ height: 240%; object-position: 0 0; }}
  .title {{ white-space: normal; font-size: clamp(30px, 9vw, 42px); line-height: 1.02; text-wrap: balance; }}
  .big {{ width: auto; height: auto; font-size: clamp(88px, 28vw, 140px); margin-top: 8px; }}
  .deck {{ width: auto; font-size: 20px; margin-top: 6px; max-width: 24ch; }}
  .change {{ font-size: 19px; margin-top: 8px; white-space: normal; }}
  .links {{ position: relative; left: auto; top: auto; width: auto; font-size: 17px; gap: 8px 12px; margin-top: 10px; }}
  .links li + li::before {{ margin-right: 12px; }}
  .links a {{ padding: 4px 0; color: var(--plaster); }}
  .stage {{ margin: 22px -16px 0; position: relative; }}
  .casts {{ position: relative; left: auto; top: auto; width: min(70%, 340px); margin: 0 12px -7px auto; z-index: 1; }}
  .cast-nos {{ font-size: clamp(22px, 6vw, 32px); height: auto; padding-bottom: 2px; }}
  .face {{ position: relative; padding: 46px 14px 54px 50px; background: url(assets/plates/studio.webp) 4% 93.5% / auto 205% no-repeat, var(--slate); box-shadow: inset 0 1px 0 rgb(236 230 221 / .25); }}
  .casts-label {{ position: absolute; left: auto; right: 14px; top: 12px; font-size: 16px; white-space: normal; text-align: right; }}
  .chart {{ position: relative; left: auto; top: auto; width: 100%; height: clamp(190px, 56vw, 260px); }}
  .tick b {{ font-size: 13px; right: 14px; }}
  .tick {{ width: 5px; }} .tick.major {{ width: 9px; }}
  .chart {{ --eh: 54cqh; --el: 4px; --eg: 12px; }}
  .einstein {{ bottom: -3px; }}
  .einstein-label {{ position: absolute; left: 40px; top: auto; bottom: 10px; width: auto; padding: 3px 8px; font-size: 14px; }}
  .series {{ right: 6px; }}
  .date {{ font-size: 12px; }}
  .date:nth-child(even) {{ display: none; }}
  .readout {{ font-size: 13px; margin-top: 10px; }}
  .jaw {{ left: -6px; width: 12px; border-top-width: 3px; }}
  .band {{ position: relative; left: auto; top: auto; height: auto; margin: 0 -16px; padding: 22px 16px 4px; background: var(--oxblood); place-items: start; }}
  .hero::after {{ display: none; }}
  .band h2 {{ font-size: 40px; }}
  .pull {{ padding-top: 14px; }}
  .pull-grid, .how, .section-head {{ grid-template-columns: minmax(0, 1fr); }}
  .scale, .strip {{ grid-template-columns: minmax(0, 1fr); gap: 8px; }}
  .scale > span {{ display: none; }}
  .strip {{ margin-top: 14px; }}
  .strip-name {{ grid-template-columns: auto auto 1fr; column-gap: 10px; }}
  .strip-name small {{ grid-column: auto; text-align: right; }}
  .crate li {{ grid-template-columns: 3.2ch minmax(0, 1fr) auto; }}
  .bar {{ display: none; }}
  .val.none {{ grid-column: 3; font-size: 13px; white-space: nowrap; }}
  .next a {{ font-size: 26px; }}
}}
@container (max-width: 380px) {{
  .links {{ flex-direction: column; align-items: flex-start; gap: 0; }}
  .links li + li {{ border-left: 0; padding-left: 0; }}
  .strip-name {{ grid-template-columns: auto 1fr; }}
  .strip-name small {{ grid-column: 1 / -1; text-align: left; }}
}}
</style>
</head>
<body>
<header class="hero" id="top">
  <div class="frame">
    <picture class="studio" aria-hidden="true"><source srcset="assets/plates/studio.webp" type="image/webp"><img src="assets/plates/studio.png" alt="" width="1920" height="942" fetchpriority="high"></picture>
    <h1 class="title">AI-driven homogenization of expression — real-time tracker</h1>
    <p class="big" aria-describedby="deck">{data['sim']:.2f}</p>
    <p class="deck" id="deck">How alike Google's top 5 answers are this week, 0 to 1.</p>
    <p class="change"><b>{change_txt}</b> since {prev_txt}</p>
    <ul class="links">
      <li><a href="{METHODOLOGY_URL}">Methodology and data</a></li>
      <li><a href="{DASHBOARD_URL}">Full dashboard</a></li>
    </ul>
    <div class="stage">
      <p class="cast-nos" aria-hidden="true"><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span><span>6</span></p>
      <div class="casts">
        <div class="cast-row" role="img" aria-label="Six identical plaster casts of one helmeted figure: identical copies, where we're heading">
          <figure><picture><source srcset="assets/plates/cast.webp" type="image/webp"><img src="assets/plates/cast.png" alt="" width="321" height="420"></picture></figure>
          <figure><picture><source srcset="assets/plates/cast.webp" type="image/webp"><img src="assets/plates/cast.png" alt="" width="321" height="420"></picture></figure>
          <figure><picture><source srcset="assets/plates/cast.webp" type="image/webp"><img src="assets/plates/cast.png" alt="" width="321" height="420"></picture></figure>
          <figure><picture><source srcset="assets/plates/cast.webp" type="image/webp"><img src="assets/plates/cast.png" alt="" width="321" height="420"></picture></figure>
          <figure><picture><source srcset="assets/plates/cast.webp" type="image/webp"><img src="assets/plates/cast.png" alt="" width="321" height="420"></picture></figure>
          <figure><picture><source srcset="assets/plates/cast.webp" type="image/webp"><img src="assets/plates/cast.png" alt="" width="321" height="420"></picture></figure>
        </div>
      </div>
      <div class="face">
        <p class="casts-label" aria-hidden="true">Identical copies — where we're heading</p>
        <figure class="chart" aria-label="{e(chart_label)}">
          <div class="axis" aria-hidden="true">{ticks_html}<span class="jaw" style="top:{(1 - last['sim']) * 100:.3f}%"></span></div>
          <div class="baseline" aria-hidden="true"></div>
          <div class="einstein"><picture><source srcset="assets/plates/einstein.webp" type="image/webp"><img src="assets/plates/einstein.png" alt="A hand-carved stone bust of Albert Einstein: distinct voices" width="570" height="666"></picture></div>
          <div class="series">
            <div class="segs" aria-hidden="true">{segs_html}</div>
            {''.join(runs_html)}
            <p class="readout" aria-live="polite" style="left:100%;top:{(1 - last['sim']) * 100:.3f}%">{fmt_day(last['date'])} · <b>{last['sim']:.2f}</b></p>
            <div class="dates" aria-hidden="true">{''.join(dates_html)}</div>
          </div>
          <table class="sr"><caption>How alike Google's top 5 answers are, by run</caption><thead><tr><th scope="col">Run</th><th scope="col">Similarity, 0 to 1</th><th scope="col">Questions read</th></tr></thead><tbody>{table_rows}</tbody></table>
        </figure>
        <p class="einstein-label" aria-hidden="true">Distinct voices</p>
      </div>
    </div>
    <div class="band"><h2 id="pull-h">This week's pull</h2></div>
  </div>
</header>

<main>
  <section class="pull" aria-labelledby="pull-h">
    <div class="wrap pull-grid">
      <div>
        <dl class="docket">
          <div><dt>How alike the top 5 answers are, 0 to 1</dt><dd>{data['sim']:.2f}</dd></div>
          <div><dt>Change since {prev_txt}</dt><dd>{change_txt}</dd></div>
          <div><dt>Distinct pages out of 5, on average</dt><dd>{data['distinct']:.2f}</dd></div>
          <div><dt>Questions read this week</dt><dd>{data['n_read']}<small>of {data['n_queries']}</small></dd></div>
          <div><dt>Questions above 0.80</dt><dd>{pct(data['share_above_080'])}</dd></div>
          <div><dt>Questions with fewer than 2 distinct pages</dt><dd>{pct(data['share_below_2'])}</dd></div>
        </dl>
        <p class="docket-note">Run of {fmt_long(latest)}. Shares are of the {data['n_read']} questions read this week. Week-to-week movement is small; the series has {data['runs']} runs since {fmt_long(first)}.</p>
      </div>
      <div class="specimens">
        {specimen("Most alike this week", most, "most")}
        {specimen("Least alike this week", least, "least")}
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="calliper-h">
    <div class="wrap">
      <div class="section-head">
        <h2 id="calliper-h">Every question read this week, on one scale</h2>
        <p>Each mark is one question; the red jaws mark each domain's average. Run a finger or the pointer along a rule to read the question under it.</p>
      </div>
      <div class="seam" aria-hidden="true"></div>
      <div class="calliper">
        <div class="scale" aria-hidden="true"><span></span><div class="scale-row"><span style="left:0">0 · nothing in common</span><span style="left:50%">0.5</span><span style="left:100%">1 · the same thing</span></div></div>
        {''.join(strips)}
      </div>
      <p class="calliper-note">The full list, with each question's score, is in the ledger below.</p>
    </div>
  </section>

  <section class="section" aria-labelledby="ledger-h">
    <div class="wrap">
      <div class="section-head">
        <h2 id="ledger-h">The ledger: all {data['n_queries']} questions</h2>
        <p>Latest run. Higher means the top 5 pages say more of the same thing. Questions that could not be read this week are marked.</p>
      </div>
      <div class="seam" aria-hidden="true"></div>
      <div class="ledger">{''.join(ledger)}</div>
    </div>
  </section>

  <section class="section" aria-labelledby="how-h">
    <div class="wrap">
      <div class="section-head"><h2 id="how-h">How it's measured</h2></div>
      <div class="seam" aria-hidden="true"></div>
      <div class="how">
        <div>
          <p>Every week the tracker asks Google the same everyday questions in {", ".join(d["name"] for d in data["domains"][:-1])} and {data["domains"][-1]["name"]}. For each one it reads the first five pages that can be read and compares what they say by meaning, not exact wording. This week {data['n_read']} of the {data['n_queries']} questions could be read.</p>
          <p>The score runs from 0, where the five pages share nothing, to 1, where they say the same thing. The line is the average over the questions read in each run. {growth_txt} Questions are never edited or removed.</p>
          <p>The carved bust and the cast figures are scale anchors, not data: low on the scale means many distinct voices, high means one face repeated. Movement from week to week is still small and the series is young, so read the line as a level, not a trend.</p>
        </div>
        <ul class="next">
          <li><a href="{METHODOLOGY_URL}"><span>Methodology and data<small>How pages are chosen and compared; the raw CSVs</small></span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"/></svg></a></li>
          <li><a href="{DASHBOARD_URL}"><span>Full dashboard<small>Every run, domain and question in detail</small></span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"/></svg></a></li>
        </ul>
      </div>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <p>Updated weekly · last run {fmt_long(latest)} · {data['runs']} runs since {fmt_long(first)}</p>
    <p><a href="{REPO_URL}">Source code and data</a> · Bust and casts are original generated images</p>
  </div>
</footer>

<script>
(() => {{
  const runs = [...document.querySelectorAll('.run')];
  const readout = document.querySelector('.readout');
  const jaw = document.querySelector('.axis .jaw');
  function pick(btn) {{
    for (const r of runs) {{ const on = r === btn; r.classList.toggle('on', on); r.setAttribute('aria-pressed', String(on)); }}
    readout.style.left = btn.style.left; readout.style.top = btn.dataset.y + '%';
    readout.style.transform = parseFloat(btn.style.left) > 60 ? 'translate(-100%, 0)' : parseFloat(btn.style.left) < 12 ? 'translate(-20%, 0)' : 'translate(-50%, 0)';
    readout.innerHTML = btn.dataset.date + ' · <b>' + Number(btn.dataset.v).toFixed(2) + '</b>';
    jaw.style.top = btn.dataset.y + '%';
  }}
  runs.forEach(r => {{
    r.addEventListener('mouseenter', () => pick(r));
    r.addEventListener('focus', () => pick(r));
    r.addEventListener('click', () => pick(r));
  }});
  document.querySelector('.series').addEventListener('mouseleave', () => {{ if (!runs.some(r => r === document.activeElement)) pick(runs[runs.length - 1]); }});

  for (const rule of document.querySelectorAll('.rule')) {{
    const ticks = [...rule.querySelectorAll('i')];
    const out = rule.querySelector('.reading');
    let hot = null;
    function read(ev) {{
      const box = rule.getBoundingClientRect();
      const x = Math.min(Math.max((ev.clientX - box.left) / box.width, 0), 1);
      let best = null, bd = Infinity;
      for (const t of ticks) {{ const d = Math.abs(parseFloat(t.style.left) / 100 - x); if (d < bd) {{ bd = d; best = t; }} }}
      if (!best) return;
      if (hot) hot.classList.remove('hot');
      hot = best; hot.classList.add('hot');
      const left = parseFloat(best.style.left);
      out.hidden = false;
      out.style.left = Math.min(Math.max(left, 14), 86) + '%';
      out.innerHTML = '<b>' + best.dataset.v + '</b> · no. ' + best.dataset.n + ' · ' + best.dataset.q;
    }}
    rule.addEventListener('pointermove', read);
    rule.addEventListener('pointerdown', read);
    rule.addEventListener('pointerleave', () => {{ out.hidden = true; if (hot) hot.classList.remove('hot'); hot = null; }});
  }}

  const root = document.documentElement;
  const motionOk = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const scrollAnim = CSS.supports && CSS.supports('animation-timeline: scroll()');
  if (motionOk && !scrollAnim) {{
    const onScroll = () => {{
      const y = window.scrollY || 0;
      const t = Math.min(Math.max(y / (window.innerHeight * 0.8), 0), 1);
      root.style.setProperty('--rake', t.toFixed(4));
    }};
    onScroll();
    window.addEventListener('scroll', onScroll, {{ passive: true }});
  }}
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(render(load()))
    print(f"wrote {OUT.relative_to(TRACKER.parent)}")
