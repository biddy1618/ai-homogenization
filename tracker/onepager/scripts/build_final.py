import re, sys, os, itertools
ASSETS, OUT = sys.argv[1], sys.argv[2]
_ctr = itertools.count(1)

def fig(name, px, label=None):
    s = open(os.path.join(ASSETS, name + ".svg")).read()
    s = re.sub(r'<\?xml[^>]*\?>', '', s).strip()
    n = next(_ctr)
    s = s.replace(f'c_{name}"', f'c_{name}_{n}"').replace(f'url(#c_{name})', f'url(#c_{name}_{n})')
    s = s.replace('width="200" height="200"', f'width="{px}" height="{px}"', 1)
    a11y = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    s = s.replace('<svg ', f'<svg {a11y} style="display: block; flex-shrink: 0" ', 1)
    return s

def qr(px):
    s = open(os.path.join(ASSETS, "qr-dashboard.svg")).read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    d = re.search(r' d="([^"]+)"', s).group(1)
    return (f'<svg viewBox="{vb}" width="{px}" height="{px}" role="img" aria-label="QR code linking to the live dashboard" style="display: block">'
            f'<path d="{d}" fill="#0D0E12"/></svg>')

# ---------- real data (runs_top5.csv, core-45 series; latest run all questions) ----------
SERIES = [(0,'4 Oct',0.7017),(1,'5 Oct',0.7316),(8,'12 Oct',0.7433),(15,'19 Oct',0.7879),(22,'26 Oct',0.7863),(29,'2 Nov',0.7836)]
PROVIDER_DAY = 11.5   # between 12 Oct (SerpAPI) and 19 Oct (Serper.dev)

def sparkline(w, h, label, mark='search provider changed', left=False):
    lo, hi = 0.69, 0.80
    X = lambda d: 10 + d/29*(w-20)
    Y = lambda v: (h-8) - (v-lo)/(hi-lo)*(h-22)
    pts = " L".join(f"{X(d):.1f} {Y(v):.1f}" for d,_,v in SERIES)
    px = X(PROVIDER_DAY)
    dots = "".join(f'<circle cx="{X(d):.1f}" cy="{Y(v):.1f}" r="4" fill="#FFFFFF"/>' for d,_,v in SERIES[:-1])
    d,_,v = SERIES[-1]
    marktxt = (f'<text x="{px-8:.1f}" y="16" text-anchor="end" font-family="Inter" font-size="12" fill="#8E96A3">{mark}</text>' if left
               else f'<text x="{px+8:.1f}" y="16" font-family="Inter" font-size="12" fill="#8E96A3">{mark}</text>')
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{label}">'
            f'<line x1="0" y1="{h-1}" x2="{w}" y2="{h-1}" stroke="#262A33" stroke-width="1"/>'
            f'<line x1="{px:.1f}" y1="0" x2="{px:.1f}" y2="{h-1}" stroke="#4A515E" stroke-width="1" stroke-dasharray="4 4"/>'
            f'{marktxt}'
            f'<path d="M{pts}" fill="none" stroke="#FFFFFF" stroke-width="2.8" stroke-linejoin="round" stroke-linecap="round"/>'
            f'{dots}<circle cx="{X(d):.1f}" cy="{Y(v):.1f}" r="6" fill="#E8863C"/></svg>')

