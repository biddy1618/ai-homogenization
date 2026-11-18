"""Build the one-page public summary (tracker/designs/concordance/index.html) from the tracker CSVs.

    python tracker/designs/concordance/build.py

Every number on the page is computed here from tracker/data/runs_top5.csv and
tracker/queries.txt; nothing is hard-coded.
"""
import csv
import html
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACKER = HERE.parent.parent
DATA = TRACKER / "data"
OUT = HERE / "index.html"

DASHBOARD_URL = "../../dashboard/"
METHODOLOGY_URL = "https://github.com/biddy1618/ai-homogenization/blob/main/tracker/README.md"
REPO_URL = "https://github.com/biddy1618/ai-homogenization"
PAGE_URL = "https://biddy1618.github.io/ai-homogenization/tracker/designs/concordance/"

TITLE = "AI-driven homogenization of expression — real-time tracker"

e = html.escape


# ---------------------------------------------------------------- data

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
        }

    overall = summary(lambda r: True)
    sectors = [dict(summary(lambda r, c=cat: r["category"] == c), name=cat) for cat in categories]

    def question(r):
        return {"query": r["query"], "category": r["category"],
                "sim": float(r["mean_pairwise_cosine"]), "distinct": float(r["vendi"])}

    meta = list(csv.DictReader(open(DATA / "_runs_meta.csv")))
    original = int(meta[0]["n_queries"])
    added_on = next((m["run_date"] for m in meta if int(m["n_queries"]) == len(queries)), None)

    latest_rows = by_date[latest]
    ranked = sorted((question(r) for r in latest_rows), key=lambda q: q["sim"])
    series = overall["series"]
    return {
        "series": series,
        "sim": overall["sim"],
        "distinct": overall["distinct"],
        "sectors": sorted(sectors, key=lambda s: -s["sim"]),
        "latest": latest,
        "previous": series[-2]["date"] if len(series) > 1 else None,
        "change": series[-1]["sim"] - series[-2]["sim"] if len(series) > 1 else None,
        "week": len(dates),
        "first": dates[0],
        "most": ranked[-1],
        "least": ranked[0],
        "ranked": ranked,
        "n_queries": len(queries),
        "n_read": len(latest_rows),
        "original": original,
        "added": len(queries) - original,
        "added_on": added_on,
        "share_high": sum(q["sim"] > 0.80 for q in ranked) / len(ranked),
        "share_few": sum(q["distinct"] < 2 for q in ranked) / len(ranked),
    }


# ---------------------------------------------------------------- formatting

def d_short(d):
    dt = date.fromisoformat(d)
    return f"{dt.day:02d} {dt.strftime('%b')}"


def d_long(d):
    dt = date.fromisoformat(d)
    return f"{dt.day} {dt.strftime('%b')} {dt.year}"


def f2(v):
    return f"{v:.2f}"


def f3(v):
    return f"{v:.3f}"


def signed(v):
    s = f"{v:+.3f}"
    return s.replace("-", "−")


def pct(v):
    return f"{round(v * 100)}%"


def floor_1(v):
    return f"{int(v * 10) / 10:.1f}"


# ---------------------------------------------------------------- chart

