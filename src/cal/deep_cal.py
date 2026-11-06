"""Deeper analysis tab (Bangla) for the calibration report: significance, error sources, cost and progress.
Reads the dashboard data already inside src/reports/cal.html and rewrites the <!--DEEP--> panel. Also keeps the page branding.
    python3 -I src/cal/deep_cal.py            (update_cal.py runs this automatically)"""
import json, math, os, re
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
CAL = f"{SRC}/reports/cal.html"
# LPG value used for the cost of over-filling: BERC retail price for a 12 kg cylinder, November 2026 (incl. VAT).
PRICE_12KG, PRICE_NOTE = 2060.0, "BERC retail price for November 2026 (Tk 2,060 per 12 kg, incl. VAT)"
BN = str.maketrans("0123456789", "0123456789")
def bn(x): return str(x).translate(BN)
def _r(x, d):   # half away from zero, so a stored 0.285 shows as 0.29 like the unrounded value
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)) if x == x else x
def f(x, d=1, sign=False): x = _r(x, d); return bn(f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}").replace("-", "−")
def pfmt(p): return "p < 0.001" if p < 0.001 else "p = " + bn(f"{p:.3f}")
def pcls(p): return "sig" if p < 0.05 else ("mid" if p < 0.10 else "ns")
def lakh(x): return "Tk " + (bn(f"{x / 1e5:,.1f}") + " lakh" if abs(x) < 1e7 else bn(f"{x / 1e7:,.2f}") + " crore")