def main_chart():
    W, H, L, T, B = 700, 560, 56, 18, 540
    X = lambda d: L + 14 + d/29*(W - L - 54)
    Y = lambda v: T + (1-v)*(B-T)
    g = ""
    for v in (0, .25, .5, .75, 1):
        y = Y(v)
        g += f'<line x1="{L}" y1="{y:.1f}" x2="{W}" y2="{y:.1f}" stroke="{"#3A404B" if v==0 else "#22262E"}" stroke-width="{1.5 if v==0 else 1}"/>'
        g += f'<text x="{L-12}" y="{y+5:.1f}" text-anchor="end" font-family="Inter" font-size="14" fill="#8E96A3">{v:.2f}</text>'
    g += f'<line x1="{L}" y1="{T}" x2="{L}" y2="{B}" stroke="#3A404B" stroke-width="1.5"/>'
    px = X(PROVIDER_DAY)
    g += f'<line x1="{px:.1f}" y1="{Y(.95):.1f}" x2="{px:.1f}" y2="{B}" stroke="#4A515E" stroke-width="1" stroke-dasharray="4 4"/>'
    g += f'<text x="{px+8:.1f}" y="{Y(.95)+14:.1f}" font-family="Inter" font-size="13" fill="#8E96A3">search provider changed</text>'
    d_last, _, v_last = SERIES[-1]
    g += f'<line x1="{L}" y1="{Y(v_last):.1f}" x2="{X(d_last):.1f}" y2="{Y(v_last):.1f}" stroke="#E8863C" stroke-width="1" stroke-dasharray="2 5" opacity="0.7"/>'
    pts = " L".join(f"{X(d):.1f} {Y(v):.1f}" for d,_,v in SERIES)
    g += f'<path d="M{pts}" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>'
    for d,_,v in SERIES[:-1]:
        g += f'<circle cx="{X(d):.1f}" cy="{Y(v):.1f}" r="5" fill="#FFFFFF"/>'
    g += f'<circle cx="{X(d_last):.1f}" cy="{Y(v_last):.1f}" r="11" fill="#E8863C" opacity="0.25"/><circle cx="{X(d_last):.1f}" cy="{Y(v_last):.1f}" r="7" fill="#E8863C"/>'
    g += f'<text x="{X(d_last):.1f}" y="{Y(v_last)-22:.1f}" text-anchor="end" font-family="Space Grotesk" font-size="22" font-weight="700" fill="#E8863C">0.78</text>'
    d0,_,v0 = SERIES[0]
    g += f'<text x="{X(d0)+4:.1f}" y="{Y(v0)+28:.1f}" font-family="Inter" font-size="14" font-weight="600" fill="#AEB4BF">0.70</text>'
    for d,lab,_ in [SERIES[0], SERIES[2], SERIES[3], SERIES[4], SERIES[5]]:
        g += f'<text x="{X(d):.1f}" y="{B+22}" text-anchor="middle" font-family="Inter" font-size="13" fill="#8E96A3">{lab}</text>'
    return (f'<svg viewBox="0 0 {W} {H+10}" width="100%" role="img" aria-label="Line chart on a full zero-to-one scale. Average similarity of Google\'s top five pages rose from 0.70 on 4 October 2026 to 0.78 on 2 November 2026; the largest step coincides with a change of search provider.">{g}</svg>')

