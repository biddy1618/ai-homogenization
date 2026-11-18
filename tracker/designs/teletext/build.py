"""Build the one-page public summary (tracker/designs/teletext/index.html) from the tracker CSVs.

    python tracker/designs/teletext/build.py

Every number on the page is computed here from tracker/data/runs_top5.csv and
tracker/queries.txt; nothing is hard-coded.
"""
import csv
import html
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

# Chart geometry in comp pixels (1280 x 720 frame).
Y_TOP, Y_BOTTOM = 258, 576          # value 1.0 and 0.0
X_FIRST, X_LAST = 250, 1236         # first and latest run
CELL = 9                            # mosaic cell size: the line's stroke weight

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
    page_of = {q: 101 + i for i, (_, q) in enumerate(queries)}
    categories = list(dict.fromkeys(cat for cat, _ in queries))

    rows = list(csv.DictReader(open(DATA / "runs_top5.csv")))
    by_date = defaultdict(list)
    for r in rows:
        by_date[r["date"]].append(r)
    dates = sorted(by_date)
    latest = dates[-1]
    latest_rows = {r["query"]: r for r in by_date[latest]}

    def summary(pick):
        series = []
        for d in dates:
            rs = [r for r in by_date[d] if pick(r)]
            if rs:
                series.append({"date": d, "sim": mean([float(r["mean_pairwise_cosine"]) for r in rs])})
        lr = [r for r in by_date[latest] if pick(r)]
        return {
            "series": series,
            "sim": series[-1]["sim"],
            "distinct": mean([float(r["vendi"]) for r in lr]),
        }

    subpages = [dict(summary(lambda r: True), name="ALL")]
    for cat in categories:
        subpages.append(dict(summary(lambda r, c=cat: r["category"] == c), name=cat.upper()))

    def question(r):
        return {"page": page_of.get(r["query"]), "query": r["query"], "category": r["category"],
                "sim": float(r["mean_pairwise_cosine"]), "distinct": float(r["vendi"])}

    ranked = sorted(by_date[latest], key=lambda r: float(r["mean_pairwise_cosine"]))

    index = []
    for cat in categories:
        items = []
        for c, q in queries:
            if c != cat:
                continue
            r = latest_rows.get(q)
            items.append({"page": page_of[q], "query": q,
                          "sim": float(r["mean_pairwise_cosine"]) if r else None})
        index.append({"name": cat.upper(), "sim": next(s["sim"] for s in subpages if s["name"] == cat.upper()),
                      "items": items})

    overall = subpages[0]["series"]
    return {
        "subpages": subpages,
        "latest": latest,
        "previous": overall[-2]["date"] if len(overall) > 1 else None,
        "change": overall[-1]["sim"] - overall[-2]["sim"] if len(overall) > 1 else None,
        "week": len(dates),
        "most": question(ranked[-1]),
        "least": question(ranked[0]),
        "n_queries": len(queries),
        "n_read": len(by_date[latest]),
        "index": index,
    }


def fmt_day(d):
    dt = date.fromisoformat(d)
    return f"{dt.day:02d} {dt.strftime('%b').upper()}"


def fmt_long(d):
    dt = date.fromisoformat(d)
    return f"{dt.day} {dt.strftime('%b').upper()} {dt.year}"


def x_of(i, n):
    return X_FIRST + (i / max(n - 1, 1)) * (X_LAST - X_FIRST)


def y_of(v):
    return Y_BOTTOM - v * (Y_BOTTOM - Y_TOP)


def snap(v):
    return round(v / CELL) * CELL


def u(v):
    return f"calc({v:.0f} * var(--u))"