BRAND_CSS = """<style id="brand">
:root { --wmtile: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='560' height='320'%3E%3Cg transform='rotate(-18 280 160)' fill='%23cfe6ff' font-family='Arial' font-weight='700'%3E%3Ctext x='150' y='150' font-size='38' letter-spacing='3'%3EBM LP GAS%E2%84%A2%3C/text%3E%3Ctext x='152' y='178' font-size='14' letter-spacing='5'%3EBARABKUNDA LPG PLANT%3C/text%3E%3Ctext x='300' y='268' font-size='13' letter-spacing='3'%3EAKIB FATEH%3C/text%3E%3C/g%3E%3C/svg%3E") }
.brandwm { position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: .045; background-image: var(--wmtile); background-size: 560px 320px }
body { background: transparent !important }
:root { --bg: #050b16; --panel: #0b1730; --line: #1d3050; --fg: #eaf2fc; --muted: #93a7c2; --accent: #ff8a3d; --accent2: #22d3ee; --stage: #030812;
  --color-fg: #eaf2fc; --color-fg-muted: #93a7c2; --color-bg: #050b16; --color-panel: #0b1730; --color-border-line: #1d3050; --color-ok: #22d39a; --color-warn: #ffb020; --color-bad: #ff5d6c;
  --cds-text-primary: #eaf2fc; --cds-text-secondary: #93a7c2; --cds-border: #1d3050; --cds-chart-axis: #7d90aa; --cds-chart-grid: #16263f; --cds-chart-muted: #62758f;
  --cds-chart-categorical-1: #3b9cff; --cds-chart-reference: #ff8a3d; --cds-chart-status-critical: #ff5d6c; --cds-surface-popover: #0e1d38; --cds-shadow-popover: 0 8px 24px rgba(0,0,0,.6);
  --font-ui-sans: "Inter", "IBM Plex Sans", "Segoe UI", system-ui, sans-serif; color-scheme: dark }
html { background: #050b16 !important }
.brandbg { position: fixed; inset: 0; z-index: -1; pointer-events: none; background: linear-gradient(180deg, rgba(5,11,22,.9), rgba(5,11,22,.96)), url("assets/plant_1920.webp") center/cover no-repeat }
@media (min-width: 1600px) { .brandbg { background-image: linear-gradient(180deg, rgba(5,11,22,.9), rgba(5,11,22,.96)), url("assets/plant_3840.webp") } }
.up .card, .dp .card, .dp .kp > div { position: relative; backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); background: color-mix(in srgb, var(--panel) 86%, transparent) !important }
.up .card::after, .dp .card::after { content: ""; position: absolute; right: 12px; bottom: 10px; width: 60px; height: 45px; background: url("assets/logo-alpha.webp") center/contain no-repeat; opacity: .2; pointer-events: none }
.tmk { font: 600 10.5px/1 "JetBrains Mono", ui-monospace, monospace; color: #22d3ee; letter-spacing: .08em; border: 1px solid rgba(34,211,238,.35); border-radius: 6px; padding: 3px 6px; white-space: nowrap }
.ftm { display: block; margin-top: 6px; font-size: 12px; opacity: .8 }
@media (max-width: 640px) { .tmk { display: none } }
.brandwm { background-image: url("assets/logo-alpha.webp"), var(--wmtile) !important; background-size: min(64vw, 560px) auto, 560px 320px !important; background-position: center 58%, 0 0 !important; background-repeat: no-repeat, repeat !important; opacity: .12 !important }
.tp-bar { background: color-mix(in srgb, var(--panel) 88%, transparent) !important; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px) }
.tp-bar h1 { display: flex; align-items: center; gap: 10px; font-family: var(--font-ui-sans) !important; font-weight: 600 !important }
@media (max-width: 640px) { .dp .card, .up .fig { overflow-x: auto } .dp .card svg, .up .fig svg { min-width: 560px } }
.logob { background: #fff; border-radius: 9px; padding: 2px 6px; display: inline-grid; place-items: center; box-shadow: 0 2px 10px rgba(0,0,0,.14); flex: none }
.logob img { height: 28px; width: auto; display: block } .brandfoot .logob img { height: 56px } .brandfoot .logob { padding: 6px 10px; border-radius: 12px }
.tp-bar .byline { font-family: "Dancing Script", cursive; font-size: 20px; color: var(--accent); white-space: nowrap; margin-left: auto; padding-left: 12px }
.brandfoot { position: relative; z-index: 1; max-width: 1100px; margin: 24px auto 40px; padding: 16px; border-top: 1px solid var(--line); color: var(--muted); font: 14px/1.6 var(--font-ui-sans); display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; align-items: flex-end }
.brandfoot .sig { font-family: "Dancing Script", cursive; font-size: 30px; color: var(--accent); line-height: 1 }
.dp .grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr)); gap: 16px }
.dp table { border-collapse: collapse; width: 100%; font-size: 14px } .dp th, .dp td { text-align: left; padding: 8px 9px; border-bottom: 1px solid var(--line); vertical-align: top; white-space: normal !important; overflow-wrap: break-word }
.dp .tw table { min-width: 760px } .dp td:first-child { min-width: 200px } .dp td.num, .dp td:has(.pv) { white-space: nowrap !important }
.dp th { color: var(--muted); font-weight: 600 } .dp td.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums }
.dp .tw { overflow-x: auto } .dp svg { width: 100%; height: auto; display: block } .dp svg text { font-family: var(--font-ui-sans); fill: var(--muted); font-size: 12px }
.dp .pv { font-size: 12.5px; padding: 2px 8px; border-radius: 99px; white-space: nowrap } .dp .pv.sig { background: color-mix(in srgb, var(--color-ok) 18%, transparent); color: var(--color-ok) }
.dp .pv.mid { background: color-mix(in srgb, var(--color-warn) 18%, transparent); color: var(--color-warn) } .dp .pv.ns { background: color-mix(in srgb, var(--muted) 14%, transparent); color: var(--muted) }
.dp .big { font: 700 30px/1.2 var(--font-ui-sans) } .dp .kp { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr)); gap: 12px }
.dp .kp > div { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px } .dp .kp span { color: var(--muted); font-size: 13px; display: block }
.dp .bar { display: flex; height: 26px; border-radius: 8px; overflow: hidden; margin: 8px 0 } .dp .bar i { display: block; height: 100% }
.dp .legend { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 13px; color: var(--muted) } .dp .legend b { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: -1px }
</style>"""

def nice_step(span, n=5):
    raw = span / n; mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    return next(k * mag for k in (1, 2, 2.5, 5, 10) if k * mag >= raw)

