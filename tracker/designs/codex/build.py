"""Build the codex one-page public summary (tracker/designs/codex/index.html) from the tracker CSVs.

    python tracker/designs/codex/build.py

Every number on the page is computed here from tracker/data/runs_top5.csv and
tracker/queries.txt; nothing is hard-coded.
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
    domains = []
    for cat in categories:
        s = summary(lambda r, c=cat: r["category"] == c)
        s["name"] = cat
        s["panel"] = sum(1 for c, _ in queries if c == cat)
        domains.append(s)

    def question(r):
        return {"query": r["query"], "category": r["category"],
                "sim": float(r["mean_pairwise_cosine"]), "distinct": float(r["vendi"])}

    ranked = sorted(by_date[latest], key=lambda r: float(r["mean_pairwise_cosine"]))
    latest_q = [question(r) for r in by_date[latest]]
    n_read = len(latest_q)

    index = []
    for cat in categories:
        items = []
        for c, q in queries:
            if c != cat:
                continue
            r = latest_rows.get(q)
            items.append({"query": q, "sim": float(r["mean_pairwise_cosine"]) if r else None,
                          "distinct": float(r["vendi"]) if r else None})
        index.append({"name": cat, "items": items})

    ser = overall["series"]
    first_n = ser[0]["n"]
    grew = next((p for p in ser if p["n"] > first_n * 1.5), None)

    panel = defaultdict(int)
    for m in csv.DictReader(open(DATA / "_runs_meta.csv")):
        panel[m["run_date"]] = max(panel[m["run_date"]], int(m["n_queries"]))
    panel_dates = sorted(panel)
    panel_first = panel[panel_dates[0]]
    panel_grew = next((d for d in panel_dates if panel[d] > panel_first), None)

    steady = None
    for i in range(len(ser) - 2):
        vals = [p["sim"] for p in ser[i:]]
        if max(vals) - min(vals) <= 0.02:
            steady = {"from": ser[i]["date"], "i": i, "spread": max(vals) - min(vals), "low": min(vals)}
            break
    return {
        "series": ser,
        "sim": overall["sim"],
        "distinct": overall["distinct"],
        "domains": domains,
        "latest": latest,
        "first": dates[0],
        "previous": ser[-2]["date"] if len(ser) > 1 else None,
        "change": ser[-1]["sim"] - ser[-2]["sim"] if len(ser) > 1 else None,
        "runs": len(dates),
        "most": question(ranked[-1]),
        "least": question(ranked[0]),
        "n_queries": len(queries),
        "n_read": n_read,
        "share_high": sum(1 for q in latest_q if q["sim"] > 0.80) / n_read,
        "share_few": sum(1 for q in latest_q if q["distinct"] < 2) / n_read,
        "latest_q": latest_q,
        "index": index,
        "grew": grew,
        "first_n": first_n,
        "panel_first": panel_first,
        "panel_grew": panel_grew,
        "steady": steady,
    }


def signed(x, places=3):
    return f"{x:+.{places}f}".replace("-", "\u2212")


def d_of(d):
    return date.fromisoformat(d)


def fmt_day(d):
    dt = d_of(d)
    return f"{dt.day} {dt.strftime('%b')}"


def fmt_long(d):
    dt = d_of(d)
    return f"{dt.day} {dt.strftime('%B')} {dt.year}"


def t_of(d, first, last):
    span = (d_of(last) - d_of(first)).days or 1
    return (d_of(d) - d_of(first)).days / span


def line_path(series, first, last, w=1000, h=1000):
    pts = [(t_of(p["date"], first, last) * w, (1 - p["sim"]) * h) for p in series]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def dodge(values, width=0.012):
    """Deterministic beeswarm lanes: close points stack above and below the rule instead of overlapping."""
    order = [0, -1, 1, -2, 2]
    placed, lanes = [], []
    for v in values:
        lane = next((l for l in order if not any(abs(v - pv) < width and pl == l for pv, pl in placed)), 0)
        placed.append((v, lane))
        lanes.append(lane)
    return lanes


CSS = r"""
@font-face { font-family: Jost; src: url(fonts/Jost.woff2) format('woff2'); font-weight: 100 900; font-style: normal; font-display: swap; }
@font-face { font-family: Jost; src: url(fonts/Jost-Italic.woff2) format('woff2'); font-weight: 100 900; font-style: italic; font-display: swap; }
:root {
  --sanguine: #7A2A1B; --sanguine-deep: #5E1F13; --ink: #1A0B07; --lead: #F7ECDF; --lead-2: #F4BFA6;
  --gall: #160E0B; --gall-2: #B9A595; --chalk: #DD6A4B;
  --rule: rgb(26 11 7 / .42); --rule-soft: rgb(26 11 7 / .22);
  --gut: clamp(16px, 2.2vw, 40px);
  --ease: cubic-bezier(.16, 1, .3, 1);
  color-scheme: dark;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { background: var(--sanguine); color: var(--lead); scrollbar-color: var(--lead-2) var(--sanguine-deep); -webkit-text-size-adjust: 100%; }
body { font-family: Jost, ui-sans-serif, system-ui, sans-serif; font-size: 17px; line-height: 1.5; font-weight: 400; font-variant-numeric: lining-nums; }
::selection { background: var(--lead); color: var(--sanguine); }
a { color: inherit; text-decoration-line: underline; text-decoration-thickness: 1px; text-underline-offset: .22em; text-decoration-color: var(--lead-2); }
a:hover { text-decoration-color: var(--lead); text-decoration-thickness: 2px; }
:focus-visible { outline: 2px solid var(--lead); outline-offset: 3px; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.num { font-variant-numeric: tabular-nums lining-nums; }

/* Prepared ground: sanguine wash with a chalk grain, never flat. */
.ground { position: relative; isolation: isolate; }
.ground::before { content: ''; position: absolute; inset: 0; z-index: -1; pointer-events: none; opacity: .5; mix-blend-mode: soft-light;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .55 0'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)'/%3E%3C/svg%3E"),
    radial-gradient(120% 90% at 30% 20%, rgb(255 210 180 / .16), transparent 60%),
    radial-gradient(90% 80% at 90% 100%, rgb(40 8 2 / .45), transparent 70%); }
.plate { background: var(--gall); color: var(--lead); }
.plate .ground::before, .plate.ground::before { mix-blend-mode: normal; opacity: .35;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .5 0 0 0 0 .3 0 0 0 0 .2 0 0 0 .18 0'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)'/%3E%3C/svg%3E"); }

/* ---------- The sheet: first viewport ---------- */
.sheet { min-height: 100svh; max-height: 1180px; height: 100svh; display: grid;
  grid-template-columns: minmax(280px, 25.5%) 1fr; grid-template-rows: auto auto minmax(0, 1fr);
  column-gap: clamp(18px, 2.4vw, 44px); padding: 0 var(--gut) clamp(10px, 1.6vh, 22px); }
.folio { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 24px; height: clamp(38px, 5.4vh, 50px);
  border-bottom: 1px solid var(--rule); font-size: 14px; letter-spacing: .14em; text-transform: uppercase; }
.folio .mark { display: flex; flex-wrap: wrap; gap: 2px 1.4em; align-items: baseline; }
.folio .mark > * { white-space: nowrap; }
.folio .mark b { font-weight: 600; letter-spacing: .16em; }
.folio .mark span { color: var(--lead-2); }
.folio nav { display: flex; gap: 2em; white-space: nowrap; }
.folio nav a { text-decoration: none; padding: .5em 0; border-bottom: 1px solid transparent; }
.folio nav a:hover { border-bottom-color: var(--lead); }
h1 { grid-column: 1 / -1; font-weight: 500; font-size: min(3.02vw, 6.2vh); line-height: 1.12; letter-spacing: -.012em; white-space: nowrap;
  padding: clamp(10px, 2vh, 22px) 0 clamp(8px, 1.6vh, 18px); }
h1 .dash { font-weight: 300; color: var(--lead-2); }

.margin { grid-row: 3; display: flex; flex-direction: column; min-height: 0; padding-top: clamp(4px, 1vh, 14px); position: relative; }
.big { position: relative; font-weight: 300; font-size: min(10.4vw, 19vh); line-height: .86; letter-spacing: -.035em; margin-left: -.04em; width: max-content; }
.big .num { position: relative; z-index: 1; }
.guide { position: absolute; left: -.5em; right: -.35em; border-top: 1px solid var(--ink); opacity: .7; transform-origin: left; }
.guide.cap { top: .095em; } .guide.base { top: .8em; }
.compass { position: absolute; left: .3em; top: .45em; width: .84em; height: .84em; margin: -.42em 0 0 -.42em; border: 1px solid var(--ink); border-radius: 50%; opacity: .6; }
.compass::before { content: ''; position: absolute; left: 50%; top: -.16em; bottom: -.16em; border-left: 1px solid var(--ink); }
.compass::after { content: ''; position: absolute; left: 50%; top: 50%; width: 1.7em; border-top: 1px solid var(--ink); transform-origin: left; rotate: -27deg; translate: -.1em .3em; }
.lede { margin-top: clamp(10px, 2.2vh, 24px); font-size: clamp(15px, min(1.28vw, 2.3vh), 19px); line-height: 1.42; max-width: 30ch; }
.ledger { margin-top: clamp(10px, 2.2vh, 26px); display: grid; gap: clamp(4px, .9vh, 10px); max-width: 32ch; }
.ledger div { display: grid; grid-template-columns: 1fr auto; align-items: baseline; gap: .6em; font-size: clamp(14px, min(1.12vw, 2vh), 17px); }
.ledger dt { color: var(--lead-2); display: flex; align-items: baseline; gap: .5em; }
.ledger dt::after { content: ''; flex: 1; border-bottom: 1px dotted var(--rule); transform: translateY(-.25em); min-width: 1em; }
.ledger dd { font-weight: 500; font-size: 1.24em; }
.actions { margin-top: auto; padding-top: clamp(10px, 2vh, 20px); display: grid; gap: clamp(6px, 1vh, 10px); }
.actions a { display: flex; justify-content: space-between; align-items: center; gap: 1em; text-decoration: none; font-weight: 500;
  font-size: clamp(15px, min(1.2vw, 2.2vh), 18px); padding: .55em 0; border-top: 1px solid var(--rule); transition: padding .4s var(--ease), color .2s; }
.actions a:last-child { border-bottom: 1px solid var(--rule); }
.actions a:hover { padding-left: .5em; }
.actions svg { width: 1.6em; height: .7em; flex: none; stroke: currentColor; fill: none; stroke-width: 1.3; }

/* The chart is the plate's drawing. Every length derives from the sheet so the gap matches the portrait. */
.chart { grid-row: 3; grid-column: 2; position: relative; min-height: 0; container-type: size; outline-offset: 6px; }
.chart-in { position: absolute; inset: 0;
  --top: 27cqh; --bot: calc(100cqh - 46px); --ph: calc(var(--bot) - var(--top));
  --left: 46px; --ew: calc(var(--ph) * .4 * .775); --x0: calc(var(--left) + var(--ew) + 1.4cqw); --x1: calc(100cqw - 2.4cqw); }
.chart-in > * { position: absolute; }
.chart-in > .contents { display: contents; }
.contents > * { position: absolute; }
.gl { left: var(--left); right: 0; height: 0; border-top: 1px solid var(--rule-soft); top: calc(var(--top) + (1 - var(--v)) * var(--ph)); transform-origin: left; }
.gl.major { border-top-color: var(--rule); }
.gl.zero { border-top: 1.5px solid var(--lead); opacity: .85; }
.gl.one { border-top: 1px solid var(--lead-2); opacity: .7; }
.yax { left: var(--left); top: calc(var(--top) - 12px); bottom: calc(100cqh - var(--bot)); border-left: 1.5px solid var(--lead); opacity: .85; }
.yl { left: 0; width: calc(var(--left) - 12px); text-align: right; font-size: 14px; line-height: 1; transform: translateY(-50%); top: calc(var(--top) + (1 - var(--v)) * var(--ph)); }
.ycap { left: calc(var(--left) + 10px); top: calc(var(--top) - 34px); font-size: 13px; letter-spacing: .12em; text-transform: uppercase; color: var(--lead-2); white-space: nowrap; }
.xt { top: calc(var(--bot) + 8px); transform: translateX(-50%); font-size: 13.5px; line-height: 1.15; text-align: center; white-space: nowrap; color: var(--lead-2);
  left: calc(var(--x0) + var(--t) * (var(--x1) - var(--x0))); }
.xt b { display: block; font-weight: 500; color: var(--lead); font-size: 14.5px; }
.xt::before { content: ''; position: absolute; left: 50%; top: -9px; height: 6px; border-left: 1px solid var(--lead); }
.xt.near { display: none; }

.einstein { left: calc(var(--left) + .4cqw); bottom: calc(100cqh - var(--bot) + 1px); height: calc(var(--ph) * .4); width: auto; }
.file { right: 0; bottom: calc(100cqh - var(--top) + 1px); height: calc(var(--top) - 6px); display: flex; align-items: flex-end; }
.file img { height: 100%; width: auto; margin-left: calc(var(--top) * -.12); }
.file img:first-child { margin-left: 0; }
.note { font-style: italic; font-weight: 400; line-height: 1.25; white-space: nowrap; font-size: 15px; }
.note-e { left: var(--left); top: calc(var(--bot) + 10px); width: calc(var(--x0) - var(--left) - 14px); text-align: center; white-space: normal; }
.note-e b, .note-c b { display: block; font-style: normal; font-weight: 600; font-size: 12.5px; letter-spacing: .14em; text-transform: uppercase; }
.note-c { bottom: calc(100cqh - var(--top) + 10px); right: calc(var(--fw, 220px) + 14px); text-align: right; }
.gap { left: var(--left); width: calc(var(--x0) - var(--left)); top: calc(var(--top) + .36 * var(--ph)); height: 14px;
  border-left: 1px solid var(--ink); border-right: 1px solid var(--ink); }
.gap::before { content: ''; position: absolute; left: 0; right: 0; top: 50%; border-top: 1px solid var(--ink); }
.gap span { position: absolute; left: 50%; top: 18px; transform: translateX(-50%); font-size: 13px; font-style: italic; color: var(--lead-2); white-space: nowrap; text-align: center; line-height: 1.2; }

.span { left: calc(var(--x1) + 1.2cqw); width: 10px; margin-left: -5px; top: var(--top); height: calc((1 - var(--v)) * var(--ph) - 12px);
  border-top: 1px solid var(--ink); border-bottom: 1px solid var(--ink); transform-origin: bottom; }
.span::before { content: ''; position: absolute; left: 50%; top: 0; bottom: 0; border-left: 1px solid var(--ink); }
.span span { position: absolute; right: 16px; top: 4px; white-space: nowrap; font-style: italic; font-size: 14px; color: var(--lead-2); }
.chart.probing .steady span { opacity: 0; }
.steady span { transition: opacity .2s; }
.ht { left: var(--left); width: 7px; height: 0; border-top: 1px solid var(--lead); opacity: .55; top: calc(var(--top) + (1 - var(--v)) * var(--ph)); }
.steady { left: calc(var(--x0) + var(--t0) * (var(--x1) - var(--x0))); right: calc(100cqw - var(--x1)); top: calc(var(--top) + (1 - var(--v)) * var(--ph) + 22px); height: 12px;
  border-left: 1px solid var(--ink); border-right: 1px solid var(--ink); }
.steady::before { content: ''; position: absolute; left: 0; right: 0; top: 50%; border-top: 1px solid var(--ink); }
.steady span { position: absolute; left: 50%; top: 16px; transform: translateX(-50%); white-space: nowrap; text-align: center; font-style: italic; font-size: 14px; line-height: 1.25; color: var(--lead-2); }

.trace { left: var(--x0); width: calc(var(--x1) - var(--x0)); top: var(--top); height: var(--ph); overflow: visible; }
.trace path { fill: none; vector-effect: non-scaling-stroke; stroke-linejoin: round; stroke-linecap: round; }
.trace .under { stroke: var(--ink); stroke-width: 7; opacity: .35; }
.trace .stroke { stroke: var(--lead); stroke-width: 3.2; }
.pt { width: 11px; height: 11px; margin: -5.5px 0 0 -5.5px; border-radius: 50%; background: var(--sanguine); border: 2px solid var(--lead);
  left: calc(var(--x0) + var(--t) * (var(--x1) - var(--x0))); top: calc(var(--top) + (1 - var(--v)) * var(--ph)); }
.pt.last { width: 15px; height: 15px; margin: -7.5px 0 0 -7.5px; background: var(--lead); }
.pt.last::after { content: ''; position: absolute; inset: -9px; border-radius: 50%; border: 1px solid var(--lead); opacity: .7; }
.val { transform: translate(-50%, -100%); margin-top: -14px; font-size: 15px; font-weight: 500; white-space: nowrap;
  left: calc(var(--x0) + var(--t) * (var(--x1) - var(--x0))); top: calc(var(--top) + (1 - var(--v)) * var(--ph)); }
.val.first { transform: translate(calc(-100% - 12px), -50%); margin-top: 0; }
.val.last { font-size: 22px; transform: translate(-60%, -100%); margin-top: -16px; }
.plumb { top: calc(var(--top) - 8px); bottom: calc(100cqh - var(--bot)); border-left: 1px dashed var(--lead); opacity: 0; transition: opacity .2s; pointer-events: none; }
.readout { min-width: 13em; padding: .55em .8em; background: var(--sanguine-deep); border: 1px solid var(--lead-2); font-size: 14px; line-height: 1.35; opacity: 0;
  transition: opacity .2s; pointer-events: none; box-shadow: 0 10px 30px -10px rgb(20 4 0 / .6); }
.readout b { font-size: 20px; font-weight: 500; }
.chart.probing .plumb, .chart.probing .readout { opacity: 1; }

/* The sheet draws itself: construction first, then the line in white lead, then the notes turn readable. */
@media (prefers-reduced-motion: no-preference) {
  .js .gl { animation: rule 900ms var(--ease) both; animation-delay: calc(var(--v) * 260ms); }
  .js .yax { animation: fade 600ms ease-out both; }
  .js .guide { animation: rule 1100ms var(--ease) both; } .js .guide.base { animation-delay: 120ms; }
  .js .compass { animation: compass 1300ms var(--ease) 300ms both; }
  @keyframes compass { from { opacity: 0; scale: .3; rotate: -90deg; } }
  .js .einstein, .js .file img { animation: bleed 1100ms var(--ease) both; animation-delay: 350ms; }
  .js .file img:nth-child(2) { animation-delay: 470ms; } .js .file img:nth-child(3) { animation-delay: 590ms; } .js .file img:nth-child(4) { animation-delay: 710ms; }
  .js .trace { animation: wipe 1700ms cubic-bezier(.5, 0, .2, 1) 700ms both; }
  .js .pt, .js .val { animation: prick 500ms var(--ease) both; animation-delay: calc(800ms + var(--t) * 1500ms); }
  .js .span { animation: rise 900ms var(--ease) 2500ms both; }
  @keyframes rise { from { transform: scaleY(0); } }
  .js .steady { animation: rule 900ms var(--ease) 2300ms both; transform-origin: left; }
  .js .note, .js .steady span, .js .span span, .js .gap span { animation: mirror 900ms var(--ease) both; animation-delay: 1500ms; }
  .js .note-c { animation-delay: 2200ms; }
  @keyframes rule { from { transform: scaleX(0); } }
  @keyframes fade { from { opacity: 0; } }
  @keyframes bleed { from { opacity: 0; filter: blur(6px); } }
  @keyframes wipe { from { clip-path: inset(-20% 100% -20% -2%); } to { clip-path: inset(-20% -2% -20% -2%); } }
  @keyframes prick { from { opacity: 0; scale: .2; } }
  @keyframes mirror { 0% { transform: scaleX(-1); opacity: .2; } 55% { transform: scaleX(-1); opacity: .8; } 100% { transform: none; } }
}

/* ---------- Below the sheet ---------- */
.band { padding: clamp(64px, 10vw, 150px) var(--gut); position: relative; overflow-x: clip; }
.sheet { overflow-x: clip; }
.band::after { content: ''; position: absolute; left: var(--gut); right: var(--gut); top: clamp(24px, 3.4vw, 52px); height: 9px; pointer-events: none;
  border-left: 1px solid currentColor; border-right: 1px solid currentColor; opacity: .32;
  background: linear-gradient(currentColor, currentColor) 0 50% / 100% 1px no-repeat, linear-gradient(currentColor, currentColor) 50% 0 / 1px 100% no-repeat; }
.band h2 { font-weight: 500; font-size: clamp(30px, 4.2vw, 64px); line-height: 1.02; letter-spacing: -.02em; max-width: 18ch; text-wrap: balance; }
.band .say { font-size: clamp(17px, 1.35vw, 21px); line-height: 1.5; max-width: 58ch; margin-top: 1.1em; }
.band .say + .say { margin-top: .8em; }
.plate .say { color: var(--lead); }
.plate .quiet, .plate em.q { color: var(--gall-2); }
.quiet { color: var(--lead-2); }

/* Scale anchors: two oversized studies and the measured rule between them. */
.anchors { display: grid; grid-template-columns: 1fr minmax(0, 1.1fr) 1fr; align-items: end; gap: 0 clamp(16px, 3vw, 60px); margin-top: clamp(40px, 6vw, 90px); }
.study { position: relative; }
.study img { display: block; width: 100%; height: auto; }
.study-e img { width: 118%; margin-left: -12%; }
.study-c img { width: 120%; max-width: none; margin-right: -14%; }
.study figcaption { margin-top: 10px; font-style: italic; color: var(--gall-2); font-size: 15px; }
.study figcaption b { display: block; font-style: normal; color: var(--chalk); font-weight: 600; letter-spacing: .14em; text-transform: uppercase; font-size: 13px; }
.study-c figcaption { text-align: right; }
.scale { align-self: center; padding-bottom: 8%; }
.rule { position: relative; height: 140px; margin: 0 4px; }
.rule .bar, .rule .tk, .rule .mk { translate: 0 20px; }
.rule .bar { position: absolute; left: 0; right: 0; top: 38px; border-top: 1.5px solid var(--lead); }
.rule .tk { position: absolute; top: 31px; height: 15px; border-left: 1px solid var(--gall-2); left: calc(var(--v) * 100%); }
.rule .tk.m { top: 26px; height: 25px; border-left-color: var(--lead); }
.rule .tk span { position: absolute; top: 20px; left: 0; transform: translateX(-50%); font-size: 13px; color: var(--gall-2); }
.rule .mk { position: absolute; top: 38px; left: calc(var(--v) * 100%); }
.rule .mk i { position: absolute; width: 12px; height: 12px; margin: -6px 0 0 -6px; border-radius: 50%; border: 2px solid var(--chalk); background: var(--gall); }
.rule .mk.now i { width: 18px; height: 18px; margin: -9px 0 0 -9px; background: var(--lead); border-color: var(--lead); }
.rule .mk span { position: absolute; bottom: 16px; left: 0; transform: translateX(-50%); white-space: nowrap; font-size: 14px; color: var(--chalk); text-align: center; line-height: 1.2; }
.rule .mk.now span { color: var(--lead); font-size: 20px; font-weight: 500; bottom: auto; top: 44px; }
.rule .mk.low span { transform: translateX(-80%); }
.scale p { margin-top: 34px; font-size: 16px; line-height: 1.5; color: var(--gall-2); max-width: 40ch; }

/* Every question on its rule. */
.measures { display: grid; grid-template-columns: minmax(0, 1fr) minmax(260px, 30%); gap: 32px clamp(24px, 4vw, 72px); margin-top: clamp(36px, 5vw, 70px); align-items: start; }
.rows { display: grid; gap: 6px; }
.row { display: grid; grid-template-columns: 7.5em 1fr; align-items: center; gap: 18px; }
.row h3 { font-size: 15px; font-weight: 500; letter-spacing: .12em; text-transform: uppercase; line-height: 1.2; }
.row h3 span { display: block; letter-spacing: 0; text-transform: none; font-weight: 400; color: var(--lead-2); font-size: 14px; }
.track { position: relative; height: 78px; }
.track::before { content: ''; position: absolute; left: 0; right: 0; top: 50%; border-top: 1px solid var(--rule); }
.track .tick { position: absolute; top: calc(50% - 5px); height: 10px; border-left: 1px solid var(--rule); left: calc(var(--v) * 100%); }
.track .mean { position: absolute; top: 8px; bottom: 8px; border-left: 2px solid var(--lead); left: calc(var(--v) * 100%); opacity: .9; }
.q { position: absolute; width: 22px; height: 22px; margin: -11px 0 0 -11px; border: 0; background: none; cursor: pointer; border-radius: 50%;
  left: calc(var(--v) * 100%); top: calc(50% + var(--lane) * 11px); }
.q::before { content: ''; position: absolute; inset: 6px; border-radius: 50%; background: var(--lead); opacity: .82; transition: scale .25s var(--ease), opacity .2s; }
.q:hover::before, .q[aria-pressed="true"]::before { opacity: 1; scale: 1.7; }
.q[aria-pressed="true"]::after { content: ''; position: absolute; inset: -2px; border-radius: 50%; border: 1px solid var(--lead); }
.axis-row { display: grid; grid-template-columns: 7.5em 1fr; gap: 18px; font-size: 13px; color: var(--lead-2); }
.axis-row div { position: relative; height: 22px; }
.axis-row em { font-style: normal; }
.axis-row div span { white-space: nowrap; position: absolute; transform: translateX(-50%); left: calc(var(--v) * 100%); }
.axis-row div span:first-child { transform: none; } .axis-row div span:last-child { transform: translateX(-100%); }
.pick { border-top: 1.5px solid var(--lead); padding-top: 16px; min-height: 260px; }
.pick .kind { font-style: italic; color: var(--lead-2); font-size: 15px; margin-top: 4px; }
.pick .qq { font-size: clamp(22px, 2vw, 30px); line-height: 1.2; font-weight: 500; text-wrap: balance; }
.pick .qq::before { content: '\201C'; } .pick .qq::after { content: '\201D'; }
.pick .facts { margin-top: 14px; display: grid; gap: 4px; font-size: 16px; }
.pick .facts b { font-weight: 500; font-size: 1.25em; }
.pick .hint { margin-top: 18px; font-size: 14px; font-style: italic; color: var(--lead-2); }
.share { margin-top: clamp(36px, 5vw, 64px); max-width: 40ch; font-style: italic; font-size: clamp(20px, 1.9vw, 28px); line-height: 1.4; padding-left: 22px; border-left: 1px solid var(--rule); }
.share b { font-style: normal; font-weight: 500; }
details.all { margin-top: clamp(40px, 5vw, 70px); border-top: 1px solid var(--rule); }
details.all summary { cursor: pointer; list-style: none; padding: 18px 0; font-weight: 500; font-size: 18px; display: flex; justify-content: space-between; gap: 1em; }
details.all summary::-webkit-details-marker { display: none; }
details.all summary svg { width: 18px; height: 18px; flex: none; stroke: currentColor; stroke-width: 1.3; fill: none; align-self: center; }
details.all summary svg .v { transition: scale .3s var(--ease); transform-origin: center; }
details.all[open] summary svg .v { scale: 1 0; }
.cols { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 330px), 1fr)); gap: 30px 44px; padding-bottom: 20px; }
.cols h3 { font-size: 14px; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; border-bottom: 1px solid var(--rule); padding-bottom: 6px; margin-bottom: 4px; }
.cols ol { list-style: none; }
.cols li { display: grid; grid-template-columns: 1fr auto; gap: 1em; padding: 5px 0; font-size: 15px; line-height: 1.35; border-bottom: 1px dotted var(--rule-soft); }
.cols li .v { font-weight: 500; }
.cols li .v.none { font-weight: 400; font-style: italic; color: var(--lead-2); }