def chart_svg(data, w, h, variant):
    """Full 0-1 scale line chart. Two figures only: Einstein lower left, the identical units top right."""
    mobile = variant == "m"
    pad_l, pad_r = (46, 64) if mobile else (64, 24)
    pad_t, pad_b = (118, 46) if mobile else (74, 42)
    x0, x1 = pad_l, w - pad_r
    y0, y1 = h - pad_b, pad_t          # value 0 and value 1

    first = date.fromisoformat(data["first"])
    last = date.fromisoformat(data["latest"])
    span = (last - first).days
    start = first - timedelta(days=round(span * (0.42 if mobile else 0.36)))
    end = last + timedelta(days=round(span * (0.30 if mobile else 0.24)))
    total = (end - start).days

    def X(d):
        return x0 + (date.fromisoformat(d) - start).days / total * (x1 - x0)

    def Y(v):
        return y0 - v * (y0 - y1)

    out = [f'<svg class="chart chart-{variant}" viewBox="0 0 {w} {h}" role="img" '
           f'aria-labelledby="chart-title-{variant} chart-desc-{variant}" preserveAspectRatio="xMidYMid meet">',
           f'<title id="chart-title-{variant}">Average similarity of Google\'s top 5 answers, week by week</title>',
           f'<desc id="chart-desc-{variant}">Line on a scale from 0 (all five answers different) to 1 (all identical). '
           f'No data before {d_long(data["first"])}. '
           + "; ".join(f'{d_long(p["date"])}: {f3(p["sim"])}' for p in data["series"]) + ".</desc>",
           '<defs><pattern id="hatch-' + variant + '" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(-12)">'
           '<line x1="0" y1="0" x2="0" y2="9" class="hatch"/></pattern></defs>']

    # no-data period
    gx = X(data["first"])
    out.append(f'<rect class="gap" x="{x0:.1f}" y="{y1:.1f}" width="{gx - x0 - 8:.1f}" height="{y0 - y1:.1f}" fill="url(#hatch-{variant})"/>')
    gcx = (x0 + gx - 8) / 2
    lines = ["no data", "before", d_short(data["first"])] if mobile else ["no data", f"before {d_short(data['first'])}"]
    gy = Y(0.97) if mobile else Y(0.62)
    out.append(f'<text class="gap-label" x="{gcx:.1f}" y="{gy:.1f}" text-anchor="middle">'
               + "".join(f'<tspan x="{gcx:.1f}" dy="{0 if k == 0 else 1.25}em">{e(t)}</tspan>' for k, t in enumerate(lines))
               + '</text>')

    # grid and y axis
    for v in (0, 0.25, 0.5, 0.75, 1):
        y = Y(v)
        cls = "grid grid-base" if v == 0 else "grid"
        out.append(f'<line class="{cls}" x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}"/>')
        label = "0" if v == 0 else ("1" if v == 1 else f"{v:.2f}".rstrip("0"))
        out.append(f'<text class="tick" x="{x0 - 10}" y="{y + 4:.1f}" text-anchor="end">{label}</text>')
    out.append(f'<line class="axis" x1="{x0}" x2="{x0}" y1="{y1 - 8:.1f}" y2="{y0:.1f}"/>')

    # x ticks: run dates, skipping ones that would collide
    last_x = -1e9
    min_gap = 56 if mobile else 64
    for i, p in enumerate(data["series"]):
        x = X(p["date"])
        if x - last_x < min_gap and i != len(data["series"]) - 1:
            continue
        if i == len(data["series"]) - 1 and x - last_x < min_gap:
            out.pop()
        out.append(f'<text class="tick tick-x" x="{x:.1f}" y="{y0 + 24:.1f}" text-anchor="middle">{d_short(p["date"])}</text>')
        last_x = x

    # line
    pts = [(X(p["date"]), Y(p["sim"])) for p in data["series"]]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    out.append(f'<path class="line" d="{path}" pathLength="1"/>')
    for (x, y), p in zip(pts, data["series"]):
        out.append(f'<rect class="pt" x="{x - 4:.1f}" y="{y - 4:.1f}" width="8" height="8">'
                   f'<title>{d_long(p["date"])}: {f3(p["sim"])}</title></rect>')
    lx, ly = pts[-1]
    out.append(f'<rect class="pt-last" x="{lx - 7:.1f}" y="{ly - 7:.1f}" width="14" height="14"/>')
    out.append(f'<text class="end-val" x="{lx + 14:.1f}" y="{ly + 8:.1f}">{f2(data["sim"])}</text>')
    if data["change"] is not None:
        since = f'since {d_short(data["previous"])}'
        chg = signed(data["change"])
        if mobile:
            out.append(f'<text class="end-chg" x="{lx + 14:.1f}" y="{ly + 30:.1f}"><tspan class="end-chg-n">{chg}</tspan>'
                       f'<tspan x="{lx + 14:.1f}" dy="1.25em">{since}</tspan></text>')
        else:
            out.append(f'<text class="end-chg" x="{lx + 14:.1f}" y="{ly + 32:.1f}"><tspan class="end-chg-n">{chg}</tspan> {since}</text>')

    # figure: Einstein, lower left, just right of the origin
    ew = 92 if mobile else 104
    eh = ew * 666 / 520
    ex = x0 + 6
    ey = y0 - eh + 2
    out.append(f'<image class="fig" href="assets/einstein.webp" x="{ex:.1f}" y="{ey:.1f}" width="{ew}" height="{eh:.1f}"/>')
    out.append(f'<text class="fig-label" x="{ex + ew + 10:.1f}" y="{y0 - 14:.1f}">distinct voices</text>')

    # figure: four identical units, top right, at the 1.0 end of the scale
    cw = 44 if mobile else 54
    ch = cw * 657 / 520
    gapc = 2 if mobile else 6
    group_w = 4 * cw + 3 * gapc
    cx = x1 - group_w
    cy = Y(1) - ch + (12 if mobile else 16)
    out.append('<g class="fig fig-units">')
    for k in range(4):
        out.append(f'<image href="assets/clone-unit.webp" x="{cx + k * (cw + gapc):.1f}" y="{cy:.1f}" width="{cw}" height="{ch:.1f}"/>')
    out.append('</g>')
    out.append(f'<text class="fig-label" x="{x1:.1f}" y="{cy - 12:.1f}" text-anchor="end">where we\'re heading</text>')

    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- page

def slots_html(distinct, cls=""):
    cells = []
    for i in range(5):
        f = max(0.0, min(1.0, distinct - i))
        cells.append(f'<span class="slot" style="--f:{f:.3f}"><img src="assets/clone-unit.webp" alt="" width="52" height="65"></span>')
    return f'<span class="slots {cls}" aria-hidden="true">{"".join(cells)}</span>'


def legion_html(cols=6, rows=3):
    cells = []
    for i in range(cols * rows):
        cells.append(f'<span class="unit"><img src="assets/clone-unit.webp" alt="" width="52" height="65" loading="lazy" decoding="async">'
                     f'<span>CU-{i + 1:04d}</span></span>')
    return "\n".join(cells)


def ranks_band(n_rows=7, accent_row=3):
    rows = []
    for i in range(n_rows):
        if i == accent_row:
            rows.append('<p class="rank rank-accent" aria-hidden="true"><span>one distinct voice</span></p>')
        else:
            words = "the same answer · " * 8
            rows.append(f'<p class="rank" aria-hidden="true" style="--dir:{1 if i % 2 else -1}"><span>{words}</span></p>')
    return "\n".join(rows)