def plot_layer(series, all_dates):
    """Stepped mosaic line plus value labels, positioned on the overall run grid."""
    n = len(all_dates)
    pos = {d: i for i, d in enumerate(all_dates)}
    pts = [(snap(x_of(pos[p["date"]], n)), snap(y_of(p["sim"]))) for p in series]
    h = CELL / 2
    segs = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        segs.append((x0 - h, y0 - h, x1 - x0 + CELL, CELL))
        if y1 != y0:
            lo, hi = sorted((y0, y1))
            segs.append((x1 - h, lo - h, CELL, hi - lo + CELL))
    segs.append((pts[-1][0] - h, pts[-1][1] - h, CELL, CELL))
    cells = "".join(
        f'<i style="left:{u(x)};top:{u(y)};width:{u(w)};height:{u(hh)}"></i>' for x, y, w, hh in segs)
    vals = []
    for i, (p, (x, y)) in enumerate(zip(series, pts)):
        if i + 1 < len(pts):
            vals.append(f'<span class="val" style="left:{u((x + pts[i + 1][0]) / 2)};top:{u(y + 12)}">{p["sim"]:.2f}</span>')
        else:
            vals.append(f'<span class="val last" style="left:{u(x + h)};top:{u(y - 40)}">{p["sim"]:.2f}</span>')
    return cells, "".join(vals)


def render(data):
    subs = data["subpages"]
    all_dates = [p["date"] for p in subs[0]["series"]]
    n_subs = len(subs)
    first = all_dates[0]
    latest = data["latest"]

    dates_html = "".join(
        f'<span class="tick" style="left:{u(snap(x_of(i, len(all_dates))))}">{fmt_day(d).split()[0]}<br>{fmt_day(d).split()[1]}</span>'
        for i, d in enumerate(all_dates))
    y_ticks = "".join(
        f'<span class="ytick{" mid" if 0 < v < 1 else ""}" style="top:{u(y_of(v) - 9 - 248)}">{lab}</span>'
        for v, lab in [(1, "1"), (0.8, "0.8"), (0.6, "0.6"), (0.4, "0.4"), (0.2, "0.2"), (0, "0")])

    heads, layers = [], []
    for k, s in enumerate(subs):
        on = " on" if k == 0 else ""
        cells, vals = plot_layer(s["series"], all_dates)
        series_text = "; ".join(f"{fmt_day(p['date'])}: {p['sim']:.2f}" for p in s["series"])
        scope = "all questions" if s["name"] == "ALL" else f"{s['name'].lower()} questions"
        label = (f"Line chart, {scope}, on a 0 to 1 scale of how alike Google's top 5 answers are, "
                 f"weekly from {fmt_day(first)} to {fmt_day(latest)}: {series_text}. "
                 f"0 means distinct voices, 1 means identical copies.")
        line1 = ("How alike Google's top 5 answers are this week." if s["name"] == "ALL"
                 else f"{s['name']}: how alike the top 5 answers are.")
        heads.append(
            f'<div class="layer head{on}" data-sub="{k}">'
            f'<p class="big mosaic" aria-hidden="true">{s["sim"]:.2f}</p>'
            f'<p class="deck">{e(line1)}<br>They add up to {s["distinct"]:.2f} distinct answers out of 5.</p></div>')
        layers.append(
            f'<div class="layer plot-layer{on}" data-sub="{k}">'
            f'<div class="chart" role="img" aria-label="{e(label)}">{cells}</div>'
            f'<div class="vals" aria-hidden="true">{vals}</div></div>')

    most, least = data["most"], data["least"]

    def reveal_item(kind, q):
        return (f'<div class="reveal-item"><p class="reveal-q"><span class="pg">P{q["page"]}</span> {e(q["query"])}</p>'
                f'<p class="reveal-n"><span class="kind">{kind}</span> · <span class="cy">{q["sim"]:.2f}</span> alike · '
                f'{q["distinct"]:.2f} distinct answers out of 5 · {e(q["category"])}</p></div>')

    reveal_html = reveal_item("Most alike this week", most) + reveal_item("Least alike this week", least)

    change = data["change"]
    change_txt = f"{change:+.2f}" if change is not None else "—"

    index_html = ""
    for block in data["index"]:
        rows = ""
        for it in block["items"]:
            if it["sim"] is None:
                val = '<span class="q-val none">Not read this week</span>'
                bar = ""
            else:
                val = f'<span class="q-val">{it["sim"]:.2f}</span>'
                bar = f'<span class="q-bar" style="--v:{it["sim"]:.3f}"></span>'
            rows += (f'<li><span class="q-pg">{it["page"]}</span><span class="q-text">{e(it["query"])}</span>'
                     f'{bar}{val}</li>')
        index_html += (f'<section class="domain" aria-labelledby="d-{block["name"].lower()}">'
                       f'<h3 id="d-{block["name"].lower()}"><span>{block["name"]}</span>'
                       f'<span class="cy">{block["sim"]:.2f}</span></h3><ol>{rows}</ol></section>')

    page_first = data["index"][0]["items"][0]["page"]
    page_last = data["index"][-1]["items"][-1]["page"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI-driven homogenization of expression — real-time tracker</title>
<meta name="description" content="Every week the tracker asks Google the same {data['n_queries']} everyday questions and measures how alike the top 5 answers are. This week: {subs[0]['sim']:.2f} on a 0 to 1 scale.">
<meta property="og:title" content="AI-driven homogenization of expression — real-time tracker">
<meta property="og:description" content="Google's top 5 answers to everyday questions now add up to {subs[0]['distinct']:.2f} distinct answers out of 5. Measured weekly.">
<meta property="og:type" content="website">
<meta name="theme-color" content="#080808">
<style>
@font-face {{ font-family: 'Jersey 15'; src: url(fonts/Jersey15-400.woff2) format('woff2'); font-weight: 400; font-display: block; }}
:root {{
  --black: #080808; --yellow: #ECD517; --cyan: #17A6C2; --white: #F3F2F2; --grey: #9A9A9A;
  --red: #B11314; --red-ink: #FF5A4D; --green: #1F6C20; --blue: #082799;
  --u: calc(100cqw / 1280);
  --font: 'Jersey 15', ui-monospace, monospace;
  color-scheme: dark;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ background: var(--black); color: var(--white); scrollbar-color: var(--cyan) var(--black); }}
body {{ container-type: inline-size; font-family: var(--font); font-weight: 400; text-transform: uppercase; }}
::selection {{ background: var(--cyan); color: var(--black); }}
a {{ color: inherit; text-decoration: none; }}
button {{ font: inherit; color: inherit; background: none; border: 0; cursor: pointer; text-transform: inherit; letter-spacing: inherit; }}
:focus-visible {{ outline: max(2px, calc(3 * var(--u))) solid var(--yellow); outline-offset: max(2px, calc(2 * var(--u))); }}
.cy {{ color: var(--cyan); }}
.sr {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }}