def chart_line(xs, ys, w=640, h=230, ref=None, band=None, ylab=lambda v: bn(f"{v:g}"), colors=None, xl=None, title="", cap=None):
    m = dict(l=52, r=12, t=14, b=30); ymin = min(min(ys), *(r for r, _ in (ref or []))) if ref else min(ys); ymax = max(max(ys), *(r for r, _ in (ref or []))) if ref else max(ys)
    if band: ymin, ymax = min(ymin, band[0]), max(ymax, band[1])
    pad = (ymax - ymin) * 0.08 or 1; ymin -= pad; ymax += pad
    if cap: ymax = min(ymax, cap)
    st = nice_step(ymax - ymin); ticks = [k * st for k in range(math.ceil(ymin / st), math.floor(ymax / st) + 1)]
    X = lambda i: m["l"] + (w - m["l"] - m["r"]) * (i / max(1, len(xs) - 1)); Y = lambda v: h - m["b"] - (h - m["t"] - m["b"]) * (v - ymin) / (ymax - ymin)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{title}">']
    for v in ticks:
        o.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--line)"/><text x="{m["l"] - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{ylab(v)}</text>')
    if band: o.append(f'<rect x="{m["l"]}" y="{Y(band[1]):.1f}" width="{w - m["l"] - m["r"]}" height="{Y(band[0]) - Y(band[1]):.1f}" fill="var(--color-ok)" opacity=".10"/>')
    for v, lab in (ref or []):
        o.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--accent)" stroke-dasharray="5 4"/><text x="{w - m["r"]}" y="{Y(v) - 4:.1f}" text-anchor="end" style="fill:var(--accent)">{lab}</text>')
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(ys))
    o.append(f'<polyline points="{pts}" fill="none" stroke="var(--accent2)" stroke-width="2"/>')
    for i, v in enumerate(ys):
        c = (colors or ["var(--accent2)"] * len(ys))[i]
        o.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.6" fill="{c}"><title>{xs[i]}: {ylab(v)}</title></circle>')
    for i in (xl or [0, len(xs) - 1]):
        o.append(f'<text x="{X(i):.1f}" y="{h - 8}" text-anchor="{"start" if i == 0 else ("end" if i == len(xs) - 1 else "middle")}">{xs[i]}</text>')
    return "".join(o) + "</svg>"

def chart_bars(labels, vals, w=640, h=240, fmt=lambda v: bn(f"{v:,.1f}"), col=lambda v: "var(--accent2)", title=""):
    m = dict(l=52, r=12, t=18, b=50 if min(vals) < 0 else 34); vmin = min(0, min(vals)) * 1.1; vmax = max(vals) * 1.15 or 1
    bw = (w - m["l"] - m["r"]) / len(vals); Y = lambda v: h - m["b"] - (h - m["t"] - m["b"]) * (v - vmin) / (vmax - vmin)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{title}">', f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--line)"/>']
    for i, (lab, v) in enumerate(zip(labels, vals)):
        x = m["l"] + i * bw + bw * 0.15; y0, y1 = sorted([Y(0), Y(v)])
        o.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw * 0.7:.1f}" height="{max(1, y1 - y0):.1f}" rx="3" fill="{col(v)}"><title>{lab}: {fmt(v)}</title></rect>')
        o.append(f'<text x="{x + bw * 0.35:.1f}" y="{(Y(v) - 5 if v >= 0 else Y(v) + 14):.1f}" text-anchor="middle" style="fill:var(--fg);font-weight:600">{fmt(v)}</text>')
        o.append(f'<text x="{x + bw * 0.35:.1f}" y="{h - 12}" text-anchor="middle">{lab}</text>')
    return "".join(o) + "</svg>"

MS3 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
def bmon(s):
    s = str(s)
    if re.match(r"^\d{4}-\d{2}$", s): return f"{MS3[int(s[5:]) - 1]} {s[2:4]}"
    m = re.match(r"^(\d{4}) (.+)$", s)
    return f"{m.group(2)} {m.group(1)}" if m else s