def render(d):
    change = d["change"]
    change_txt = signed(change) if change is not None else "—"
    if change is None:
        change_note = "the first week of the record"
    elif abs(change) < 0.01:
        change_note = f"since {d_short(d['previous'])}, a small move on a 0–1 scale"
    else:
        change_note = f"since {d_short(d['previous'])}, on a 0–1 scale"

    questions_js = json.dumps([
        {"q": q["query"], "c": q["category"], "s": round(q["sim"], 3), "v": round(q["distinct"], 2)}
        for q in d["ranked"]
    ], ensure_ascii=False)

    sectors = "\n".join(
        f'<li class="sector"><span class="plate-label">{e(s["name"].capitalize())}</span>'
        f'<span class="bar" style="--v:{s["sim"]:.3f}"><span></span></span>'
        f'<span class="sector-val" data-resolve>{f2(s["sim"])}</span></li>'
        for s in d["sectors"]
    )
    record = "\n".join(
        f'<tr><th scope="row">{d_long(p["date"])}</th><td>{p["n"]}</td><td>{f3(p["sim"])}</td></tr>'
        for p in d["series"]
    )
    most, least = d["most"], d["least"]
    start_idx = len(d["ranked"]) // 2

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(TITLE)}</title>
<meta name="description" content="Every week, the same 100 everyday questions to Google. This week the top 5 answers are {f2(d['sim'])} alike on a 0–1 scale: {d['distinct']:.2f} distinct answers out of 5.">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(TITLE)}">
<meta property="og:description" content="Google's top 5 answers to 100 everyday questions are {f2(d['sim'])} alike this week: {d['distinct']:.2f} distinct answers out of 5.">
<meta property="og:image" content="{PAGE_URL}assets/share.jpg">
<meta property="og:url" content="{PAGE_URL}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b3b38">
<link rel="preload" href="fonts/anybody.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/scene.webp" as="image" media="(min-width: 761px)">
<link rel="preload" href="assets/scene-sm.webp" as="image" media="(max-width: 760px)">
<style>
@font-face {{ font-family: "Anybody"; src: url("fonts/anybody.woff2") format("woff2"); font-weight: 100 900; font-stretch: 50% 150%; font-display: swap; }}
@font-face {{ font-family: "Archivo"; src: url("fonts/archivo.woff2") format("woff2"); font-weight: 100 900; font-stretch: 62% 125%; font-display: swap; }}

:root {{
  --void: #061b1a;
  --field: #0b3b38;
  --field-2: #0f4a45;
  --verdigris: #3d8a78;
  --bone: #efe6d2;
  --bone-2: #b3dccb;
  --marigold: #f4b331;
  --marigold-deep: #c98a12;
  --display: "Anybody", "Archivo", system-ui, sans-serif;
  --body: "Archivo", system-ui, sans-serif;
  --gut: clamp(18px, 3.4vw, 56px);
  --cut: 4.5vw;
  color-scheme: dark;
}}
* {{ box-sizing: border-box; }}
html {{ background: var(--field); scrollbar-color: var(--verdigris) var(--void); }}
body {{ margin: 0; color: var(--bone); font: 400 1.0625rem/1.55 var(--body); font-stretch: 100%;
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }}
::selection {{ background: var(--marigold); color: var(--void); }}
a {{ color: inherit; text-underline-offset: .22em; text-decoration-thickness: 1px; }}
a:hover {{ color: var(--marigold); }}
:focus-visible {{ outline: 3px solid var(--marigold); outline-offset: 3px; }}
img {{ display: block; max-width: 100%; }}
.wrap {{ padding-inline: var(--gut); max-width: 1680px; margin-inline: auto; }}
.num {{ font-variant-numeric: tabular-nums lining-nums; }}
.sr {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }}

/* ---------- header strip */
.strip {{ display: flex; align-items: center; gap: 24px; padding-block: 12px; border-bottom: 1px solid rgb(239 230 210 / .16);
  font: 600 .8125rem/1 var(--display); font-stretch: 120%; letter-spacing: .08em; text-transform: uppercase; }}
.mark {{ display: flex; align-items: center; gap: 10px; text-decoration: none; }}
.mark svg {{ width: 18px; height: 22px; }}
.strip .week {{ color: var(--bone-2); font-weight: 500; }}
.strip nav {{ margin-left: auto; display: flex; align-items: center; gap: 22px; }}
.strip nav a {{ text-decoration: none; }}
.btn {{ display: inline-flex; align-items: center; gap: .6em; background: var(--marigold); color: var(--void);
  padding: .78em 1.1em .72em; text-decoration: none; font: 800 .8125rem/1 var(--display); font-stretch: 120%;
  letter-spacing: .08em; text-transform: uppercase; clip-path: polygon(0 0, 100% 0, calc(100% - 10px) 100%, 0 100%);
  transition: background-color .2s cubic-bezier(.2,.7,.2,1); }}
.btn:hover {{ background: var(--bone); color: var(--void); }}
.btn svg {{ width: 14px; height: 10px; }}

/* ---------- title */
.title {{ margin: 0; padding-top: clamp(16px, 1.8vw, 28px); white-space: nowrap; overflow: hidden; text-shadow: 0 1px 12px rgb(6 27 26 / .6);
  font: 850 3vw/1 var(--display); font-stretch: 112%; letter-spacing: -.01em; text-transform: uppercase; }}

/* ---------- scene band */
.scene {{ position: relative; z-index: 1; isolation: isolate; height: clamp(400px, 33vw, 620px); overflow: hidden;
  clip-path: polygon(0 0, 100% 0, 100% calc(100% - var(--cut)), 0 100%); margin-bottom: calc(var(--cut) * -1); }}
.scene picture {{ position: absolute; inset: 0; z-index: -1; }}
.scene img.bg {{ position: absolute; inset: -8% 0 0 0; width: 100%; height: 116%; object-fit: cover; object-position: 50% 58%; will-change: transform; }}
.scene::after {{ content: ""; position: absolute; inset: 0; z-index: -1;
  background: linear-gradient(180deg, rgb(6 27 26 / .62) 0%, rgb(6 27 26 / 0) 22%, rgb(6 27 26 / 0) 40%, rgb(6 27 26 / .74) 90%),
              linear-gradient(90deg, rgb(6 27 26 / 0) 40%, rgb(6 27 26 / .38) 100%); }}