/* First viewport: the P100 screen, laid out on the approved 1280 x 720 frame. */
.screen {{ position: relative; width: 100%; aspect-ratio: 1280 / 720; overflow: hidden; }}
.screen > * {{ position: absolute; }}
.layer {{ display: none; }}
.layer.on {{ display: block; }}
.mosaic {{
  -webkit-mask: repeating-linear-gradient(90deg, #000 0 calc(3.4 * var(--u)), transparent calc(3.4 * var(--u)) calc(3.75 * var(--u))),
                repeating-linear-gradient(0deg, #000 0 calc(3.4 * var(--u)), transparent calc(3.4 * var(--u)) calc(3.75 * var(--u)));
  -webkit-mask-composite: source-in; mask-composite: intersect;
}}
.big.mosaic {{
  -webkit-mask: repeating-linear-gradient(90deg, #000 0 calc(6.5 * var(--u)), transparent calc(6.5 * var(--u)) calc(7.6 * var(--u))),
                repeating-linear-gradient(0deg, #000 0 calc(6.5 * var(--u)), transparent calc(6.5 * var(--u)) calc(7.6 * var(--u)));
  -webkit-mask-composite: source-in; mask-composite: intersect;
}}
.header {{ left: calc(10 * var(--u)); top: calc(-2 * var(--u)); font-size: calc(45 * var(--u)); line-height: 1.05; color: var(--yellow); letter-spacing: .06em; white-space: nowrap; }}
.subpage {{ right: calc(12 * var(--u)); top: calc(13 * var(--u)); font-size: calc(18 * var(--u)); letter-spacing: .04em; white-space: nowrap; display: flex; gap: calc(30 * var(--u)); align-items: baseline; }}
.hold[aria-pressed="true"] {{ color: var(--black); background: var(--yellow); padding: 0 calc(4 * var(--u)); }}
.hold:hover {{ color: var(--yellow); }}
.nav {{ left: calc(10 * var(--u)); top: calc(52 * var(--u)); height: calc(28 * var(--u)); width: calc(480 * var(--u)); background: var(--blue); display: flex; align-items: center; justify-content: space-between; padding: 0 calc(14 * var(--u)); font-size: calc(22 * var(--u)); letter-spacing: .1em; box-shadow: inset 0 0 0 calc(1 * var(--u)) #2a4fd6; }}
.nav a:hover, .nav .hi, .nav .next:hover {{ color: var(--yellow); }}
.title {{ left: calc(10 * var(--u)); top: calc(86 * var(--u)); width: calc(1250 * var(--u)); font-weight: 400; font-size: calc(51 * var(--u)); line-height: 1.1; color: var(--yellow); letter-spacing: .02em; white-space: nowrap; }}
.rule {{ left: 0; top: calc(147 * var(--u)); width: 100%; height: calc(2 * var(--u)); background: var(--cyan); opacity: .55; }}
.heads {{ left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; }}
.big {{ position: absolute; left: calc(10 * var(--u)); top: calc(150 * var(--u)); font-size: calc(105 * var(--u)); line-height: 1; color: var(--cyan); }}
.deck {{ position: absolute; left: calc(208 * var(--u)); top: calc(164 * var(--u)); font-size: calc(30 * var(--u)); line-height: 1.3; letter-spacing: .05em; white-space: nowrap; }}

.plot {{ left: 0; top: 0; width: 100%; height: 100%; container-type: inline-size; pointer-events: none; }}
.plot-in {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; }}
.plot-in > * {{ position: absolute; }}
.plate {{ display: block; }}
.clones {{ left: calc(964 * var(--u)); top: calc(152 * var(--u)); width: calc(308 * var(--u)); height: calc(80 * var(--u)); object-fit: cover; }}
.einstein {{ left: calc(50 * var(--u)); top: calc(494 * var(--u)); width: calc(137 * var(--u)); height: calc(142 * var(--u)); object-fit: contain; }}
.label {{ font-size: calc(25 * var(--u)); letter-spacing: .03em; white-space: nowrap; }}
.clones-label {{ left: calc(1000 * var(--u)); top: calc(234 * var(--u)); letter-spacing: .05em; }}
.einstein-label {{ left: calc(28 * var(--u)); top: calc(640 * var(--u)); }}
.gap-label {{ left: calc(70 * var(--u)); top: calc(426 * var(--u)); font-size: calc(21 * var(--u)); letter-spacing: .02em; white-space: nowrap; }}
.yaxis {{ left: calc(12 * var(--u)); top: calc(248 * var(--u)); width: calc(56 * var(--u)); height: calc(340 * var(--u)); }}
.yaxis::after {{ content: ''; position: absolute; right: calc(1 * var(--u)); top: calc(6 * var(--u)); bottom: calc(12 * var(--u)); width: calc(2 * var(--u)); background: var(--white); }}
.ytick {{ position: absolute; right: calc(26 * var(--u)); font-size: calc(22.5 * var(--u)); line-height: 1; letter-spacing: .02em; }}
.ytick::after {{ content: ''; position: absolute; left: calc(100% + calc(6 * var(--u))); top: 50%; width: calc(16 * var(--u)); height: calc(2 * var(--u)); background: var(--white); }}
.baseline {{ left: calc(218 * var(--u)); top: calc(575 * var(--u)); width: calc(1048 * var(--u)); height: calc(2 * var(--u)); background: var(--white); opacity: .75; }}
.plot-layer {{ left: 0; top: 0; width: 100%; height: 100%; }}
.chart, .vals {{ position: absolute; inset: 0; }}
.chart i {{ position: absolute; background:
  repeating-linear-gradient(90deg, transparent 0 calc(8 * var(--u)), rgb(8 8 8 / .7) calc(8 * var(--u)) calc(9 * var(--u))),
  var(--cyan); }}
.val {{ position: absolute; transform: translateX(-50%); white-space: nowrap; color: var(--cyan); font-size: calc(30 * var(--u)); letter-spacing: .04em; }}
.val.last {{ transform: translateX(-100%); }}
.dates {{ left: 0; top: calc(584 * var(--u)); width: 100%; }}
.tick {{ position: absolute; transform: translateX(-50%); text-align: center; font-size: calc(22.5 * var(--u)); line-height: 1.05; letter-spacing: .04em; }}

.keys {{ left: calc(240 * var(--u)); top: calc(644 * var(--u)); display: flex; gap: calc(14 * var(--u)); }}
.key {{ height: calc(40 * var(--u)); display: inline-flex; align-items: center; justify-content: center; padding: 0 calc(12 * var(--u)); font-size: calc(22.5 * var(--u)); letter-spacing: .06em; color: var(--white); white-space: nowrap;
  background-image: repeating-linear-gradient(90deg, transparent 0 calc(2 * var(--u)), rgb(0 0 0 / .16) calc(2 * var(--u)) calc(2.5 * var(--u))),
                    repeating-linear-gradient(0deg, transparent 0 calc(2 * var(--u)), rgb(0 0 0 / .16) calc(2 * var(--u)) calc(2.5 * var(--u)));
  box-shadow: inset 0 0 0 calc(2 * var(--u)) rgb(0 0 0 / .45); }}
.key-red {{ width: calc(314 * var(--u)); background-color: var(--red); }}
.key-green {{ width: calc(242 * var(--u)); background-color: var(--green); }}
.key-yellow {{ width: calc(182 * var(--u)); background-color: var(--yellow); color: var(--black); }}
.key-cyan {{ width: calc(238 * var(--u)); background-color: var(--cyan); color: var(--black); }}
.key:hover {{ filter: brightness(1.15); }}
.key-red[aria-expanded="true"] {{ box-shadow: inset 0 0 0 calc(3 * var(--u)) var(--white); }}

.reveal {{ left: calc(270 * var(--u)); top: calc(266 * var(--u)); width: calc(996 * var(--u)); height: calc(304 * var(--u)); background: var(--black); border: calc(2 * var(--u)) solid var(--red); padding: calc(22 * var(--u)) calc(28 * var(--u)); display: grid; grid-template-columns: 1fr 1fr; gap: calc(40 * var(--u)); }}
.reveal[hidden] {{ display: none; }}
.reveal-n .kind {{ color: var(--red-ink); }}
.reveal-q .pg {{ color: var(--black); background: var(--yellow); padding: 0 .15em; margin-right: .2em; }}
.reveal-q {{ margin-top: 0; font-size: calc(45 * var(--u)); line-height: 1.15; color: var(--yellow); text-wrap: balance; }}
.reveal-n {{ margin-top: calc(16 * var(--u)); font-size: calc(22.5 * var(--u)); letter-spacing: .05em; line-height: 1.3; }}

@media (prefers-reduced-motion: no-preference) {{
  .wipe {{ animation: wipe 420ms steps(12, end); }}
  @keyframes wipe {{ from {{ clip-path: inset(0 0 100% 0); }} to {{ clip-path: inset(0 0 0 0); }} }}
}}

/* Below the first viewport: the facts behind the screen. */
.page {{ --s: max(16px, calc(22.5 * var(--u))); font-size: var(--s); letter-spacing: .05em; line-height: 1.25; padding: 0 calc(12 * var(--u)) calc(60 * var(--u)); }}
.band {{ border-top: calc(2 * var(--u)) solid rgb(23 166 194 / .55); padding-top: max(28px, calc(44 * var(--u))); margin-top: max(36px, calc(56 * var(--u))); }}
.band-head {{ display: flex; align-items: baseline; gap: 1.2em; flex-wrap: wrap; margin-bottom: max(18px, calc(28 * var(--u))); }}
.band-head h2 {{ font-weight: 400; color: var(--yellow); font-size: max(30px, calc(51 * var(--u))); line-height: 1; letter-spacing: .02em; }}
.band-head .pg {{ color: var(--black); background: var(--yellow); padding: 0 .3em; }}
.band-head p {{ color: var(--grey); }}
.facts {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: max(14px, calc(20 * var(--u))); }}
.fact {{ padding-top: .4em; }}
.fact b {{ display: block; font-weight: 400; color: var(--cyan); font-size: max(40px, calc(75 * var(--u))); line-height: 1; }}
.fact span {{ display: block; margin-top: .35em; max-width: 22ch; }}
.extremes {{ display: grid; grid-template-columns: 1fr 1fr; gap: max(14px, calc(20 * var(--u))); margin-top: max(22px, calc(32 * var(--u))); }}
.extremes .reveal-q {{ font-size: max(24px, calc(45 * var(--u))); }}
.extremes .reveal-n {{ font-size: var(--s); }}
.domains {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 420px), 1fr)); gap: max(22px, calc(32 * var(--u))) max(22px, calc(40 * var(--u))); }}
.domain h3 {{ display: flex; justify-content: space-between; font-weight: 400; font-size: max(24px, calc(37.5 * var(--u))); color: var(--yellow); border-bottom: 2px solid var(--blue); padding-bottom: .15em; margin-bottom: .35em; }}
.domain ol {{ list-style: none; }}
.domain li {{ display: grid; grid-template-columns: 3.2ch 1fr 4.5em 2.6ch; align-items: center; gap: .6em; padding: .18em 0; font-size: max(15px, calc(19.5 * var(--u))); letter-spacing: .04em; }}
.domain li:hover {{ background: rgb(8 39 153 / .45); }}
.q-pg {{ color: var(--yellow); font-variant-numeric: tabular-nums; }}
.q-text {{ min-width: 0; }}
.q-bar {{ height: .55em; background:
  repeating-linear-gradient(90deg, transparent 0 calc(var(--s) * .3), var(--black) calc(var(--s) * .3) calc(var(--s) * .36)),
  linear-gradient(90deg, var(--cyan) calc(var(--v) * 100%), rgb(243 242 242 / .12) 0); }}