def render(C):
    ck = pd.DataFrame(C["checks"]); rd = pd.DataFrame(C["rounds"]); K = {k["metric"]: k for k in C["kpis"]}
    ck["date"] = pd.to_datetime(ck.date); rd["date"] = pd.to_datetime(rd.date)
    c26, c24 = ck[ck.year == 2026], ck[ck.year == 2024]; r26 = rd[rd.year == 2026].sort_values("date")
    last = ck.date.max()
    sig = []
    t1 = stats.ttest_1samp(r26.mean_g, 0); mu, se = r26.mean_g.mean(), r26.mean_g.std(ddof=1) / math.sqrt(len(r26))
    sig.append(("Are cylinders really being overfilled in 2026 (mean error above zero)?", "One-sample t-test (on round means, so cylinders of the same round are not counted separately)", t1.pvalue,
                f"Round mean {f(mu, 1, True)} g (95% range {f(mu - 1.96 * se, 0, True)} to {f(mu + 1.96 * se, 0, True)}), {bn(len(r26))} rounds", "Yes, overfilling confirmed" if t1.pvalue < 0.05 and mu > 0 else "Not confirmed"))
    r24 = rd[rd.year == 2024]; t2 = stats.ttest_ind(r26.mean_g, r24.mean_g, equal_var=False)
    sig.append(("Is the 2026 mean error higher than in 2024?", "Welch t-test (round means)", t2.pvalue, f"{f(r24.mean_g.mean(), 1, True)} → {f(mu, 1, True)} g",
                "Significantly higher" if t2.pvalue < 0.05 else "Difference not confirmed"))
    lv = stats.levene(c26.error_g, c24.error_g, center="median")
    sig.append(("Has the cylinder-to-cylinder spread in weight increased?", "Brown–Forsythe (Levene, median-centred)", lv.pvalue, f"Standard deviation {f(c24.error_g.std(), 0)} → {f(c26.error_g.std(), 0)} g",
                "Yes, spread has increased significantly" if lv.pvalue < 0.05 else "Not confirmed"))
    kw = stats.kruskal(*[g.error_g.values for _, g in c26.groupby("head")])
    gm = c26.error_g.mean(); ssb = sum(len(g) * (g.error_g.mean() - gm) ** 2 for _, g in c26.groupby("head")); sst = ((c26.error_g - gm) ** 2).sum()
    sig.append(("Is there a real difference between heads?", "Kruskal–Wallis (24 heads, 2026)", kw.pvalue, f"Head alone explains {f(ssb / sst * 100, 1)}% of the spread (η²)",
                "Yes, some heads are consistently different" if kw.pvalue < 0.05 else "Head difference not confirmed"))
    kt = stats.kendalltau(np.arange(len(r26)), r26.mean_g.values); ts = stats.theilslopes(r26.mean_g.values, np.arange(len(r26)))
    sig.append(("Is the mean error steadily rising or falling over the 2026 rounds?", "Mann–Kendall trend, Theil–Sen slope", kt.pvalue, f"{f(ts.slope, 1, True)} g per round (95% range {f(ts.low_slope, 1, True)} to {f(ts.high_slope, 1, True)})",
                "No reliable one-way trend: it fluctuates" if kt.pvalue >= 0.05 else ("Upward trend" if ts.slope > 0 else "Downward trend")))
    rec = c26[c26.date >= "2026-09-01"]; early = c26[c26.date < "2026-09-01"]; mw = stats.mannwhitneyu(rec.error_g, early.error_g)
    sig.append(("Has the situation worsened since September 2026?", "Mann–Whitney U", mw.pvalue, f"Median {f(early.error_g.median(), 0, True)} → {f(rec.error_g.median(), 0, True)} g ({bn(len(early))} and {bn(len(rec))} cylinders)",
                "Yes, significantly more overfilling" if mw.pvalue < 0.05 and rec.error_g.median() > early.error_g.median() else ("Significant change" if mw.pvalue < 0.05 else "Difference not confirmed")))
    sig_rows = "".join(f'<tr><td>{q}</td><td>{t}</td><td class="num"><span class="pv {pcls(p)}">{pfmt(p)}</span></td><td>{e}</td><td><b>{v}</b></td></tr>' for q, t, p, e, v in sig)
    # error sources: round, head, remaining scatter (2026)
    e = c26.error_g; g0 = e.mean(); sst = ((e - g0) ** 2).sum()
    rm = c26.groupby("round").error_g.transform("mean"); ss_r = ((rm - g0) ** 2).sum()
    e1 = e - rm; hm = e1.groupby(c26["head"]).transform("mean"); ss_h = (hm ** 2).sum(); ss_e = sst - ss_r - ss_h
    sh = [ss_r / sst * 100, ss_h / sst * 100, ss_e / sst * 100]
    # cost of over-filling
    gv = pd.DataFrame(C["giveaway"]); kg = PRICE_12KG / 12
    tot = C["summary"][0]; val, lo, hi = tot["value"] * 1000 * kg, tot["low"] * 1000 * kg, tot["high"] * 1000 * kg
    days = (pd.Timestamp("2026-10-25") - pd.Timestamp("2026-03-01")).days + 1; cyl = gv.cylinders_12kg.sum(); per_year = cyl / days * 365
    ten_g = per_year * 0.010 / 1000; ten_tk = ten_g * 1000 * kg
    mvals = (gv.overdelivered_mt * 1000 * kg).tolist(); mlabs = [bmon(m) for m in gv.month]
    # progress
    per = C["periods"]; cpk = [p["cpk150"] for p in per]; plabs = [bmon(p["period"]) for p in per]
    rr = rd.sort_values("date"); rl = [bn(d.strftime("%d.%m.%y")) for d in rr.date]
    w150 = rr.within150_pct.tolist(); cols = ["var(--color-ok)" if v >= 95 else ("var(--color-warn)" if v >= 80 else "var(--color-bad)") for v in w150]
    ucl, lcl = float(rd.mean_ucl.iloc[0]), float(rd.mean_lcl.iloc[0])
    means = rr.mean_g.tolist(); mcols = ["var(--color-bad)" if (v > ucl or v < lcl) else "var(--accent2)" for v in means]
    xi = [0] + [i for i in range(1, len(rr)) if rr.year.iloc[i] != rr.year.iloc[i - 1]] + [len(rr) - 1]
    html = f'''<div class="up dp">
<h2>Deep analysis: significance, error sources, cost and progress</h2>
<p class="meta">Data {bn(ck.date.min().strftime("%d.%m.%Y"))} – {bn(last.strftime("%d.%m.%Y"))} · {bn(len(ck))} weight checks of 12 kg cylinders, {bn(len(rd))} rounds · Prepared by: <b>Akib Fateh</b>, Barabkunda LPG Plant (CTG) · For review by a qualified engineer</p>
<div class="kp" style="margin-bottom:16px">
<div><span>2026 average overfill</span><b class="big">{f(K["Average error (g)"]["y2026"], 1, True)} g</b><span>2024: {f(K["Average error (g)"]["base_2024"], 1, True)} · latest: {f(K["Average error (g)"]["latest"], 1, True)}</span></div>
<div><span>Process capability Cpk (±150 g)</span><b class="big">{f(K["Cpk (±150 g)"]["y2026"], 2)}</b><span>target ≥ 1.33 · 2024: {f(K["Cpk (±150 g)"]["base_2024"], 2)}</span></div>
<div><span>Value of LPG given away, March – 25 October 2026</span><b class="big">{lakh(val)}</b><span>95% range {lakh(lo)} – {lakh(hi)}</span></div>
<div><span>Per 10 g of average overfill, per year</span><b class="big">{f(ten_g, 1)} t</b><span>≈ {lakh(ten_tk)} (at the current production rate)</span></div></div>
<div class="card"><h3>Statistical significance</h3><p>p &lt; 0.05 = significant; 0.05–0.10 = weak evidence; above that, the difference could be chance.</p>
<div class="tw"><table style="table-layout:fixed;min-width:760px"><colgroup><col style="width:25%"><col style="width:21%"><col style="width:11%"><col style="width:24%"><col style="width:19%"></colgroup><thead><tr><th>Question</th><th>Test</th><th class="num">p-value</th><th>Effect size</th><th>Verdict</th></tr></thead><tbody>{sig_rows}</tbody></table></div></div>
<div class="grid2">
<div class="card"><h3>Where the error comes from (2026)</h3><p>The spread of each cylinder's error is split three ways: day-to-day or round-to-round change (calibration, temperature, density), lasting differences between heads, and the remaining random scatter.</p>
<div class="bar"><i style="width:{sh[0]:.1f}%;background:var(--accent)" title="Round"></i><i style="width:{sh[1]:.1f}%;background:var(--accent2)" title="Head"></i><i style="width:{max(0, sh[2]):.1f}%;background:var(--muted);opacity:.45" title="Rest"></i></div>
<div class="legend"><span><b style="background:var(--accent)"></b>Round/day {f(sh[0], 0)}%</span><span><b style="background:var(--accent2)"></b>Head {f(sh[1], 0)}%</span><span><b style="background:var(--muted)"></b>Random scatter {f(sh[2], 0)}%</span></div>
<p style="margin-top:10px">Meaning: round and head together account for about {f(sh[0] + sh[1], 0)}% of the error, which is controllable (a zero check every shift and head-by-head calibration). The rest is random scatter from valve-closing time, seals and scale resolution, which equipment maintenance reduces.</p></div>
<div class="card"><h3>Cost of overfilling, month by month</h3><p>Daily mean error × that day's 12 kg production, at the {PRICE_NOTE}. Negative = underfill (customer loss and legal risk).</p>
{chart_bars(mlabs, [v / 1e5 for v in mvals], fmt=lambda v: bn(f"{v:,.1f}"), col=lambda v: "var(--color-bad)" if v > 0 else "var(--color-warn)", title="Monthly cost")}<p class="meta" style="margin:6px 0 0">Unit: Tk lakh. Valued at the retail price, so this is an upper bound; it is lower at the plant-gate price. Production data after 25 October is not yet available.</p></div>
<div class="card"><h3>Progress: process capability (Cpk)</h3><p>Cpk for each period. Green ≥ 1.33 (target), amber 0.67–1.33, red &lt; 0.67. Since 2024 capability has fallen to less than half.</p>
{chart_bars(plabs, cpk, fmt=lambda v: bn(f"{v:.2f}"), col=lambda v: "var(--color-ok)" if v >= 1.33 else ("var(--color-warn)" if v >= 0.67 else "var(--color-bad)"), title="Cpk")}</div>
<div class="card"><h3>Progress: share within ±150 g in each round</h3><p>Green ≥ 95% (plant target), amber 80–95%, red &lt; 80%.</p>
{chart_line(rl, w150, ref=[(95, "target 95%")], ylab=lambda v: bn(f"{v:.0f}") + "%", colors=cols, xl=xi, title="Within ±150 g", cap=100)}</div>
</div>
<div class="card"><h3>Mean error of each round and the control limits</h3><p>Green band = 2024 control limits ({f(lcl, 0, True)} to {f(ucl, 0, True)} g). Red dots = outside the limits: the process has changed and the cause must be found.</p>
{chart_line(rl, means, w=1000, h=300, band=(lcl, ucl), ref=[(0, "0 g")], ylab=lambda v: "0" if abs(v) < 1e-9 else f(v, 0, True), colors=mcols, xl=xi, title="Round mean error")}</div>
<p class="meta">Method: t-tests on round means, so cylinders in the same round are not treated as independent; error sources by sequential sums of squares (round first, then head). Cost = mass of excess LPG × retail price; production from the daily production reports.</p>
</div>'''
    return html