.scene-inner {{ height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding-bottom: calc(var(--cut) + clamp(10px, 1.2vw, 22px)); }}
.verdict {{ position: relative; display: flex; align-items: flex-end; gap: clamp(18px, 2.2vw, 40px); align-self: flex-end; max-width: 60%; }}
.big {{ display: block; flex: none; margin-left: -.04em; font: 900 clamp(5rem, 10.5vw, 11.5rem)/.8 var(--display); font-stretch: 150%;
  letter-spacing: -.04em; color: var(--marigold); }}
.verdict p {{ margin: 0 0 .2em; max-width: 31ch; background: rgb(6 27 26 / .94); border: 1px solid rgb(239 230 210 / .18); padding: .8em 1em .85em; font: 600 clamp(1.05rem, 1.45vw, 1.6rem)/1.28 var(--body); font-stretch: 96%; text-wrap: balance; }}
.verdict p strong {{ color: var(--marigold); font-weight: 750; }}

/* ---------- chart panel */
.panel {{ position: relative; background: var(--void); padding-top: calc(var(--cut) * .6); }}
.chart-wrap {{ position: relative; }}
.chart {{ display: block; width: 100%; height: auto; }}
.chart-m {{ display: none; }}
.chart .grid {{ stroke: rgb(239 230 210 / .11); stroke-width: 1; }}
.chart .grid-base, .chart .axis {{ stroke: rgb(239 230 210 / .5); stroke-width: 1.5; }}
.chart .tick {{ fill: var(--bone-2); font: 500 13px var(--body); font-variant-numeric: tabular-nums; }}
.chart .hatch {{ stroke: rgb(239 230 210 / .07); stroke-width: 4; }}
.chart .gap-label {{ fill: rgb(239 230 210 / .55); font: 600 12px var(--display); font-stretch: 120%; letter-spacing: .08em; text-transform: uppercase; }}
.chart .line {{ fill: none; stroke: var(--marigold); stroke-width: 4; stroke-linejoin: round; stroke-linecap: square; }}
.chart .pt {{ fill: var(--void); stroke: var(--marigold); stroke-width: 2; }}
.chart .pt-last {{ fill: var(--marigold); }}
.chart .end-val {{ fill: var(--marigold); font: 850 26px var(--display); font-stretch: 130%; }}
.chart .end-chg {{ fill: var(--bone); font: 600 14px var(--body); }}
.chart .end-chg-n {{ fill: var(--marigold); font-weight: 800; }}
.chart .fig-label {{ fill: var(--bone); font: 700 13px var(--display); font-stretch: 125%; letter-spacing: .1em; text-transform: uppercase; }}
.readout {{ display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 10px 32px;
  padding-block: 14px 30px; border-top: 1px solid rgb(239 230 210 / .14); color: var(--bone-2); font-size: .95rem; }}
.readout .change {{ color: var(--bone); font-weight: 600; }}
.readout .change b {{ color: var(--marigold); font: 800 1.1em var(--body); font-variant-numeric: tabular-nums; }}

/* ---------- sections */
section {{ position: relative; }}
.s-pad {{ padding-block: clamp(64px, 8vw, 128px); }}
h2 {{ margin: 0 0 .5em; font: 850 clamp(2.2rem, 4.6vw, 4.6rem)/.95 var(--display); font-stretch: 140%; letter-spacing: -.02em; text-transform: uppercase; text-wrap: balance; }}
h2 em {{ font-style: normal; color: var(--marigold); }}
.lede {{ max-width: 62ch; color: var(--bone-2); font-size: 1.125rem; margin: 0 0 2.2em; }}
.lede strong {{ color: var(--bone); font-weight: 650; }}

/* how it works: five slots */
.how {{ display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr); gap: clamp(32px, 5vw, 88px); align-items: center; }}
.slots {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: clamp(6px, .8vw, 12px); }}
.slot {{ position: relative; aspect-ratio: 52 / 78; background: var(--void); overflow: hidden; border: 1px solid rgb(239 230 210 / .14); }}
.slot img {{ position: absolute; left: 50%; bottom: 6%; width: 78%; transform: translateX(-50%); height: auto; }}
.slot::before {{ content: ""; position: absolute; inset: auto 0 0 0; height: calc(var(--f) * 100%); background: var(--marigold); z-index: 1;
  transition: height .7s cubic-bezier(.16,1,.3,1); }}
.slots-caption {{ display: flex; justify-content: space-between; margin-top: 12px; color: var(--bone-2); font-size: .875rem; }}
.slots-caption b {{ color: var(--marigold); font-weight: 700; }}
.plates {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; background: rgb(239 230 210 / .16); border: 1px solid rgb(239 230 210 / .16); margin-top: 28px; }}
.plate {{ background: var(--field); padding: 16px 18px 18px; display: grid; gap: 6px; }}
.plate-label {{ font: 650 .75rem/1.2 var(--display); font-stretch: 120%; letter-spacing: .1em; text-transform: uppercase; color: var(--bone-2); }}
.plate-val {{ font: 850 clamp(2rem, 3.4vw, 3rem)/1 var(--display); font-stretch: 140%; color: var(--bone); }}
.plate p {{ margin: 0; font-size: .9375rem; color: var(--bone-2); }}

