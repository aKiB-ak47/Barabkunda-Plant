"""Deeper analysis tab (Bangla) for the calibration report: significance, error sources, cost and progress.
Reads the dashboard data already inside src/reports/cal.html and rewrites the <!--DEEP--> panel. Also keeps the page branding.
    python3 -I src/cal/deep_cal.py            (update_cal.py runs this automatically)"""
import json, math, os, re
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
CAL = f"{SRC}/reports/cal.html"
# LPG value used for the cost of over-filling: BERC retail price for a 12 kg cylinder, November 2026 (incl. VAT).
PRICE_12KG, PRICE_NOTE = 2060.0, "বিইআরসি-নির্ধারিত নভেম্বর ২০২৬-এর খুচরা দাম (১২ কেজি ২,০৬০ টাকা, ভ্যাটসহ)"
BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
def bn(x): return str(x).translate(BN)
def f(x, d=1, sign=False): return bn(f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}").replace("-", "−")
def pfmt(p): return "p < ০.০০১" if p < 0.001 else "p = " + bn(f"{p:.3f}")
def pcls(p): return "sig" if p < 0.05 else ("mid" if p < 0.10 else "ns")
def lakh(x): return bn(f"{x / 1e5:,.1f}") + " লাখ টাকা" if abs(x) < 1e7 else bn(f"{x / 1e7:,.2f}") + " কোটি টাকা"

BRAND_CSS = """<style id="brand">
.brandwm { position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: .045; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='560' height='320'%3E%3Cg transform='rotate(-18 280 160)' fill='%23777' font-family='Arial' font-weight='700'%3E%3Ctext x='150' y='150' font-size='38' letter-spacing='3'%3EBM LP GAS%3C/text%3E%3Ctext x='152' y='178' font-size='14' letter-spacing='5'%3EBARABKUNDA LPG PLANT%3C/text%3E%3Ctext x='300' y='268' font-size='13' letter-spacing='3'%3EAKIB FATEH%3C/text%3E%3C/g%3E%3C/svg%3E"); background-size: 560px 320px }
.tp-bar .byline { font-family: "Dancing Script", cursive; font-size: 20px; color: var(--accent); white-space: nowrap; margin-left: auto; padding-left: 12px }
.brandfoot { position: relative; z-index: 1; max-width: 1100px; margin: 24px auto 40px; padding: 16px; border-top: 1px solid var(--line); color: var(--muted); font: 14px/1.6 "Hind Siliguri", var(--font-ui-sans); display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; align-items: flex-end }
.brandfoot .sig { font-family: "Dancing Script", cursive; font-size: 30px; color: var(--accent); line-height: 1 }
.dp .grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr)); gap: 16px }
.dp table { border-collapse: collapse; width: 100%; font-size: 14px } .dp th, .dp td { text-align: left; padding: 8px 9px; border-bottom: 1px solid var(--line); vertical-align: top; overflow-wrap: anywhere }
.dp th { color: var(--muted); font-weight: 600 } .dp td.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums }
.dp .tw { overflow-x: auto } .dp svg { width: 100%; height: auto; display: block } .dp svg text { font-family: "Hind Siliguri", var(--font-ui-sans); fill: var(--muted); font-size: 12px }
.dp .pv { font-size: 12.5px; padding: 2px 8px; border-radius: 99px; white-space: nowrap } .dp .pv.sig { background: color-mix(in srgb, var(--color-ok) 18%, transparent); color: var(--color-ok) }
.dp .pv.mid { background: color-mix(in srgb, var(--color-warn) 18%, transparent); color: var(--color-warn) } .dp .pv.ns { background: color-mix(in srgb, var(--muted) 14%, transparent); color: var(--muted) }
.dp .big { font: 700 30px/1.2 "Hind Siliguri", var(--font-ui-sans) } .dp .kp { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr)); gap: 12px }
.dp .kp > div { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px } .dp .kp span { color: var(--muted); font-size: 13px; display: block }
.dp .bar { display: flex; height: 26px; border-radius: 8px; overflow: hidden; margin: 8px 0 } .dp .bar i { display: block; height: 100% }
.dp .legend { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 13px; color: var(--muted) } .dp .legend b { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: -1px }
</style>"""