/* Five domains as a sheet of small studies, all on the same full scale. */
.studies { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 34px clamp(20px, 2.4vw, 40px); margin-top: clamp(36px, 5vw, 70px); }
.mini { position: relative; padding: 12px 4px 14px; }
.mini::before { content: ''; position: absolute; left: 0; right: 0; bottom: 0; border-bottom: 1px solid rgb(185 165 149 / .45); pointer-events: none; }
.mini::after { content: ''; position: absolute; inset: -7px; pointer-events: none;
  background: linear-gradient(var(--gall-2), var(--gall-2)) 0 7px / 14px 1px no-repeat, linear-gradient(var(--gall-2), var(--gall-2)) 7px 0 / 1px 14px no-repeat,
    linear-gradient(var(--gall-2), var(--gall-2)) 100% calc(100% - 7px) / 14px 1px no-repeat, linear-gradient(var(--gall-2), var(--gall-2)) calc(100% - 7px) 100% / 1px 14px no-repeat; opacity: .7; }
.mini .note-m { font-style: italic; font-size: 14px; color: var(--gall-2); margin-top: 8px; }
.mini h3 { font-size: 14px; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; color: var(--chalk); }
.mini .now { font-weight: 300; font-size: clamp(34px, 2.8vw, 46px); line-height: 1; letter-spacing: -.03em; margin: 4px 0 2px; }
.mini .dl { font-size: 14px; color: var(--gall-2); }
.mini svg { display: block; width: 100%; height: auto; margin-top: 12px; overflow: visible; }
.mini svg .g { stroke: rgb(185 165 149 / .2); stroke-width: 1; }
.mini svg .g.ax { stroke: rgb(185 165 149 / .7); }
.mini svg .ln { fill: none; stroke: var(--chalk); stroke-width: 2.4; stroke-linejoin: round; stroke-linecap: round; }
.mini svg .end { fill: var(--lead); }
.mini svg text { fill: var(--gall-2); font-size: 12px; font-family: Jost, sans-serif; }
.foot { margin-top: 24px; font-size: 15px; color: var(--gall-2); max-width: 70ch; }