/* scan the ranks: question slider */
.scan {{ background: var(--void); }}
.scan-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr); gap: clamp(32px, 5vw, 88px); align-items: start; }}
.dossier {{ border: 1px solid rgb(239 230 210 / .18); background: var(--field); }}
.dossier-head {{ display: grid; grid-template-columns: 1fr auto; gap: 4px 20px; padding: 18px 20px; border-bottom: 1px solid rgb(239 230 210 / .14); }}
.dossier-q {{ grid-column: 1 / -1; margin: 6px 0 0; min-height: 2.5em; font: 750 clamp(1.35rem, 2.2vw, 2rem)/1.15 var(--display); font-stretch: 105%; text-wrap: balance; }}
.dossier-body {{ display: grid; grid-template-columns: auto 1fr; gap: 20px 28px; align-items: center; padding: 20px; }}
.dossier-sim {{ font: 900 clamp(3.2rem, 6vw, 5.4rem)/.85 var(--display); font-stretch: 150%; color: var(--marigold); letter-spacing: -.03em; }}
.scale {{ position: relative; height: 10px; background: rgb(239 230 210 / .12); margin-top: 6px; }}
.scale span {{ position: absolute; inset: 0 auto 0 0; width: calc(var(--v) * 100%); background: var(--marigold); transition: width .5s cubic-bezier(.16,1,.3,1); }}
.scale-ends {{ display: flex; justify-content: space-between; margin-top: 6px; font-size: .8125rem; color: var(--bone-2); }}
.dossier .slots {{ grid-column: 1 / -1; }}
.dossier .slots-caption {{ grid-column: 1 / -1; margin-top: -8px; }}
.picker {{ margin-top: 26px; }}
.picker label {{ display: block; margin-bottom: 10px; }}
.range {{ -webkit-appearance: none; appearance: none; width: 100%; height: 44px; background: transparent; cursor: pointer; }}
.range::-webkit-slider-runnable-track {{ height: 4px; background: linear-gradient(90deg, var(--bone-2), var(--marigold)); }}
.range::-moz-range-track {{ height: 4px; background: linear-gradient(90deg, var(--bone-2), var(--marigold)); }}
.range::-webkit-slider-thumb {{ -webkit-appearance: none; width: 22px; height: 30px; margin-top: -13px; background: var(--bone); border: 3px solid var(--void); clip-path: polygon(0 0, 100% 0, 100% 72%, 50% 100%, 0 72%); }}
.range::-moz-range-thumb {{ width: 22px; height: 30px; background: var(--bone); border: 0; border-radius: 0; }}
.range-ends {{ display: flex; justify-content: space-between; gap: 16px; font-size: .875rem; color: var(--bone-2); }}
.jumps {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
.jump {{ font: 650 .8125rem/1 var(--display); font-stretch: 115%; letter-spacing: .06em; text-transform: uppercase; color: var(--bone);
  background: transparent; border: 1px solid rgb(239 230 210 / .35); padding: .85em 1em; cursor: pointer; transition: border-color .2s, color .2s; }}
.jump:hover {{ border-color: var(--marigold); color: var(--marigold); }}

/* sectors */
.sectors {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }}
.sector {{ display: grid; grid-template-columns: 7.5rem 1fr 4rem; gap: 18px; align-items: center; padding: 14px 0; border-bottom: 1px solid rgb(239 230 210 / .12); }}
.sector .plate-label {{ color: var(--bone); font-size: .875rem; }}
.bar {{ position: relative; height: 22px; background: rgb(239 230 210 / .08); }}
.bar span {{ position: absolute; inset: 0 auto 0 0; width: calc(var(--v) * 100%); background: var(--bone); }}
.sector:first-child .bar span {{ background: var(--marigold); }}
.sector-val {{ text-align: right; font: 800 1.5rem/1 var(--display); font-stretch: 130%; font-variant-numeric: tabular-nums; }}
.sector-axis {{ display: grid; grid-template-columns: 7.5rem 1fr 4rem; gap: 18px; padding-top: 8px; font-size: .8125rem; color: var(--bone-2); }}
.sector-axis span:nth-child(2) {{ display: flex; justify-content: space-between; }}

/* massed ranks */
.ranks {{ overflow: hidden; padding-block: clamp(36px, 5vw, 72px); background: var(--field); border-block: 1px solid rgb(239 230 210 / .12); }}
.rank {{ margin: 0; white-space: nowrap; font: 800 clamp(1.6rem, 3.6vw, 3.4rem)/1.02 var(--display); font-stretch: 50%; letter-spacing: .01em;
  text-transform: uppercase; color: rgb(179 220 203 / .3); }}
.rank span {{ display: inline-block; }}
.rank-accent {{ color: var(--marigold); font-stretch: 150%; font-weight: 900; padding-left: var(--gut); }}
@supports (animation-timeline: view()) {{
  @media (prefers-reduced-motion: no-preference) {{
    .rank:not(.rank-accent) span {{ animation: march linear both; animation-timeline: view(); }}
    @keyframes march {{ from {{ transform: translateX(calc(var(--dir) * -4%)); }} to {{ transform: translateX(calc(var(--dir) * 4% - 8%)); }} }}
  }}
}}

/* record */
.record-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: clamp(32px, 5vw, 88px); align-items: start; }}
table {{ width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }}
caption {{ text-align: left; margin-bottom: 10px; color: var(--bone-2); font-size: .875rem; }}
th, td {{ text-align: left; padding: 10px 0; border-bottom: 1px solid rgb(239 230 210 / .12); font-weight: 400; }}
thead th {{ font: 650 .75rem/1.2 var(--display); font-stretch: 120%; letter-spacing: .1em; text-transform: uppercase; color: var(--bone-2); }}
td:last-child, th:last-child {{ text-align: right; }}
td:nth-child(2), thead th:nth-child(2) {{ text-align: right; padding-right: 8%; color: var(--bone-2); }}
tbody tr:last-child td:last-child {{ color: var(--marigold); font-weight: 700; }}