HEAD = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%%TITLE%%</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap">
  <style>
    body { margin: 0; font-family: Inter, system-ui, sans-serif; }
    a { color: #E8995C; } a:hover { color: #F2B37E; }
  </style>
</helmet>'''

TAIL = '''</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":%%W%%,"height":%%H%%}}'>
%%LOGIC%%
</script>
</body>
</html>
'''
EMPTY_LOGIC = '''class Component extends DCLogic {
  renderVals() {
    return {};
  }
}'''

MASTHEAD = '''<div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 22px; border-bottom: 1px solid #262A33; margin-bottom: 44px">
    <div style="display: flex; align-items: center; gap: 12px">
      <div style="display: flex; gap: 4px" aria-hidden="true">
        <div style="width: 10px; height: 10px; border-radius: 50%; background: #2A3744"></div>
        <div style="width: 10px; height: 10px; border-radius: 50%; background: #475362"></div>
        <div style="width: 10px; height: 10px; border-radius: 50%; background: #7A7158"></div>
        <div style="width: 10px; height: 10px; border-radius: 50%; background: #B98E48"></div>
        <div style="width: 10px; height: 10px; border-radius: 50%; background: #E89B4C"></div>
      </div>
      <div style="font-family: 'Space Grotesk', sans-serif; font-size: 15px; font-weight: 700; letter-spacing: 0.04em">HOMOGENIZATION TRACKER</div>
    </div>
    <div style="font-size: 13px; color: #8E96A3">Weekly &middot; Run 6 &middot; <span style="color: #F2F3F5; font-weight: 500">Updated 2 Nov 2026</span></div>
  </div>'''

FOOTER = '''<div style="border-top: 1px solid #262A33; padding-top: 22px; display: flex; align-items: center; gap: 28px">
    <div style="flex-grow: 1; font-size: 12px; line-height: 1.6; color: #8E96A3">
      Based on 100 questions in finance, health, law, science and tech; 96 returned readable results on 2 Nov 2026. The trend follows the original 45 questions so it stays comparable after the panel grew to 100 on 26 Oct. Search provider changed from SerpAPI to Serper.dev on 19 Oct.
      <div style="margin-top: 10px; font-size: 13px; display: flex; gap: 22px">
        <a href="https://biddy1618.github.io/ai-homogenization/tracker/dashboard/">Full dashboard &rarr;</a>
        <a href="https://github.com/biddy1618/ai-homogenization">Methodology and data &rarr;</a>
      </div>
    </div>
    <div style="display: flex; align-items: center; gap: 12px; flex-shrink: 0">
      <div style="font-size: 12px; color: #8E96A3; text-align: right; line-height: 1.4">Scan for the<br>live dashboard</div>
      <div style="background: #F2F3F5; border-radius: 8px; padding: 6px">%%QR%%</div>
    </div>
  </div>'''

def page(title, w, h, body, logic=EMPTY_LOGIC):
    s = HEAD.replace('%%TITLE%%', title) + '\n' + body + '\n' + TAIL.replace('%%W%%', str(w)).replace('%%H%%', str(h)).replace('%%LOGIC%%', logic)
    s = s.replace('%%MASTHEAD%%', MASTHEAD).replace('%%FOOTER%%', FOOTER).replace('%%QR%%', qr(76))
    return s

def poster(inner):
    return ('<div style="width: 1000px; height: 1414px; box-sizing: border-box; background: #0D0E12; color: #F2F3F5; padding: 48px 72px 48px; display: flex; flex-direction: column">\n  %%MASTHEAD%%\n'
            + inner + '\n  <div style="flex-grow: 1"></div>\n  %%FOOTER%%\n</div>')

EYEBROW = '<div style="font-family: \'Space Grotesk\', sans-serif; font-size: 13px; letter-spacing: 0.18em; text-transform: uppercase; color: #E8863C; font-weight: 500; margin-bottom: 16px">%s</div>'

# ======================= A =======================
names = [("aristotle","Aristotle"),("shakespeare","Shakespeare"),("davinci","Leonardo da Vinci"),("einstein","Albert Einstein"),("curie","Marie Curie")]
distinct = "".join(f'<div style="display: flex; align-items: center; gap: 10px">{fig(n,48,f"Illustration of {lab}")}<span style="font-size: 12px; color: #AEB4BF">{lab.split()[-1] if n!="davinci" else "da Vinci"}</span></div>' for n,lab in names)
clones = "".join(fig("clone",44) for _ in range(6))
A_inner = (EYEBROW % "Real Time Tracker") + '''
  <h1 style="margin: 0 0 16px; font-family: 'Space Grotesk', sans-serif; font-size: 54px; line-height: 1.02; font-weight: 700; letter-spacing: -0.025em">AI-Driven Homogenization<br>of Expression</h1>
  <p style="margin: 0 0 32px; max-width: 700px; font-size: 18px; line-height: 1.5; color: #AEB4BF">Every Monday we ask Google 100 informational questions, read the top five pages that can be read in full, and measure how alike they are. The higher the line, the closer the web gets to saying one thing.</p>

  <div style="background: #14161C; border: 1px solid #22262E; border-radius: 12px; padding: 28px 28px 20px; display: flex; gap: 22px">
    <div style="width: 150px; flex-shrink: 0; display: flex; flex-direction: column; justify-content: space-between; padding-bottom: 34px">
      <div style="display: flex; flex-direction: column; gap: 10px">
        <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; width: 144px">''' + clones + '''</div>
        <div role="img" aria-label="Six identical helmeted figures: every page says the same thing" style="font-size: 11px; line-height: 1.35; color: #E8995C; font-weight: 600; letter-spacing: 0.06em">ONE ANSWER,<br>FIVE TIMES</div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 8px">
        <div style="font-size: 11px; line-height: 1.35; color: #AEB4BF; font-weight: 600; letter-spacing: 0.06em">FIVE MINDS,<br>FIVE ANSWERS</div>
        ''' + distinct + '''
      </div>
    </div>
    <div style="flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px">
      <div style="font-family: 'Space Grotesk', sans-serif; font-size: 14px; font-weight: 500; color: #F2F3F5">Homogenization <span style="color: #8E96A3; font-family: Inter, sans-serif; font-weight: 400">(average cosine similarity of Google's top 5 pages)</span></div>
      ''' + main_chart() + '''
    </div>
  </div>

  <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 24px">
    <div style="background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 18px 20px">
      <div style="font-family: 'Space Grotesk', sans-serif; font-size: 38px; font-weight: 700; line-height: 1">1.98</div>
      <div style="font-size: 13px; color: #AEB4BF; line-height: 1.4; margin-top: 8px">genuinely different pages out of the 5 Google returns</div>
    </div>
    <div style="background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 18px 20px">
      <div style="font-family: 'Space Grotesk', sans-serif; font-size: 38px; font-weight: 700; line-height: 1">50%</div>
      <div style="font-size: 13px; color: #AEB4BF; line-height: 1.4; margin-top: 8px">of questions return a top 5 more than 80% alike</div>
    </div>
    <div style="background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 18px 20px">
      <div style="font-family: 'Space Grotesk', sans-serif; font-size: 38px; font-weight: 700; line-height: 1; color: #E8863C">0.91</div>
      <div style="font-size: 13px; color: #AEB4BF; line-height: 1.4; margin-top: 8px">most uniform: <span style="color: #F2F3F5">is intermittent fasting healthy</span></div>
    </div>
  </div>'''

# ======================= B =======================
def chrome(dim=False):
    dot = "#4A515E" if not dim else "#3A3F4A"
    return (f'<div style="display: flex; align-items: center; gap: 4px; padding: 7px 8px; border-bottom: 1px solid {"#2A2F39" if not dim else "#2A2620"}">'
            f'<div style="width: 6px; height: 6px; border-radius: 50%; background: {dot}"></div><div style="width: 6px; height: 6px; border-radius: 50%; background: {dot}"></div><div style="width: 6px; height: 6px; border-radius: 50%; background: {dot}"></div>'
            f'<div style="flex-grow: 1; height: 8px; border-radius: 4px; background: {"#262A33" if not dim else "#221F1B"}; margin-left: 6px"></div></div>')
def bar(w, c, h=5): return f'<div style="height: {h}px; width: {w}%; background: {c}; border-radius: 3px"></div>'
card1 = (f'<div style="background: #1A1D24; border: 1px solid #333945; border-radius: 8px; height: 214px; overflow: hidden">{chrome()}'
         f'<div style="padding: 12px; display: flex; flex-direction: column; gap: 8px"><div style="height: 46px; border-radius: 4px; background: #2B3947"></div>'
         + bar(78,"#F2F3F5",7) + bar(100,"#4A515E") + bar(90,"#4A515E") + bar(96,"#4A515E") + bar(58,"#4A515E") + '</div></div>')
def card2(dim=False):
    tc, lc, bc = ("#F2F3F5","#4A515E","#262A33") if not dim else ("#8E7A5F","#3A3F4A","#1E1C19")
    rows = "".join(f'<div style="display: flex; gap: 6px; align-items: center"><div style="width: 7px; height: 7px; border-radius: 50%; background: {tc}; flex-shrink: 0"></div>{bar(w,lc)}</div>' for w in (88,74,92))
    inner = (f'<div style="padding: 12px; display: flex; flex-direction: column; gap: 9px">{bar(56,tc,7)}{bar(94,lc)}{rows}'
             f'<div style="border-left: 2px solid {tc}; padding: 6px 8px; background: {bc}; display: flex; flex-direction: column; gap: 5px">{bar(90,lc,4)}{bar(64,lc,4)}</div></div>')
    if not dim:
        return f'<div style="background: #1A1D24; border: 1px solid #333945; border-radius: 8px; height: 214px; overflow: hidden">{chrome()}{inner}</div>'
    return (f'<div style="position: relative; background: #131417; border: 1px dashed #6B5235; border-radius: 8px; height: 214px; overflow: hidden">{chrome(True)}{inner}'
            f'<div style="position: absolute; top: 34px; right: 8px; background: #3A2A1E; color: #F2B37E; font-size: 10px; font-weight: 600; padding: 3px 6px; border-radius: 4px">&asymp; page 2</div></div>')
heads = (f'<div style="display: flex; justify-content: center">{fig("curie",68,"Illustration of Marie Curie: a distinct page")}</div>'
         f'<div style="display: flex; justify-content: center">{fig("einstein",68,"Illustration of Albert Einstein: a second distinct page")}</div>'
         + "".join(f'<div style="display: flex; justify-content: center">{fig("clone",68,"Identical helmeted figure: a repeated page")}</div>' for _ in range(3)))
B_inner = (EYEBROW % "Real Time Tracker &middot; AI-Driven Homogenization of Expression") + '''
  <h1 style="margin: 0 0 16px; font-family: 'Space Grotesk', sans-serif; font-size: 58px; line-height: 1.02; font-weight: 700; letter-spacing: -0.025em">Google gives you five answers.<br><span style="color: #E8863C">Two of them are actually different.</span></h1>
  <p style="margin: 0 0 36px; max-width: 680px; font-size: 18px; line-height: 1.5; color: #AEB4BF">Each week we put 100 informational questions to Google, read the top five pages that can be read in full, and count how much genuinely new material they contain.</p>

  <div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 16px; margin-bottom: 14px">''' + heads + '''</div>
  <div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 16px">''' + card1 + card2() + card2(True) + card2(True) + card2(True) + '''</div>
  <div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 16px; margin-top: 12px">
    <div style="font-size: 12px; color: #AEB4BF; text-align: center">page 1 &middot; new</div>
    <div style="font-size: 12px; color: #AEB4BF; text-align: center">page 2 &middot; new</div>
    <div style="grid-column: span 3; border-top: 1px solid #6B5235; padding-top: 8px; font-size: 12px; color: #E8995C; text-align: center">pages 3&ndash;5 repeat what you already read</div>
  </div>

  <div style="display: flex; align-items: flex-end; gap: 28px; margin-top: 44px">
    <div style="font-family: 'Space Grotesk', sans-serif; font-size: 136px; line-height: 0.8; font-weight: 700; letter-spacing: -0.045em; color: #E8863C">1.98</div>
    <div style="padding-bottom: 8px">
      <div style="font-family: 'Space Grotesk', sans-serif; font-size: 24px; font-weight: 500">distinct pages out of 5</div>
      <div style="font-size: 14px; color: #8E96A3; margin-top: 4px">Vendi score, averaged over 96 questions, 2 Nov 2026</div>
    </div>
  </div>

  <div style="display: flex; gap: 32px; align-items: stretch; margin-top: 36px">
    <div style="flex-grow: 1; min-width: 0; background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 18px 20px">
      <div style="font-size: 13px; color: #AEB4BF; margin-bottom: 8px; font-weight: 500">How alike the top five pages are, week by week</div>
      ''' + sparkline(560, 96, "Sparkline. Average similarity rose from 0.70 on 4 October 2026 to 0.78 on 2 November 2026; the largest step coincides with a change of search provider on 19 October.") + '''
      <div style="display: flex; justify-content: space-between; font-size: 12px; color: #8E96A3; margin-top: 6px"><span>0.70 &middot; 4 Oct</span><span>0.78 &middot; 2 Nov</span></div>
    </div>
    <div style="width: 230px; flex-shrink: 0; display: flex; flex-direction: column; gap: 14px">
      <div style="background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 14px 16px; flex-grow: 1">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 30px; font-weight: 700; line-height: 1">59%</div>
        <div style="font-size: 12px; color: #AEB4BF; line-height: 1.4; margin-top: 6px">of questions return fewer than 2 distinct pages</div>
      </div>
      <div style="background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 14px 16px; flex-grow: 1">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 30px; font-weight: 700; line-height: 1">Science</div>
        <div style="font-size: 12px; color: #AEB4BF; line-height: 1.4; margin-top: 6px">most uniform domain; law the least</div>
      </div>
    </div>
  </div>'''

# ======================= C =======================
C_LOGIC = '''class Component extends DCLogic {
  renderVals() {
    var data = [
      ['Finance', [0.896,0.881,0.879,0.873,0.863,0.862,0.846,0.826,0.796,0.79,0.783,0.781,0.748,0.741,0.724,0.71,0.691,0.635,0.61,0.553]],
      ['Health',  [0.905,0.887,0.884,0.872,0.866,0.866,0.864,0.854,0.852,0.839,0.837,0.829,0.827,0.826,0.805,0.763,0.712,0.679,0.65,0.174]],
      ['Law',     [0.865,0.865,0.863,0.858,0.845,0.831,0.824,0.802,0.795,0.786,0.768,0.755,0.754,0.743,0.698,0.691,0.67,0.653,0.544,0.451]],
      ['Science', [0.889,0.88,0.867,0.85,0.841,0.839,0.831,0.815,0.814,0.809,0.807,0.78,0.777,0.764,0.752,0.732,0.655,0.546]],
      ['Tech',    [0.868,0.868,0.861,0.844,0.835,0.805,0.797,0.775,0.769,0.768,0.759,0.723,0.719,0.709,0.653,0.64,0.615,0.608]]
    ];
    function shade(v) {
      if (v < 0.60) return '#2A3744';
      if (v < 0.70) return '#475362';
      if (v < 0.78) return '#7A7158';
      if (v < 0.85) return '#B98E48';
      return '#E89B4C';
    }
    var rows = data.map(function (d) {
      var sum = d[1].reduce(function (a, b) { return a + b; }, 0);
      return {
        name: d[0],
        avg: (sum / d[1].length).toFixed(2),
        cells: d[1].map(function (v) {
          return {
            style: 'width: 28px; height: 28px; border-radius: 4px; background: ' + shade(v) + (v >= 0.9 || v < 0.2 ? '; box-shadow: 0 0 0 2px #F2F3F5' : ''),
            label: d[0] + ' question, similarity ' + v.toFixed(3)
          };
        })
      };
    });
    return { rows: rows };
  }
}'''
legend_left = "".join(f'<div style="margin-left: {"0" if i==0 else "-10px"}">{fig(n,38)}</div>' for i,n in enumerate(["aristotle","davinci","curie"]))
legend_right = "".join(f'<div style="margin-left: {"0" if i==0 else "-10px"}">{fig("clone",38)}</div>' for i in range(3))
C_inner = (EYEBROW % "Real Time Tracker &middot; AI-Driven Homogenization of Expression") + '''
  <h1 style="margin: 0 0 16px; font-family: 'Space Grotesk', sans-serif; font-size: 56px; line-height: 1.02; font-weight: 700; letter-spacing: -0.025em">Ninety-six questions.<br>Half of them already<br><span style="color: #E8863C">have one answer.</span></h1>
  <p style="margin: 0 0 32px; max-width: 680px; font-size: 18px; line-height: 1.5; color: #AEB4BF">Each square is one question we put to Google on 2 November 2026. The brighter it burns, the more alike the top five results were.</p>

  <div style="background: #14161C; border: 1px solid #22262E; border-radius: 12px; padding: 24px 24px 22px">
    <div style="display: flex; flex-direction: column; gap: 12px">
      <sc-for list="{{rows}}" as="row" hint-placeholder-count="5">
        <div style="display: flex; align-items: center; gap: 14px">
          <div style="width: 70px; flex-shrink: 0; font-size: 13px; color: #F2F3F5; font-weight: 500">{{row.name}}</div>
          <div style="display: flex; gap: 5px; flex-grow: 1">
            <sc-for list="{{row.cells}}" as="cell" hint-placeholder-count="20">
              <div role="img" aria-label="{{cell.label}}" title="{{cell.label}}" style="{{cell.style}}"></div>
            </sc-for>
          </div>
          <div style="width: 40px; flex-shrink: 0; text-align: right; font-size: 13px; color: #8E96A3">{{row.avg}}</div>
        </div>
      </sc-for>
    </div>
    <div style="display: flex; align-items: center; gap: 16px; margin-top: 26px; padding-top: 20px; border-top: 1px solid #22262E">
      <div style="display: flex; align-items: center">''' + legend_left + '''</div>
      <div style="font-size: 12px; color: #AEB4BF; width: 92px; line-height: 1.3">five different answers</div>
      <div style="display: flex; gap: 3px; flex-grow: 1" aria-hidden="true">
        <div style="flex-grow: 1; height: 14px; background: #2A3744; border-radius: 3px 0 0 3px"></div>
        <div style="flex-grow: 1; height: 14px; background: #475362"></div>
        <div style="flex-grow: 1; height: 14px; background: #7A7158"></div>
        <div style="flex-grow: 1; height: 14px; background: #B98E48"></div>
        <div style="flex-grow: 1; height: 14px; background: #E89B4C; border-radius: 0 3px 3px 0"></div>
      </div>
      <div style="font-size: 12px; color: #E8995C; width: 80px; line-height: 1.3; text-align: right">one answer, five times</div>
      <div style="display: flex; align-items: center">''' + legend_right + '''</div>
    </div>
  </div>

  <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 20px">
    <div style="background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 16px 18px; display: flex; gap: 14px; align-items: center">
      <div style="width: 30px; height: 30px; border-radius: 4px; background: #E89B4C; box-shadow: 0 0 0 2px #F2F3F5; flex-shrink: 0"></div>
      <div><div style="font-size: 11px; color: #E8995C; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600">Most uniform &middot; 0.905</div>
      <div style="font-size: 18px; margin-top: 4px; font-weight: 500">is intermittent fasting healthy</div></div>
    </div>
    <div style="background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 16px 18px; display: flex; gap: 14px; align-items: center">
      <div style="width: 30px; height: 30px; border-radius: 4px; background: #2A3744; box-shadow: 0 0 0 2px #F2F3F5; flex-shrink: 0"></div>
      <div><div style="font-size: 11px; color: #AEB4BF; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600">Most varied &middot; 0.174</div>
      <div style="font-size: 18px; margin-top: 4px; font-weight: 500">what causes lower back pain</div></div>
    </div>
  </div>

  <div style="display: flex; gap: 16px; align-items: stretch; margin-top: 20px">
    <div style="flex-grow: 1; min-width: 0; background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 16px 20px">
      <div style="font-size: 13px; color: #AEB4BF; margin-bottom: 6px; font-weight: 500">Average similarity, week by week</div>
      ''' + sparkline(480, 80, mark="provider change", left=True, label="Sparkline. Average similarity rose from 0.70 on 4 October 2026 to 0.78 on 2 November 2026; the largest step coincides with a change of search provider on 19 October.") + '''
      <div style="display: flex; justify-content: space-between; font-size: 12px; color: #8E96A3; margin-top: 4px"><span>0.70 &middot; 4 Oct</span><span>0.78 &middot; 2 Nov</span></div>
    </div>
    <div style="width: 150px; flex-shrink: 0; background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 16px 18px">
      <div style="font-family: 'Space Grotesk', sans-serif; font-size: 34px; font-weight: 700; line-height: 1">1.98</div>
      <div style="font-size: 12px; color: #AEB4BF; line-height: 1.4; margin-top: 6px">distinct pages out of 5</div>
    </div>
    <div style="width: 150px; flex-shrink: 0; background: #14161C; border: 1px solid #22262E; border-radius: 10px; padding: 16px 18px">
      <div style="font-family: 'Space Grotesk', sans-serif; font-size: 34px; font-weight: 700; line-height: 1">50%</div>
      <div style="font-size: 12px; color: #AEB4BF; line-height: 1.4; margin-top: 6px">of questions above 0.80</div>
    </div>
  </div>'''

open(os.path.join(OUT, "Main.dc.html"), "w").write(page("Final A — The Axis Is the Argument", 1000, 1414, poster(A_inner)))
open(os.path.join(OUT, "B-TwoOfFive.dc.html"), "w").write(page("Final B — Two of Five", 1000, 1414, poster(B_inner)))
open(os.path.join(OUT, "C-QuestionGrid.dc.html"), "w").write(page("Final C — Ninety-Six Questions", 1000, 1414, poster(C_inner), C_LOGIC))
for f in sorted(os.listdir(OUT)): print(f, os.path.getsize(os.path.join(OUT, f)))