def main():
    page = open(CAL, encoding="utf8").read()
    C = json.loads(re.search(r'<script id="dash-data" type="application/json">(.*?)</script>', page, re.S).group(1))
    if 'data-k="deep"' not in page:
        page = re.sub(r'(<button class="tp-tab" role="tab" data-k="dash"[^>]*>.*?</button>)', lambda m: m.group(1) + '\n<button class="tp-tab" role="tab" data-k="deep" aria-selected="false">Deep analysis <small>significance · cost · progress</small></button>', page, count=1, flags=re.S)
        page = page.replace("<!--/UPDATE--></section>", '<!--/UPDATE--></section>\n\n<section class="tp-panel" id="tp-deep" lang="en" hidden><!--DEEP--><!--/DEEP--></section>', 1)
    page = re.sub(r"<!--DEEP-->.*?<!--/DEEP-->", lambda m: "<!--DEEP-->" + render(C) + "<!--/DEEP-->", page, count=1, flags=re.S)
    # branding: watermark, byline, footer, fonts (idempotent)
    if 'id="brand"' in page:
        page = re.sub(r'<style id="brand">.*?</style>', lambda m: BRAND_CSS, page, count=1, flags=re.S)
    else:
        page = page.replace("</head>", BRAND_CSS + "\n</head>", 1)
        page = page.replace("family=Hind+Siliguri:wght@400;500;600;700&display=swap", "family=Hind+Siliguri:wght@400;500;600;700&family=Dancing+Script:wght@600;700&display=swap", 1)
        page = re.sub(r'(<header class="tp-bar"><h1>.*?</h1>)', lambda m: m.group(1) + '<span class="byline">Akib Fateh</span>', page, count=1, flags=re.S)
        page = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + '\n<div class="brandwm" aria-hidden="true"></div>', page, count=1)
        page = page.replace("</body>", '<footer class="brandfoot"><div><b>Cylinder Weight Accuracy Report</b> · BM Energy (BD) Limited, Barabkunda LPG Plant, Sitakunda, Chattogram<br>Prepared by: <b>Akib Fateh</b> · Decision support; safety-related calculations are for review by a qualified engineer<span class="ftm">BM LP GAS™ and the BM LP GAS logo are trademarks of BM Energy (BD) Limited. © 2026 BM Energy (BD) Limited.</span></div><div class="sig">Akib Fateh</div></footer>\n</body>', 1)
    # keep the tab label, footer and fonts current on every run
    page = re.sub(r'<button class="tp-tab" role="tab" data-k="deep"[^>]*>.*?</button>', '<button class="tp-tab" role="tab" data-k="deep" aria-selected="false">Deep analysis <small>significance · cost · progress</small></button>', page, count=1, flags=re.S)
    page = re.sub(r'<footer class="brandfoot">.*?</footer>', lambda m: '<footer class="brandfoot"><span class="logob"><img src="assets/logo.png" alt="BM LP GAS" width="74" height="56"></span><div><b>Cylinder Weight Accuracy Report</b> · BM Energy (BD) Limited, Barabkunda LPG Plant, Sitakunda, Chattogram<br>Prepared by: <b>Akib Fateh</b> · Decision support; safety-related calculations are for review by a qualified engineer<span class="ftm">BM LP GAS™ and the BM LP GAS logo are trademarks of BM Energy (BD) Limited. © 2026 BM Energy (BD) Limited.</span></div><div class="sig">Akib Fateh</div></footer>', page, count=1, flags=re.S)
    page = page.replace('&family=Hind+Siliguri:wght@400;500;600;700', '').replace('"IBM Plex Sans", "Hind Siliguri", ', '"IBM Plex Sans", ').replace('lang="bn"', 'lang="en"')
    page = re.sub(r"[\"']Hind Siliguri[\"'],\s*", "", page)
    # plant image behind the page, logo in the header and footer (idempotent)
    if 'class="brandbg"' not in page:
        page = page.replace('<div class="brandwm" aria-hidden="true"></div>', '<div class="brandbg" aria-hidden="true"></div>\n<div class="brandwm" aria-hidden="true"></div>', 1)
    page = re.sub(r'<header class="tp-bar"><h1>.*?</h1>', lambda m: '<header class="tp-bar"><h1><span class="logob"><img src="assets/logo.png" alt="BM LP GAS" width="37" height="28"></span>Cylinder weight accuracy and calibration <span class="tmk">BM LP GAS™</span></h1>', page, count=1, flags=re.S)
    if '<footer class="brandfoot"><span class="logob">' not in page:
        page = page.replace('<footer class="brandfoot"><div>', '<footer class="brandfoot"><span class="logob"><img src="assets/logo.png" alt="BM LP GAS" width="74" height="56"></span><div>', 1)
    if "family=Inter:" not in page:
        page = page.replace("family=IBM+Plex+Sans:", "family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&family=IBM+Plex+Sans:", 1)
    page = re.sub(r"<title>.*?</title>", "<title>Cylinder Weight Accuracy · Barabkunda LPG Plant · Akib Fateh</title>", page, count=1, flags=re.S)
    open(CAL, "w", encoding="utf8").write(page)
    print("cal.html deep tab written")

if __name__ == "__main__":
    main()