/* close */
.close {{ background: var(--void); text-align: left; overflow: hidden; }}
.close h2 {{ max-width: 16ch; }}
.close-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: clamp(32px, 5vw, 88px); align-items: center; }}
.legion {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 1px; background: rgb(239 230 210 / .1); border: 1px solid rgb(239 230 210 / .1); }}
.unit {{ background: var(--void); padding: 10px 8px 8px; display: grid; justify-items: center; gap: 6px; }}
.unit img {{ width: 72%; height: auto; }}
.unit span {{ font: 600 .625rem/1 var(--display); font-stretch: 110%; letter-spacing: .12em; color: rgb(239 230 210 / .66); font-variant-numeric: tabular-nums; }}
.actions {{ display: flex; flex-wrap: wrap; gap: 14px 28px; align-items: center; margin-top: 8px; }}
.actions .btn {{ font-size: .9375rem; padding: 1em 1.3em .95em; }}
.foot {{ display: flex; flex-wrap: wrap; gap: 8px 28px; justify-content: space-between; padding-block: 22px 28px; border-top: 1px solid rgb(239 230 210 / .12); color: var(--bone-2); font-size: .8125rem; }}

/* ---------- motion */
@media (prefers-reduced-motion: no-preference) {{
  .chart .line {{ stroke-dasharray: 1; stroke-dashoffset: 0; }}
  .js .chart .line.draw {{ animation: draw 1.6s cubic-bezier(.16,1,.3,1) .25s both; }}
  @keyframes draw {{ from {{ stroke-dashoffset: 1; }} }}
}}