def chart_line(xs, ys, w=640, h=230, ref=None, band=None, ylab=lambda v: bn(f"{v:g}"), colors=None, xl=None, title=""):
    m = dict(l=52, r=12, t=14, b=30); ymin = min(min(ys), *(r for r, _ in (ref or []))) if ref else min(ys); ymax = max(max(ys), *(r for r, _ in (ref or []))) if ref else max(ys)
    if band: ymin, ymax = min(ymin, band[0]), max(ymax, band[1])
    pad = (ymax - ymin) * 0.12 or 1; ymin -= pad; ymax += pad
    X = lambda i: m["l"] + (w - m["l"] - m["r"]) * (i / max(1, len(xs) - 1)); Y = lambda v: h - m["b"] - (h - m["t"] - m["b"]) * (v - ymin) / (ymax - ymin)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{title}">']
    for k in range(5):
        v = ymin + (ymax - ymin) * k / 4; o.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="var(--line)"/><text x="{m["l"] - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{ylab(v)}</text>')
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
    m = dict(l=52, r=12, t=18, b=34); vmin = min(0, min(vals)); vmax = max(vals) * 1.15 or 1
    bw = (w - m["l"] - m["r"]) / len(vals); Y = lambda v: h - m["b"] - (h - m["t"] - m["b"]) * (v - vmin) / (vmax - vmin)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{title}">', f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--line)"/>']
    for i, (lab, v) in enumerate(zip(labels, vals)):
        x = m["l"] + i * bw + bw * 0.15; y0, y1 = sorted([Y(0), Y(v)])
        o.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw * 0.7:.1f}" height="{max(1, y1 - y0):.1f}" rx="3" fill="{col(v)}"><title>{lab}: {fmt(v)}</title></rect>')
        o.append(f'<text x="{x + bw * 0.35:.1f}" y="{(Y(v) - 5 if v >= 0 else Y(v) + 14):.1f}" text-anchor="middle" style="fill:var(--fg);font-weight:600">{fmt(v)}</text>')
        o.append(f'<text x="{x + bw * 0.35:.1f}" y="{h - 12}" text-anchor="middle">{lab}</text>')
    return "".join(o) + "</svg>"

MONB = {"Jan": "জানু", "Feb": "ফেব্রু", "Mar": "মার্চ", "Apr": "এপ্রিল", "May": "মে", "Jun": "জুন", "Jul": "জুলাই", "Aug": "আগস্ট", "Sep": "সেপ্টে", "Oct": "অক্টো", "Nov": "নভে", "Dec": "ডিসে"}
def bmon(s):
    for k, v in MONB.items(): s = s.replace(k, v)
    return bn(s)