/* Method and links. */
.method { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr); gap: 40px clamp(32px, 6vw, 110px); margin-top: clamp(30px, 4vw, 56px); }
.method p { font-size: clamp(17px, 1.3vw, 20px); line-height: 1.55; max-width: 60ch; }
.method p + p { margin-top: .9em; }
.method .actions { margin-top: 0; padding-top: 0; align-content: start; }
.method .actions a { font-size: clamp(18px, 1.6vw, 24px); padding: .75em 0; }

/* Close: a file of identical automata, moving as depth planes. */
.close { overflow: hidden; padding-bottom: clamp(40px, 5vw, 70px); }
.close h2 { max-width: 16ch; }
.ranks { position: relative; height: clamp(260px, 34vw, 520px); margin: clamp(40px, 5vw, 70px) calc(var(--gut) * -1) 0; }
.ranks .r { position: absolute; left: 0; right: 0; bottom: 0; display: flex; justify-content: center; }
.ranks img { height: 100%; width: auto; display: block; }
.ranks .r1 { height: 100%; z-index: 3; gap: 1.2%; }
.ranks .r2 { height: 70%; bottom: 26%; z-index: 2; opacity: .3; filter: brightness(.55) blur(1px); gap: 3.4%; }
@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    .ranks .r2 { animation: drift2 linear both; animation-timeline: view(); }
    .ranks .r1 { animation: drift1 linear both; animation-timeline: view(); }
    @keyframes drift1 { from { translate: -4% 0; } to { translate: 4% 0; } }
    @keyframes drift2 { from { translate: 3% 0; } to { translate: -3% 0; } }
  }
}
.colophon { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px 30px; margin-top: 36px; padding-top: 18px; border-top: 1px solid rgb(185 165 149 / .3);
  font-size: 14px; color: var(--gall-2); }