/* ---------- responsive */
@media (max-width: 1100px) {{
  .how, .scan-grid, .record-grid {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 760px) {{
  :root {{ --cut: 9vw; }}
  .strip {{ gap: 12px; font-size: .6875rem; white-space: nowrap; }}
  .strip .btn {{ font-size: .6875rem; padding: .8em .95em .75em; }}
  .mark span, .strip .wk {{ display: none; }}
  .close-grid {{ grid-template-columns: 1fr; }}
  .legion {{ grid-template-columns: repeat(4, 1fr); }}
  .legion .unit:nth-child(n+13) {{ display: none; }}
  .strip nav {{ gap: 14px; }}
  .strip nav .meth {{ display: none; }}
  .title {{ font-stretch: 56%; font-size: 3.9vw; }}
  .scene {{ height: auto; display: flex; flex-direction: column; clip-path: polygon(0 0, 100% 0, 100% calc(100% - var(--cut)), 0 100%); }}
  .scene-inner {{ display: contents; }}
  .scene .title {{ order: -1; padding: 14px var(--gut) 12px; text-shadow: none; }}
  .scene .verdict {{ padding-inline: var(--gut); max-width: none; align-self: stretch; }}
  .scene picture {{ position: relative; display: block; aspect-ratio: 5 / 4; overflow: hidden; }}
  .scene img.bg {{ inset: -6% 0 0 0; height: 112%; object-position: 24% 50%; }}
  .scene {{ background: var(--field); }}
  .scene::after {{ display: none; }}
  .scene picture::after {{ content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgb(11 59 56 / 0) 52%, var(--field) 100%); }}
  .scene .verdict {{ display: block; margin-top: -16vw; padding-bottom: calc(var(--cut) + 34px); }}
  .verdict p {{ background: none; border: 0; padding: 0; }}
  .big {{ font-size: 29vw; margin-bottom: 14px; }}
  .chart-d {{ display: none; }}
  .chart-m {{ display: block; }}
  .chart .tick {{ font-size: 15px; }}
  .chart .fig-label {{ font-size: 14px; }}
  .chart .gap-label {{ font-size: 11px; letter-spacing: .03em; }}
  .chart .end-chg {{ font-size: 13px; }}
  .sector, .sector-axis {{ grid-template-columns: 5.2rem 1fr 3.4rem; gap: 12px; }}
  .plates {{ grid-template-columns: 1fr; }}
  .dossier-body {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<header class="wrap strip">
  <a class="mark" href="./" aria-label="Homogenization Tracker, home">
    <svg viewBox="0 0 18 22" aria-hidden="true"><ellipse cx="9" cy="8" rx="7" ry="8" fill="#3d8a78"/><rect x="8" y="3.5" width="2" height="8" fill="#efe6d2"/><rect x="2" y="17" width="14" height="3" fill="#3d8a78"/></svg>
    <span>Homogenization Tracker</span>
  </a>
  <span class="week num"><span class="wk">Week {d['week']} · </span>{d_long(d['latest'])}</span>
  <nav aria-label="Primary">
    <a class="meth" href="{METHODOLOGY_URL}">Methodology</a>
    <a class="btn" href="{DASHBOARD_URL}">All {d['n_queries']} questions <svg viewBox="0 0 14 10" aria-hidden="true"><path d="M0 5h12M8 1l4 4-4 4" fill="none" stroke="currentColor" stroke-width="2"/></svg></a>
  </nav>
</header>

<main>
<section class="scene" aria-labelledby="page-title">
  <picture>
    <source media="(max-width: 760px)" srcset="assets/scene-sm.webp">
    <img class="bg" src="assets/scene.webp" alt="" width="2048" height="1152" fetchpriority="high">
  </picture>
  <div class="wrap scene-inner">
    <h1 class="title" id="page-title" data-fit>{e(TITLE)}</h1>
    <div class="verdict">
      <span class="big num" data-resolve aria-hidden="true">{f2(d['sim'])}</span>
      <p id="verdict-text"><span class="sr">{f2(d['sim'])}. </span>This week Google's top 5 answers to {d['n_read']} everyday questions were <strong>{f2(d['sim'])} alike</strong>, on a scale where 1 means identical: <strong>{d['distinct']:.2f} distinct answers out of 5</strong>.</p>
    </div>
  </div>
</section>

<section class="panel" aria-label="Similarity over time">
  <div class="wrap">
    <figure class="chart-wrap" style="margin:0">
      {chart_svg(d, 1200, 380, "d")}
      {chart_svg(d, 420, 440, "m")}
    </figure>
    <div class="readout">
      <span class="change num">Weekly change <b>{change_txt}</b> {e(change_note)}</span>
      <span class="num">{d['n_read']} of {d['n_queries']} questions read on {d_long(d['latest'])} · week {d['week']} of the record · <a href="{METHODOLOGY_URL}">Methodology</a></span>
    </div>
  </div>
</section>

<section class="s-pad" aria-labelledby="how-h">
  <div class="wrap how">
    <div>
      <h2 id="how-h">Five answers. <em>{d['distinct']:.2f}</em> voices.</h2>
      <p class="lede">Every week the tracker asks Google the same <strong>{d['n_queries']} everyday questions</strong> about money, health, law, science and technology. It reads the first 5 readable pages behind each one and measures how much they say the same thing. A score of 0 would mean five different answers; 1 would mean five copies of one.</p>
      <div class="plates">
        <div class="plate"><span class="plate-label">Questions above 0.80</span><span class="plate-val num" data-resolve>{pct(d['share_high'])}</span><p>of this week's questions return answers that are mostly alike.</p></div>
        <div class="plate"><span class="plate-label">Fewer than 2 distinct pages</span><span class="plate-val num" data-resolve>{pct(d['share_few'])}</span><p>of questions get less than two distinct pages out of five.</p></div>
      </div>
    </div>
    <div>
      {slots_html(d['distinct'], 'slots-hero')}
      <p class="slots-caption num"><span>Top 5 pages this week: marigold is distinct, a helmet is a repeat</span><span><b>{d['distinct']:.2f}</b> of 5 distinct</span></p>
    </div>
  </div>
</section>

<section class="scan s-pad" aria-labelledby="scan-h">
  <div class="wrap scan-grid">
    <div>
      <h2 id="scan-h">Scan the <em>ranks</em></h2>
      <p class="lede">All {d['n_read']} questions read this week, lined up from the most varied answers to the most alike. Drag through them.</p>
      <div class="picker">
        <label for="q-range" class="plate-label">Question, least to most alike</label>
        <input id="q-range" class="range" type="range" min="0" max="{len(d['ranked']) - 1}" value="{start_idx}" step="1" aria-describedby="q-out">
        <div class="range-ends"><span>Most varied</span><span>Most alike</span></div>
        <div class="jumps">
          <button class="jump" type="button" data-jump="0">Least alike</button>
          <button class="jump" type="button" data-jump="{len(d['ranked']) - 1}">Most alike</button>
        </div>
      </div>
    </div>
    <article class="dossier" id="q-out" aria-live="polite">
      <div class="dossier-head">
        <span class="plate-label" id="q-cat">{e(d['ranked'][start_idx]['category'].capitalize())}</span>
        <span class="plate-label num" id="q-rank">{start_idx + 1} of {len(d['ranked'])}</span>
        <p class="dossier-q" id="q-text">“{e(d['ranked'][start_idx]['query'])}”</p>
      </div>
      <div class="dossier-body">
        <span class="dossier-sim num" id="q-sim">{f2(d['ranked'][start_idx]['sim'])}</span>
        <div>
          <span class="plate-label">Similarity of its top 5 pages</span>
          <div class="scale" id="q-scale" style="--v:{d['ranked'][start_idx]['sim']:.3f}"><span></span></div>
          <div class="scale-ends"><span>0 all different</span><span>1 identical</span></div>
        </div>
        {slots_html(d['ranked'][start_idx]['distinct'], 'q-slots')}
        <p class="slots-caption num"><span>Distinct pages</span><span><b id="q-distinct">{d['ranked'][start_idx]['distinct']:.2f}</b> of 5</span></p>
      </div>
    </article>
  </div>
</section>

<section class="s-pad" aria-labelledby="sec-h">
  <div class="wrap">
    <h2 id="sec-h">Five sectors, <em>all above {floor_1(d['sectors'][-1]['sim'])}</em></h2>
    <p class="lede">Average similarity by topic this week, on the full 0–1 scale. <strong>{e(d['sectors'][0]['name'].capitalize())}</strong> answers are the most alike; <strong>{e(d['sectors'][-1]['name'].capitalize())}</strong> the least.</p>
    <ul class="sectors">
{sectors}
    </ul>
    <div class="sector-axis" aria-hidden="true"><span></span><span><span>0</span><span>0.5</span><span>1</span></span><span></span></div>
  </div>
</section>

<div class="ranks" aria-hidden="true">
{ranks_band()}
</div>

<section class="s-pad" aria-labelledby="rec-h">
  <div class="wrap record-grid">
    <div>
      <h2 id="rec-h">The <em>record</em></h2>
      <p class="lede">Questions are never edited or removed. {d['original']} have been asked since {d_long(d['first'])}; {d['added']} more joined on {d_long(d['added_on']) if d['added_on'] else 'a later run'}. The Questions column counts those read in each run. Week-to-week movement is small and the series is young, so read the line as a level, not a trend.</p>
      <p class="lede">Most alike this week: <strong>“{e(most['query'])}”</strong> at {f3(most['sim'])}. Least alike: <strong>“{e(least['query'])}”</strong> at {f3(least['sim'])}.</p>
    </div>
    <table>
      <caption>Average similarity of the top 5 pages, per run</caption>
      <thead><tr><th scope="col">Run</th><th scope="col">Questions</th><th scope="col">Similarity</th></tr></thead>
      <tbody>
{record}
      </tbody>
    </table>
  </div>
</section>

<section class="close s-pad" aria-labelledby="close-h">
  <div class="wrap close-grid">
    <div>
    <h2 id="close-h">Measured live, <em>not argued</em></h2>
    <p class="lede">Real Google results, a fixed panel, a weekly run, and every number public in the repository. The full method, including how pages are chosen and compared, is one click away.</p>
    <div class="actions">
      <a class="btn" href="{DASHBOARD_URL}">All {d['n_queries']} questions <svg viewBox="0 0 14 10" aria-hidden="true"><path d="M0 5h12M8 1l4 4-4 4" fill="none" stroke="currentColor" stroke-width="2"/></svg></a>
      <a href="{METHODOLOGY_URL}">Methodology</a>
      <a href="{REPO_URL}">Code and data</a>
    </div>
    </div>
    <div class="legion" aria-hidden="true">
{legion_html()}
    </div>
  </div>
</section>
</main>

<footer class="wrap foot">
  <span class="num">Built from the run of {d_long(d['latest'])}. Updated weekly.</span>
  <span>Illustrations are generated artwork; the helmeted figure is an original design.</span>
</footer>

<script>
(() => {{
  document.documentElement.classList.add('js');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const Q = {questions_js};

  // one-line title: fit to its column
  const title = document.querySelector('[data-fit]');
  function fit() {{
    title.style.fontSize = '';
    const cs = getComputedStyle(title);
    const avail = title.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    const span = document.createElement('span');
    span.textContent = title.textContent;
    span.style.whiteSpace = 'nowrap';
    title.textContent = '';
    title.appendChild(span);
    const w = span.getBoundingClientRect().width;
    const size = parseFloat(cs.fontSize) * (avail / w) * 0.995;
    title.textContent = span.textContent;
    title.style.fontSize = size + 'px';
  }}
  document.fonts.ready.then(fit);
  addEventListener('resize', fit);

  // figures resolve character by character
  function resolve(el) {{
    const final = el.textContent;
    if (reduced) return;
    let t = 0;
    const steps = 14;
    const id = setInterval(() => {{
      t++;
      el.textContent = [...final].map((ch, i) => (/\\d/.test(ch) && t < steps - (final.length - i) * 2) ? String((Math.random() * 10) | 0) : ch).join('');
      if (t >= steps) {{ clearInterval(id); el.textContent = final; }}
    }}, 42);
  }}
  const io = new IntersectionObserver(entries => {{
    for (const en of entries) if (en.isIntersecting) {{ resolve(en.target); io.unobserve(en.target); }}
  }}, {{ threshold: .6 }});
  document.querySelectorAll('[data-resolve]').forEach(el => io.observe(el));

  // the line draws once it is on screen
  const lines = document.querySelectorAll('.chart .line');
  const lo = new IntersectionObserver(entries => {{
    for (const en of entries) if (en.isIntersecting) {{ en.target.classList.add('draw'); lo.unobserve(en.target); }}
  }}, {{ threshold: .4 }});
  lines.forEach(l => lo.observe(l));

  // scene parallax
  const bg = document.querySelector('.scene img.bg');
  if (!reduced && bg) {{
    let ticking = false;
    addEventListener('scroll', () => {{
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {{
        const y = Math.min(scrollY, innerHeight);
        bg.style.transform = `translate3d(0, ${{y * 0.18}}px, 0) scale(${{1 + y * 0.00008}})`;
        ticking = false;
      }});
    }}, {{ passive: true }});
  }}

  // question scanner
  const range = document.getElementById('q-range');
  const out = {{
    cat: document.getElementById('q-cat'), rank: document.getElementById('q-rank'), text: document.getElementById('q-text'),
    sim: document.getElementById('q-sim'), scale: document.getElementById('q-scale'), distinct: document.getElementById('q-distinct'),
    slots: document.querySelectorAll('.q-slots .slot')
  }};
  function show(i) {{
    const q = Q[i];
    out.cat.textContent = q.c.charAt(0).toUpperCase() + q.c.slice(1);
    out.rank.textContent = `${{i + 1}} of ${{Q.length}}`;
    out.text.textContent = `“${{q.q}}”`;
    out.sim.textContent = q.s.toFixed(2);
    out.scale.style.setProperty('--v', q.s);
    out.distinct.textContent = q.v.toFixed(2);
    out.slots.forEach((s, k) => s.style.setProperty('--f', Math.max(0, Math.min(1, q.v - k))));
    range.setAttribute('aria-valuetext', `${{q.q}}: similarity ${{q.s.toFixed(2)}}, ${{q.v.toFixed(2)}} of 5 distinct`);
  }}
  range.addEventListener('input', () => show(+range.value));
  document.querySelectorAll('[data-jump]').forEach(b => b.addEventListener('click', () => {{ range.value = b.dataset.jump; show(+range.value); }}));
  show(+range.value);
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(render(load()))
    print(f"wrote {OUT.relative_to(TRACKER.parent)}")