def render(C):
    ck = pd.DataFrame(C["checks"]); rd = pd.DataFrame(C["rounds"]); K = {k["metric"]: k for k in C["kpis"]}
    ck["date"] = pd.to_datetime(ck.date); rd["date"] = pd.to_datetime(rd.date)
    c26, c24 = ck[ck.year == 2026], ck[ck.year == 2024]; r26 = rd[rd.year == 2026].sort_values("date")
    last = ck.date.max()
    sig = []
    t1 = stats.ttest_1samp(r26.mean_g, 0); mu, se = r26.mean_g.mean(), r26.mean_g.std(ddof=1) / math.sqrt(len(r26))
    sig.append(("২০২৬-এ সিলিন্ডার কি সত্যিই বেশি ভরা হচ্ছে (গড় ত্রুটি শূন্যের বেশি)?", "এক-নমুনা t-পরীক্ষা (রাউন্ডের গড়, যাতে একই রাউন্ডের সিলিন্ডার আলাদা না গোনা হয়)", t1.pvalue,
                f"রাউন্ডের গড় {f(mu, 1, True)} গ্রাম (৯৫% পরিসর {f(mu - 1.96 * se, 0, True)} থেকে {f(mu + 1.96 * se, 0, True)}), {bn(len(r26))}টি রাউন্ড", "হ্যাঁ, অতিরিক্ত ভরাট নিশ্চিত" if t1.pvalue < 0.05 and mu > 0 else "নিশ্চিত নয়"))
    r24 = rd[rd.year == 2024]; t2 = stats.ttest_ind(r26.mean_g, r24.mean_g, equal_var=False)
    sig.append(("২০২৬-এর গড় ত্রুটি কি ২০২৪-এর চেয়ে বেশি?", "ওয়েলচ t-পরীক্ষা (রাউন্ডের গড়)", t2.pvalue, f"{f(r24.mean_g.mean(), 1, True)} → {f(mu, 1, True)} গ্রাম",
                "তাৎপর্যপূর্ণভাবে বেশি" if t2.pvalue < 0.05 else "পার্থক্য নিশ্চিত নয়"))
    lv = stats.levene(c26.error_g, c24.error_g, center="median")
    sig.append(("সিলিন্ডারে-সিলিন্ডারে ওজনের ছড়ানো কি বেড়েছে?", "ব্রাউন–ফরসাইথ (লেভিন, মধ্যমা-কেন্দ্রিক)", lv.pvalue, f"আদর্শ বিচ্যুতি {f(c24.error_g.std(), 0)} → {f(c26.error_g.std(), 0)} গ্রাম",
                "হ্যাঁ, ছড়ানো তাৎপর্যপূর্ণভাবে বেড়েছে" if lv.pvalue < 0.05 else "নিশ্চিত নয়"))
    kw = stats.kruskal(*[g.error_g.values for _, g in c26.groupby("head")])
    gm = c26.error_g.mean(); ssb = sum(len(g) * (g.error_g.mean() - gm) ** 2 for _, g in c26.groupby("head")); sst = ((c26.error_g - gm) ** 2).sum()
    sig.append(("হেডগুলোর মধ্যে কি আসল পার্থক্য আছে?", "ক্রুসকাল–ওয়ালিস (২৪টি হেড, ২০২৬)", kw.pvalue, f"হেড একাই ছড়ানোর {f(ssb / sst * 100, 1)}% ব্যাখ্যা করে (η²)",
                "হ্যাঁ, কিছু হেড নিয়মিতভাবে আলাদা" if kw.pvalue < 0.05 else "হেডের পার্থক্য নিশ্চিত নয়"))
    kt = stats.kendalltau(np.arange(len(r26)), r26.mean_g.values); ts = stats.theilslopes(r26.mean_g.values, np.arange(len(r26)))
    sig.append(("২০২৬-এর রাউন্ডগুলোতে গড় ত্রুটি কি নিয়মিতভাবে বাড়ছে বা কমছে?", "ম্যান–কেন্ডাল প্রবণতা, থাইল–সেন ঢাল", kt.pvalue, f"প্রতি রাউন্ডে {f(ts.slope, 1, True)} গ্রাম (৯৫% পরিসর {f(ts.low_slope, 1, True)} থেকে {f(ts.high_slope, 1, True)})",
                "নির্ভরযোগ্য একমুখী প্রবণতা নেই: ওঠানামা করছে" if kt.pvalue >= 0.05 else ("ঊর্ধ্বমুখী প্রবণতা" if ts.slope > 0 else "নিম্নমুখী প্রবণতা")))
    rec = c26[c26.date >= "2026-09-01"]; early = c26[c26.date < "2026-09-01"]; mw = stats.mannwhitneyu(rec.error_g, early.error_g)
    sig.append(("সেপ্টেম্বর ২০২৬ থেকে কি অবস্থা খারাপ হয়েছে?", "ম্যান–হুইটনি U", mw.pvalue, f"মধ্যমা {f(early.error_g.median(), 0, True)} → {f(rec.error_g.median(), 0, True)} গ্রাম ({bn(len(early))} ও {bn(len(rec))}টি সিলিন্ডার)",
                "হ্যাঁ, তাৎপর্যপূর্ণভাবে বেশি ভরাট" if mw.pvalue < 0.05 and rec.error_g.median() > early.error_g.median() else ("তাৎপর্যপূর্ণ পরিবর্তন" if mw.pvalue < 0.05 else "পার্থক্য নিশ্চিত নয়")))
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
<h2>গভীর বিশ্লেষণ: তাৎপর্য, ত্রুটির উৎস, খরচ ও অগ্রগতি</h2>
<p class="meta">তথ্য {bn(ck.date.min().strftime("%d.%m.%Y"))} – {bn(last.strftime("%d.%m.%Y"))} · ১২ কেজির {bn(len(ck))}টি ওজন-পরীক্ষা, {bn(len(rd))}টি রাউন্ড · প্রস্তুত করেছেন: <b>Akib Fateh</b>, বাড়বকুণ্ড এলপিজি প্ল্যান্ট (সিটিজি) · যোগ্য প্রকৌশলীর পর্যালোচনার জন্য</p>
<div class="kp" style="margin-bottom:16px">
<div><span>২০২৬-এর গড় অতিরিক্ত ভরাট</span><b class="big">{f(K["Average error (g)"]["y2026"], 1, True)} গ্রাম</b><span>২০২৪: {f(K["Average error (g)"]["base_2024"], 1, True)} · সর্বশেষ: {f(K["Average error (g)"]["latest"], 1, True)}</span></div>
<div><span>প্রক্রিয়া-সক্ষমতা Cpk (±১৫০ গ্রাম)</span><b class="big">{f(K["Cpk (±150 g)"]["y2026"], 2)}</b><span>লক্ষ্য ≥ ১.৩৩ · ২০২৪: {f(K["Cpk (±150 g)"]["base_2024"], 2)}</span></div>
<div><span>বিনামূল্যে যাওয়া এলপিজির মূল্য, মার্চ – ২৫ অক্টোবর ২০২৬</span><b class="big">{lakh(val)}</b><span>৯৫% পরিসর {lakh(lo)} – {lakh(hi)}</span></div>
<div><span>প্রতি ১০ গ্রাম গড় অতিরিক্ত ভরাটে বছরে</span><b class="big">{f(ten_g, 1)} টন</b><span>≈ {lakh(ten_tk)} (বর্তমান উৎপাদন-হারে)</span></div></div>
<div class="card"><h3>পরিসংখ্যানিক তাৎপর্য</h3><p>p &lt; ০.০৫ = তাৎপর্যপূর্ণ; ০.০৫–০.১০ = দুর্বল প্রমাণ; এর বেশি = পার্থক্যটি দৈবও হতে পারে।</p>
<div class="tw"><table style="table-layout:fixed;min-width:760px"><colgroup><col style="width:25%"><col style="width:21%"><col style="width:11%"><col style="width:24%"><col style="width:19%"></colgroup><thead><tr><th>প্রশ্ন</th><th>পরীক্ষা</th><th class="num">p-মান</th><th>প্রভাবের মাপ</th><th>সিদ্ধান্ত</th></tr></thead><tbody>{sig_rows}</tbody></table></div></div>
<div class="grid2">
<div class="card"><h3>ত্রুটি কোথা থেকে আসে (২০২৬)</h3><p>প্রতিটি সিলিন্ডারের ত্রুটির ছড়ানোকে তিন ভাগে ভাগ করা হয়েছে: দিনে দিনে বা রাউন্ডে রাউন্ডে পরিবর্তন (ক্যালিব্রেশন, তাপমাত্রা, ঘনত্ব), হেডে হেডে স্থায়ী পার্থক্য, আর বাকি এলোমেলো ছড়ানো।</p>
<div class="bar"><i style="width:{sh[0]:.1f}%;background:var(--accent)" title="রাউন্ড"></i><i style="width:{sh[1]:.1f}%;background:var(--accent2)" title="হেড"></i><i style="width:{max(0, sh[2]):.1f}%;background:var(--muted);opacity:.45" title="বাকি"></i></div>
<div class="legend"><span><b style="background:var(--accent)"></b>রাউন্ড/দিন {f(sh[0], 0)}%</span><span><b style="background:var(--accent2)"></b>হেড {f(sh[1], 0)}%</span><span><b style="background:var(--muted)"></b>এলোমেলো ছড়ানো {f(sh[2], 0)}%</span></div>
<p style="margin-top:10px">অর্থ: রাউন্ড ও হেড মিলে প্রায় {f(sh[0] + sh[1], 0)}% ত্রুটি নিয়ন্ত্রণযোগ্য (প্রতি শিফটে শূন্য-বিন্দু যাচাই ও হেড-ভিত্তিক ক্যালিব্রেশন)। বাকিটা ভালভ বন্ধের সময়, সিল ও ওজন-যন্ত্রের সূক্ষ্মতার এলোমেলো ছড়ানো, যা যন্ত্রের রক্ষণাবেক্ষণে কমে।</p></div>
<div class="card"><h3>অতিরিক্ত ভরাটের খরচ, মাসে মাসে</h3><p>প্রতিদিনের গড় ত্রুটি × সেদিনের ১২ কেজি উৎপাদন, {PRICE_NOTE} দরে। ঋণাত্মক = কম ভরাট (গ্রাহকের ক্ষতি ও আইনি ঝুঁকি)।</p>
{chart_bars(mlabs, [v / 1e5 for v in mvals], fmt=lambda v: bn(f"{v:,.1f}"), col=lambda v: "var(--color-bad)" if v > 0 else "var(--color-warn)", title="মাসিক খরচ")}<p class="meta" style="margin:6px 0 0">একক: লাখ টাকা। খুচরা দামে মূল্যায়ন বলে এটি ঊর্ধ্বসীমা; প্ল্যান্ট-গেট দামে কম। ২৫ অক্টোবরের পরের উৎপাদন-তথ্য এখনো নেই।</p></div>
<div class="card"><h3>অগ্রগতি: প্রক্রিয়া-সক্ষমতা (Cpk)</h3><p>প্রতিটি সময়কালের Cpk। সবুজ ≥ ১.৩৩ (লক্ষ্য), হলুদ ০.৬৭–১.৩৩, লাল &lt; ০.৬৭। ২০২৪-এর পর সক্ষমতা অর্ধেকেরও নিচে নেমেছে।</p>
{chart_bars(plabs, cpk, fmt=lambda v: bn(f"{v:.2f}"), col=lambda v: "var(--color-ok)" if v >= 1.33 else ("var(--color-warn)" if v >= 0.67 else "var(--color-bad)"), title="Cpk")}</div>
<div class="card"><h3>অগ্রগতি: প্রতিটি রাউন্ডে ±১৫০ গ্রামের ভেতরে</h3><p>সবুজ ≥ ৯৫% (প্ল্যান্ট-লক্ষ্য), হলুদ ৮০–৯৫%, লাল &lt; ৮০%।</p>
{chart_line(rl, w150, ref=[(95, "লক্ষ্য ৯৫%")], ylab=lambda v: bn(f"{v:.0f}") + "%", colors=cols, xl=xi, title="±১৫০ গ্রামের ভেতরে")}</div>
</div>
<div class="card"><h3>প্রতিটি রাউন্ডের গড় ত্রুটি ও নিয়ন্ত্রণ-সীমা</h3><p>সবুজ পটি = ২০২৪-এর নিয়ন্ত্রণ-সীমা ({f(lcl, 0, True)} থেকে {f(ucl, 0, True)} গ্রাম)। লাল বিন্দু = সীমার বাইরে: প্রক্রিয়া বদলে গেছে, কারণ খুঁজতে হবে।</p>
{chart_line(rl, means, band=(lcl, ucl), ref=[(0, "০")], ylab=lambda v: f(v, 0, True), colors=mcols, xl=xi, title="রাউন্ডের গড় ত্রুটি")}</div>
<p class="meta">পদ্ধতি: রাউন্ডের গড়ের ওপর t-পরীক্ষা, যাতে একই রাউন্ডের সিলিন্ডারগুলো স্বাধীন ধরা না হয়; ত্রুটির উৎস ক্রমিক বর্গসমষ্টি দিয়ে (আগে রাউন্ড, তারপর হেড)। খরচ = অতিরিক্ত এলপিজির ভর × খুচরা দাম; উৎপাদন দৈনিক উৎপাদন-প্রতিবেদন থেকে।</p>
</div>'''
    return html

def main():
    page = open(CAL, encoding="utf8").read()
    C = json.loads(re.search(r'<script id="dash-data" type="application/json">(.*?)</script>', page, re.S).group(1))
    if 'data-k="deep"' not in page:
        page = re.sub(r'(<button class="tp-tab" role="tab" data-k="dash"[^>]*>.*?</button>)', lambda m: m.group(1) + '\n<button class="tp-tab" role="tab" data-k="deep" aria-selected="false" style="font-family:\'Hind Siliguri\',var(--font-ui-sans)">গভীর বিশ্লেষণ <small>তাৎপর্য · খরচ · অগ্রগতি</small></button>', page, count=1, flags=re.S)
        page = page.replace("<!--/UPDATE--></section>", '<!--/UPDATE--></section>\n\n<section class="tp-panel" id="tp-deep" lang="bn" hidden><!--DEEP--><!--/DEEP--></section>', 1)
    page = re.sub(r"<!--DEEP-->.*?<!--/DEEP-->", lambda m: "<!--DEEP-->" + render(C) + "<!--/DEEP-->", page, count=1, flags=re.S)
    # branding: watermark, byline, footer, fonts (idempotent)
    if 'id="brand"' in page:
        page = re.sub(r'<style id="brand">.*?</style>', lambda m: BRAND_CSS, page, count=1, flags=re.S)
    else:
        page = page.replace("</head>", BRAND_CSS + "\n</head>", 1)
        page = page.replace("family=Hind+Siliguri:wght@400;500;600;700&display=swap", "family=Hind+Siliguri:wght@400;500;600;700&family=Dancing+Script:wght@600;700&display=swap", 1)
        page = re.sub(r'(<header class="tp-bar"><h1>.*?</h1>)', lambda m: m.group(1) + '<span class="byline">Akib Fateh</span>', page, count=1, flags=re.S)
        page = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + '\n<div class="brandwm" aria-hidden="true"></div>', page, count=1)
        page = page.replace("</body>", '<footer class="brandfoot"><div><b>সিলিন্ডার ওজন-নির্ভুলতা রিপোর্ট</b> · বিএম এনার্জি (বিডি) লিমিটেড, বাড়বকুণ্ড এলপিজি প্ল্যান্ট, সীতাকুণ্ড, চট্টগ্রাম<br>প্রস্তুত করেছেন: <b>Akib Fateh</b> · সিদ্ধান্ত-সহায়তার জন্য; নিরাপত্তা-সংক্রান্ত হিসাব যোগ্য প্রকৌশলীর পর্যালোচনার জন্য</div><div class="sig">Akib Fateh</div></footer>\n</body>', 1)
    open(CAL, "w", encoding="utf8").write(page)
    print("cal.html deep tab written")

if __name__ == "__main__":
    main()
