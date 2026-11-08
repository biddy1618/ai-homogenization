import os, sys
out = sys.argv[1]

SKIN, SHADE, LINE, FEAT = "#E6DED2", "#C7BBAA", "#2A2D33", "#8C8173"
SHOULDERS = "M14 200 C18 162 50 144 100 144 C150 144 182 162 186 200 Z"

def wrap(bg, body, cid):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
<defs><clipPath id="{cid}"><circle cx="100" cy="100" r="100"/></clipPath></defs>
<circle cx="100" cy="100" r="100" fill="{bg}"/>
<g clip-path="url(#{cid})">{body}</g>
</svg>'''

def face(skin=SKIN, shade=SHADE, ears=True, eyes=True, nose=True, mouth=True, statue=False):
    s = f'<path d="M87 112 L87 150 L113 150 L113 112 Z" fill="{shade}"/>'
    if ears:
        s += f'<ellipse cx="70" cy="92" rx="6" ry="10" fill="{shade}"/><ellipse cx="130" cy="92" rx="6" ry="10" fill="{shade}"/>'
    s += f'<ellipse cx="100" cy="88" rx="30" ry="38" fill="{skin}"/>'
    s += f'<path d="M72 98 C74 116 86 126 100 126 C114 126 126 116 128 98 C124 112 114 120 100 120 C86 120 76 112 72 98 Z" fill="{shade}" opacity="0.55"/>'
    if eyes:
        if statue:
            s += f'<path d="M83 91 Q89 87 95 91" stroke="{FEAT}" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M105 91 Q111 87 117 91" stroke="{FEAT}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
        else:
            s += f'<ellipse cx="89" cy="91" rx="3.6" ry="2.6" fill="{LINE}"/><ellipse cx="111" cy="91" rx="3.6" ry="2.6" fill="{LINE}"/>'
    if nose:
        s += f'<path d="M100 92 L95.5 106 Q100 109 104.5 106" stroke="{FEAT}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    if mouth:
        s += f'<path d="M92 115 Q100 118.5 108 115" stroke="{FEAT}" stroke-width="2" fill="none" stroke-linecap="round"/>'
    return s

def brows(color, w=2.8, y=83):
    return f'<path d="M81 {y} Q89 {y-4} 96 {y-1}" stroke="{color}" stroke-width="{w}" fill="none" stroke-linecap="round"/><path d="M104 {y-1} Q111 {y-4} 119 {y}" stroke="{color}" stroke-width="{w}" fill="none" stroke-linecap="round"/>'

# 1 Aristotle — marble bust
M, MS, MD = "#DCD7CD", "#B9B1A3", "#A39A8B"
ari = f'<path d="{SHOULDERS}" fill="{M}"/>'
ari += f'<path d="M30 200 C40 172 70 156 112 150 L150 200 Z" fill="{MS}"/>'
ari += f'<path d="M60 176 Q100 160 140 190" stroke="{MD}" stroke-width="2" fill="none"/><path d="M54 190 Q96 172 132 200" stroke="{MD}" stroke-width="2" fill="none"/>'
ari += face(M, MS, statue=True, mouth=False)
ari += brows(MD, 2.6)
ari += f'<path d="M70 94 C70 132 84 152 100 154 C116 152 130 132 130 94 C125 112 114 121 100 121 C86 121 75 112 70 94 Z" fill="#CFC9BD"/>'
for (x,y,r) in [(78,128,6),(88,140,6.5),(100,146,7),(112,140,6.5),(122,128,6),(84,118,5),(116,118,5),(100,132,6),(73,112,5),(127,112,5)]:
    ari += f'<circle cx="{x}" cy="{y}" r="{r}" fill="#C4BDB0" stroke="{MD}" stroke-width="1.2"/>'
ari += f'<path d="M86 112 Q93 107 100 110 Q107 107 114 112 Q107 116 100 113 Q93 116 86 112 Z" fill="#C4BDB0" stroke="{MD}" stroke-width="1.2"/>'
for (x,y) in [(72,66),(80,56),(90,51),(100,49),(110,51),(120,56),(128,66),(68,78),(132,78)]:
    ari += f'<circle cx="{x}" cy="{y}" r="7.5" fill="#CFC9BD" stroke="{MD}" stroke-width="1.2"/>'
ari += f'<rect x="70" y="60" width="60" height="5" rx="2.5" fill="{MD}"/>'

# 2 Shakespeare
sh = f'<path d="{SHOULDERS}" fill="#1E1D22"/>'
sh += f'<path d="M66 150 L134 150 L146 170 L100 178 L54 170 Z" fill="#F1EEE7"/><path d="M100 150 L100 178" stroke="#CFC9BD" stroke-width="1.5"/><path d="M98 170 L94 192 M102 170 L106 192" stroke="#CFC9BD" stroke-width="1.6"/>'
sh += f'<path d="M70 74 C62 92 60 116 64 136 L80 136 C74 118 72 98 74 82 Z" fill="#5A4433"/><path d="M130 74 C138 92 140 116 136 136 L120 136 C126 118 128 98 126 82 Z" fill="#5A4433"/>'
sh += face()
sh += f'<path d="M71 82 C70 60 84 50 100 50 C116 50 130 60 129 82 C124 70 114 66 100 66 C86 66 76 70 71 82 Z" fill="#E0D6C8"/>'
sh += f'<path d="M70 80 C70 72 72 66 76 62 L78 84 Z" fill="#5A4433"/><path d="M130 80 C130 72 128 66 124 62 L122 84 Z" fill="#5A4433"/>'
sh += brows("#5A4433")
sh += f'<path d="M88 110 Q94 106 100 109 Q106 106 112 110 Q106 113 100 111 Q94 113 88 110 Z" fill="#5A4433"/>'
sh += f'<path d="M95 120 Q100 132 105 120 Z" fill="#5A4433"/>'
sh += f'<circle cx="67" cy="106" r="3.2" fill="#D9A441"/>'

# 3 Da Vinci
dv = f'<path d="{SHOULDERS}" fill="#4A2E29"/>'
dv += f'<path d="M72 70 C60 100 56 150 58 200 L76 200 C74 160 76 118 82 96 Z" fill="#CFCAC0"/><path d="M128 70 C140 100 144 150 142 200 L124 200 C126 160 124 118 118 96 Z" fill="#CFCAC0"/>'
dv += face()
dv += brows("#B5AFA4", 3.4, 82)
dv += f'<path d="M72 96 C70 124 74 170 92 200 L108 200 C126 170 130 124 128 96 C124 114 114 121 100 121 C86 121 76 114 72 96 Z" fill="#DAD6CD"/>'
for x0 in [82,90,98,106,114]:
    dv += f'<path d="M{x0} 126 Q{x0-4} 152 {x0+2} 178 Q{x0+6} 190 {x0} 198" stroke="#B9B4A9" stroke-width="1.6" fill="none"/>'
dv += f'<path d="M86 110 Q93 105 100 108 Q107 105 114 110 Q107 115 100 112 Q93 115 86 110 Z" fill="#C9C4B9"/>'
dv += f'<path d="M58 66 C58 44 78 36 100 36 C122 36 142 44 142 66 C132 60 118 58 100 58 C82 58 68 60 58 66 Z" fill="#33322E"/><ellipse cx="100" cy="64" rx="44" ry="7" fill="#26251F"/>'

# 4 Einstein
ei = f'<path d="{SHOULDERS}" fill="#4B5261"/>'
ei += f'<path d="M84 146 L100 172 L116 146 Z" fill="#F1EEE7"/><path d="M96 152 L100 186 L104 152 L100 148 Z" fill="#2A2D33"/>'
ei += f'<path d="M84 146 L74 200 L58 200 L68 150 Z" fill="#3C4250"/><path d="M116 146 L126 200 L142 200 L132 150 Z" fill="#3C4250"/>'
for (x,y,r) in [(62,92,15),(58,74,14),(66,56,16),(82,44,16),(100,40,17),(118,44,16),(134,56,16),(142,74,14),(138,92,15),(70,108,10),(130,108,10)]:
    ei += f'<circle cx="{x}" cy="{y}" r="{r}" fill="#EEF0F3"/>'
for (x1,y1,x2,y2) in [(50,64,40,58),(56,46,48,36),(78,32,74,22),(100,26,100,16),(122,32,128,22),(144,46,152,36),(150,64,160,58),(46,90,36,92),(154,90,164,92)]:
    ei += f'<path d="M{x1} {y1} L{x2} {y2}" stroke="#EEF0F3" stroke-width="4" stroke-linecap="round"/>'
ei += face(ears=False)
ei += f'<path d="M72 74 C78 64 90 62 100 64 C110 62 122 64 128 74 C118 70 110 70 100 72 C90 70 82 70 72 74 Z" fill="#EEF0F3"/>'
ei += brows("#C9CDD3", 3.6, 84)
ei += f'<path d="M84 96 Q89 99 94 96" stroke="{FEAT}" stroke-width="1.4" fill="none"/><path d="M106 96 Q111 99 116 96" stroke="{FEAT}" stroke-width="1.4" fill="none"/>'
ei += f'<path d="M82 112 C86 104 96 104 100 107 C104 104 114 104 118 112 C112 116 106 114 100 112 C94 114 88 116 82 112 Z" fill="#D8DCE1"/>'

# 5 Marie Curie
mc = f'<path d="{SHOULDERS}" fill="#1D1C21"/>'
mc += f'<path d="M84 128 L84 152 L116 152 L116 128 Z" fill="#1D1C21"/><path d="M84 148 Q100 156 116 148" stroke="#E9E4DA" stroke-width="3" fill="none"/><circle cx="100" cy="164" r="4" fill="#B9A27A"/>'
mc += face()
mc += f'<circle cx="100" cy="42" r="15" fill="#4A3A30"/>'
mc += f'<path d="M64 98 C58 68 76 48 100 48 C124 48 142 68 136 98 C132 84 128 74 122 70 C114 66 106 64 100 66 C94 64 86 66 78 70 C72 74 68 84 64 98 Z" fill="#4A3A30"/>'
mc += f'<path d="M100 50 Q99 58 100 66" stroke="#2F241D" stroke-width="1.6" fill="none"/>'
mc += f'<path d="M78 70 Q88 62 100 66" stroke="#5E4B3E" stroke-width="2" fill="none"/><path d="M122 70 Q112 62 100 66" stroke="#5E4B3E" stroke-width="2" fill="none"/>'
mc += brows("#4A3A30", 2.4, 84)

# Clone — identical figure (original design)
A, AL, AD = "#E8863C", "#F3A766", "#B9662A"
cl = f'<path d="{SHOULDERS}" fill="{AD}"/>'
cl += f'<path d="M40 200 C44 172 66 158 100 158 C134 158 156 172 160 200 Z" fill="{A}"/>'
cl += f'<path d="M78 172 L122 172 L114 200 L86 200 Z" fill="{AD}" opacity="0.6"/>'
cl += f'<rect x="84" y="128" width="32" height="26" rx="4" fill="{AD}"/><path d="M84 140 L116 140" stroke="#8E4C1E" stroke-width="2"/>'
cl += f'<path d="M64 96 C64 58 80 42 100 42 C120 42 136 58 136 96 L136 116 C136 128 128 136 116 136 L84 136 C72 136 64 128 64 116 Z" fill="{A}"/>'
cl += f'<path d="M74 70 C78 56 88 50 98 49" stroke="{AL}" stroke-width="6" fill="none" stroke-linecap="round"/>'
cl += f'<rect x="68" y="84" width="64" height="15" rx="7.5" fill="#1B1410"/><rect x="76" y="88" width="16" height="3" rx="1.5" fill="#3A2A1E"/>'
cl += f'<path d="M80 118 L120 118" stroke="{AD}" stroke-width="3" stroke-linecap="round"/>'

figs = {"aristotle": ("#2C3440", ari), "shakespeare": ("#3A2E2A", sh), "davinci": ("#2E3A33", dv),
        "einstein": ("#26303D", ei), "curie": ("#3B2F3A", mc), "clone": ("#3A2A1E", cl)}
for name, (bg, body) in figs.items():
    open(os.path.join(out, f"{name}.svg"), "w").write(wrap(bg, body, f"c_{name}"))

import qrcode, qrcode.image.svg
img = qrcode.make("https://biddy1618.github.io/ai-homogenization/tracker/dashboard/", image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
img.save(os.path.join(out, "qr-dashboard.svg"))
print(sorted(os.listdir(out)))
