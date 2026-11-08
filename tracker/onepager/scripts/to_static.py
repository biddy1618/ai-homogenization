# Convert .dc.html artboards into standalone HTML (no canvas runtime needed).
import re, sys, os
src_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

C_DATA = [
  ('Finance', [0.896,0.881,0.879,0.873,0.863,0.862,0.846,0.826,0.796,0.79,0.783,0.781,0.748,0.741,0.724,0.71,0.691,0.635,0.61,0.553]),
  ('Health',  [0.905,0.887,0.884,0.872,0.866,0.866,0.864,0.854,0.852,0.839,0.837,0.829,0.827,0.826,0.805,0.763,0.712,0.679,0.65,0.174]),
  ('Law',     [0.865,0.865,0.863,0.858,0.845,0.831,0.824,0.802,0.795,0.786,0.768,0.755,0.754,0.743,0.698,0.691,0.67,0.653,0.544,0.451]),
  ('Science', [0.889,0.88,0.867,0.85,0.841,0.839,0.831,0.815,0.814,0.809,0.807,0.78,0.777,0.764,0.752,0.732,0.655,0.546]),
  ('Tech',    [0.868,0.868,0.861,0.844,0.835,0.805,0.797,0.775,0.769,0.768,0.759,0.723,0.719,0.709,0.653,0.64,0.615,0.608]),
]
def shade(v):
    return '#2A3744' if v<0.60 else '#475362' if v<0.70 else '#7A7158' if v<0.78 else '#B98E48' if v<0.85 else '#E89B4C'
def render_grid(tpl_row):
    out = []
    for name, vals in C_DATA:
        cells = "".join(
            f'<div role="img" aria-label="{name} question, similarity {v:.3f}" title="{name} question, similarity {v:.3f}" '
            f'style="width: 28px; height: 28px; border-radius: 4px; background: {shade(v)}{"; box-shadow: 0 0 0 2px #F2F3F5" if v>=0.9 or v<0.2 else ""}"></div>'
            for v in vals)
        row = tpl_row
        row = re.sub(r'<sc-for list="\{\{row\.cells\}\}".*?</sc-for>', cells, row, flags=re.S)
        row = row.replace('{{row.name}}', name).replace('{{row.avg}}', f"{sum(vals)/len(vals):.2f}")
        out.append(row)
    return "".join(out)

for f in sorted(os.listdir(src_dir)):
    if not f.endswith('.dc.html'): continue
    s = open(os.path.join(src_dir, f), encoding='utf-8').read()
    title = re.search(r'<title>(.*?)</title>', s, re.S).group(1)
    helmet = re.search(r'<helmet>(.*?)</helmet>', s, re.S).group(1)
    body = re.search(r'<x-dc>(.*?)</x-dc>', s, re.S).group(1)
    body = re.sub(r'<helmet>.*?</helmet>', '', body, flags=re.S)
    m = re.search(r'<sc-for list="\{\{rows\}\}"[^>]*>(.*)</sc-for>\s*</div>', body, re.S)
    if m:
        inner = m.group(1)
        last = inner.rfind('</sc-for>')  # inner = row template incl. nested sc-for
        body = body.replace(m.group(0), render_grid(inner) + '\n    </div>', 1)
    assert '{{' not in body and '<sc-' not in body, f"unrendered template in {f}"
    print_css = '<style>@page { size: A4; margin: 0 } @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact } }</style>'
    html = f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{title}</title>\n{helmet.strip()}\n{print_css}\n</head>\n<body>\n{body.strip()}\n</body>\n</html>\n'
    out = os.path.join(out_dir, f.replace('.dc.html', '.html'))
    open(out, 'w', encoding='utf-8').write(html)
    print(out, len(html))