.q-val {{ color: var(--cyan); text-align: right; font-variant-numeric: tabular-nums; }}
.q-val.none {{ grid-column: 3 / 5; color: var(--grey); }}
.how {{ display: grid; grid-template-columns: 1.3fr 1fr; gap: max(22px, calc(40 * var(--u))); }}
.how p + p {{ margin-top: .8em; }}
.how p {{ max-width: 62ch; text-transform: none; letter-spacing: .03em; font-size: max(17px, calc(24 * var(--u))); line-height: 1.3; }}
.links {{ list-style: none; display: grid; gap: .5em; align-content: start; }}
.links a {{ display: inline-block; padding: .2em .6em; background: var(--blue); }}
.links a:hover {{ color: var(--yellow); }}
.links .pg {{ color: var(--yellow); margin-right: .6em; }}
.colophon {{ margin-top: max(28px, calc(44 * var(--u))); color: var(--grey); }}

/* Narrow screens: the P100 screen stacks; the plot keeps its own scale with legible floors. */
@container (max-width: 760px) {{
  .screen {{ aspect-ratio: auto; overflow: visible; display: flex; flex-direction: column; gap: 10px; padding: 10px 12px 4px; }}
  .screen > * {{ position: static; }}
  .header {{ font-size: 18px; white-space: normal; order: 0; }}
  .subpage {{ font-size: 16px; order: 1; justify-content: space-between; }}
  .nav {{ width: 100%; height: 34px; font-size: 16px; order: 2; padding: 0 10px; }}
  .title {{ width: auto; white-space: normal; font-size: 34px; line-height: 1; order: 3; }}
  .rule {{ height: 2px; order: 4; }}
  .heads {{ height: auto; order: 5; }}
  .layer.head.on {{ display: grid; grid-template-columns: auto 1fr; gap: 12px; align-items: center; }}
  .big {{ position: static; font-size: 64px; }}
  .deck {{ position: static; font-size: 17px; white-space: normal; line-height: 1.3; }}
  .mosaic, .big.mosaic {{ -webkit-mask: none; mask: none; }}
  .plot {{ position: relative; order: 6; aspect-ratio: 1280 / 560; margin: 0 -12px; width: calc(100% + 24px); }}
  .gl-more {{ display: none; }}
  .ytick:not(:first-child) {{ visibility: hidden; }}
  .einstein {{ top: calc(468 * var(--u)); }}
  .einstein-label {{ top: calc(632 * var(--u)); }}
  .plot-in {{ top: calc(-140 * var(--u)); height: calc(720 * var(--u)); }}
  .val, .tick, .label, .gap-label, .ytick {{ font-size: max(11px, calc(22.5 * var(--u))); }}
  .label {{ letter-spacing: .04em; }}
  .gap-label {{ top: calc(400 * var(--u)); }}
  .keys {{ order: 7; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
  .key {{ width: auto; height: 44px; font-size: 16px; padding: 0 8px; white-space: normal; text-align: center; line-height: 1; }}
  .reveal {{ position: static; order: 8; width: auto; height: auto; grid-template-columns: 1fr; gap: 18px; padding: 14px; border-width: 2px; }}
  .reveal-q {{ font-size: 26px; }}
  .reveal-n {{ font-size: 15px; }}
  .page {{ padding: 0 12px 40px; }}
  .facts {{ grid-template-columns: 1fr 1fr; }}
  .extremes, .how {{ grid-template-columns: 1fr; }}
  .domain li {{ grid-template-columns: 3.2ch minmax(0, 1fr) auto; }}
  .q-bar {{ display: none; }}
  .q-val.none {{ grid-column: 3; white-space: nowrap; font-size: 13px; }}
  .q-text {{ overflow-wrap: anywhere; }}
}}
</style>
</head>
<body>
<main class="screen" id="top" aria-labelledby="title">
  <p class="header">P100 HOMOGENIZATION TRACKER &nbsp;WK {data['week']} &nbsp;{fmt_day(latest)}</p>
  <p class="subpage"><span>SUBPAGE <span class="sub-n">1</span>/{n_subs}</span><button class="hold" type="button" aria-pressed="false" hidden>HOLD</button></p>
  <nav class="nav" aria-label="Site">
    <a href="#top" aria-current="page">&lt;&lt; <span class="hi">100</span> HOME</a>
    <a class="hi" href="{DASHBOARD_URL}">DASHBOARD</a>
    <a href="{METHODOLOGY_URL}">METHODOLOGY</a>
    <button class="next" type="button" aria-label="Next subpage" hidden>&gt;&gt;</button>
  </nav>
  <h1 id="title" class="title mosaic">AI-driven homogenization of expression — real-time tracker</h1>
  <div class="rule" aria-hidden="true"></div>
  <div class="heads">{''.join(heads)}</div>
  <div class="plot">
    <div class="plot-in">
      <img class="plate clones" src="assets/plates/clones.png" alt="Four identical helmeted figures: identical copies">
      <p class="label clones-label" aria-hidden="true">IDENTICAL COPIES</p>
      <div class="yaxis" aria-hidden="true">{y_ticks}</div>
      <div class="baseline" aria-hidden="true"></div>
      {''.join(layers)}
      <p class="gap-label" aria-hidden="true">NO DATA<span class="gl-more"> BEFORE {fmt_day(first)}</span></p>
      <div class="dates" aria-hidden="true">{dates_html}</div>
      <img class="plate einstein" src="assets/plates/einstein.png" alt="Albert Einstein: distinct voices">
      <p class="label einstein-label" aria-hidden="true">DISTINCT<span class="gl-more"> VOICES</span></p>
    </div>
  </div>
  <div class="keys">
    <a class="key key-red" href="#this-week" aria-controls="reveal">REVEAL MOST ALIKE QUESTION</a>
    <a class="key key-green" href="#questions">ALL {data['n_queries']} QUESTIONS</a>
    <a class="key key-yellow" href="{DASHBOARD_URL}">DASHBOARD</a>
    <a class="key key-cyan" href="#how">HOW IT'S MEASURED</a>
  </div>
  <p class="sr" id="sub-status" aria-live="polite"></p>
  <section class="reveal" id="reveal" aria-label="Most and least alike questions this week" hidden>{reveal_html}</section>
</main>

<div class="page">
  <section class="band" id="this-week" aria-labelledby="this-week-h">
    <div class="band-head"><h2 id="this-week-h"><span class="pg">P300</span> This week</h2><p>Run of {fmt_long(latest)}</p></div>
    <div class="facts">
      <p class="fact"><b>{subs[0]['sim']:.2f}</b><span>How alike the top 5 answers are, 0 to 1</span></p>
      <p class="fact"><b>{change_txt}</b><span>Change since {fmt_day(data['previous']) if data['previous'] else 'last run'}</span></p>
      <p class="fact"><b>{subs[0]['distinct']:.2f}</b><span>Distinct answers out of 5</span></p>
      <p class="fact"><b>{data['n_read']}</b><span>Of {data['n_queries']} questions readable this week</span></p>
    </div>
    <div class="extremes">{reveal_html}</div>
  </section>

  <section class="band" id="questions" aria-labelledby="questions-h">
    <div class="band-head"><h2 id="questions-h"><span class="pg">P{page_first}–{page_last}</span> All {data['n_queries']} questions</h2><p>Latest run · higher means the top 5 answers say more of the same thing</p></div>
    <div class="domains">{index_html}</div>
  </section>

  <section class="band" id="how" aria-labelledby="how-h">
    <div class="band-head"><h2 id="how-h"><span class="pg">P400</span> How it's measured</h2></div>
    <div class="how">
      <div>
        <p>Every week the tracker asks Google the same {data['n_queries']} everyday questions, twenty each in finance, health, law, science and tech. It reads the first five pages that answer each one and compares what they say, by meaning rather than exact wording.</p>
        <p>The score runs from 0, where the five pages share nothing, to 1, where they say the same thing. The line is the average across all questions; the subpages show each domain. The panel of questions never changes, so weeks can be compared. Movement week to week is still small, and the series is young.</p>
      </div>
      <ul class="links">
        <li><a href="{METHODOLOGY_URL}"><span class="pg">401</span>Methodology and data</a></li>
        <li><a href="{DASHBOARD_URL}"><span class="pg">402</span>Full dashboard</a></li>
        <li><a href="{REPO_URL}"><span class="pg">403</span>Source code</a></li>
      </ul>
    </div>
    <p class="colophon">Updated weekly · last run {fmt_long(latest)} · {data['week']} runs since {fmt_long(first)}</p>
  </section>
</div>

<script>
(() => {{
  const layers = [...document.querySelectorAll('.layer')];
  const count = {n_subs};
  const subN = document.querySelector('.sub-n');
  const hold = document.querySelector('.hold');
  const next = document.querySelector('.next');
  const key = document.querySelector('.key-red');
  const reveal = document.getElementById('reveal');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let k = 0, timer = null;

  function show(n) {{
    k = (n + count) % count;
    for (const el of layers) {{
      const on = Number(el.dataset.sub) === k;
      el.classList.toggle('on', on);
      if (on) {{ el.classList.remove('wipe'); void el.offsetWidth; el.classList.add('wipe'); }}
    }}
    subN.textContent = k + 1;
  }}
  const status = document.getElementById('sub-status');
  function announce() {{ status.textContent = `Subpage ${{k + 1}} of ${{count}}: ` + layers.find(l => l.classList.contains('head') && l.classList.contains('on')).textContent; }}
  function held() {{ return hold.getAttribute('aria-pressed') === 'true'; }}
  function schedule() {{
    clearInterval(timer);
    if (!held() && reveal.hidden && !document.hidden) timer = setInterval(() => show(k + 1), 8000);
  }}

  hold.hidden = false; next.hidden = false;
  if (reduced) hold.setAttribute('aria-pressed', 'true');
  hold.addEventListener('click', () => {{ hold.setAttribute('aria-pressed', String(!held())); schedule(); }});
  next.addEventListener('click', () => {{ show(k + 1); announce(); schedule(); }});
  document.addEventListener('visibilitychange', schedule);

  key.setAttribute('role', 'button');
  key.setAttribute('aria-expanded', 'false');
  function toggleReveal(open) {{
    reveal.hidden = !open;
    key.setAttribute('aria-expanded', String(open));
    if (open && !reduced) {{ reveal.classList.remove('wipe'); void reveal.offsetWidth; reveal.classList.add('wipe'); }}
    schedule();
  }}
  key.addEventListener('click', ev => {{ ev.preventDefault(); toggleReveal(reveal.hidden); }});
  key.addEventListener('keydown', ev => {{ if (ev.key === ' ') {{ ev.preventDefault(); toggleReveal(reveal.hidden); }} }});
  document.addEventListener('keydown', ev => {{ if (ev.key === 'Escape' && !reveal.hidden) {{ toggleReveal(false); key.focus(); }} }});

  schedule();
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(render(load()))
    print(f"wrote {OUT.relative_to(TRACKER.parent)}")