.colophon a { text-decoration-color: var(--gall-2); }

/* ---------- Narrow screens ---------- */
@media (max-width: 1100px) and (min-width: 901px) {
  .studies { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 900px), (orientation: portrait) and (max-width: 1100px), (max-height: 560px) {
  body { font-size: 16px; }
  .sheet { height: auto; max-height: none; min-height: 0; grid-template-columns: 1fr; grid-template-rows: auto; padding-bottom: 28px; }
  .folio { height: auto; padding: 12px 0; font-size: 12px; flex-wrap: wrap; gap: 6px 16px; }
  .folio .mark span.wk { display: none; }
  .folio nav { gap: 1.6em; font-size: 12px; }
  .folio nav a { padding: .7em 0; }
  h1 { white-space: normal; font-size: clamp(27px, 8.2vw, 36px); line-height: 1.06; text-wrap: balance; padding: 16px 0 12px; }
  .margin { grid-row: auto; display: grid; grid-template-columns: auto 1fr; column-gap: 18px; align-items: end; padding-top: 6px; }
  .big { font-size: clamp(76px, 25vw, 104px); grid-row: 1 / 3; }
  .lede { margin-top: 0; font-size: 15px; max-width: none; grid-column: 2; grid-row: 1 / 3; align-self: center; }
  .ledger { grid-column: 1 / -1; max-width: none; margin-top: 18px; }
  .ledger div { font-size: 15px; }
  .margin > .actions { display: none; }
  .chart { grid-row: auto; grid-column: 1; height: clamp(330px, 98vw, 440px); margin: 22px -6px 0 -10px; }
  .chart-in { --top: 27cqh; --bot: calc(100cqh - 52px); --left: 30px; --x1: calc(100cqw - 5cqw); }
  .yl { font-size: 12px; width: calc(var(--left) - 7px); }
  .yl.odd { display: none; }
  .ycap { display: none; }
  .xt { font-size: 11.5px; } .xt b { font-size: 12px; }
  .xt.mid { display: none; }
  .note { font-size: 12.5px; } .note-e b, .note-c b { font-size: 10.5px; }
  .note-e { width: auto; text-align: left; white-space: nowrap; top: auto; bottom: calc(100cqh - var(--bot) + var(--ph) * .4 + 6px); left: calc(var(--left) + 4px); }
  .note-c { right: calc(var(--fw, 120px) + 6px); }
  .note-c .more { display: none; }
  .gap span { display: none; }
  .span span { display: none; }
  .steady span { left: auto; right: 0; transform: none; text-align: right; font-size: 12px; }
  .val { font-size: 13px; } .val.last { font-size: 17px; }
  .band { padding: 64px 18px; }
  .anchors { grid-template-columns: 1fr 1fr; }
  .scale { grid-column: 1 / -1; grid-row: 2; padding: 30px 0 0; }
  .study-e img { width: 112%; margin-left: -8%; }
  .study-c img { width: 112%; margin-right: -8%; }
  .measures { grid-template-columns: 1fr; }
  .pick { position: static; min-height: 0; order: -1; }
  .row, .axis-row { grid-template-columns: 1fr; gap: 0; }
  .row h3 { display: flex; justify-content: space-between; }
  .row h3 span { display: inline; }
  .axis-row > i, .axis-row em { display: none; }
  .studies { grid-template-columns: 1fr 1fr; }
  .method { grid-template-columns: 1fr; }
  .ranks { height: 64vw; }
}
@media (max-width: 380px) {
  .studies { grid-template-columns: 1fr 1fr; gap: 24px 14px; }
}
"""

JS = r"""
(() => {
  const D = __DATA__;
  const chart = document.getElementById('chart');
  const plumb = chart.querySelector('.plumb');
  const readout = chart.querySelector('.readout');
  const pts = [...chart.querySelectorAll('.pt')];
  let k = -1;
  function place(i) {
    k = i;
    const p = pts[i], r = D.runs[i];
    plumb.style.left = getComputedStyle(p).left;
    readout.innerHTML = `<b>${r.v}</b> on ${r.long}<br>${r.n} questions read`;
    const box = chart.getBoundingClientRect();
    const px = p.getBoundingClientRect();
    const x = px.left - box.left + px.width / 2, y = px.top - box.top;
    const w = readout.offsetWidth;
    readout.style.left = Math.min(Math.max(x - w / 2, 0), box.width - w) + 'px';
    readout.style.top = (y > box.height * .55 ? y - readout.offsetHeight - 22 : y + 26) + 'px';
    chart.classList.add('probing');
  }
  function nearest(clientX) {
    let best = 0, bd = Infinity;
    pts.forEach((p, i) => { const r = p.getBoundingClientRect(); const d = Math.abs(r.left + r.width / 2 - clientX); if (d < bd) { bd = d; best = i; } });
    return best;
  }
  chart.addEventListener('pointermove', ev => place(nearest(ev.clientX)));
  chart.addEventListener('pointerleave', () => { if (document.activeElement !== chart) chart.classList.remove('probing'); });
  chart.addEventListener('focus', () => place(k < 0 ? pts.length - 1 : k));
  chart.addEventListener('blur', () => chart.classList.remove('probing'));
  chart.addEventListener('keydown', ev => {
    if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') {
      ev.preventDefault();
      place(Math.min(Math.max((k < 0 ? pts.length - 1 : k) + (ev.key === 'ArrowRight' ? 1 : -1), 0), pts.length - 1));
    } else if (ev.key === 'Home' || ev.key === 'End') { ev.preventDefault(); place(ev.key === 'Home' ? 0 : pts.length - 1); }
  });
  const file = chart.querySelector('.file');
  const fit = () => chart.style.setProperty('--fw', file.offsetWidth + 'px');
  new ResizeObserver(fit).observe(file); fit();

  const pick = document.getElementById('pick');
  const qs = [...document.querySelectorAll('.q')];
  function show(btn, kind) {
    qs.forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
    const q = D.questions[btn.dataset.i];
    pick.querySelector('.kind').textContent = kind;
    pick.querySelector('.qq').textContent = q.query;
    pick.querySelector('.f-sim').textContent = q.sim;
    pick.querySelector('.f-dis').textContent = q.distinct;
  }
  qs.forEach(b => {
    b.addEventListener('click', () => show(b, D.questions[b.dataset.i].category + (b.dataset.i == D.most ? ' · the most alike question this week' : b.dataset.i == D.least ? ' · the least alike question this week' : '')));
    b.addEventListener('mouseenter', () => show(b, D.questions[b.dataset.i].category + (b.dataset.i == D.most ? ' · the most alike question this week' : b.dataset.i == D.least ? ' · the least alike question this week' : '')));
    b.addEventListener('focus', () => show(b, D.questions[b.dataset.i].category + (b.dataset.i == D.most ? ' · the most alike question this week' : b.dataset.i == D.least ? ' · the least alike question this week' : '')));
    b.addEventListener('keydown', ev => {
      const row = [...b.parentElement.querySelectorAll('.q')].sort((a, c) => a.dataset.v - c.dataset.v);
      const i = row.indexOf(b);
      let j = null;
      if (ev.key === 'ArrowRight') j = Math.min(i + 1, row.length - 1);
      if (ev.key === 'ArrowLeft') j = Math.max(i - 1, 0);
      if (j !== null) { ev.preventDefault(); b.tabIndex = -1; row[j].tabIndex = 0; row[j].focus(); }
    });
  });
})();
"""

ARROW = '<svg viewBox="0 0 40 14" aria-hidden="true"><path d="M0 7h38M31 1l7 6-7 6"/></svg>'


def render(data):
    series = data["series"]
    first, latest = data["first"], data["latest"]
    sim, change = data["sim"], data["change"]
    n_read, n_q = data["n_read"], data["n_queries"]

    # Chart pieces.
    grid = "".join(
        f'<i class="gl{" zero" if v == 0 else " one" if v == 10 else " major" if v == 5 else ""}" style="--v:{v / 10}"></i>'
        for v in range(11))
    ylabels = "".join(
        f'<span class="yl{" odd" if v in (2, 6) else ""}" style="--v:{v / 10}">{"0" if v == 0 else "1" if v == 10 else f"0.{v}"}</span>'
        for v in range(0, 11, 2))
    ticks, prev_month = [], None
    for i, p in enumerate(series):
        dt = d_of(p["date"])
        t = t_of(p["date"], first, latest)
        near = i > 0 and (dt - d_of(series[i - 1]["date"])).days < 3
        month = dt.strftime("%b")
        cls = "xt" + (" near" if near else "") + (" mid" if 0 < i < len(series) - 1 and i % 2 == 1 else "")
        month_txt = month if month != prev_month else "&nbsp;"
        prev_month = month
        ticks.append(f'<span class="{cls}" style="--t:{t:.4f}"><b>{dt.day}</b>{month_txt}</span>')
    points = "".join(
        f'<i class="pt{" last" if i == len(series) - 1 else ""}" style="--t:{t_of(p["date"], first, latest):.4f};--v:{p["sim"]:.4f}"></i>'
        for i, p in enumerate(series))
    vals = (f'<span class="val first" style="--t:0;--v:{series[0]["sim"]:.4f}">{series[0]["sim"]:.2f}</span>'
            f'<span class="val last" style="--t:1;--v:{series[-1]["sim"]:.4f}">{series[-1]["sim"]:.2f}</span>')
    path = line_path(series, first, latest)
    series_text = "; ".join(f"{fmt_day(p['date'])}: {p['sim']:.2f}" for p in series)
    chart_label = (f"Line chart on a 0 to 1 scale of how alike Google's top 5 answers are, averaged over the questions read each run, "
                   f"from {fmt_day(first)} to {fmt_day(latest)}: {series_text}. "
                   f"A portrait of Einstein marks the low end, distinct voices; a row of identical helmeted automata, one face repeated, marks the top, identical copies. "
                   f"Use the left and right arrow keys to read each run.")
    table_rows = "".join(
        f"<tr><th scope=\"row\">{fmt_long(p['date'])}</th><td>{p['sim']:.3f}</td><td>{p['n']}</td></tr>" for p in series)

    change_txt = signed(change) if change is not None else "—"
    halfticks = "".join(f'<i class="ht" style="--v:{v / 20}" aria-hidden="true"></i>' for v in range(1, 20, 2))
    st = data["steady"]
    steady_html = ""
    if st:
        t0 = t_of(st["from"], first, latest)
        steady_html = (f'<div class="steady" aria-hidden="true" style="--t0:{t0:.4f};--v:{st["low"]:.4f}">'
                       f'<span>within {st["spread"]:.3f} of each other<br>since {fmt_day(st["from"])}</span></div>')
    prev_txt = fmt_day(data["previous"]) if data["previous"] else "last run"

    # Scale anchors rule.
    most, least = data["most"], data["least"]
    rule_ticks = "".join(
        f'<i class="tk{" m" if v in (0, 5, 10) else ""}" style="--v:{v / 10}">{f"<span>{v / 10:g}</span>" if v in (0, 5, 10) else ""}</i>'
        for v in range(11))

    # Questions on their rules.
    qdata = []
    rows_html = []
    for dom in data["domains"]:
        qs = sorted([q for q in data["latest_q"] if q["category"] == dom["name"]], key=lambda q: q["sim"])
        lanes = dodge([q["sim"] for q in qs], width=0.014)
        btns = []
        for j, (q, lane) in enumerate(zip(qs, lanes)):
            idx = len(qdata)
            qdata.append({"query": q["query"], "category": q["category"].capitalize(),
                          "sim": f"{q['sim']:.2f}", "distinct": f"{q['distinct']:.2f}"})
            lane = max(-2, min(2, lane))
            btns.append(f'<button class="q" type="button" data-i="{idx}" data-v="{q["sim"]:.4f}" tabindex="{0 if j == 0 else -1}" '
                        f'aria-pressed="false" style="--v:{q["sim"]:.4f};--lane:{lane}" '
                        f'aria-label="{e(q["query"])}: {q["sim"]:.2f} alike"></button>')
        tks = "".join(f'<i class="tick" style="--v:{v / 10}"></i>' for v in range(11))
        rows_html.append(
            f'<div class="row"><h3>{e(dom["name"].capitalize())}<span>mean {dom["sim"]:.2f} · {len(qs)} read</span></h3>'
            f'<div class="track" role="group" aria-label="{e(dom["name"].capitalize())} questions, arrow keys move along the rule">{tks}'
            f'<i class="mean" style="--v:{dom["sim"]:.4f}" aria-hidden="true"></i>{"".join(btns)}</div></div>')
    most_i = next(i for i, q in enumerate(qdata) if q["query"] == most["query"])

    cols = ""
    for block in data["index"]:
        lis = ""
        for it in sorted(block["items"], key=lambda x: -(x["sim"] if x["sim"] is not None else -1)):
            v = (f'<span class="v">{it["sim"]:.2f}</span>' if it["sim"] is not None
                 else '<span class="v none">not read this week</span>')
            lis += f'<li><span>{e(it["query"])}</span>{v}</li>'
        cols += f'<section><h3>{e(block["name"].capitalize())}</h3><ol>{lis}</ol></section>'

    # Domain studies.
    minis = ""
    for dom in data["domains"]:
        s = dom["series"]
        W, H, L = 300, 190, 22
        pts = [(L + t_of(p["date"], first, latest) * (W - L - 6), 8 + (1 - p["sim"]) * (H - 16)) for p in s]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        g = "".join(f'<line class="g{" ax" if v in (0,) else ""}" x1="{L}" x2="{W}" y1="{8 + (1 - v / 10) * (H - 16):.1f}" y2="{8 + (1 - v / 10) * (H - 16):.1f}"/>'
                    for v in range(0, 11, 2))
        lab = "".join(f'<text x="{L - 6}" y="{8 + (1 - v) * (H - 16) + 4:.1f}" text-anchor="end">{v:g}</text>' for v in (0, 1))
        dch = s[-1]["sim"] - s[-2]["sim"] if len(s) > 1 else None
        stext = "; ".join(f"{fmt_day(p['date'])}: {p['sim']:.2f}" for p in s)
        minis += (f'<figure class="mini"><h3>{e(dom["name"].capitalize())}</h3><p class="now num">{dom["sim"]:.2f}</p>'
                  f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{e(dom["name"].capitalize())}, 0 to 1 scale: {stext}">{g}{lab}'
                  f'<line class="g ax" x1="{L}" x2="{L}" y1="4" y2="{H - 8}"/>'
                  f'<path class="ln" d="{d}"/><circle class="end" cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="4"/></svg>'
                  f'<p class="note-m">{f"{signed(dch)} since {prev_txt}" if dch is not None else ""}</p></figure>')
    panel_per = data["domains"][0]["panel"]
    grew = data["grew"]
    grew_note, panel_txt = "", ""
    pg = data["panel_grew"]
    if pg:
        before = [p["n"] for p in series if p["date"] < pg]
        after = [p["n"] for p in series if p["date"] >= pg]
        panel_txt = (f"The panel started with {data['panel_first']} questions on {fmt_day(first)} and grew to {n_q} on {fmt_day(pg)}, "
                     f"so earlier points average fewer questions. ")
        grew_note = (f"The panel grew from {data['panel_first']} to {n_q} questions on {fmt_day(pg)}. Before then each run read "
                     f"{min(before)}–{max(before)} of the original {data['panel_first']}; since then, {min(after)}–{max(after)} of {n_q}. "
                     f"A question counts only in weeks when five of its pages could be read.")

    js_data = {
        "runs": [{"v": f"{p['sim']:.3f}", "long": fmt_long(p["date"]), "n": p["n"]} for p in series],
        "questions": qdata,
        "most": most_i,
        "least": next(i for i, q in enumerate(qdata) if q["query"] == least["query"]),
    }

    automaton = '<img src="assets/codex-automaton-s-sm.webp" width="160" height="450" alt="">'
    ranks = lambda cls, n: f'<div class="r {cls}">' + "".join(
        '<img src="assets/codex-automaton-d.webp" width="420" height="1181" alt="" loading="lazy" decoding="async">' for _ in range(n)) + "</div>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI-driven homogenization of expression — real-time tracker</title>
<meta name="description" content="Every week the tracker asks Google a fixed panel of {n_q} everyday questions and measures how alike the top 5 answers are. This week: {sim:.2f} on a 0 to 1 scale, across the {n_read} questions it could read.">
<meta property="og:title" content="AI-driven homogenization of expression — real-time tracker">
<meta property="og:description" content="How alike are Google's top 5 answers to everyday questions? This week {sim:.2f} on a 0 to 1 scale: about {data['distinct']:.1f} distinct answers out of 5. Measured weekly.">
<meta property="og:type" content="website">
<meta name="theme-color" content="#7A2A1B">
<link rel="preload" href="fonts/Jost.woff2" as="font" type="font/woff2" crossorigin>
<style>{CSS}</style>
<script>document.documentElement.classList.add('js')</script>
</head>
<body>
<main>
<section class="sheet ground" aria-labelledby="title">
  <header class="folio">
    <p class="mark"><b>Homogenization Tracker</b><span class="wk">Run {data['runs']}</span><span>{fmt_long(latest)}</span></p>
    <nav aria-label="Details"><a href="{METHODOLOGY_URL}">Methodology and data</a><a href="{DASHBOARD_URL}">Full dashboard</a></nav>
  </header>
  <h1 id="title">AI-driven homogenization of expression <span class="dash">—</span> real-time tracker</h1>

  <div class="margin">
    <p class="big"><i class="guide cap" aria-hidden="true"></i><i class="guide base" aria-hidden="true"></i><i class="compass" aria-hidden="true"></i><span class="num">{sim:.2f}</span><span class="sr"> out of 1</span></p>
    <p class="lede">How alike Google’s top 5 answers are, averaged over the {n_read} of {n_q} everyday questions it could read this week. 0 would be five different answers; 1, the same answer five times.</p>
    <dl class="ledger">
      <div><dt>Change since {prev_txt}</dt><dd class="num">{change_txt}</dd></div>
      <div><dt>Distinct answers, of 5</dt><dd class="num">{data['distinct']:.2f}</dd></div>
      <div><dt>Questions read</dt><dd class="num">{n_read} of {n_q}</dd></div>
    </dl>
    <nav class="actions" aria-label="Go deeper"><a href="{METHODOLOGY_URL}">Methodology and data {ARROW}</a><a href="{DASHBOARD_URL}">Full dashboard {ARROW}</a></nav>
  </div>

  <figure class="chart" id="chart" tabindex="0" role="group" aria-label="{e(chart_label)}">
    <div class="chart-in">
      {grid}
      <i class="yax" aria-hidden="true"></i>
      <div class="contents" aria-hidden="true">{ylabels}</div>
      <span class="ycap" aria-hidden="true">How alike, 0 to 1</span>
      <img class="einstein" src="assets/codex-einstein-s-sm.webp" width="300" height="387" alt="Albert Einstein, drawn in ink and chalk: distinct voices">
      <p class="note note-e" aria-hidden="true"><b>Distinct voices</b></p>
      <div class="span" aria-hidden="true" style="--v:{sim:.4f}"><span>{1 - sim:.2f} below 1</span></div>
      {halfticks}
      {steady_html}
      <div class="gap" aria-hidden="true"><span>no runs<br>before {fmt_day(first)}</span></div>
      <div class="file" aria-hidden="true">{automaton * 4}</div>
      <p class="note note-c" aria-hidden="true"><b>Identical copies</b><span class="more">where we’re heading</span></p>
      <svg class="trace" viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true"><path class="under" d="{path}"/><path class="stroke" d="{path}"/></svg>
      {points}
      <div class="contents" aria-hidden="true">{vals}</div>
      <div class="contents" aria-hidden="true">{''.join(ticks)}</div>
      <i class="plumb" aria-hidden="true"></i>
      <p class="readout" aria-live="polite"></p>
    </div>
    <table class="sr"><caption>Weekly average similarity</caption><thead><tr><th>Run</th><th>Similarity, 0 to 1</th><th>Questions read</th></tr></thead><tbody>{table_rows}</tbody></table>
  </figure>
</section>

<section class="band plate ground" aria-labelledby="anchors-h">
  <h2 id="anchors-h">Two ends of one scale.</h2>
  <p class="say">The pictures are scale anchors, not data. Near 0, the five pages behind an answer each say something of their own: many distinct voices. Near 1, they say the same thing: one face, repeated.</p>
  <div class="anchors">
    <figure class="study study-e"><img src="assets/codex-einstein-d.webp" width="640" height="825" alt="Study of Albert Einstein in red chalk and white" loading="lazy" decoding="async"><figcaption><b>Low end · 0</b>Many distinct voices</figcaption></figure>
    <div class="scale">
      <div class="rule" role="img" aria-label="This week's average, {sim:.2f}, on the 0 to 1 scale, between the least alike question at {least['sim']:.2f} and the most alike at {most['sim']:.2f}">
        <i class="bar"></i>{rule_ticks}
        <span class="mk low" style="--v:{least['sim']:.4f}"><i></i><span>least alike<br>{least['sim']:.2f}</span></span>
        <span class="mk" style="--v:{most['sim']:.4f}"><i></i><span>most alike<br>{most['sim']:.2f}</span></span>
        <span class="mk now" style="--v:{sim:.4f}"><i></i><span>this week<br>{sim:.2f}</span></span>
      </div>
      <p>This week’s average sits at {sim:.2f}. Its questions range from “{e(least['query'])}” at {least['sim']:.2f} to “{e(most['query'])}” at {most['sim']:.2f}.</p>
    </div>
    <figure class="study study-c"><img src="assets/codex-automaton-head-d.webp" width="900" height="1002" alt="Study of the automaton's helmeted head, its visor one calm sculpted face, in red chalk and white" loading="lazy" decoding="async"><figcaption><b>High end · 1</b>One face, repeated</figcaption></figure>
  </div>
</section>

<section class="band ground" aria-labelledby="every-h">
  <h2 id="every-h">Every question, measured this week.</h2>
  <p class="say">Each point is one of the {n_read} questions read on {fmt_long(latest)}, placed on the same 0 to 1 rule. The taller stroke is the domain’s average.</p>
  <div class="measures">
    <div class="rows">
      <div class="axis-row" aria-hidden="true"><i></i><div><span style="--v:0">0<em> · all different</em></span><span style="--v:.5">0.5</span><span style="--v:1">1<em> · the same</em></span></div></div>
      {''.join(rows_html)}
    </div>
    <aside class="pick" id="pick" aria-live="polite">
      <p class="qq">{e(most['query'])}</p>
      <p class="facts"><span><b class="f-sim num">{most['sim']:.2f}</b> alike, 0 to 1</span><span><b class="f-dis num">{most['distinct']:.2f}</b> distinct answers of 5</span><span class="kind">{e(most['category'].capitalize())} · the most alike question this week</span></p>
      <p class="hint">Point at, tap or tab to any question to read it here.</p>
    </aside>
  </div>
  <p class="share"><b class="num">{data['share_high'] * 100:.0f}%</b> of the {n_read} questions read this week score above 0.80, and <b class="num">{data['share_few'] * 100:.0f}%</b> come to fewer than 2 distinct answers out of 5.</p>
  <details class="all"><summary>Read all {n_q} questions and this week’s scores<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M2 10h16"/><path class="v" d="M10 2v16"/></svg></summary><div class="cols">{cols}</div></details>
</section>

<section class="band plate ground" aria-labelledby="dom-h">
  <h2 id="dom-h">Five fields, one scale.</h2>
  <p class="say">The same measure for each domain, run by run, on the full 0 to 1 scale. Week-to-week movement is small; the series is young.</p>
  <div class="studies">{minis}</div>
  <p class="foot">{e(grew_note)}</p>
</section>

<section class="band ground" aria-labelledby="how-h">
  <h2 id="how-h">How it’s measured.</h2>
  <div class="method">
    <div>
      <p>Every week the tracker asks Google a fixed panel of everyday questions, now {n_q}: {panel_per} each in {", ".join(d["name"] for d in data["domains"][:-1])} and {data["domains"][-1]["name"]}. It reads the first five pages that answer each one and compares what they say, by meaning rather than exact wording.</p>
      <p>The score runs from 0, where the five pages share nothing, to 1, where they say the same thing. The line is the average over the questions that could be read that week. {panel_txt}Questions are never edited or removed, and the data and code are public.</p>
    </div>
    <nav class="actions" aria-label="Methodology and dashboard"><a href="{METHODOLOGY_URL}">Methodology and data {ARROW}</a><a href="{DASHBOARD_URL}">Full dashboard {ARROW}</a><a href="{REPO_URL}">Source code {ARROW}</a></nav>
  </div>
</section>

<section class="band close plate ground" aria-labelledby="close-h">
  <h2 id="close-h">At 1, every answer is the same answer.</h2>
  <p class="say">This week the web’s answers measure {sim:.2f}. The tracker will keep reading, every week, to see which way the line goes.</p>
  <div class="ranks" aria-hidden="true">{ranks("r2", 8)}{ranks("r1", 7)}</div>
  <footer class="colophon"><span>Updated weekly · last run {fmt_long(latest)} · {data['runs']} runs since {fmt_long(first)}</span><span>Drawings generated for this page · <a href="{REPO_URL}">ai-homogenization</a></span></footer>
</section>
</main>
<script>{JS.replace("__DATA__", json.dumps(js_data))}</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(render(load()))
    print(f"wrote {OUT.relative_to(TRACKER.parent)}")
