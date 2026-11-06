"""Original cutaway illustrations of LPG plant equipment (inline SVG, numbered parts).
Every part sits in <g class="pt" data-p="n"> so the parts list can highlight it."""
import math

DEFS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<linearGradient id="gSteel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a9b8c9"/><stop offset=".45" stop-color="#6f8096"/><stop offset="1" stop-color="#3a4757"/></linearGradient>
<linearGradient id="gSteelH" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3a4757"/><stop offset=".5" stop-color="#a9b8c9"/><stop offset="1" stop-color="#3a4757"/></linearGradient>
<linearGradient id="gBrass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffe2a0"/><stop offset=".5" stop-color="#e0a33d"/><stop offset="1" stop-color="#9a6514"/></linearGradient>
<radialGradient id="gBall" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#f4f8fc"/><stop offset=".45" stop-color="#9fb0c4"/><stop offset="1" stop-color="#46546a"/></radialGradient>
<linearGradient id="gRed" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff7a6b"/><stop offset="1" stop-color="#b8322a"/></linearGradient>
<linearGradient id="gCyl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7a1d1d"/><stop offset=".35" stop-color="#e2453c"/><stop offset=".6" stop-color="#c22f28"/><stop offset="1" stop-color="#6b1515"/></linearGradient>
<linearGradient id="gBlue" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1f4f8f"/><stop offset=".45" stop-color="#4c9bff"/><stop offset="1" stop-color="#173a6b"/></linearGradient>
<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7" fill="#56677c"/><line x1="0" y1="0" x2="0" y2="7" stroke="#2f3b4b" stroke-width="2.2"/></pattern>
<pattern id="mesh" width="5" height="5" patternUnits="userSpaceOnUse"><rect width="5" height="5" fill="none"/><path d="M0 0H5M0 0V5" stroke="#c9d4e2" stroke-width=".8"/></pattern>
<pattern id="powder" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#f3e3b3"/><circle cx="1.5" cy="1.5" r=".9" fill="#d8bf7a"/><circle cx="4.5" cy="4" r=".7" fill="#c9ad62"/></pattern>
<marker id="mA" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#2fd1ae"/></marker>
<marker id="mR" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#ff8a2a"/></marker>
<filter id="hot" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#ffc46b" flood-opacity=".95"/></filter>
</defs></svg>"""

FL = "#123447"          # LPG inside the cut (cavity)
INK = "#0b1220"

def g(n, body): return f'<g class="pt" data-p="{n}">{body}</g>'
def _st(extra): return "" if "stroke=" in extra else f'stroke="{INK}" stroke-width="1.2"'
def R(x, y, w, h, fill="url(#gSteel)", rx=0, extra=""): return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {_st(extra)} {extra}/>'
def P(d, fill="url(#hatch)", sw=1.2, extra=""): return f'<path d="{d}" fill="{fill}" {"" if "stroke=" in extra else f"stroke=\"{INK}\""} stroke-width="{sw}" {extra}/>'
def C(cx, cy, r, fill="url(#gSteel)", extra=""): return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" {_st(extra)} {extra}/>'
def L(x1, y1, x2, y2, col="#c9d4e2", w=1.5, extra=""): return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" {extra}/>'
def flow(x1, y1, x2, y2, dash=False): return f'<line class="fl" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#2fd1ae" stroke-width="2.4" marker-end="url(#mA)" {"stroke-dasharray=\"5 4\"" if dash else ""}/>'
def flowp(d, dash=False, col="#2fd1ae", mk="mA"): return f'<path class="fl" d="{d}" fill="none" stroke="{col}" stroke-width="2.4" marker-end="url(#{mk})" {"stroke-dasharray=\"5 4\"" if dash else ""}/>'
def T(x, y, s, size=11, anchor="middle", col="#93a2b8", extra=""): return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{col}" {extra}>{s}</text>'
def spring(x1, y1, x2, y2, coils=8, amp=10, col="#d7e0ea", w=2):
    """zig-zag spring between two points"""
    dx, dy = x2 - x1, y2 - y1; ln = math.hypot(dx, dy); ux, uy = dx / ln, dy / ln; px, py = -uy, ux
    pts = [(x1, y1)]
    for i in range(1, coils * 2):
        t = i / (coils * 2); s = amp if i % 2 else -amp
        pts.append((x1 + dx * t + px * s, y1 + dy * t + py * s))
    pts.append((x2, y2))
    return f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linejoin="round"/>'
def bolts_v(x, y1, y2, n=1): return "".join(R(x - 3, y1, 6, y2 - y1, "#8696a8") + R(x - 7, y1 - 6, 14, 7, "#5d6d81", 1) for _ in range(n))
def flange_v(x, cy, h=100, w=14):
    """vertical pipe flange (seen in section) with two bolt heads"""
    return (R(x, cy - h / 2, w, h, "url(#hatch)") + R(x - 4, cy - h / 2 + 8, w + 8, 9, "#7e8ea2", 1) + R(x - 4, cy + h / 2 - 17, w + 8, 9, "#7e8ea2", 1))
def pipe_h(x1, x2, cy, r=22, wall=11):
    return (R(x1, cy - r - wall, x2 - x1, wall, "url(#hatch)") + R(x1, cy + r, x2 - x1, wall, "url(#hatch)") + f'<rect x="{x1}" y="{cy - r}" width="{x2 - x1}" height="{2 * r}" fill="{FL}"/>')
def svg(body, w=480, h=300, title="", y0=0):
    return f'<svg viewBox="0 {y0} {w} {h}" role="img" aria-label="{title}"><title>{title}</title>{body}</svg>'
def callouts(items):
    """items: (n, px, py, lx, ly): leader from part point to numbered bubble"""
    out = []
    for n, px, py, lx, ly in items:
        out.append(f'<g class="co" data-p="{n}"><line x1="{px}" y1="{py}" x2="{lx}" y2="{ly}" stroke="#ffc46b" stroke-width="1" opacity=".85"/>'
                   f'<circle cx="{px}" cy="{py}" r="2.4" fill="#ffc46b"/><circle cx="{lx}" cy="{ly}" r="10" fill="#ffc46b" stroke="{INK}" stroke-width="1"/>'
                   f'<text x="{lx}" y="{ly + 4}" font-size="11.5" font-weight="700" text-anchor="middle" fill="#060a12">{n}</text></g>')
    return "".join(out)

# ------------------------------------------------------------------ 1. swing check valve (NRV)
def nrv_swing():
    cy = 180
    b = flange_v(30, cy, 112) + flange_v(436, cy, 112) + pipe_h(44, 150, cy) + pipe_h(330, 436, cy)
    body = (P("M150 146 L150 132 Q150 98 186 98 L294 98 Q330 98 330 132 L330 146 L330 214 L330 222 Q330 236 316 236 L164 236 Q150 236 150 222 Z")
            + R(188, 84, 104, 16, "url(#hatch)")
            + f'<path d="M164 112 Q164 110 180 110 L300 110 Q316 110 316 126 L316 220 Q316 222 300 222 L180 222 Q164 222 164 206 Z" fill="{FL}"/>'
            + f'<rect x="146" y="{cy - 22}" width="22" height="44" fill="{FL}"/><rect x="312" y="{cy - 22}" width="22" height="44" fill="{FL}"/>')
    cover = R(182, 66, 116, 18, "url(#gSteel)", 3)
    gasket = R(186, 82.5, 108, 3, "#ff5a5f")
    studs = R(194, 58, 6, 44, "#8696a8") + R(280, 58, 6, 44, "#8696a8") + R(190, 54, 14, 7, "#5d6d81", 1) + R(276, 54, 14, 7, "#5d6d81", 1)
    seat = P("M178 150 L188 148 L194 210 L184 212 Z", "url(#gBrass)")
    closed = f'<g opacity=".55" stroke-dasharray="4 3"><rect x="186" y="146" width="11" height="66" rx="4" fill="none" stroke="#ffc46b" stroke-width="1.4"/></g>'
    arm_disc = (f'<g transform="rotate(-62 214 122)">' + L(214, 122, 199, 179, "#c9d4e2", 5) + R(188, 145, 12, 68, "url(#gBrass)", 4) + C(205, 179, 5, "#6f8096") + '</g>')
    pin = C(214, 122, 6, "#2b3646") + C(214, 122, 2.2, "#c9d4e2")
    fl = flow(60, cy, 135, cy) + flowp("M200 205 Q250 222 300 196") + flow(345, cy, 420, cy)
    body_all = (b + g(1, body) + g(9, R(30, cy - 56, 14, 112, "url(#hatch)") + R(436, cy - 56, 14, 112, "url(#hatch)")) + g(2, cover) + g(3, gasket) + g(8, studs)
                + g(7, seat) + closed + g(6, arm_disc) + g(4, pin) + fl
                + T(390, 110, "Flow direction", 11, "middle", "#2fd1ae") + T(240, 284, "Disc opens with flow; back-pressure seats it shut (dashed = closed position)", 11))
    co = callouts([(1, 316, 228, 352, 262), (2, 240, 70, 240, 30), (3, 292, 84, 330, 48), (4, 214, 122, 150, 60), (5, 236, 136, 268, 52),
                   (6, 262, 160, 300, 140), (7, 190, 200, 120, 250), (8, 283, 60, 372, 46), (9, 37, 130, 70, 100)])
    return svg(body_all + co, title="Swing check valve cutaway")

# ------------------------------------------------------------------ 2. dual-plate wafer check valve (plan view + end view)
def nrv_dual():
    cy = 170
    b = pipe_h(20, 186, cy, 52, 12) + pipe_h(250, 330, cy, 52, 12) + flange_v(172, cy, 150) + flange_v(250, cy, 150)
    studs = L(160, cy - 86, 270, cy - 86, "#8696a8", 5) + L(160, cy + 86, 270, cy + 86, "#8696a8", 5) + R(154, cy - 92, 9, 12, "#5d6d81", 1) + R(264, cy - 92, 9, 12, "#5d6d81", 1) + R(154, cy + 80, 9, 12, "#5d6d81", 1) + R(264, cy + 80, 9, 12, "#5d6d81", 1)
    wafer = R(186, cy - 66, 64, 14, "url(#hatch)") + R(186, cy + 52, 64, 14, "url(#hatch)") + f'<rect x="186" y="{cy - 52}" width="64" height="104" fill="{FL}"/>'
    seat = R(198, cy - 54, 6, 108, "#ff5a5f", 2)
    pinx = 204
    plates_closed = f'<line x1="{pinx + 3}" y1="{cy - 50}" x2="{pinx + 3}" y2="{cy + 50}" stroke="#ffc46b" stroke-width="1.4" stroke-dasharray="4 3" opacity=".6"/>'
    ang = math.radians(28); ln = 50
    plates = (f'<line x1="{pinx}" y1="{cy - 3}" x2="{pinx + ln * math.cos(ang):.1f}" y2="{cy - 3 - ln * math.sin(ang):.1f}" stroke="url(#gBrass)" stroke-width="7" stroke-linecap="round"/>'
              f'<line x1="{pinx}" y1="{cy + 3}" x2="{pinx + ln * math.cos(ang):.1f}" y2="{cy + 3 + ln * math.sin(ang):.1f}" stroke="url(#gBrass)" stroke-width="7" stroke-linecap="round"/>')
    pin = C(pinx, cy, 6, "#2b3646") + C(pinx, cy, 2.2, "#c9d4e2")
    spr = f'<circle cx="{pinx}" cy="{cy}" r="11" fill="none" stroke="#d7e0ea" stroke-width="2" stroke-dasharray="3 2"/>'
    stop = C(262, cy, 5, "#c9d4e2")
    fl = flow(40, cy, 150, cy) + flowp(f"M215 {cy - 36} L300 {cy - 36}") + flowp(f"M215 {cy + 36} L300 {cy + 36}")
    # end view
    ex, ey = 405, 170
    end = (C(ex, ey, 62, "url(#hatch)") + C(ex, ey, 48, FL) + f'<path d="M{ex - 2} {ey - 46} A46 46 0 0 0 {ex - 2} {ey + 46} Z" fill="url(#gBrass)" stroke="{INK}"/>'
           f'<path d="M{ex + 2} {ey - 46} A46 46 0 0 1 {ex + 2} {ey + 46} Z" fill="url(#gBrass)" stroke="{INK}" opacity=".85"/>' + R(ex - 3, ey - 56, 6, 112, "#2b3646", 2)
           + T(ex, 254, "Front view (closed)", 11))
    body_all = (b + g(7, studs) + g(1, wafer) + g(6, seat) + plates_closed + g(2, plates) + g(4, spr) + g(3, pin) + g(5, stop) + fl + end
                + T(160, 278, "Top view: plates open like a book, springs shut them", 11))
    co = callouts([(1, 220, cy - 60, 220, 40), (2, 240, cy - 22, 300, 70), (3, pinx, cy, 120, 60), (4, pinx - 9, cy + 8, 120, 260), (5, 262, cy, 300, 250),
                   (6, 201, cy + 40, 160, 255), (7, 266, cy - 86, 300, 36)])
    return svg(body_all + co, title="Dual-plate check valve")

# ------------------------------------------------------------------ 3. butterfly valve (front view + side section)
def butterfly():
    cx, cy = 175, 180
    lugs = "".join(f'<rect x="{cx + 104 * math.cos(math.radians(a)) - 9:.1f}" y="{cy + 104 * math.sin(math.radians(a)) - 9:.1f}" width="18" height="18" rx="4" fill="url(#gSteel)" stroke="{INK}"/>'
                   f'<circle cx="{cx + 104 * math.cos(math.radians(a)):.1f}" cy="{cy + 104 * math.sin(math.radians(a)):.1f}" r="4" fill="#0b1220"/>' for a in (20, 70, 110, 160, 200, 340, 250, 290))
    body = lugs + C(cx, cy, 94, "url(#hatch)")
    liner = C(cx, cy, 72, "#e9e2cf") + C(cx, cy, 62, FL)
    disc = f'<ellipse cx="{cx}" cy="{cy}" rx="30" ry="61" fill="url(#gSteelH)" stroke="{INK}" stroke-width="1.2"/><ellipse cx="{cx - 4}" cy="{cy}" rx="22" ry="54" fill="none" stroke="#e6edf5" stroke-width="1" opacity=".6"/>'
    stem = R(cx - 5, 70, 10, 200, "#c9d4e2", 2) + f'<rect x="{cx - 5}" y="{cy - 61}" width="10" height="122" fill="#c9d4e2" opacity=".35"/>'
    bush = R(cx - 9, cy - 80, 18, 10, "#e0a33d", 2) + R(cx - 9, cy + 70, 18, 10, "#e0a33d", 2)
    neck = R(cx - 16, 58, 32, 32, "url(#hatch)") + R(cx - 11, 66, 22, 6, "#ff5a5f", 2)
    top = R(cx - 34, 46, 68, 12, "url(#gSteel)", 2)
    gbox = R(cx - 42, 10, 84, 36, "url(#gSteel)", 6) + f'<circle cx="{cx + 66}" cy="28" r="18" fill="none" stroke="#c9d4e2" stroke-width="4"/>' + L(cx + 42, 28, cx + 48, 28, "#c9d4e2", 4) + L(cx + 66, 10, cx + 66, 46, "#c9d4e2", 2) + L(cx + 48, 28, cx + 84, 28, "#c9d4e2", 2)
    ind = f'<path d="M{cx - 14} 6 L{cx + 14} 6 L{cx} -6 Z" fill="#ffc46b" stroke="{INK}" transform="translate(0 2)"/>'
    bottom = R(cx - 10, 270, 20, 12, "url(#gSteel)", 2)
    # side section
    sx, sy = 395, 190
    side = (pipe_h(318, 472, sy, 40, 10) + R(372, sy - 52, 46, 104, "none", 0, 'stroke="#56677c" stroke-dasharray="3 3"')
            + f'<line x1="{sx - 32 * math.cos(math.radians(55)):.1f}" y1="{sy + 32 * math.sin(math.radians(55)):.1f}" x2="{sx + 32 * math.cos(math.radians(55)):.1f}" y2="{sy - 32 * math.sin(math.radians(55)):.1f}" stroke="url(#gSteelH)" stroke-width="8" stroke-linecap="round"/>'
            + C(sx, sy, 5, "#c9d4e2") + flow(326, sy - 22, 372, sy - 22) + flow(418, sy + 22, 466, sy + 22) + flow(326, sy + 24, 372, sy + 24) + flow(418, sy - 20, 466, sy - 20)
            + T(395, 260, "Side view: disc 55° open", 11))
    body_all = (g(1, body) + g(2, liner) + g(4, stem) + g(3, disc) + g(5, bush) + g(6, neck) + g(7, top) + g(8, gbox) + g(9, ind) + bottom + side
                + T(250, 302, "Front view: disc turns on the stem; 90° = open", 11))
    co = callouts([(1, 105, 240, 60, 270), (2, 238, 150, 285, 120), (3, 160, 200, 70, 150), (4, cx - 5, 262, 100, 288), (5, cx + 9, cy - 75, 260, 92),
                   (6, cx - 16, 74, 70, 70), (7, cx + 34, 52, 250, 58), (8, cx - 42, 28, 80, 22), (9, cx + 10, 2, 120, -4)])
    return svg(body_all + co, h=322, title="Butterfly valve", y0=-16)

# ------------------------------------------------------------------ 4. ball valve (3-piece, fire-safe)
def ball():
    cy = 185
    caps = (P(f"M70 {cy - 46} L150 {cy - 46} L150 {cy + 46} L70 {cy + 46} Z") + P(f"M310 {cy - 46} L390 {cy - 46} L390 {cy + 46} L310 {cy + 46} Z")
            + f'<rect x="66" y="{cy - 22}" width="90" height="44" fill="{FL}"/><rect x="304" y="{cy - 22}" width="90" height="44" fill="{FL}"/>')
    fls = flange_v(56, cy, 120) + flange_v(390, cy, 120)
    bodyc = (P(f"M150 {cy - 74} L310 {cy - 74} L310 {cy + 74} L150 {cy + 74} Z") + f'<rect x="160" y="{cy - 64}" width="140" height="128" rx="30" fill="{FL}"/>' + R(207, 96, 46, 22, "url(#hatch)"))
    bal = C(230, cy, 56, "url(#gBall)") + f'<rect x="174" y="{cy - 21}" width="112" height="42" fill="{FL}" stroke="{INK}"/>' + R(222, cy - 60, 16, 10, "#2b3646", 1)
    seats = P(f"M164 {cy - 44} L176 {cy - 40} L176 {cy + 40} L164 {cy + 44} Z", "#efe7d2") + P(f"M296 {cy - 44} L284 {cy - 40} L284 {cy + 40} L296 {cy + 44} Z", "#efe7d2")
    graph = R(156, cy - 48, 6, 96, "#2b3646", 1) + R(298, cy - 48, 6, 96, "#2b3646", 1)
    stem = R(222, 60, 16, 70, "#c9d4e2", 2)
    gland = R(210, 98, 40, 6, "#ff5a5f", 1) + R(210, 105, 40, 6, "#ff5a5f", 1) + R(206, 88, 48, 9, "url(#gSteel)", 2) + R(214, 76, 32, 10, "#5d6d81", 2)
    lever = f'<g transform="rotate(-6 230 66)">' + R(226, 58, 150, 14, "url(#gSteel)", 4) + R(318, 56, 64, 18, "#ff8a2a", 8) + '</g>'
    relief = C(178, cy - 30, 4, "#060a12", 'stroke="#ffc46b" stroke-width="1.6"')
    anti = spring(230, 122, 230, 132, 3, 3, "#ffc46b", 1.4)
    fl = flow(80, cy, 160, cy) + flow(190, cy, 272, cy) + flow(312, cy, 380, cy)
    body_all = (fls + g(2, caps) + g(1, bodyc) + g(4, seats) + g(5, graph) + g(3, bal) + g(6, stem) + g(7, gland) + g(8, lever) + g(9, relief) + g(10, anti) + fl
                + T(230, 288, "Fully open: ball bore in line with the pipe; turn 90° to close", 11))
    co = callouts([(1, 300, 252, 340, 270), (2, 100, 232, 60, 268), (3, 252, cy + 44, 260, 268), (4, 168, cy + 36, 128, 268), (5, 159, cy - 44, 112, 108),
                   (6, 232, 120, 175, 40), (7, 250, 101, 330, 120), (8, 360, 54, 420, 90), (9, 178, cy - 30, 120, 160), (10, 236, 127, 290, 96)])
    return svg(body_all + co, title="Fire-safe ball valve")

# ------------------------------------------------------------------ 5. globe valve
def globe():
    cy = 225
    b = flange_v(24, cy, 104) + flange_v(442, cy, 104) + pipe_h(38, 160, cy) + pipe_h(300, 442, cy)
    body = (P(f"M160 {cy - 40} Q160 160 210 158 L250 158 Q300 160 300 {cy - 40} L300 {cy + 46} Q300 286 250 286 L210 286 Q160 286 160 {cy + 46} Z")
            + f'<path d="M172 {cy - 30} Q172 172 212 170 L248 170 Q288 172 288 {cy - 30} L288 {cy + 36} Q288 274 248 274 L212 274 Q172 274 172 {cy + 36} Z" fill="{FL}"/>'
            + f'<rect x="156" y="{cy - 22}" width="22" height="44" fill="{FL}"/><rect x="282" y="{cy - 22}" width="22" height="44" fill="{FL}"/>')
    part = f'<path d="M172 186 C196 186 202 200 206 214" fill="none" stroke="url(#hatch)" stroke-width="13"/><path d="M254 214 C258 238 268 262 288 264" fill="none" stroke="url(#hatch)" stroke-width="13"/>'
    seat = R(200, 210, 12, 9, "url(#gBrass)", 2) + R(248, 210, 12, 9, "url(#gBrass)", 2)
    disc = R(206, 176, 48, 16, "url(#gBrass)", 4)
    bonnet = R(198, 110, 64, 50, "url(#hatch)") + R(190, 150, 80, 10, "url(#gSteel)", 2)
    gland = R(214, 116, 32, 7, "#ff5a5f", 1) + R(214, 124, 32, 7, "#ff5a5f", 1)
    stem = R(225, 30, 10, 148, "#c9d4e2", 2) + "".join(L(225, y, 235, y + 4, "#7e8ea2", 1) for y in range(46, 104, 6))
    yoke = f'<path d="M204 110 L204 52 L256 52 L256 110" fill="none" stroke="url(#gSteel)" stroke-width="9"/>' + R(214, 44, 32, 12, "#e0a33d", 2)
    wheel = f'<ellipse cx="230" cy="26" rx="62" ry="11" fill="none" stroke="#c9d4e2" stroke-width="5"/>' + L(170, 26, 290, 26, "#c9d4e2", 2) + C(230, 26, 6, "#5d6d81")
    fl = flow(50, cy, 150, cy) + flowp(f"M180 {cy + 22} Q230 262 230 214 L230 200") + flowp("M244 182 Q280 196 290 215 L300 225") + flow(312, cy, 430, cy)
    body_all = (b + g(1, body) + g(9, part) + g(8, seat) + g(7, disc) + g(2, bonnet) + g(6, gland) + g(4, stem) + g(5, yoke) + g(3, wheel) + fl
                + T(380, 160, "S-path: in below, out above", 11, "middle", "#2fd1ae"))
    co = callouts([(1, 172, 268, 120, 282), (2, 262, 128, 320, 112), (3, 290, 26, 340, 34), (4, 235, 80, 320, 74), (5, 204, 70, 150, 64),
                   (6, 214, 120, 150, 112), (7, 254, 184, 330, 190), (8, 206, 214, 150, 160), (9, 280, 256, 340, 270)])
    return svg(body_all + co, h=300, title="Globe valve")

# ------------------------------------------------------------------ 6. gate valve
def gate():
    cy = 230
    b = flange_v(24, cy, 104) + flange_v(442, cy, 104) + pipe_h(38, 170, cy) + pipe_h(290, 442, cy)
    body = (P(f"M170 {cy - 44} L170 150 L290 150 L290 {cy - 44} L290 {cy + 44} Q290 286 260 286 L200 286 Q170 286 170 {cy + 44} Z")
            + f'<rect x="182" y="160" width="96" height="116" rx="14" fill="{FL}"/><rect x="166" y="{cy - 22}" width="128" height="44" fill="{FL}"/>')
    seats = R(196, cy - 26, 8, 52, "url(#gBrass)", 2) + R(256, cy - 26, 8, 52, "url(#gBrass)", 2)
    wedge = P("M206 172 L254 172 L250 226 L210 226 Z", "url(#gSteelH)")
    bonnet = R(196, 100, 68, 50, "url(#hatch)") + R(186, 140, 88, 10, "url(#gSteel)", 2)
    gland = R(214, 106, 32, 7, "#ff5a5f", 1) + R(214, 114, 32, 7, "#ff5a5f", 1)
    stem = R(225, 20, 10, 156, "#c9d4e2", 2) + "".join(L(225, y, 235, y + 4, "#7e8ea2", 1) for y in range(30, 96, 6))
    yoke = f'<path d="M202 100 L202 44 L258 44 L258 100" fill="none" stroke="url(#gSteel)" stroke-width="9"/>' + R(214, 36, 32, 12, "#e0a33d", 2)
    wheel = f'<ellipse cx="230" cy="40" rx="62" ry="11" fill="none" stroke="#c9d4e2" stroke-width="5"/>' + L(170, 40, 290, 40, "#c9d4e2", 2)
    fl = flow(50, cy + 8, 160, cy + 8) + flow(212, cy + 12, 250, cy + 12) + flow(300, cy + 8, 430, cy + 8)
    body_all = (b + g(1, body) + g(6, seats) + g(5, wedge) + g(2, bonnet) + g(7, gland) + g(4, stem) + g(8, yoke) + g(3, wheel) + fl
                + T(370, 128, "Half open: as the gate rises", 11, "middle", "#2fd1ae") + T(370, 143, "the passage opens fully", 11, "middle", "#2fd1ae"))
    co = callouts([(1, 176, 270, 120, 284), (2, 264, 118, 320, 104), (3, 290, 40, 340, 50), (4, 235, 70, 320, 80), (5, 250, 196, 330, 196),
                   (6, 200, cy + 20, 140, 180), (7, 214, 110, 150, 104), (8, 202, 60, 150, 56)])
    return svg(body_all + co, h=300, title="Gate valve")

# ------------------------------------------------------------------ 7. pressure safety (relief) valve
def psv():
    inlet = R(176, 274, 88, 14, "url(#hatch)") + P("M190 274 L190 206 L230 206 L230 274 Z") + R(198, 206, 24, 70, FL)
    body = (P("M160 274 L160 170 Q160 150 180 150 L260 150 Q290 150 290 170 L290 168 L392 168 L392 240 L290 240 L290 274 Z")
            + f'<path d="M172 266 L172 176 Q172 162 186 162 L254 162 Q278 162 278 180 L278 180 L392 180 L392 228 L278 228 L278 266 Z" fill="{FL}"/>' + R(392, 154, 14, 100, "url(#hatch)"))
    nozzle = P("M190 266 L190 204 L230 204 L230 266", "url(#hatch)") + f'<rect x="198" y="204" width="24" height="62" fill="{FL}"/>'
    seat = R(194, 199, 32, 6, "url(#gBrass)", 2)
    disc = R(190, 190, 40, 10, "url(#gBrass)", 3)
    guide = R(194, 152, 32, 38, "url(#hatch)")
    bonnet = R(172, 62, 76, 90, "url(#gSteel)", 6) + R(180, 70, 60, 74, "#0e1726")
    spindle = R(206, 40, 8, 152, "#c9d4e2", 2)
    spr = spring(210, 80, 210, 136, 7, 18, "#d7e0ea", 2.4)
    washers = R(186, 136, 48, 6, "#e0a33d", 2) + R(186, 74, 48, 6, "#e0a33d", 2)
    adj = R(200, 38, 20, 36, "#7e8ea2", 2) + R(194, 52, 32, 8, "#5d6d81", 2)
    cap = P("M186 40 Q186 18 210 18 Q234 18 234 40 Z", "url(#gSteel)") + C(244, 30, 4, "#ff5a5f") + L(234, 30, 240, 30, "#ff5a5f", 1)
    fl = flow(210, 296, 210, 280, False) + flowp("M210 186 Q214 176 240 176 L250 176 Q300 204 380 204", True) + flow(420, 204, 470, 204, True)
    body_all = (g(1, inlet) + g(10, body) + g(1, nozzle) + g(3, seat) + g(2, disc) + g(4, guide) + g(5, spindle) + g(6, spr + bonnet[:0]) + g(7, washers) + g(8, adj) + g(9, cap) + fl
                + T(375, 96, "Above set pressure", 11, "middle", "#2fd1ae") + T(375, 111, "the disc lifts", 11, "middle", "#2fd1ae") + T(375, 128, "(dashed = flow when open)", 10.5))
    body_all = bonnet + body_all if False else body_all
    pre = R(172, 62, 76, 90, "url(#gSteel)", 6) + R(180, 70, 60, 74, "#0e1726")
    co = callouts([(1, 196, 250, 120, 262), (2, 228, 194, 300, 150), (3, 194, 202, 120, 196), (4, 194, 170, 120, 158), (5, 214, 60, 280, 50),
                   (6, 226, 110, 300, 90), (7, 186, 139, 120, 128), (8, 220, 56, 280, 20), (9, 196, 24, 130, 20), (10, 380, 236, 420, 270)])
    return svg(pre + body_all + co, h=300, title="Pressure safety valve")

# ------------------------------------------------------------------ 8. excess flow valve
def efv():
    cy = 160
    b = flange_v(40, cy, 104) + flange_v(426, cy, 104) + pipe_h(54, 426, cy, 30, 14)
    body = R(54, cy - 44, 372, 14, "url(#hatch)") + R(54, cy + 30, 372, 14, "url(#hatch)")
    stop = R(120, cy - 30, 8, 60, "#7e8ea2", 1) + L(124, cy - 30, 124, cy + 30, "#0b1220", 1)
    seat = P(f"M300 {cy - 30} L318 {cy - 30} L318 {cy - 10} L300 {cy - 14} Z", "url(#gBrass)") + P(f"M300 {cy + 30} L318 {cy + 30} L318 {cy + 10} L300 {cy + 14} Z", "url(#gBrass)")
    poppet = P(f"M128 {cy - 18} L188 {cy - 18} Q214 {cy - 18} 222 {cy} Q214 {cy + 18} 188 {cy + 18} L128 {cy + 18} Z", "url(#gSteelH)")
    bleed = f'<line x1="140" y1="{cy}" x2="222" y2="{cy}" stroke="#060a12" stroke-width="2.4"/>' + C(222, cy, 2.6, "#ffc46b")
    spr = spring(224, cy, 298, cy, 8, 12, "#d7e0ea", 2.2)
    closed = f'<path d="M226 {cy - 18} L286 {cy - 18} Q312 {cy - 18} 320 {cy} Q312 {cy + 18} 286 {cy + 18} L226 {cy + 18}" fill="none" stroke="#ffc46b" stroke-dasharray="4 3" opacity=".6"/>'
    fl = flow(70, cy - 8, 116, cy - 8) + flowp(f"M130 {cy - 24} L290 {cy - 24}") + flowp(f"M130 {cy + 24} L290 {cy + 24}") + flow(330, cy, 410, cy)
    txt = (T(240, 236, "The spring holds the poppet open; a burst-pipe surge", 11) + T(240, 252, "slams it shut (dashed). It reopens once pressure equalises.", 11))
    body_all = b + g(1, body) + g(6, stop) + g(4, seat) + closed + g(2, poppet) + g(5, bleed) + g(3, spr) + fl + txt
    co = callouts([(1, 380, cy + 40, 400, 210), (2, 170, cy - 18, 170, 80), (3, 262, cy - 10, 262, 80), (4, 310, cy - 24, 350, 80), (5, 200, cy, 200, 210), (6, 124, cy + 28, 100, 210)])
    return svg(body_all + co, h=270, title="Excess flow valve")

# ------------------------------------------------------------------ 9. emergency shutdown valve (remote operated, fail-close)
def esdv():
    cy = 240
    b = flange_v(50, cy, 90) + flange_v(410, cy, 90) + pipe_h(64, 180, cy, 18, 10) + pipe_h(290, 410, cy, 18, 10)
    body = P(f"M180 {cy - 42} L290 {cy - 42} L290 {cy + 42} L180 {cy + 42} Z") + C(235, cy, 34, "url(#gBall)") + f'<rect x="201" y="{cy - 12}" width="68" height="24" fill="{FL}" stroke="{INK}"/>'
    bracket = R(222, 168, 26, 30, "url(#gSteel)", 2) + R(200, 160, 70, 10, "url(#gSteel)", 2)
    act = R(110, 92, 240, 68, "url(#gSteel)", 10) + R(206, 98, 58, 56, "#2b3646", 6) + f'<path d="M220 110 L250 142 M250 110 L220 142" stroke="#c9d4e2" stroke-width="3"/>'
    spr = R(118, 100, 84, 52, "#0e1726", 6) + spring(124, 126, 198, 126, 7, 16, "#d7e0ea", 2.4)
    cylinder = R(268, 100, 76, 52, "#0e1726", 6) + R(296, 104, 10, 44, "url(#gSteelH)", 2) + L(264, 126, 296, 126, "#c9d4e2", 4)
    sol = R(330, 48, 46, 30, "#2b3646", 5) + R(340, 40, 26, 10, "#4c9bff", 2) + L(353, 78, 353, 100, "#93a2b8", 3)
    lsb = R(208, 50, 54, 32, "url(#gSteel)", 6) + C(235, 46, 8, "#3ddc97") + L(235, 82, 235, 92, "#93a2b8", 3)
    air = flowp("M470 62 L380 62", False, "#7fd3ff") + T(440, 44, "Instrument air", 10.5, "middle", "#7fd3ff") + R(390, 52, 18, 20, "#5d6d81", 3)
    esd = R(420, 140, 46, 46, "#2b3646", 8) + C(443, 163, 14, "url(#gRed)") + T(443, 204, "ESD button", 10.5) + f'<path d="M420 163 L380 163 L380 78 L376 78" fill="none" stroke="#ff5a5f" stroke-width="1.4" stroke-dasharray="4 3"/>' + C(150, 182, 6, "#ffc46b") + T(150, 203, "Fusible plug", 10, "middle")
    fl = flow(76, cy, 170, cy) + flow(300, cy, 400, cy)
    txt = T(240, 296, "Air holds it open; ESD, fire or air loss lets the spring close it", 11)
    body_all = b + g(1, body) + bracket + g(2, act) + g(3, spr) + g(4, cylinder) + g(5, sol) + g(6, lsb) + g(7, air) + g(8, esd) + fl + txt
    co = callouts([(1, 280, cy + 36, 320, 290 - 14), (2, 235, 152, 175, 182 - 10), (3, 160, 140, 100, 186), (4, 330, 140, 380, 210), (5, 376, 62, 330, 22), (6, 220, 60, 160, 34), (7, 399, 62, 420, 92), (8, 443, 150, 470, 126)])
    return svg(body_all + co, h=305, title="Emergency shutdown valve")

# ------------------------------------------------------------------ 10. Y-strainer
def strainer():
    cy = 120
    b = flange_v(30, cy, 92) + flange_v(436, cy, 92) + pipe_h(44, 160, cy) + pipe_h(320, 436, cy)
    body = (P(f"M160 {cy - 36} L320 {cy - 36} L320 {cy + 36} L290 {cy + 36} L332 222 L292 262 L222 {cy + 50} L160 {cy + 36} Z")
            + f'<path d="M166 {cy - 24} L314 {cy - 24} L314 {cy + 24} L286 {cy + 24} L316 222 L294 244 L232 {cy + 30} L166 {cy + 24} Z" fill="{FL}"/>'
            + f'<rect x="156" y="{cy - 22}" width="20" height="44" fill="{FL}"/><rect x="306" y="{cy - 22}" width="20" height="44" fill="{FL}"/>')
    screen = f'<g transform="rotate(45 268 186)"><rect x="236" y="166" width="96" height="40" fill="url(#mesh)" stroke="#c9d4e2" stroke-width="1.6" rx="3"/></g>'
    cap = f'<g transform="rotate(45 312 242)"><rect x="296" y="226" width="40" height="34" rx="4" fill="url(#gSteel)" stroke="{INK}"/></g>' + R(318, 246, 18, 3, "#ff5a5f")
    blow = f'<line x1="330" y1="262" x2="352" y2="284" stroke="#8696a8" stroke-width="6"/>' + R(346, 276, 22, 14, "#e0a33d", 3)
    gauges = (L(110, cy - 34, 110, cy - 60, "#8696a8", 4) + C(110, cy - 72, 14, "#e9eef4") + L(110, cy - 72, 118, cy - 80, "#b8322a", 2)
              + L(370, cy - 34, 370, cy - 60, "#8696a8", 4) + C(370, cy - 72, 14, "#e9eef4") + L(370, cy - 72, 360, cy - 78, "#b8322a", 2) + T(240, 30, "ΔP = inlet − outlet pressure", 11, "middle", "#ffc46b"))
    fl = flow(56, cy, 150, cy) + flowp(f"M180 {cy + 6} Q220 {cy + 30} 250 168") + flowp(f"M276 160 Q290 {cy + 10} 330 {cy}") + flow(334, cy, 424, cy)
    body_all = b + g(1, body) + g(2, screen) + g(3, cap) + g(4, blow) + g(5, gauges) + fl + T(130, 250, "ΔP rises as dirt builds up in the screen:", 11) + T(130, 266, "time to clean", 11)
    co = callouts([(1, 190, cy + 40, 150, 200), (2, 268, 200, 210, 220), (3, 300, 238, 390, 220), (4, 352, 284, 400, 280), (5, 370, cy - 86, 420, 30)])
    return svg(body_all + co, h=300, title="Y-strainer")

# ------------------------------------------------------------------ 11. pressure gauge (Bourdon tube)
def gauge():
    cx, cy, r = 190, 140, 104
    ticks = []
    for i in range(0, 26):
        a = math.radians(225 - i * 270 / 25); ln = 14 if i % 5 == 0 else 7
        x1, y1 = cx + (r - 14) * math.cos(a), cy - (r - 14) * math.sin(a); x2, y2 = cx + (r - 14 - ln) * math.cos(a), cy - (r - 14 - ln) * math.sin(a)
        ticks.append(L(f"{x1:.1f}", f"{y1:.1f}", f"{x2:.1f}", f"{y2:.1f}", "#0b1220", 2 if i % 5 == 0 else 1))
        if i % 5 == 0: ticks.append(T(f"{cx + (r - 42) * math.cos(a):.1f}", f"{cy - (r - 42) * math.sin(a) + 4:.1f}", str(i), 12, "middle", "#0b1220", 'font-weight="600"'))
    a0, a1 = math.radians(225 - 18 * 270 / 25), math.radians(225 - 25 * 270 / 25)
    red = f'<path d="M{cx + (r - 16) * math.cos(a0):.1f} {cy - (r - 16) * math.sin(a0):.1f} A{r - 16} {r - 16} 0 0 1 {cx + (r - 16) * math.cos(a1):.1f} {cy - (r - 16) * math.sin(a1):.1f}" fill="none" stroke="#e2453c" stroke-width="6"/>'
    dial = C(cx, cy, r + 8, "url(#gSteel)") + C(cx, cy, r, "#f2f5f8") + red + "".join(ticks) + T(cx, cy + 46, "bar", 12, "middle", "#0b1220")
    ap = math.radians(225 - 9 * 270 / 25)
    pointer = f'<line x1="{cx}" y1="{cy}" x2="{cx + (r - 24) * math.cos(ap):.1f}" y2="{cy - (r - 24) * math.sin(ap):.1f}" stroke="#0b1220" stroke-width="3.4" stroke-linecap="round"/>' + C(cx, cy, 6, "#0b1220")
    bour = f'<path d="M{cx + 8} {cy + r - 4} L{cx + 8} {cy + 66} A46 46 0 1 1 {cx - 40} {cy + 30}" fill="none" stroke="#c98a2b" stroke-width="7" opacity=".6"/>'
    link = L(cx - 40, cy + 30, cx - 22, cy + 34, "#4b5b6e", 2.4, 'opacity=".85"')
    sector = f'<path d="M{cx - 22} {cy + 34} L{cx - 4} {cy + 12} A28 28 0 0 1 {cx + 12} {cy + 26} Z" fill="#9aa8b8" opacity=".6"/>' + C(cx, cy + 14, 5, "#6f8096", 'opacity=".8"')
    hair = f'<path d="M{cx} {cy} m-9 0 a9 9 0 1 0 18 0 a7 7 0 1 0 -14 0" fill="none" stroke="#4b5b6e" stroke-width="1" opacity=".7"/>'
    sock = R(cx - 16, cy + r + 6, 32, 18, "url(#gBrass)", 2) + R(cx - 9, cy + r + 24, 18, 26, "url(#gBrass)") + "".join(L(cx - 9, y, cx + 9, y + 3, "#9a6514", 1) for y in range(cy + r + 27, cy + r + 50, 4))
    fill = T(cx + 60, cy - 56, "", 1) + C(cx + 70, cy - 70, 6, "#ffc46b", 'opacity=".9"')
    iso = R(340, 232, 70, 16, "url(#gSteel)", 3) + R(368, 206, 14, 26, "#7e8ea2", 2) + R(356, 198, 38, 9, "#ff8a2a", 3) + L(306, 240, 340, 240, "#8696a8", 6) + L(410, 240, 450, 240, "#8696a8", 6) + T(375, 270, "Isolation valve", 10.5)
    body_all = g(1, dial) + g(3, bour) + g(4, link) + g(5, sector) + g(6, hair) + g(2, pointer) + g(7, sock) + g(8, fill) + g(9, iso) + T(380, 120, "Pointer at 9 bar", 11, "middle", "#2fd1ae") + T(380, 136, "Red zone: near maximum", 11)
    co = callouts([(1, cx + 90, cy + 50, 330, 196 - 20), (2, cx - 50, cy - 40, 60, 40), (3, cx + 50, cy + 26, 330, 210 + 10), (4, cx - 32, cy + 32, 60, 220), (5, cx + 4, cy + 22, 70, 268),
                   (6, cx - 9, cy + 2, 40, 140), (7, cx - 9, cy + r + 30, 120, 290 - 4), (8, cx + 70, cy - 70, 300, 30), (9, 375, 210, 440, 196)])
    return svg(body_all + co, h=300, title="Bourdon-tube pressure gauge")

# ------------------------------------------------------------------ 12. sliding-vane LPG pump
def pump():
    cx, cy = 210, 160
    suct = pipe_h(20, 116, cy, 24, 12) + flange_v(20, cy, 88)
    disch = pipe_h(304, 420, cy, 24, 12) + flange_v(406, cy, 88)
    casing = C(cx, cy, 108, "url(#hatch)") + f'<rect x="100" y="{cy - 24}" width="40" height="48" fill="{FL}"/><rect x="280" y="{cy - 24}" width="40" height="48" fill="{FL}"/>'
    liner = C(cx, cy, 84, "#7e8ea2") + C(cx, cy, 78, FL)
    rx, ry, rr = cx - 14, cy, 54
    rotor = C(rx, ry, rr, "url(#gSteel)")
    vanes = ""
    for k in range(6):
        a = math.radians(k * 60 + 15); ux, uy = math.cos(a), math.sin(a)
        # distance from rotor centre to liner along this ray
        dx, dy = rx - cx, ry - cy; bq = 2 * (dx * ux + dy * uy); cq = dx * dx + dy * dy - 78 * 78; t = (-bq + math.sqrt(bq * bq - 4 * cq)) / 2
        x1, y1 = rx + (rr - 22) * ux, ry + (rr - 22) * uy; x2, y2 = rx + t * ux, ry + t * uy
        vanes += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="url(#gBrass)" stroke-width="9" stroke-linecap="butt"/>'
        vanes += f'<line x1="{rx + (rr - 22) * ux:.1f}" y1="{ry + (rr - 22) * uy:.1f}" x2="{rx + rr * ux:.1f}" y2="{ry + rr * uy:.1f}" stroke="#0b1220" stroke-width="11" opacity=".25"/>'
    shaft = C(rx, ry, 14, "#c9d4e2") + R(rx - 3, ry - 18, 6, 8, "#2b3646", 1)
    relief = R(cx - 34, 20, 68, 34, "url(#gSteel)", 6) + spring(cx - 22, 37, cx + 18, 37, 5, 8, "#d7e0ea", 1.8) + flowp(f"M300 {cy - 40} Q300 60 {cx + 34} 40", True, "#ff8a2a", "mR") + flowp(f"M{cx - 34} 40 Q120 60 120 {cy - 40}", True, "#ff8a2a", "mR")
    seal = C(rx, ry, 22, "none", 'stroke="#ff5a5f" stroke-width="2" stroke-dasharray="3 2"')
    fl = flow(32, cy, 104, cy) + flowp(f"M{cx - 60} {cy + 70} Q{cx} {cy + 96} {cx + 64} {cy + 62}") + flow(316, cy, 400, cy)
    body_all = (g(8, suct) + g(9, disch) + g(1, casing) + g(2, liner) + g(3, rotor) + g(4, vanes) + g(6, seal) + g(5, shaft) + g(7, relief) + fl
                + T(360, 270, "Off-centre rotor: large pockets at suction,", 11) + T(360, 286, "small at discharge push the liquid out", 11))
    co = callouts([(1, cx + 76, cy + 76, 330, 230 - 20), (2, cx + 82, cy - 20, 345, 70), (3, rx - 30, ry + 30, 110, 268), (4, cx + 40, cy - 40, 300, 96), (5, rx, ry, 60, 236),
                   (6, rx + 18, ry + 14, 160, 290), (7, cx + 30, 26, 300, 20), (8, 60, cy - 36, 60, 88 + 10 - 20), (9, 360, cy - 36, 400, 88)])
    return svg(body_all + co, h=300, title="Sliding-vane LPG pump")

# ------------------------------------------------------------------ 13. reciprocating LPG compressor (tanker unloading)
def compressor():
    cyl = R(170, 54, 100, 76, "url(#hatch)") + R(182, 62, 76, 62, FL)
    piston = R(184, 92, 72, 16, "url(#gSteelH)", 3) + L(184, 96, 256, 96, "#2b3646", 1) + L(184, 104, 256, 104, "#2b3646", 1)
    valves = (R(176, 40, 30, 16, "url(#gSteel)", 3) + R(234, 40, 30, 16, "url(#gSteel)", 3) + L(191, 40, 191, 26, "#8696a8", 6) + L(249, 40, 249, 26, "#8696a8", 6)
              + L(191, 26, 120, 26, "#8696a8", 6) + L(249, 26, 330, 26, "#8696a8", 6))
    rod = R(215, 108, 10, 68, "#c9d4e2", 2)
    pack = R(204, 130, 32, 14, "#ff5a5f", 3)
    xhead = R(198, 170, 44, 20, "url(#gSteel)", 3) + R(190, 160, 6, 40, "#5d6d81") + R(244, 160, 6, 40, "#5d6d81")
    conrod = L(220, 190, 236, 236, "#c9d4e2", 9)
    crank = R(150, 206, 140, 80, "url(#gSteel)", 10) + C(220, 248, 28, "#2b3646") + C(236, 236, 6, "#c9d4e2") + C(220, 248, 7, "#c9d4e2")
    trap = R(56, 40, 54, 150, "url(#gSteel)", 24) + R(64, 120, 38, 58, FL, 14) + C(83, 112, 9, "#ffc46b") + L(83, 112, 110, 112, "#ffc46b", 1.4) + L(83, 40, 83, 26, "#8696a8", 6) + L(83, 26, 120, 26, "#8696a8", 6)
    fourway = R(330, 14, 40, 26, "url(#gBrass)", 5) + L(350, 40, 350, 80, "#8696a8", 6) + L(370, 27, 440, 27, "#8696a8", 6) + L(350, 80, 440, 80, "#8696a8", 6)
    fl = (flowp("M20 60 L50 60", False, "#7fd3ff") + T(26, 52, "From", 10, "start") + T(26, 76, "tanker", 10, "start")
          + flowp("M380 27 L470 27", False, "#7fd3ff") + T(420, 18, "To storage / tanker", 10) + flowp("M440 80 L380 80", False, "#7fd3ff"))
    body_all = (g(8, trap) + g(1, cyl) + g(3, valves) + g(2, piston) + g(4, pack) + g(6, conrod) + g(5, rod + xhead) + g(7, crank) + g(9, fourway) + fl
                + T(380, 140, "Pulls vapour from storage", 11) + T(380, 156, "and pressurises the tanker,", 11)
                + T(380, 172, "forcing liquid into storage;", 11) + T(380, 188, "the 4-way valve reverses it.", 11) + T(83, 210, "Liquid trap", 10.5))
    co = callouts([(1, 266, 70, 320, 110 - 20), (2, 256, 100, 320, 120), (3, 206, 48, 150, 70), (4, 204, 136, 150, 140), (5, 242, 178, 300, 200),
                   (6, 230, 214, 300, 240), (7, 160, 270, 120, 290), (8, 102, 150, 140, 190), (9, 350, 14, 300, 8)])
    return svg(body_all + co, h=300, title="LPG compressor")

# ------------------------------------------------------------------ 14. loading hose with breakaway coupling
def breakaway():
    def hose(x1, x2, y):
        d = f"M{x1} {y}" + "".join(f" Q{x + 6} {y - 6} {x + 12} {y} T{x + 24} {y}" for x in range(x1, x2 - 24, 24))
        return f'<path d="{d}" fill="none" stroke="#9fb0c4" stroke-width="16" stroke-linecap="round"/><path d="{d}" fill="none" stroke="#56677c" stroke-width="16" stroke-dasharray="2 4" stroke-linecap="butt" opacity=".7"/>'
    y1 = 80
    top = (R(20, y1 - 40, 30, 80, "url(#gSteel)", 4) + hose(50, 190, y1) + R(190, y1 - 20, 34, 40, "url(#gBrass)", 6) + R(226, y1 - 20, 34, 40, "url(#gBrass)", 6) + L(224, y1 - 22, 224, y1 + 22, "#ff5a5f", 2.4)
           + hose(262, 400, y1) + R(400, y1 - 18, 40, 36, "url(#gSteel)", 6) + R(440, y1 - 30, 24, 60, "#2b3646", 4) + T(240, 30, "Connected", 11, "middle", "#2fd1ae"))
    y2 = 210
    def half(x, flip):
        s = -1 if flip else 1
        body = R(x, y2 - 26, 70, 52, "url(#gBrass)", 8) + f'<rect x="{x + 10}" y="{y2 - 14}" width="50" height="28" fill="{FL}"/>'
        pop = P(f"M{x + (52 if not flip else 18)} {y2 - 14} L{x + (62 if not flip else 8)} {y2} L{x + (52 if not flip else 18)} {y2 + 14} Z", "url(#gSteelH)")
        spr = spring(x + (18 if not flip else 52), y2, x + (50 if not flip else 20), y2, 4, 7, "#d7e0ea", 1.8)
        return body, pop, spr
    b1, p1, s1 = half(130, False); b2, p2, s2 = half(290, True)
    bot = (hose(40, 130, y2) + hose(360, 450, y2) + T(240, 160, "Pulled apart: both halves seal", 11, "middle", "#ff8a2a")
           + f'<path d="M206 {y2 - 34} L222 {y2 - 20} M276 {y2 - 34} L260 {y2 - 20}" stroke="#ff5a5f" stroke-width="2"/>')
    earth = L(420, y1 + 24, 420, 130, "#3ddc97", 2, 'stroke-dasharray="4 3"') + R(408, 130, 24, 12, "#3ddc97", 3) + T(420, 158, "Earthing", 10.5)
    body_all = g(1, top + bot) + g(2, b1 + b2) + g(3, p1 + p2 + s1 + s2) + g(4, L(224, y1 - 22, 224, y1 + 22, "#ff5a5f", 3)) + g(5, R(400, y1 - 18, 40, 36, "url(#gSteel)", 6)) + g(6, earth)
    body_all += T(240, 284, "On tanker hoses: parts safely instead of the hose tearing", 11)
    co = callouts([(1, 120, y1 - 6, 120, 40), (2, 200, y1 - 18, 176, 30), (3, 182, y2, 182, 262), (4, 224, y1 + 20, 270, 124), (5, 420, y1 - 16, 450, 30 + 6), (6, 420, 136, 460, 112)])
    return svg(body_all + co, h=300, title="Hose with breakaway coupling")

# ------------------------------------------------------------------ 15. carousel filling head with weighing platform
def filler():
    cyl = (P("M160 140 Q160 118 200 116 Q240 118 240 140 L240 252 Q240 266 226 266 L174 266 Q160 266 160 252 Z", "url(#gCyl)")
           + R(180, 96, 40, 22, "#7a1d1d", 4) + T(200, 200, "12 kg", 13, "middle", "#ffe6e1", 'font-weight="700"'))
    valve = R(193, 84, 14, 14, "url(#gBrass)", 2)
    head = R(176, 52, 48, 34, "url(#gSteel)", 6) + R(186, 82, 28, 6, "#ff5a5f", 2)
    act = R(184, 14, 32, 38, "url(#gSteelH)", 5) + L(200, 8, 200, 14, "#c9d4e2", 4)
    hose = f'<path d="M176 66 Q120 66 110 40 Q100 14 60 14" fill="none" stroke="#9fb0c4" stroke-width="9" stroke-linecap="round"/>' + C(60, 14, 7, "url(#gBrass)") + T(60, 36, "LPG", 10)
    plat = R(130, 266, 140, 12, "url(#gSteel)", 3)
    cell = R(180, 278, 40, 16, "url(#gBrass)", 3) + L(186, 286, 214, 286, "#9a6514", 1)
    ctrl = (R(320, 120, 120, 92, "#0e1726", 8) + R(332, 134, 96, 34, "#06111e", 4) + T(380, 158, "12.04 kg", 16, "middle", "#3ddc97", 'font-family="JetBrains Mono,monospace"')
            + T(380, 192, "Set: 12.00 kg + tare", 10.5) + f'<path d="M320 166 L270 166 L270 34 L216 34" fill="none" stroke="#ffc46b" stroke-width="1.4" stroke-dasharray="4 3"/>'
            + f'<path d="M220 286 L300 286 L300 200 L320 200" fill="none" stroke="#ffc46b" stroke-width="1.4" stroke-dasharray="4 3"/>')
    body_all = (g(5, plat) + g(6, cell) + cyl + g(8, valve) + g(1, head) + g(3, R(186, 82, 28, 6, "#ff5a5f", 2)) + g(2, act) + g(4, hose) + g(7, ctrl)
                + T(380, 240, "At set weight:", 11) + T(380, 256, "close the filling valve", 11))
    co = callouts([(1, 224, 66, 270, 92), (2, 184, 30, 140, 20 + 30), (3, 214, 86, 280, 116), (4, 110, 40, 90, 80), (5, 140, 272, 90, 250), (6, 200, 290, 130, 296), (7, 320, 140, 300, 110 - 20 + 6), (8, 193, 92, 130, 110)])
    return svg(body_all + co, h=305, title="Carousel filling head and weighing platform")

# ------------------------------------------------------------------ 16. cylinder valve (self-closing, 12 kg domestic)
def cylvalve():
    neck = P("M120 230 L120 190 Q120 176 140 176 L300 176 Q320 176 320 190 L320 230", "url(#gCyl)") + T(220, 262, "Cylinder neck (boss)", 11)
    thread = P("M180 176 L186 236 L254 236 L260 176 Z", "url(#gBrass)") + "".join(L(184 + (y - 176) * 0.1, y, 256 - (y - 176) * 0.1, y + 3, "#9a6514", 1) for y in range(180, 234, 5))
    body = P("M170 176 L170 96 L188 82 L252 82 L270 96 L270 176 Z", "url(#gBrass)") + f'<rect x="206" y="96" width="28" height="140" fill="{FL}"/>'
    poppet = R(204, 112, 32, 18, "url(#gSteelH)", 4)
    spr = spring(220, 132, 220, 184, 5, 9, "#d7e0ea", 2)
    oring = f'<ellipse cx="220" cy="104" rx="20" ry="4" fill="none" stroke="#ff5a5f" stroke-width="4"/>'
    collar = R(160, 66, 120, 16, "url(#gSteel)", 4) + R(196, 50, 48, 16, "url(#gSteel)", 4)
    cap = f'<path d="M184 42 Q184 18 220 18 Q256 18 256 42 Z" fill="#4c9bff" stroke="{INK}" opacity=".9"/>' + f'<path d="M256 34 Q300 30 300 70" fill="none" stroke="#93a2b8" stroke-width="1.4"/>'
    fl = flowp("M220 196 L220 140", True) + T(380, 230, "Regulator on: poppet opens", 11) + T(380, 246, "Regulator off: spring closes", 11)
    body_all = neck + g(2, thread) + g(1, body) + g(4, spr) + g(3, poppet) + g(5, oring) + g(6, collar) + g(7, cap) + fl
    co = callouts([(1, 266, 150, 330, 170), (2, 190, 214, 120, 150), (3, 236, 120, 320, 100), (4, 228, 170, 300, 210 + 6), (5, 202, 104, 120, 100), (6, 164, 74, 110, 60), (7, 200, 26, 140, 20)])
    return svg(body_all + co, h=280, title="Cylinder valve")

# ------------------------------------------------------------------ 17. fixed gas detector
def detector():
    box = R(150, 40, 120, 90, "url(#gSteel)", 10) + R(166, 56, 88, 40, "#06111e", 6) + T(210, 82, "12% LEL", 15, "middle", "#3ddc97", 'font-family="JetBrains Mono,monospace"') + C(178, 112, 5, "#3ddc97") + C(196, 112, 5, "#ffc46b") + C(214, 112, 5, "#ff5a5f")
    sensor = R(190, 130, 40, 40, "url(#gSteel)", 4)
    sinter = R(194, 170, 32, 14, "url(#mesh)", 3, 'stroke="#c9d4e2"') + R(194, 170, 32, 14, "#7e8ea2", 3, 'opacity=".35"')
    guard = '<path d="M180 168 L240 168 L236 198 L184 198 Z" fill="none" stroke="#93a2b8" stroke-width="1.6"/>'
    gland = R(270, 70, 26, 22, "url(#gBrass)", 3) + L(296, 81, 340, 81, "#5d6d81", 6)
    calcup = R(300, 176, 40, 22, "#2b3646", 6) + f'<path d="M340 187 Q380 187 380 220" fill="none" stroke="#9fb0c4" stroke-width="3"/>' + R(366, 220, 28, 60, "#3ddc97", 8) + T(380, 296, "Test gas", 10)
    # LEL scale
    sc = R(50, 40, 18, 240, "#0e1726", 4) + R(50, 184, 18, 96, "#3ddc97", 4, 'opacity=".55"') + R(50, 136, 18, 48, "#ffc46b", 0, 'opacity=".6"') + R(50, 40, 18, 96, "#ff5a5f", 4, 'opacity=".55"')
    sc += T(76, 188, "20% LEL: warning", 10.5, "start") + T(76, 140, "40% LEL: alarm, ESD", 10.5, "start") + T(76, 284, "0", 10.5, "start") + T(76, 46, "100% LEL", 10.5, "start")
    floor = L(140, 286, 300, 286, "#93a2b8", 2) + T(220, 270, "LPG is heavier than air: mount near the floor", 10.5)
    body_all = g(6, sc) + g(1, box) + g(2, sensor) + g(3, sinter) + g(4, guard) + g(5, gland) + g(7, calcup) + floor
    co = callouts([(1, 266, 50, 320, 30), (2, 230, 146, 290, 140), (3, 196, 178, 140, 200), (4, 238, 190, 270, 236 - 10), (5, 290, 76, 350, 56), (6, 59, 160, 30, 160), (7, 320, 180, 330, 150)])
    return svg(body_all + co, h=300, title="Fixed gas detector")

# ------------------------------------------------------------------ 18. dry-chemical-powder extinguisher
def extinguisher():
    cylb = P("M170 96 Q170 80 210 78 Q250 80 250 96 L250 268 Q250 282 236 282 L184 282 Q170 282 170 268 Z", "url(#gCyl)")
    powder = P("M176 124 L244 124 L244 266 Q244 276 234 276 L186 276 Q176 276 176 266 Z", "url(#powder)", 0.8)
    siphon = R(206, 70, 8, 200, "#c9d4e2", 2)
    valve = R(190, 52, 40, 28, "url(#gBrass)", 4) + P("M186 52 L250 36 L254 44 L192 60 Z", "url(#gSteel)") + P("M186 62 L248 64 L248 72 L186 70 Z", "url(#gSteel)")
    pin = C(176, 50, 7, "none", 'stroke="#ffc46b" stroke-width="2.4"') + L(183, 50, 196, 56, "#ffc46b", 2) + R(170, 58, 10, 6, "#3ddc97", 2)
    gge = C(240, 92, 13, "#f2f5f8") + f'<path d="M230 94 A10 10 0 0 1 250 94" fill="none" stroke="#3ddc97" stroke-width="4"/>' + L(240, 92, 247, 86, "#0b1220", 1.6)
    hose = f'<path d="M230 60 Q300 60 300 140 L300 230" fill="none" stroke="#2b3646" stroke-width="8" stroke-linecap="round"/>' + R(292, 226, 16, 30, "#2b3646", 4)
    tag = R(110, 120, 46, 64, "#f5f1e6", 4) + L(133, 120, 176, 100, "#93a2b8", 1) + "".join(L(116, y, 150, y, "#9aa8b8", 1.4) for y in range(134, 180, 9))
    body_all = (g(1, cylb) + g(2, powder) + g(3, siphon) + g(4, valve) + g(5, pin) + g(6, gge) + g(7, hose) + g(8, tag)
                + T(380, 120, "Needle in the green", 11) + T(380, 140, "Pin and seal intact", 11) + T(380, 160, "Invert to stop caking", 11))
    co = callouts([(1, 250, 250, 300 + 40, 270), (2, 230, 200, 340, 220), (3, 214, 170, 290, 180 - 40 + 6), (4, 230, 62, 300, 30), (5, 176, 50, 130, 30), (6, 252, 92, 300, 96), (7, 300, 230, 360, 250 - 16), (8, 133, 150, 80, 200)])
    return svg(body_all + co, h=300, title="Dry chemical powder fire extinguisher")

# ------------------------------------------------------------------ 19. deluge (water-spray) system
def deluge():
    main = L(20, 280, 200, 280, "#4c9bff", 12) + T(70, 300, "Fire-water main", 10.5)
    bfv = C(120, 236, 14, "url(#gSteel)") + L(120, 222, 120, 250, "#2b3646", 3) + L(120, 256, 120, 280, "#4c9bff", 12) + L(120, 222, 120, 214, "#4c9bff", 12)
    dvalve = R(96, 140, 48, 74, "url(#gSteel)", 8) + R(104, 168, 32, 6, "url(#gBrass)", 2) + C(120, 158, 8, "#2b3646")
    trim = R(150, 160, 30, 20, "#ff5a5f", 4) + L(144, 170, 150, 170, "#93a2b8", 2) + L(180, 170, 200, 170, "#93a2b8", 2) + C(206, 170, 6, "#ffc46b")
    det = f'<path d="M180 160 L180 40 L460 40" fill="none" stroke="#ff5a5f" stroke-width="1.6" stroke-dasharray="5 3"/>' + "".join(C(x, 40, 5, "#ffc46b") for x in (260, 330, 400)) + T(330, 30, "Heat-sensitive detection line", 10.5)
    riser = L(120, 140, 120, 64, "#4c9bff", 10) + L(120, 64, 440, 64, "#4c9bff", 8)
    nozz = "".join(R(x - 5, 66, 10, 10, "url(#gBrass)", 2) + f'<path d="M{x} 78 L{x - 20} 112 M{x} 78 L{x} 114 M{x} 78 L{x + 20} 112" stroke="#7fd3ff" stroke-width="1.6" stroke-dasharray="3 3"/>' for x in (270, 320, 360, 410))
    tank = ("".join(R(x - 4, 200, 8, 96, "url(#gSteelH)", 1) for x in (290, 320, 360, 390)) + C(340, 168, 52, "url(#gBall)")
            + '<path d="M288 168 Q340 180 392 168" fill="none" stroke="#e2453c" stroke-width="2"/>' + T(340, 172, "LPG sphere", 11, "middle", "#0b1220", 'font-weight="600"'))
    gong = C(50, 150, 16, "url(#gBrass)") + L(66, 150, 96, 150, "#93a2b8", 2) + T(50, 126, "Alarm", 10.5)
    drain = R(60, 220, 30, 14, "url(#gSteel)", 3) + L(90, 227, 104, 214, "#93a2b8", 2) + T(60, 252, "Drain/test", 10.5)
    body_all = main + g(5, bfv) + g(1, dvalve) + g(2, R(104, 168, 32, 6, "url(#gBrass)", 2)) + g(3, trim) + g(4, det) + riser + g(6, nozz) + tank + g(7, gong) + g(8, drain)
    co = callouts([(1, 144, 150, 180, 106), (2, 110, 171, 62, 186), (3, 168, 180, 205, 240), (4, 460, 40, 470, 18), (5, 134, 236, 170, 290), (6, 300, 76, 290, 106), (7, 34, 150, 20, 104), (8, 60, 227, 30, 210)])
    return svg(body_all + co, h=310, title="Deluge (water-spray) system")

# ------------------------------------------------------------------ 20. check-scale (weight verification after filling)
def checkscale():
    rollers = "".join(C(x, 230, 8, "url(#gSteel)") for x in range(40, 450, 26))
    frame = R(20, 238, 440, 10, "url(#gSteel)", 2)
    plat = R(150, 206, 170, 14, "url(#gSteel)", 3)
    cells = R(160, 220, 26, 14, "url(#gBrass)", 3) + R(284, 220, 26, 14, "url(#gBrass)", 3)
    jbox = R(220, 252, 30, 22, "#2b3646", 4) + L(173, 234, 220, 262, "#ffc46b", 1.2) + L(297, 234, 250, 262, "#ffc46b", 1.2)
    cylr = P("M200 100 Q200 82 235 80 Q270 82 270 100 L270 196 Q270 206 260 206 L210 206 Q200 206 200 196 Z", "url(#gCyl)") + R(222, 66, 26, 16, "#7a1d1d", 3)
    ind = (R(330, 70, 130, 100, "#0e1726", 8) + R(342, 84, 106, 36, "#06111e", 4) + T(395, 110, "12.04 kg", 17, "middle", "#3ddc97", 'font-family="JetBrains Mono,monospace"')
           + T(395, 140, "Net weight · limit ±150 g", 10.5) + C(360, 156, 6, "#3ddc97") + C(380, 156, 6, "#ff5a5f") + f'<path d="M250 263 L395 263 L395 170" fill="none" stroke="#ffc46b" stroke-width="1.2" stroke-dasharray="4 3"/>')
    rej = P("M60 196 L120 160 L126 168 L66 204 Z", "url(#gSteel)") + T(90, 140, "Reject path", 10.5) + R(56, 196, 14, 30, "#5d6d81", 3)
    wts = R(40, 270, 34, 18, "url(#gSteel)", 3) + R(80, 266, 28, 22, "url(#gSteel)", 3) + R(114, 274, 22, 14, "url(#gSteel)", 3) + T(88, 300, "Test weights", 10.5)
    body_all = rollers + frame + g(1, plat) + g(2, cells) + g(3, jbox) + cylr + g(4, ind) + g(5, rej) + g(6, wts) + T(235, 40, "Every cylinder weighed again after filling: rejected if outside the limit", 11, "middle", "#2fd1ae")
    co = callouts([(1, 316, 210, 330, 196), (2, 172, 230, 150, 270 + 10), (3, 235, 274, 260, 296), (4, 340, 90, 300, 60), (5, 92, 178, 40, 170), (6, 57, 270, 20, 260)])
    return svg(body_all + co, h=310, title="Check-scale")

# ------------------------------------------------------------------ 21. LPG storage sphere (Horton sphere)
def sphere():
    cx, cy, r = 220, 138, 92
    defs = ('<radialGradient id="gSph" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#d9e1ea"/><stop offset="1" stop-color="#8b9bb0"/></radialGradient>'
            '<clipPath id="cutQ"><path d="M220 138 L340 138 L340 260 L220 260 Z"/></clipPath><clipPath id="sphC"><circle cx="220" cy="138" r="88"/></clipPath>')
    ground = L(20, 292, 460, 292, "#56677c", 2)
    legs, fire, brace = "", "", ""
    for x in (150, 186, 254, 290):
        top = cy + math.sqrt(max(0, r * r - (x - cx) ** 2)) * 0.15
        legs += R(x - 5, cy + 4, 10, 288 - cy - 4, "url(#gSteelH)", 1)
        fire += R(x - 7, 258, 14, 32, "#9aa3ad", 2) + "".join(L(x - 7, y, x + 7, y, "#7d8692", 0.8) for y in range(264, 290, 7))
    brace = L(150, 256, 186, 228, "#7a8ca2", 2) + L(150, 228, 186, 256, "#7a8ca2", 2) + L(254, 256, 290, 228, "#7a8ca2", 2) + L(254, 228, 290, 256, "#7a8ca2", 2)
    shell = C(cx, cy, r, "url(#gSph)") + f'<path d="M{cx - r} {cy} Q{cx} {cy + 18} {cx + r} {cy}" fill="none" stroke="#e2453c" stroke-width="2.4"/>'
    # cut-away quadrant: interior with liquid level
    cut = (f'<g clip-path="url(#cutQ)"><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#hatch)"/><circle cx="{cx}" cy="{cy}" r="{r - 6}" fill="#0e1a2b"/>'
           f'<g clip-path="url(#sphC)"><rect x="{cx}" y="{cy + 10}" width="{r}" height="{r}" fill="#1c6e8c" opacity=".85"/><path d="M{cx} {cy + 10} q12 -4 24 0 t24 0 t24 0 t24 0" fill="none" stroke="#7fd3ff" stroke-width="1.6"/></g></g>'
           + L(cx, cy, cx + r, cy, INK, 1.2) + L(cx, cy, cx, cy + r, INK, 1.2))
    liquid = f'<text x="{cx + 44}" y="{cy + 48}" font-size="11" text-anchor="middle" fill="#e6f7ff">Liquid LPG</text><text x="{cx + 46}" y="{cy + 2}" font-size="10" text-anchor="middle" fill="#93a2b8" opacity="0">.</text>'
    vap = f'<text x="{cx + 52}" y="{cy - 2}" font-size="10" text-anchor="middle" fill="#c9d4e2">Vapour</text>'
    platform = R(cx - 34, cy - r - 10, 68, 6, "#7a8ca2", 2) + "".join(L(x, cy - r - 10, x, cy - r - 24, "#93a2b8", 1.4) for x in (cx - 34, cx - 12, cx + 12, cx + 34)) + L(cx - 34, cy - r - 24, cx + 34, cy - r - 24, "#93a2b8", 1.4)
    psv = (R(cx - 26, cy - r - 30, 12, 18, "url(#gBrass)", 2) + L(cx - 20, cy - r - 30, cx - 20, cy - r - 52, "#8696a8", 4)
           + R(cx - 2, cy - r - 30, 12, 18, "url(#gBrass)", 2) + L(cx + 4, cy - r - 30, cx + 4, cy - r - 52, "#8696a8", 4) + R(cx - 22, cy - r - 14, 30, 5, "#5d6d81", 2))
    level = R(cx + 16, cy - r - 28, 14, 16, "#2b3646", 3) + C(cx + 23, cy - r - 34, 6, "#3ddc97")
    gauges = L(cx - r + 4, cy - 30, cx - r - 18, cy - 30, "#8696a8", 3) + C(cx - r - 26, cy - 30, 9, "#f2f5f8") + L(cx - r - 26, cy - 30, cx - r - 21, cy - 35, "#b8322a", 1.6)
    spray = (f'<ellipse cx="{cx}" cy="{cy - 62}" rx="66" ry="12" fill="none" stroke="#4c9bff" stroke-width="4"/>'
             + "".join(f'<path d="M{cx + 66 * math.cos(math.radians(a)):.1f} {cy - 62 + 12 * math.sin(math.radians(a)):.1f} l{6 * math.cos(math.radians(a)):.1f} 10" stroke="#7fd3ff" stroke-width="1.4" stroke-dasharray="2 2"/>' for a in range(0, 360, 30))
             + L(cx + 66, cy - 62, 360, cy - 62, "#4c9bff", 4) + L(360, cy - 62, 360, 290, "#4c9bff", 4))
    outlet = (L(cx, cy + r, cx, 262, "#8696a8", 7) + L(cx, 262, 330, 262, "#8696a8", 7) + R(cx - 9, cy + r - 2, 18, 12, "url(#gBrass)", 2)
              + f'<path d="M286 254 L302 270 L302 254 L286 270 Z" fill="#0c1320" stroke="#eaf0f7" stroke-width="1.6"/>' + R(286, 236, 16, 10, "#ff5a5f", 2) + L(294, 246, 294, 254, "#eaf0f7", 1.4)
              + flow(300, 262, 340, 262) + T(380, 266, "To pumps", 10.5, "start"))
    stair = f'<path d="M110 290 L110 250 L140 236 L110 222 L140 208 L110 194 L130 150 L150 110 L184 66 L196 52" fill="none" stroke="#e2453c" stroke-width="2" stroke-dasharray="1 0"/>'
    earth = L(150, 290, 136, 300, "#3ddc97", 2) + R(124, 296, 16, 6, "#3ddc97", 2)
    body_all = (f'<defs>{defs}</defs>' + ground + g(3, legs + brace) + g(4, fire) + g(1, shell) + g(2, cut + liquid + vap) + g(10, stair + platform) + g(5, psv) + g(6, level) + g(7, gauges)
                + g(8, spray) + g(9, outlet) + g(11, earth) + T(400, 40, "Four spheres at Barabkunda", 11, "middle", "#2fd1ae") + T(400, 56, "White shell, red equator band", 10.5))
    co = callouts([(1, cx - 60, cy - 60, 70, 40), (2, cx + 40, cy + 40, 330, 120), (3, 168, 242, 112, 262), (4, 290, 274, 330, 236), (5, cx - 20, cy - r - 46, 150, 20),
                   (6, cx + 23, cy - r - 34, 290, 22), (7, cx - r - 26, cy - 30, 60, 112), (8, cx + 60, cy - 66, 300, 70), (9, 294, 238, 250, 222), (10, 120, 228, 80, 210), (11, 132, 299, 90, 300 - 6)])
    return svg(body_all + co, h=310, title="LPG storage sphere")

ALL = ["nrv_swing", "nrv_dual", "butterfly", "ball", "globe", "gate", "psv", "efv", "esdv", "strainer", "gauge", "pump", "compressor", "breakaway", "filler", "cylvalve", "detector", "extinguisher", "deluge", "checkscale", "sphere"]

# ------------------------------------------------------------------ plant flow diagram with clickable equipment symbols
def pid():
    LQ, VP, FW = "#2fd1ae", "#7fd3ff", "#4c9bff"
    def ln(d, col, w=3, dash=False): return f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" {"stroke-dasharray=\"7 5\"" if dash else ""} stroke-linejoin="round"/>'
    def hs(eq, x, y, inner, label, ly=None, la="middle", lx=None):
        ly = y + 30 if ly is None else ly; lx = x if lx is None else lx
        return (f'<g class="hs" data-eq="{eq}" tabindex="0" role="button" aria-label="{label}"><circle cx="{x}" cy="{y}" r="22" class="halo"/>{inner}'
                f'<text x="{lx}" y="{ly}" font-size="11" text-anchor="{la}" fill="#cfd9e6">{label}</text></g>')
    def bow(x, y, fill="#0c1320", col="#eaf0f7"): return f'<path d="M{x - 12} {y - 8} L{x + 12} {y + 8} L{x + 12} {y - 8} L{x - 12} {y + 8} Z" fill="{fill}" stroke="{col}" stroke-width="1.8"/>'
    def ballv(x, y): return bow(x, y) + f'<circle cx="{x}" cy="{y}" r="4.5" fill="#0c1320" stroke="#eaf0f7" stroke-width="1.6"/>'
    def globev(x, y): return bow(x, y) + f'<circle cx="{x}" cy="{y}" r="4.5" fill="#eaf0f7"/>'
    def gatev(x, y): return bow(x, y) + f'<line x1="{x}" y1="{y - 8}" x2="{x}" y2="{y - 16}" stroke="#eaf0f7" stroke-width="1.8"/><line x1="{x - 6}" y1="{y - 16}" x2="{x + 6}" y2="{y - 16}" stroke="#eaf0f7" stroke-width="1.8"/>'
    def bfly(x, y): return f'<line x1="{x - 10}" y1="{y - 10}" x2="{x - 10}" y2="{y + 10}" stroke="#eaf0f7" stroke-width="1.8"/><line x1="{x + 10}" y1="{y - 10}" x2="{x + 10}" y2="{y + 10}" stroke="#eaf0f7" stroke-width="1.8"/><line x1="{x - 7}" y1="{y + 8}" x2="{x + 7}" y2="{y - 8}" stroke="#eaf0f7" stroke-width="2.4"/><circle cx="{x}" cy="{y}" r="2.5" fill="#eaf0f7"/>'
    def chk(x, y): return f'<path d="M{x - 12} {y - 8} L{x + 12} {y + 8} L{x + 12} {y - 8} L{x - 12} {y + 8} Z" fill="#0c1320" stroke="#eaf0f7" stroke-width="1.8"/><path d="M{x + 12} {y - 8} L{x} {y} L{x + 12} {y + 8} Z" fill="#eaf0f7"/>'
    def esd(x, y): return bow(x, y) + f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y - 14}" stroke="#eaf0f7" stroke-width="1.6"/><rect x="{x - 9}" y="{y - 24}" width="18" height="11" rx="2" fill="#ff5a5f" stroke="#eaf0f7" stroke-width="1.2"/>'
    def efvs(x, y): return f'<rect x="{x - 13}" y="{y - 9}" width="26" height="18" rx="3" fill="#0c1320" stroke="#eaf0f7" stroke-width="1.6"/><text x="{x}" y="{y + 4}" font-size="9" text-anchor="middle" fill="#eaf0f7" font-weight="700">EFV</text>'
    def strn(x, y): return f'<line x1="{x - 12}" y1="{y}" x2="{x + 12}" y2="{y}" stroke="#eaf0f7" stroke-width="1.8"/><path d="M{x - 4} {y} L{x + 6} {y + 14}" stroke="#eaf0f7" stroke-width="5"/><path d="M{x - 4} {y} L{x + 6} {y + 14}" stroke="#0c1320" stroke-width="2.6"/>'
    def pumps(x, y, col="#eaf0f7"): return f'<circle cx="{x}" cy="{y}" r="13" fill="#0c1320" stroke="{col}" stroke-width="1.8"/><path d="M{x - 7} {y - 9} L{x + 12} {y} L{x - 7} {y + 9}" fill="none" stroke="{col}" stroke-width="1.6"/>'
    def comp(x, y): return f'<circle cx="{x}" cy="{y}" r="13" fill="#0c1320" stroke="#eaf0f7" stroke-width="1.8"/><path d="M{x - 9} {y - 6} L{x + 9} {y - 11} L{x + 9} {y + 11} L{x - 9} {y + 6} Z" fill="none" stroke="#eaf0f7" stroke-width="1.5"/>'
    def gaug(x, y): return f'<line x1="{x}" y1="{y + 14}" x2="{x}" y2="{y + 4}" stroke="#eaf0f7" stroke-width="1.6"/><circle cx="{x}" cy="{y - 6}" r="10" fill="#0c1320" stroke="#eaf0f7" stroke-width="1.6"/><text x="{x}" y="{y - 3}" font-size="8" text-anchor="middle" fill="#eaf0f7" font-weight="700">PI</text>'
    def psvs(x, y): return f'<path d="M{x - 8} {y + 12} L{x + 8} {y + 12} L{x} {y} Z M{x} {y} L{x + 12} {y - 8} L{x + 12} {y + 8} Z" fill="#0c1320" stroke="#eaf0f7" stroke-width="1.6"/>' + spring(x, y - 2, x, y - 18, 3, 4, "#ffc46b", 1.6)
    def gd(x, y): return f'<path d="M{x} {y - 11} L{x + 11} {y} L{x} {y + 11} L{x - 11} {y} Z" fill="#0c1320" stroke="#ffc46b" stroke-width="1.6"/><text x="{x}" y="{y + 3.5}" font-size="8" text-anchor="middle" fill="#ffc46b" font-weight="700">GD</text>'
    def ext(x, y): return f'<rect x="{x - 5}" y="{y - 10}" width="10" height="20" rx="4" fill="#e2453c" stroke="#eaf0f7" stroke-width="1.2"/><path d="M{x} {y - 10} L{x} {y - 14} L{x + 7} {y - 14}" stroke="#eaf0f7" stroke-width="1.4" fill="none"/>'
    def brk(x, y): return f'<rect x="{x - 12}" y="{y - 7}" width="11" height="14" rx="2" fill="#e0a33d" stroke="#eaf0f7" stroke-width="1.2"/><rect x="{x + 1}" y="{y - 7}" width="11" height="14" rx="2" fill="#e0a33d" stroke="#eaf0f7" stroke-width="1.2"/>'
    def nozz(x, y): return f'<path d="M{x - 6} {y} L{x + 6} {y} L{x} {y + 8} Z" fill="#7fd3ff"/><path d="M{x} {y + 8} L{x - 10} {y + 22} M{x} {y + 8} L{x} {y + 24} M{x} {y + 8} L{x + 10} {y + 22}" stroke="#7fd3ff" stroke-width="1.3" stroke-dasharray="2 2"/>'
    o = []
    # stage bands
    for x, w, t in ((10, 250, "1 · Receipt (tanker unloading)"), (270, 300, "2 · Transfer"), (580, 330, "3 · Storage (spheres)"), (920, 270, "4 · Filling, checking and dispatch")):
        o.append(f'<rect x="{x}" y="8" width="{w}" height="22" rx="11" fill="#121c2e" stroke="#1f2c43"/><text x="{x + w / 2}" y="23" font-size="11.5" text-anchor="middle" fill="#ffc46b">{t}</text>')
    o.append('<rect x="10" y="398" width="1180" height="22" rx="11" fill="#121c2e" stroke="#1f2c43"/><text x="600" y="413" font-size="11.5" text-anchor="middle" fill="#7fb6ff">5 · Fire safety (water network, deluge, detectors, extinguishers)</text>')
    # tanker
    o.append('<rect x="30" y="98" width="170" height="62" rx="31" fill="url(#gSteel)" stroke="#0b1220"/><rect x="24" y="160" width="190" height="10" fill="#2b3646"/>'
             + "".join(f'<circle cx="{x}" cy="176" r="11" fill="#1a2433" stroke="#93a2b8" stroke-width="2"/>' for x in (60, 90, 170)) + '<text x="115" y="134" font-size="12" text-anchor="middle" fill="#0b1220" font-weight="700">Bulk tanker</text>')
    # storage spheres on legs
    sph = ""
    for x in (640, 748, 856):
        sph += "".join(f'<line x1="{x + dx}" y1="128" x2="{x + dx}" y2="196" stroke="#93a2b8" stroke-width="3"/>' for dx in (-30, -12, 12, 30))
        sph += f'<path d="M{x - 30} 180 L{x - 12} 150 M{x - 12} 180 L{x - 30} 150 M{x + 12} 180 L{x + 30} 150 M{x + 30} 180 L{x + 12} 150" stroke="#6f8096" stroke-width="1.4"/>'
        sph += f'<circle cx="{x}" cy="112" r="44" fill="url(#gBall)" stroke="#0b1220"/><path d="M{x - 44} 112 Q{x} 124 {x + 44} 112" fill="none" stroke="#e2453c" stroke-width="2"/>'
    o.append(sph + '<text x="676" y="210" font-size="12" text-anchor="middle" fill="#e6efd8" font-weight="600">Storage spheres ×4</text>')
    # carousel
    o.append('<circle cx="1010" cy="318" r="56" fill="#121c2e" stroke="#4c9bff" stroke-width="2"/>' + "".join(f'<circle cx="{1010 + 46 * math.cos(math.radians(a)):.1f}" cy="{318 + 46 * math.sin(math.radians(a)):.1f}" r="5" fill="#e2453c"/>' for a in range(0, 360, 15))
             + '<text x="1010" y="322" font-size="11" text-anchor="middle" fill="#cfd9e6">Carousel</text>')
    # dispatch truck
    o.append('<rect x="1092" y="352" width="76" height="30" rx="4" fill="#2b3646" stroke="#93a2b8"/>' + "".join(f'<rect x="{1098 + i * 13}" y="356" width="9" height="20" rx="3" fill="#e2453c"/>' for i in range(5)) + '<rect x="1168" y="360" width="20" height="22" rx="3" fill="#4c9bff"/><circle cx="1110" cy="386" r="6" fill="#1a2433" stroke="#93a2b8"/><circle cx="1170" cy="386" r="6" fill="#1a2433" stroke="#93a2b8"/>'
             + '<text x="1130" y="346" font-size="11" text-anchor="middle" fill="#cfd9e6">Dispatch</text>')
    # process lines
    o.append(ln("M200 150 L586 150 L586 186 L748 186", LQ, 3.4))         # liquid unloading line into the spheres' bottom header
    o.append(ln("M150 98 L150 60 L620 60 L620 72", VP, 2.4, True))   # vapour return / compressor line
    o.append(ln("M748 186 L748 300 L960 300", LQ, 3.4))              # sphere outlet to carousel
    o.append(ln("M902 300 L902 250 L856 250 L856 196", LQ, 2, True))  # recirculation / bypass back to the spheres
    o.append(ln("M1066 318 L1100 318 L1100 300", "#93a2b8", 2.4) + ln("M1130 300 L1130 352", "#93a2b8", 2.4))
    o.append(ln("M40 380 L1010 380", FW, 3.2) + ln("M520 380 L520 40 L900 40", FW, 2.4) + ln("M1010 380 L1010 374", FW, 2.4) + ln("M960 380 L960 240 L1060 240", FW, 2.4))
    o.append('<rect x="30" y="342" width="34" height="38" rx="4" fill="#173a6b" stroke="#4c9bff"/><text x="47" y="337" font-size="10.5" text-anchor="middle" fill="#7fb6ff">Water tank</text>')
    # equipment hotspots
    H = [
        ("breakaway", 238, 150, brk(238, 150), "Breakaway"), ("esdv", 300, 150, esd(300, 150), "ESD"), ("strainer", 352, 150, strn(352, 150), "Strainer"),
        ("nrv_swing", 410, 150, chk(410, 150), "NRV"), ("ball", 466, 150, ballv(466, 150), "Ball"), ("gauge", 522, 136, gaug(522, 136), "Gauge", 180),
        ("compressor", 400, 60, comp(400, 60), "Compressors", 92), ("psv", 748, 56, psvs(748, 58), "PSV", 62, "start", 764), ("efv", 748, 238, efvs(748, 238), "EFV", 242, "start", 766),
        ("esdv", 748, 276, esd(748, 280), "ESD", 300 - 2, "start"), ("pump", 800, 300, pumps(800, 300), "Pump", 330), ("nrv_dual", 850, 300, chk(850, 300), "Dual NRV", 330),
        ("globe", 902, 268, globev(902, 268), "Bypass", 240 - 2), ("filler", 1010, 272, f'<circle cx="1010" cy="272" r="8" fill="#e2453c" stroke="#eaf0f7"/>', "Filling head", 260 - 6),
        ("checkscale", 1115, 300, '<rect x="1102" y="292" width="26" height="14" rx="2" fill="#0c1320" stroke="#eaf0f7" stroke-width="1.6"/><text x="1115" y="302" font-size="8" fill="#3ddc97" text-anchor="middle">kg</text>', "Check-scale", 286, "middle"),
        ("cylvalve", 1150, 270, '<rect x="1144" y="262" width="12" height="18" rx="4" fill="#e2453c" stroke="#eaf0f7"/><rect x="1147" y="256" width="6" height="6" fill="#e0a33d"/>', "Cylinder valve", 250),
        ("deluge", 640, 40, "".join(nozz(x, 42) for x in (640, 856)), "Deluge spray", 54, "end", 626), ("sphere", 856, 112, '<circle cx="856" cy="112" r="44" fill="transparent"/>', "", 0),
        ("pump", 110, 380, pumps(110, 380, "#7fb6ff"), "Fire pump", 366 - 2), ("nrv_swing", 170, 380, chk(170, 380), "NRV", 368 - 2), ("butterfly", 230, 380, bfly(230, 380), "Butterfly", 368 - 2),
        ("gate", 290, 380, gatev(290, 380), "Gate valve", 360 - 2), ("deluge", 520, 300, f'<rect x="510" y="292" width="20" height="18" rx="3" fill="#173a6b" stroke="#7fb6ff" stroke-width="1.6"/>', "Deluge valve", 286, "end"),
        ("detector", 612, 240, gd(612, 240), "Gas detector", 266), ("detector", 820, 346, gd(820, 346), "", 0), ("detector", 1070, 380 - 12 - 10, gd(1070, 358), "", 0),
        ("extinguisher", 930, 346, ext(930, 346), "Extinguisher", 372 - 2), ("extinguisher", 290, 212, ext(290, 212), "", 0),
    ]
    for h in H:
        eq, x, y, inner, lab = h[:5]; ly = h[5] if len(h) > 5 else None; la = h[6] if len(h) > 6 else "middle"; lx = h[7] if len(h) > 7 else None
        o.append(hs(eq, x, y, inner, lab, ly, la, lx))
    leg = ('<g font-size="11" fill="#93a2b8"><line x1="20" y1="446" x2="50" y2="446" stroke="#2fd1ae" stroke-width="3.4"/><text x="56" y="450">Liquid LPG</text>'
           '<line x1="150" y1="446" x2="180" y2="446" stroke="#7fd3ff" stroke-width="2.4" stroke-dasharray="7 5"/><text x="186" y="450">Vapour/bypass</text>'
           '<line x1="290" y1="446" x2="320" y2="446" stroke="#4c9bff" stroke-width="3.2"/><text x="326" y="450">Fire water</text>'
           '<text x="440" y="450" fill="#ffc46b">Click any symbol to see the equipment drawing, parts, risks and maintenance</text></g>')
    return f'<svg viewBox="0 0 1200 460" role="img" aria-label="LPG flow diagram"><title>LPG flow diagram</title>{"".join(o)}{leg}</svg>'
