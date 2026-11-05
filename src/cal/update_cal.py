"""Refresh the calibration report from a new copy of the Cylinder Weight Calibration workbook.

    python3 -I src/cal/update_cal.py <workbook.xlsx> [--date YYYY-MM-DD]

What it does, in order:
 1. reads every dated sheet (parse_cal.py) and keeps the same validity rules as the original review;
 2. compares with the figures currently published (the dashboard data inside src/reports/cal.html),
    or with src/cal/baseline.json when the same workbook is run again;
 3. rebuilds every dashboard dataset with the original definitions (2024 control limits, ±150 g tolerance,
    bootstrap intervals, Sep-onward 'recent' period), scores the last published forecast against what happened,
    and picks the next-check forecast method by a one-round-ahead rolling backtest;
 4. writes the Bangla 'সর্বশেষ আপডেট' view, the dated dashboard text, the hub figures and an update-log entry.
The 25 Oct slides, written report, giveaway estimate, driver weights and anomaly scores are not recomputed here."""
import argparse, datetime as dt, html, json, math, os, re, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parse_cal  # noqa: E402

CAL = f"{SRC}/reports/cal.html"
HUBDATA = f"{SRC}/hub/hubdata.json"
BASELINE = f"{HERE}/baseline.json"
TOL, FLAG, CPK_REF = 150, 60, 1.33

# ---------------------------------------------------------------- Bangla formatting
BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
MON = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
MONS = ["জানু", "ফেব্রু", "মার্চ", "এপ্রি", "মে", "জুন", "জুলা", "আগ", "সেপ্টে", "অক্টো", "নভে", "ডিসে"]
def bn(x): return str(x).translate(BN)
def num(v, dp=1, sign=False):
    if v is None or (isinstance(v, float) and math.isnan(v)): return "—"
    s = f"{abs(v):,.{dp}f}"
    pre = ("+" if v > 0 else "−" if v < 0 else "") if sign else ("−" if v < 0 else "")
    if float(s.replace(",", "")) == 0: pre = ""
    return bn(pre + s)
def bdate(iso, short=False, year=True):
    d = pd.Timestamp(iso)
    return bn(f"{d.day} {(MONS if short else MON)[d.month - 1]}" + (f" {d.year}" if year else ""))
def ldate(iso):  # Latin digits, Bangla month (hub text is converted to Bangla digits at build time)
    d = pd.Timestamp(iso); return f"{d.day} {MON[d.month - 1]}"
def edate(iso, fmt="%-d %b %Y"): return pd.Timestamp(iso).strftime(fmt)
def bround(label, iso):
    m = re.search(r"\((\d)\)", label)
    return bdate(iso, short=True, year=False) + (bn(f" ({m.group(1)})") if m else "")
def blist(xs):
    xs = [bn(x) for x in xs]
    return xs[0] if len(xs) == 1 else "، ".join(xs[:-1]) + " ও " + xs[-1] if xs else ""
esc = lambda s: html.escape(str(s), quote=False)

# ---------------------------------------------------------------- statistics
def stats(e):
    e = np.asarray(e, float)
    if e.size == 0: return dict(n=0, mean=np.nan, sd=np.nan, within100=np.nan, within150=np.nan, over150=np.nan, under150=np.nan, cpk=np.nan)
    m = e.mean(); s = e.std(ddof=1) if e.size > 1 else np.nan
    return dict(n=int(e.size), mean=m, sd=s, within100=(np.abs(e) <= 100).mean() * 100, within150=(np.abs(e) <= TOL).mean() * 100,
                over150=(e > TOL).mean() * 100, under150=(e < -TOL).mean() * 100, cpk=min(TOL - m, m + TOL) / (3 * s) if s and s > 0 else np.nan)

def ewma_pred(hist, a, cap=None):
    out = {}
    for h in hist.columns:
        s = hist[h].dropna()
        if s.empty: continue
        if cap: s = s.clip(-cap, cap)
        v = s.iloc[0]
        for x in s.iloc[1:]: v = a * x + (1 - a) * v
        out[h] = v
    return pd.Series(out, dtype=float)

METHODS = {
    "EWMA of head (α 0.3)": lambda hist: ewma_pred(hist, 0.3),
    "EWMA of head (α 0.5)": lambda hist: ewma_pred(hist, 0.5),
    "EWMA α 0.3, readings capped at ±300 g": lambda hist: ewma_pred(hist, 0.3, 300),
    "EWMA α 0.5, readings capped at ±300 g": lambda hist: ewma_pred(hist, 0.5, 300),
    "Last round average": lambda hist: pd.Series(hist.iloc[-1].mean(), index=hist.columns),
    "Head average to date": lambda hist: hist.mean(),
    "Naive (head's last check)": lambda hist: hist.ffill().iloc[-1],
}
METHOD_BN = {
    "EWMA of head (α 0.3)": "প্রতিটি হেডের EWMA (α ০.৩)", "EWMA of head (α 0.5)": "প্রতিটি হেডের EWMA (α ০.৫)",
    "EWMA α 0.3, readings capped at ±300 g": "EWMA (α ০.৩), রিডিং ±৩০০ গ্রামে সীমিত", "EWMA α 0.5, readings capped at ±300 g": "EWMA (α ০.৫), রিডিং ±৩০০ গ্রামে সীমিত",
    "Last round average": "আগের রাউন্ডের গড়", "Head average to date": "হেডের এ পর্যন্ত গড়", "Naive (head's last check)": "নাইভ: হেডের আগের রিডিং",
}

# ---------------------------------------------------------------- read inputs
def load_published(page):
    m = re.search(r'<script id="dash-data" type="application/json">(.*?)</script>', page, re.S)
    return json.loads(m.group(1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook"); ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()
    page = open(CAL, encoding="utf8").read()
    published = load_published(page)
    df, issues = parse_cal.read(a.workbook)
    import openpyxl
    sheetnames = openpyxl.load_workbook(a.workbook, read_only=True).sheetnames
    df["date"] = pd.to_datetime(df.date).dt.strftime("%Y-%m-%d")
    new_last = df[(df.nominal == 12) & df.valid].date.max()
    pub_last = max(r["date"] for r in published["rounds"])
    if new_last > pub_last:
        prev = published
        json.dump(prev, open(BASELINE, "w"), ensure_ascii=False)
    elif os.path.exists(BASELINE):
        prev = json.load(open(BASELINE, encoding="utf8"))  # same data run again: compare with what was published before it
    else:
        prev = published
    prev_last = max(r["date"] for r in prev["rounds"])
    R = compute(df, issues, prev, prev_last, sheetnames, a)
    write_all(page, R, a)
    import deep_cal; deep_cal.main()   # deeper-analysis tab and page branding

# ---------------------------------------------------------------- compute
def compute(raw, issues, prev, prev_last, sheetnames, a):
    PR = pd.DataFrame(prev["rounds"]); PH = pd.DataFrame(prev["heads"])
    UCL, LCL, SD_UCL = float(PR.mean_ucl.iloc[0]), float(PR.mean_lcl.iloc[0]), float(PR.sd_ucl.iloc[0])
    c = raw[(raw.nominal == 12) & raw.valid].copy().sort_values(["date", "block", "sl"]).reset_index(drop=True)
    order = c[["date", "block", "round"]].drop_duplicates().reset_index(drop=True); order["round_no"] = order.index + 1
    c = c.merge(order[["round", "round_no"]], on="round")
    c["year"] = pd.to_datetime(c.date).dt.year
    last_day = c.date.max(); L = pd.Timestamp(last_day)
    recent_label = (f"Sep–{L:%b}" if L.year == 2026 else f"Sep 2026–{L:%b %Y}") if L >= pd.Timestamp("2026-09-01") else "Sep–Oct"
    recent_period = f"2026 {recent_label}" if L.year == 2026 else recent_label
    def period(d):
        d = pd.Timestamp(d)
        if d.year == 2024: return "2024 Jun"
        if d < pd.Timestamp("2026-04-01"): return "2026 Jan–Mar"
        if d < pd.Timestamp("2026-09-01"): return "2026 May–Aug"
        return recent_period
    c["period"] = c.date.map(period)
    c["seq"] = c.groupby("round_no").cumcount() + 1
    c["id"] = c.round_no.map("{:02d}".format) + "-" + c.seq.map("{:02d}".format)
    checks = c[["id", "round", "round_no", "date", "year", "period", "head", "tare_kg", "before_kg", "after_kg", "net_kg", "error_g", "leftover_g"]].copy()
    checks["net_kg"] = checks.net_kg.round(3)

    rows = []
    for (rn, rnd, d), g in c.groupby(["round_no", "round", "date"]):
        s = stats(g.error_g)
        rows.append({"round": rnd, "round_no": int(rn), "date": d, "year": int(d[:4]), "cylinders": s["n"], "mean_g": round(s["mean"], 3), "sd_g": round(s["sd"], 3),
                     "within150_pct": round(s["within150"], 3), "over150_pct": round(s["over150"], 3), "under150_pct": round(s["under150"], 3),
                     "mean_ucl": UCL, "mean_lcl": LCL, "sd_ucl": SD_UCL, "mean_out": bool(s["mean"] > UCL or s["mean"] < LCL), "sd_out": bool(s["sd"] > SD_UCL)})
    rounds = pd.DataFrame(rows)
    # earlier rounds must come out the same as published; any change means the workbook's old rows were edited
    chk = rounds.merge(PR[["round", "mean_g", "sd_g", "cylinders"]], on="round", how="right", suffixes=("", "_p"))
    changed = chk[(chk.mean_g.isna()) | ((chk.mean_g - chk.mean_g_p).abs() > 0.05) | ((chk.sd_g - chk.sd_g_p).abs() > 0.05)]
    changed_rounds = [{"round": r["round"], "was": r.mean_g_p, "now": None if pd.isna(r.mean_g) else r.mean_g} for _, r in changed.iterrows()]

    periods = []
    for p in ["2024 Jun", "2026 Jan–Mar", "2026 May–Aug", recent_period]:
        g = c[c.period == p]; s = stats(g.error_g)
        periods.append({"period": p, "checks": s["n"], "days": int(g.date.nunique()), "mean_g": round(s["mean"], 3), "sd_g": round(s["sd"], 3), "within100_pct": round(s["within100"], 3),
                        "within150_pct": round(s["within150"], 3), "over150_pct": round(s["over150"], 3), "under150_pct": round(s["under150"], 3), "cpk150": round(s["cpk"], 3)})

    sb, s6, sl = stats(c[c.year == 2024].error_g), stats(c[c.year == 2026].error_g), stats(c[c.date == last_day].error_g)
    K = [("Average error (g)", "g", "down_abs", "mean"), ("Spread, standard deviation (g)", "g", "down", "sd"), ("Within ±150 g (%)", "%", "up", "within150"),
         ("Over by more than 150 g (%)", "%", "down", "over150"), ("Under by more than 150 g (%)", "%", "down", "under150"), ("Cpk (±150 g)", "", "up", "cpk")]
    kpis = [{"metric": m, "unit": u, "better": b, "base_2024": round(sb[k], 3), "y2026": round(s6[k], 3), "latest": round(sl[k], 3)} for m, u, b, k in K]
    pk = {r["metric"]: r for r in prev["kpis"]}

    rng = np.random.default_rng(42); H = []
    for h, g in c.groupby("head"):
        e = g.error_g.to_numpy(float); bm = np.array([rng.choice(e, e.size).mean() for _ in range(4000)])
        H.append({"head": int(h), "checks": int(e.size), "mean_g": round(e.mean(), 3), "ci_low_g": round(np.percentile(bm, 2.5), 3), "ci_high_g": round(np.percentile(bm, 97.5), 3),
                  "within150_pct": round((np.abs(e) <= TOL).mean() * 100, 3), "over150_pct": round((e > TOL).mean() * 100, 3),
                  "mean_2024_g": round(g[g.year == 2024].error_g.mean(), 3), "mean_2026_g": round(g[g.year == 2026].error_g.mean(), 3),
                  "recent_g": round(g[g.period == recent_period].error_g.mean(), 3)})
    heads = pd.DataFrame(H); heads["hot"] = (heads.ci_low_g > 0) & (heads.mean_g > FLAG)
    prev_hot = PH[(PH.ci_low_g > 0) & (PH.mean_g > FLAG)].sort_values("mean_g", ascending=False)["head"].astype(int).tolist()

    # score the published forecast against the first round after it
    new_r = rounds[rounds.date > prev_last]
    score = None
    if len(new_r) and "forecast_g" in PH:
        fr = new_r.iloc[0]; act = c[c.round_no == fr.round_no].groupby("head").error_g.mean()
        j = PH.set_index("head").join(act.rename("actual"), how="inner")
        pv = c[c.round_no < fr.round_no].sort_values("round_no").groupby("head").error_g.last()
        jn = j.join(pv.rename("prev"), how="inner")
        ps = {s["item"]: s for s in prev["summary"]}
        nx = next(v for k, v in ps.items() if k.startswith("Next check average")); fl = next(v for k, v in ps.items() if k.startswith("Heads expected outside"))
        pm = {r["model"]: r for r in prev["models"]}; selm = next((r["model"] for r in prev["models"] if r.get("selected")), "")
        score = {"round": fr["round"], "date": fr.date, "heads": int(len(j)), "mae_g": float((j.actual - j.forecast_g).abs().mean()),
                 "in_range": int(((j.actual >= j.forecast_low_g) & (j.actual <= j.forecast_high_g)).sum()),
                 "naive_mae": float((jn.actual - jn.prev).abs().mean()), "mean_fc": nx["value"], "mean_lo": nx["low"], "mean_hi": nx["high"],
                 "mean_act": float(act.mean()), "fail_fc": fl["value"], "fail_act": int((act.abs() > TOL).sum()), "method": selm}

    # forecast: one round ahead on the latest 8 rounds, refitted each time
    piv = c.pivot_table(index="round_no", columns="head", values="error_g", aggfunc="mean").sort_index()
    targets = piv.index[-8:]; res = {m: [] for m in METHODS}; rmean = {m: [] for m in METHODS}
    for t in targets:
        hist, actual = piv.loc[piv.index < t], piv.loc[t].dropna()
        for m, f in METHODS.items():
            p = f(hist).reindex(actual.index); ok = p.notna()
            res[m] += list(zip(actual[ok], p[ok])); rmean[m].append((actual.mean(), p[ok].mean()))
    M = []
    for m in METHODS:
        arr = np.array(res[m]); err = arr[:, 0] - arr[:, 1]
        M.append({"model": m, "mae_g": round(np.abs(err).mean(), 3), "rmse_g": round(math.sqrt((err ** 2).mean()), 3),
                  "mape_net_pct": round((np.abs(err) / (12000 + arr[:, 0])).mean() * 100, 3),
                  "direction_hit_pct": round((np.sign(arr[:, 0]) == np.sign(arr[:, 1])).mean() * 100, 3), "n": int(len(arr))})
    models = pd.DataFrame(M)
    naive = models.set_index("model").loc["Naive (head's last check)", "rmse_g"]
    models["skill_vs_naive_pct"] = ((1 - models.rmse_g / naive) * 100).round(3)
    best = models.sort_values("rmse_g").iloc[0].model; models["selected"] = models.model == best
    models = models[["model", "selected", "mae_g", "rmse_g", "mape_net_pct", "direction_hit_pct", "skill_vs_naive_pct", "n"]]
    resid = np.array(res[best]); resid = resid[:, 0] - resid[:, 1]; q10, q90 = np.percentile(resid, [10, 90])
    nxt = METHODS[best](piv); rm = np.array(rmean[best]); rres = rm[:, 0] - rm[:, 1]
    fail = {h: float((np.abs(v + resid) > TOL).mean() * 100) for h, v in nxt.items()}
    heads["forecast_g"] = heads["head"].map(nxt).round(3)
    heads["forecast_low_g"] = (heads.forecast_g + q10).round(3); heads["forecast_high_g"] = (heads.forecast_g + q90).round(3)
    heads["fail_chance_pct"] = heads["head"].map(fail).round(3)
    rnd_by_no = rounds.set_index("round_no")
    fc = {"method": best, "n_methods": len(METHODS), "first_test": rnd_by_no.loc[targets[0], "date"], "last_test": rnd_by_no.loc[targets[-1], "date"],
          "n_test": int(len(resid)), "mean": float(nxt.mean()), "mean_lo": float(nxt.mean() + np.percentile(rres, 10)), "mean_hi": float(nxt.mean() + np.percentile(rres, 90)),
          "fail_heads": float(sum(fail.values()) / 100), "q10": float(q10), "q90": float(q90)}

    big = raw[(raw.nominal != 12) & raw.valid].copy(); S = []
    for n, g in big.groupby("nominal"):
        e = g.error_g
        S.append({"size": f"{n} kg", "checks": int(len(g)), "days": int(g.date.nunique()), "mean_g": round(e.mean(), 3), "pct_of_nominal": round(e.mean() / (n * 10), 3),
                  "within150_pct": round((e.abs() <= TOL).mean() * 100, 3), "max_over_g": round(e.max(), 1)})
    newbig = big[big.date > prev_last]

    e = c.error_g; newc = c[c.date > prev_last]
    n_excl = int(((raw.nominal == 12) & ~raw.valid & raw.tare_kg.notna() & raw.after_kg.notna()).sum())
    excl_new = raw[(raw.nominal == 12) & ~raw.valid & raw.tare_kg.notna() & raw.after_kg.notna() & (raw.date > prev_last)]
    unusual = newc[newc.error_g <= -500]
    flags = [dict(f) for f in prev["flags"]]
    for f in flags:
        if f["id"] == "S1":
            f["value"] = float(e.max()); f["detail"] = (f"{int((e > 500).sum())} checks more than 500 g over, {int((e > 300).sum())} more than 300 g over; filling ratio cannot be checked "
                                                       "without water capacity. For review by a qualified engineer (NFPA 58; ISO 10691; LPG Rules 2004).")
        if f["id"] == "S2" and len(newbig):
            base = f["detail"].split(" Newest")[0].replace(" For review by a qualified engineer.", "")
            top = newbig.loc[newbig.error_g.idxmax()]
            f["value"] = float(max(f["value"], big.error_g.max()))
            f["detail"] = f"{base} Newest larger-cylinder checks ({edate(newbig.date.max())}): up to +{top.error_g:.0f} g ({int(top.nominal)} kg, head {int(top['head'])}). For review by a qualified engineer."
        if f["id"] == "S3": f["value"] = round((e > TOL).mean() * 100, 3)
        if f["id"] == "D3": f["value"] = n_excl
    nd = len([x for x in flags if x["kind"] == "Data quality"])
    for _, r in unusual.iterrows():
        nd += 1
        flags.append({"id": f"D{nd}", "kind": "Data quality", "finding": f"Unusual reading, head {int(r['head'])}, {edate(r.date)}", "value": float(r.error_g), "unit": "g",
                      "detail": "Far below this head's other readings; check the original check sheet before acting on it. Kept in the figures; forecasts cap each reading at ±300 g."})
    summary = [dict(s) for s in prev["summary"]]
    r26 = rounds[rounds.year == 2026]
    for s in summary:
        if s["item"].startswith("Heads expected outside"): s["value"] = round(fc["fail_heads"], 3)
        if s["item"].startswith("Next check average"): s.update(value=round(fc["mean"], 3), low=round(fc["mean_lo"], 3), high=round(fc["mean_hi"], 3))
        if s["item"].startswith("Rounds in 2026 inside"): s.update(value=int((~r26.mean_out & ~r26.sd_out).sum()), high=int(len(r26)))
    prev_sum = {s["item"]: s for s in prev["summary"]}

    # per-head readings in the new rounds, and the effect of unusual readings on the latest round
    new_rounds = rounds[rounds.date > prev_last]
    per_head = {int(h): {r: None for r in new_rounds["round"]} for h in heads["head"]}
    for _, r in newc.iterrows(): per_head[int(r["head"])][r["round"]] = float(r.error_g)
    rep_heads = []
    if len(new_rounds) >= 2:
        cnt = newc[newc.error_g > TOL].groupby("head").size()
        rep_heads = cnt[cnt == len(new_rounds)].index.astype(int).tolist()
    lx = c[(c.date == last_day) & (c.error_g > -500)].error_g
    new_issue_sheets = [x for x in issues if any(x[1].strip().startswith(sn.strip()) for sn in raw[raw.date > prev_last].sheet.unique())]
    four_digit = [sn.strip() for sn in raw[raw.date > prev_last].sheet.unique() if re.match(r"\s*\d{1,2}-\d{1,2}-\d{4}\s*$", sn)]
    new_sheets = [sn.strip() for sn in raw[raw.date > prev_last].sheet.unique()]
    empty_sheets = [sn.strip() for sn in sheetnames if parse_cal.sheet_date(sn) and sn not in set(raw.sheet)]

    datasets = {"checks": checks.to_dict("records"), "rounds": rounds.to_dict("records"), "periods": periods, "kpis": kpis,
                "heads": heads.drop(columns="hot").to_dict("records"), "sizes": S, "flags": flags, "summary": summary,
                "models": models.drop(columns="n").to_dict("records")}
    for k in ("giveaway", "drivers", "anomalies"): datasets[k] = prev[k]
    return dict(datasets=datasets, c=c, raw=raw, rounds=rounds, heads=heads, models=models, periods=periods, kpis=kpis, pk=pk, sb=sb, s6=s6, sl=sl,
                slx=stats(lx), prev=prev, prev_last=prev_last, last_day=last_day, new_rounds=new_rounds, newc=newc, newbig=newbig, per_head=per_head,
                rep_heads=rep_heads, unusual=unusual, excl_new=excl_new, n_excl=n_excl, prev_excl=next((f["value"] for f in prev["flags"] if f["id"] == "D3"), None),
                score=score, fc=fc, prev_hot=prev_hot, recent_label=recent_label, recent_period=recent_period, changed_rounds=changed_rounds,
                new_issue_sheets=new_issue_sheets, four_digit=four_digit, new_sheets=new_sheets, empty_sheets=empty_sheets, n_sheets=len(sheetnames),
                UCL=UCL, LCL=LCL, SD_UCL=SD_UCL, e=e, summary=summary, prev_sum=prev_sum, r26=r26, prev_r26=PR[PR.year == 2026],
                prev_periods=prev["periods"])

# ---------------------------------------------------------------- the Bangla view
def heat(v):
    if v is None: return '<td class="note">—</td>'
    a = 0.12 + 0.88 * min(1, abs(v) / 300)
    col = f"rgba(29,95,168,{a:.2f})" if v >= 0 else f"rgba(194,65,12,{a:.2f})"
    txt = "#fff" if a >= 0.5 else "var(--fg)"
    return f'<td style="background:{col};color:{txt};font-weight:600">{num(v, 0, True)}</td>'

def chart_rounds(R):
    rs = R["rounds"].sort_values("round_no").tail(16).reset_index(drop=True)
    newset = set(R["new_rounds"]["round"])
    W, Hh, l, r, t, b = 760, 270, 46, 70, 16, 46
    lo = min(R["LCL"] - 30, rs.mean_g.min() - 15); hi = max(R["UCL"] + 30, rs.mean_g.max() + 25)
    y = lambda v: t + (hi - v) / (hi - lo) * (Hh - t - b)
    x = lambda i: l + i * (W - l - r) / max(1, len(rs) - 1)
    o = [f'<svg viewBox="0 0 {W} {Hh}" role="img" aria-label="সাম্প্রতিক রাউন্ডের গড় ত্রুটি ও নিয়ন্ত্রণ-সীমা">']
    o.append(f'<rect x="{l}" y="{y(R["UCL"]):.1f}" width="{W - l - r}" height="{y(R["LCL"]) - y(R["UCL"]):.1f}" fill="var(--color-ok)" fill-opacity=".08"/>')
    step = 50 if hi - lo > 150 else 25
    for v in range(int(math.ceil(lo / step) * step), int(hi) + 1, step):
        o.append(f'<line x1="{l}" x2="{W - r}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{"var(--cds-chart-axis)" if v == 0 else "var(--cds-chart-grid)"}"/>'
                 f'<text x="{l - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{num(v, 0, True)}</text>')
    for v, lab in [(R["UCL"], "উচ্চ সীমা"), (R["LCL"], "নিম্ন সীমা")]:
        o.append(f'<line x1="{l}" x2="{W - r}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="var(--cds-chart-reference)" stroke-dasharray="5 4" stroke-width="1.5"/>'
                 f'<text x="{W - r + 6}" y="{y(v) + 4:.1f}">{lab} {num(v, 0, True)}</text>')
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(rs.mean_g))
    o.append(f'<polyline points="{pts}" fill="none" stroke="var(--cds-chart-muted)" stroke-width="1.5"/>')
    for i, rr in rs.iterrows():
        isnew = rr["round"] in newset
        col = "var(--accent)" if isnew else "var(--cds-chart-muted)"
        o.append(f'<circle cx="{x(i):.1f}" cy="{y(rr.mean_g):.1f}" r="{6 if isnew else 4.5}" fill="{col}" stroke="var(--panel)" stroke-width="1.5"><title>{esc(rr["round"])}: {rr.mean_g:+.1f} g</title></circle>')
        if isnew: o.append(f'<text class="strong" x="{x(i):.1f}" y="{y(rr.mean_g) - 11:.1f}" text-anchor="middle">{num(rr.mean_g, 0, True)}</text>')
        if isnew or i % 3 == 0:
            o.append(f'<text x="{x(i):.1f}" y="{Hh - b + 18}" text-anchor="middle"{" class=strong" if isnew else ""}>{bround(rr["round"], rr.date)}</text>')
    o.append(f'<text x="{l}" y="{Hh - 6}">ধূসর: আগের রাউন্ড · কমলা: নতুন রাউন্ড · সবুজ পটি: ২০২৪-এর নিয়ন্ত্রণ-সীমার ভেতরে</text></svg>')
    return "".join(o)

def tile(k, v, d, cls=""):
    return f'<div class="tile"><span class="k">{k}</span><span class="v {cls}">{v}</span><span class="d">{d}</span></div>'

def worse(new, old, better):
    if old is None or new is None: return ""
    if better == "up": return "bad" if new < old - 1e-9 else "ok" if new > old + 1e-9 else ""
    if better == "down_abs": return "bad" if abs(new) > abs(old) + 1e-9 else "ok" if abs(new) < abs(old) - 1e-9 else ""
    return "bad" if new > old + 1e-9 else "ok" if new < old - 1e-9 else ""

def render(R, a, updates):
    pl, ld = R["prev_last"], R["last_day"]; NR, newc = R["new_rounds"], R["newc"]; fc, sc = R["fc"], R["score"]
    pk, s6, sb, sl, slx = R["pk"], R["s6"], R["sb"], R["sl"], R["slx"]
    o = ['<div class="up">']
    o.append('<h2>সিলিন্ডার ওজন-নির্ভুলতা: সর্বশেষ আপডেট</h2>')
    o.append(f'<p class="meta">হালনাগাদ {bdate(a.date)} · তথ্য {bdate(R["rounds"].date.min())} – {bdate(ld)} · উৎস: প্ল্যান্টের ওজন-পরীক্ষার রেকর্ড '
             f'({bn(R["n_sheets"])}টি শিট; নতুন: <span class="lat">{esc(", ".join(R["new_sheets"])) or "—"}</span>) · প্রস্তুত করেছেন: <b>Akib Fateh</b>, বাড়বকুণ্ড এলপিজি প্ল্যান্ট (সিটিজি)</p>')
    if len(NR) == 0:
        o.append(f'<div class="card"><p>{bdate(pl)}-এর পর কোনো নতুন ১২ কেজি রাউন্ড পাওয়া যায়নি; সংখ্যাগুলো আগের মতোই।</p></div>')
    n_sd_out, n_mean_out = int(NR.sd_out.sum()), int(NR.mean_out.sum())
    dates = blist([bdate(d, year=False) for d in NR.date])
    lead = (f'{bdate(pl, year=False)}-এর পর {bn(len(NR))}টি নতুন রাউন্ডে ({dates}) মোট {bn(len(newc))}টি ১২ কেজি সিলিন্ডার ওজন করা হয়েছে। '
            f'{bn(len(NR))}টির {bn(n_sd_out)}টিতে ছড়ানো (<span class="lat">SD</span>) আর {bn(n_mean_out)}টিতে গড় ২০২৪-এর নিয়ন্ত্রণ-সীমার বাইরে। '
            f'২০২৬-এর গড় অতিরিক্ত ভরাট {num(pk["Average error (g)"]["y2026"], 1, True)} থেকে {num(s6["mean"], 1, True)} গ্রাম হয়েছে; সক্ষমতা <span class="lat">Cpk</span> {num(s6["cpk"], 2)} '
            f'(মানদণ্ড {num(CPK_REF, 2)}, ২০২৪-এ ছিল {num(sb["cpk"], 2)})।')
    if R["rep_heads"]: lead += f' হেড {blist(R["rep_heads"])} প্রতিটি নতুন রাউন্ডেই +১৫০ গ্রামের বেশি ভরেছে।'
    o.append(f'<p style="font-size:17px;margin:0 0 16px">{lead}</p>')

    # 1 safety
    big = R["newbig"]; e = R["e"]
    o.append('<div class="card safe"><h3>১. নিরাপত্তা আগে · যোগ্য প্রকৌশলীর পর্যালোচনার জন্য <span class="lat" style="font-weight:500">(For review by a qualified engineer)</span></h3><ul>')
    over_new = newc[newc.error_g > TOL]
    if len(newc):
        top = newc.loc[newc.error_g.idxmax()]
        o.append(f'<li><b>নতুন রাউন্ডে +১৫০ গ্রামের বেশি ভরা ১২ কেজি সিলিন্ডার: {bn(len(over_new))}টি</b> ({bn(len(newc))}টির {num(len(over_new) / len(newc) * 100, 0)}%); '
                 f'সর্বোচ্চ {num(top.error_g, 0, True)} গ্রাম (হেড {bn(int(top["head"]))}, {bdate(top.date, year=False)})। পুরো রেকর্ডে সর্বোচ্চ {num(e.max(), 0, True)} গ্রাম; '
                 f'৫০০ গ্রামের বেশি {bn(int((e > 500).sum()))}টি, ৩০০ গ্রামের বেশি {bn(int((e > 300).sum()))}টি।</li>')
    for n, g in big.groupby("nominal"):
        g2 = g[g.error_g > TOL]; top = g.loc[g.error_g.idxmax()]
        o.append(f'<li><b>{bn(int(n))} কেজি, {bdate(g.date.max(), year=False)}: {bn(len(g))}টির {bn(len(g2))}টি +১৫০ গ্রামের বেশি</b>; সর্বোচ্চ {num(top.error_g, 0, True)} গ্রাম '
                 f'(হেড {bn(int(top["head"]))}, নামমাত্র ওজনের {num(top.error_g / (n * 10), 1)}%)। রিডিং: {", ".join(num(v, 0, True) for v in g.error_g)} গ্রাম।</li>')
    o.append('<li>সিলিন্ডারের পানিধারণ ক্ষমতা (<span class="lat">water capacity</span>) রেকর্ডে নেই, তাই ভরাট-অনুপাত (<span class="lat">filling ratio</span>) যাচাই করা যায়নি। চেক-ওয়েয়ারে বাতিলের (রিজেক্ট) কোনো রেকর্ড নেই।</li>')
    o.append('</ul><p class="note">সূত্র: <span class="lat">NFPA 58</span> (কন্টেইনার ভরাটের সীমা); <span class="lat">ISO 10691</span> (ভরাটের আগে, সময়ে ও পরে পরীক্ষা); বাংলাদেশ এলপিজি বিধিমালা ২০০৪। এটি সিদ্ধান্ত-সহায়তা, প্রকৌশল-নির্দেশনা নয়।</p></div>')

    # 2 data quality
    o.append('<div class="card dq"><h3>২. তথ্যের মান: নতুন শিটে যা পাওয়া গেছে ও যা করা হয়েছে</h3><ul>')
    ex = R["excl_new"]
    if len(ex):
        for d, g in ex.groupby("date"):
            nleft = int(((R["raw"].date == d) & (R["raw"].nominal == 12) & R["raw"].valid).sum())
            o.append(f'<li><b>{bdate(d, year=False)}, হেড {blist(g["head"].astype(int).tolist())}: বাদ দেওয়া হয়েছে।</b> খালি সিলিন্ডারের ওজন ট্যারের চেয়ে ৩০০ গ্রামের বেশি কম '
                     f'({", ".join(num(v, 0, True) for v in g.leftover_g)} গ্রাম), অর্থাৎ ট্যার ভুল পড়া বা লেখা। ওই রাউন্ডে {bn(nleft)}টি সিলিন্ডার হিসাবে আছে।</li>')
    for _, r in R["unusual"].iterrows():
        h = int(r["head"]); hist = R["c"][R["c"]["head"] == h].sort_values("round_no").error_g.tail(4).tolist()
        o.append(f'<li><b>{bdate(r.date, year=False)}, হেড {bn(h)}: {num(r.error_g, 0, True)} গ্রাম।</b> এই হেডের শেষ চারটি রিডিং {", ".join(num(v, 0, True) for v in hist)} গ্রাম; '
                 f'হয় রিডিংটি ভুল, নয়তো হেডটি কম ভরতে শুরু করেছে। মূল কাগজের রেকর্ড মিলিয়ে দেখা দরকার। নিয়ম অনুযায়ী বৈধ বলে হিসাবে রাখা হয়েছে; পূর্বাভাসে প্রতিটি রিডিং ±৩০০ গ্রামে সীমিত।'
                 + (f' এই একটি রিডিং {bdate(ld, year=False)}-এর রাউন্ডের গড় {num(slx["mean"], 1, True)} থেকে {num(sl["mean"], 1, True)} গ্রামে আর <span class="lat">SD</span> {num(slx["sd"], 1)} থেকে {num(sl["sd"], 1)} গ্রামে নিয়ে গেছে।' if r.date == ld else "") + '</li>')
    for sn in R["four_digit"]:
        o.append(f'<li>শিটের নাম <span class="lat">{esc(sn)}</span> চার অঙ্কের বছরে লেখা, অন্যগুলো দুই অঙ্কে। তারিখ ঠিকভাবে পড়া হয়েছে; একই ধরনে নাম রাখলে ভুলের ঝুঁকি কমে।</li>')
    mism = [x for x in R["new_issue_sheets"] if x[0].startswith("date cell")]
    o.append(f'<li>নতুন শিটে তারিখের ঘর আর শিটের নামের অমিল: {bn(len(mism)) if mism else "নেই"}।'
             + (f' খালি টেমপ্লেট শিট (হিসাবে নেই): <span class="lat">{esc(", ".join(R["empty_sheets"]))}</span>।' if R["empty_sheets"] else "") + '</li>')
    if R["changed_rounds"]:
        o.append(f'<li class="bad"><b>আগের {bn(len(R["changed_rounds"]))}টি রাউন্ডের সংখ্যা ওয়ার্কবুকে বদলেছে</b> ({esc(", ".join(x["round"] for x in R["changed_rounds"]))}); নতুন মান ব্যবহার করা হয়েছে।</li>')
    else:
        o.append(f'<li>আগের {bn(len(R["prev"]["rounds"]))}টি রাউন্ডের প্রতিটি সংখ্যা আগের প্রকাশিত হিসাবের সঙ্গে হুবহু মিলেছে।</li>')
    o.append(f'<li>মোট বাদ দেওয়া অসম্ভব সারি: {bn(R["n_excl"])}টি (আগে {bn(int(R["prev_excl"])) if R["prev_excl"] is not None else "—"}টি)।</li></ul></div>')

    # 3 tiles
    p26 = R["prev_r26"]; prev_in = int((~p26.mean_out & ~p26.sd_out).sum()); r26 = R["r26"]; now_in = int((~r26.mean_out & ~r26.sd_out).sum())
    pl_k = pk["Average error (g)"]["latest"]
    o.append(f'<h3 style="margin:22px 0 10px">৩. আগের প্রকাশের ({bdate(pl, year=False)} পর্যন্ত) সঙ্গে তুলনা</h3><div class="tiles">')
    o.append(tile("২০২৬-এর গড় ত্রুটি", num(s6["mean"], 1, True) + " গ্রাম", f'আগে {num(pk["Average error (g)"]["y2026"], 1, True)} · ২০২৪: {num(sb["mean"], 1, True)}', worse(s6["mean"], pk["Average error (g)"]["y2026"], "down_abs")))
    o.append(tile("ছড়ানো (<span class=lat>SD</span>), ২০২৬", num(s6["sd"], 1) + " গ্রাম", f'আগে {num(pk["Spread, standard deviation (g)"]["y2026"], 1)} · ২০২৪: {num(sb["sd"], 1)}', worse(s6["sd"], pk["Spread, standard deviation (g)"]["y2026"], "down")))
    o.append(tile("±১৫০ গ্রামের মধ্যে, ২০২৬", num(s6["within150"], 1) + "%", f'আগে {num(pk["Within ±150 g (%)"]["y2026"], 1)}% · ২০২৪: {num(sb["within150"], 1)}%', worse(s6["within150"], pk["Within ±150 g (%)"]["y2026"], "up")))
    o.append(tile("সক্ষমতা <span class=lat>Cpk</span>, ২০২৬", num(s6["cpk"], 3), f'আগে {num(pk["Cpk (±150 g)"]["y2026"], 3)} · মানদণ্ড {num(CPK_REF, 2)} · ২০২৪: {num(sb["cpk"], 2)}', worse(s6["cpk"], pk["Cpk (±150 g)"]["y2026"], "up")))
    o.append(tile(f"সর্বশেষ রাউন্ড ({bdate(ld, True, False)})", num(sl["mean"], 1, True) + " গ্রাম",
                  (f'অস্বাভাবিক রিডিং বাদে {num(slx["mean"], 1, True)} · ' if slx["n"] != sl["n"] else "") + f'আগের সর্বশেষ ({bdate(pl, True, False)}): {num(pl_k, 1, True)}', ""))
    o.append(tile("২০২৬-এর রাউন্ড, দুই সীমার ভেতরে", f"{bn(len(r26))}টির {bn(now_in)}টি", f"আগে {bn(len(p26))}টির {bn(prev_in)}টি", "bad" if now_in / max(1, len(r26)) < prev_in / max(1, len(p26)) else ""))
    o.append('</div>')
    pp = R["prev_periods"][-1]; cp = R["periods"][-1]
    o.append('<div class="card"><div class="tw"><table><tr><th class="l">সময়কাল</th><th>পরীক্ষা</th><th>গড় (গ্রাম)</th><th><span class="lat">SD</span> (গ্রাম)</th><th>±১৫০-এর মধ্যে %</th><th>+১৫০-এর বেশি %</th><th><span class="lat">Cpk</span></th></tr>')
    PB = {"Jun": "জুন", "Jan–Mar": "জানু–মার্চ", "May–Aug": "মে–আগ", "Sep–Oct": "সেপ্টে–অক্টো"}
    def pbn(p):
        out = p
        for k2, v2 in PB.items(): out = out.replace(k2, v2)
        for i2, m2 in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]): out = out.replace(m2, MONS[i2])
        return bn(out)
    for p in R["periods"][:-1]:
        o.append(f'<tr><td>{pbn(p["period"])}</td><td>{num(p["checks"], 0)}</td><td>{num(p["mean_g"], 1, True)}</td><td>{num(p["sd_g"], 1)}</td><td>{num(p["within150_pct"], 1)}</td><td>{num(p["over150_pct"], 1)}</td><td>{num(p["cpk150"], 2)}</td></tr>')
    o.append(f'<tr class="note"><td>{pbn(pp["period"])} (আগের প্রকাশ)</td><td>{num(pp["checks"], 0)}</td><td>{num(pp["mean_g"], 1, True)}</td><td>{num(pp["sd_g"], 1)}</td><td>{num(pp["within150_pct"], 1)}</td><td>{num(pp["over150_pct"], 1)}</td><td>{num(pp["cpk150"], 2)}</td></tr>')
    o.append(f'<tr class="sel"><td>{pbn(cp["period"])} (এখন)</td><td>{num(cp["checks"], 0)}</td><td>{num(cp["mean_g"], 1, True)}</td><td>{num(cp["sd_g"], 1)}</td><td>{num(cp["within150_pct"], 1)}</td><td>{num(cp["over150_pct"], 1)}</td><td>{num(cp["cpk150"], 2)}</td></tr></table></div>'
             f'<p class="note">কোনো প্ল্যান্ট-লক্ষ্যমাত্রা দেওয়া হয়নি; তুলনা ২০২৪-এর ভিত্তি আর শিল্প-মানদণ্ড <span class="lat">Cpk</span> ≥ {num(CPK_REF, 2)}-এর সঙ্গে।</p></div>')

    # 4 new rounds
    if len(NR):
        o.append('<div class="card"><h3>৪. নতুন রাউন্ড, ২০২৪-এর নিয়ন্ত্রণ-সীমার বিপরীতে</h3>')
        o.append(f'<div class="fig">{chart_rounds(R)}</div><div class="tw"><table><tr><th class="l">রাউন্ড</th><th>সিলিন্ডার</th><th>গড় (গ্রাম)</th><th><span class="lat">SD</span> (গ্রাম)</th><th>±১৫০-এর মধ্যে %</th><th>+১৫০-এর বেশি %</th><th>গড় সীমার ভেতরে?</th><th><span class="lat">SD</span> সীমার ভেতরে?</th></tr>')
        for _, r in NR.iterrows():
            yn = lambda out: '<span class="bad">না</span>' if out else '<span class="ok">হ্যাঁ</span>'
            o.append(f'<tr><td>{bdate(r.date)}</td><td>{bn(int(r.cylinders))}</td><td>{num(r.mean_g, 1, True)}</td><td>{num(r.sd_g, 1)}</td><td>{num(r.within150_pct, 1)}</td><td>{num(r.over150_pct, 1)}</td><td>{yn(r.mean_out)}</td><td>{yn(r.sd_out)}</td></tr>')
        o.append(f'</table></div><p class="note">নিয়ন্ত্রণ-সীমা জুন ২০২৪-এর ৯টি রাউন্ড থেকে: গড় {num(R["LCL"], 1, True)} থেকে {num(R["UCL"], 1, True)} গ্রাম, <span class="lat">SD</span> সর্বোচ্চ {num(R["SD_UCL"], 1)} গ্রাম (প্রতি রাউন্ডে ২৪টি সিলিন্ডার)।</p></div>')

    # 5 heads
    hd = R["heads"].copy(); hd = hd.sort_values(["fail_chance_pct", "head"], ascending=[False, True])
    hot = R["heads"][R["heads"].hot].sort_values("mean_g", ascending=False)["head"].astype(int).tolist()
    added = [h for h in hot if h not in R["prev_hot"]]; dropped = [h for h in R["prev_hot"] if h not in hot]
    o.append('<div class="card"><h3>৫. হেডভিত্তিক: নতুন রিডিং, গড় ও পরের পরীক্ষার পূর্বাভাস</h3>')
    o.append(f'<p><b>চিহ্নিত হেড</b> (সামগ্রিক গড় +{bn(FLAG)} গ্রামের বেশি এবং ৯৫% আস্থা-সীমার নিম্নপ্রান্ত শূন্যের ওপরে): <b>{bn(len(hot))}টি, হেড {blist(hot)}</b>। '
             f'আগে ছিল {bn(len(R["prev_hot"]))}টি: {blist(R["prev_hot"])}।' + (f' নতুন যোগ: হেড {blist(added)}।' if added else "") + (f' বাদ পড়েছে: হেড {blist(dropped)}।' if dropped else "") + '</p>')
    cols = list(NR["round"])
    o.append('<div class="tw"><table><tr><th class="l">হেড</th>' + "".join(f'<th>{bround(r, d)}</th>' for r, d in zip(NR["round"], NR.date)) +
             f'<th>{esc(pbn(R["recent_label"]))} গড়</th><th>সামগ্রিক গড়</th><th>৯৫% নিম্নপ্রান্ত</th><th>পূর্বাভাস</th><th>৮০% পরিসর</th><th>±১৫০-এর বাইরে যাওয়ার সম্ভাবনা</th></tr>')
    for _, h in hd.iterrows():
        hh = int(h["head"]); ph = R["per_head"].get(hh, {}); isHot = bool(h.hot); ch = h.fail_chance_pct
        o.append(f'<tr><td><b>{"● " if isHot else ""}হেড {bn(hh)}</b></td>' + "".join(heat(ph.get(r)) for r in cols) +
                 f'<td>{num(h.recent_g, 0, True)}</td><td{" class=bad" if isHot else ""}>{num(h.mean_g, 1, True)}</td><td>{num(h.ci_low_g, 1, True)}</td>'
                 f'<td>{num(h.forecast_g, 0, True)}</td><td class="note">{num(h.forecast_low_g, 0, True)} থেকে {num(h.forecast_high_g, 0, True)}</td>'
                 f'<td{" class=bad" if ch >= 50 else ""}><b>{num(ch, 0)}%</b></td></tr>')
    o.append('</table></div><p class="note">সারি সাজানো ±১৫০ গ্রামের বাইরে যাওয়ার সম্ভাবনা অনুযায়ী। ● = চিহ্নিত হেড। নীল = বেশি ভরা, কমলা = কম ভরা; রং যত গাঢ়, ত্রুটি তত বড় (৩০০ গ্রামে পূর্ণ রং)।</p></div>')

    # 6 how the previous forecast did
    if sc:
        o.append(f'<div class="card"><h3>৬. আগের পূর্বাভাস কেমন মিলেছে ({bdate(pl, year=False)}-এ করা, {bdate(sc["date"], year=False)}-এর রাউন্ডে যাচাই)</h3>')
        inr = sc["mean_lo"] <= sc["mean_act"] <= sc["mean_hi"]
        o.append('<div class="tw"><table><tr><th class="l">বিষয়</th><th>পূর্বাভাস</th><th>প্রকৃত</th><th class="l">মন্তব্য</th></tr>')
        o.append(f'<tr><td>রাউন্ডের গড় ত্রুটি</td><td>{num(sc["mean_fc"], 1, True)} গ্রাম<br><span class="note">৮০%: {num(sc["mean_lo"], 1, True)} থেকে {num(sc["mean_hi"], 1, True)}</span></td><td>{num(sc["mean_act"], 1, True)} গ্রাম</td>'
                 f'<td class="l">{num(abs(sc["mean_act"] - sc["mean_fc"]), 1)} গ্রাম পার্থক্য; ' + ("৮০% পরিসরের ভেতরে" if inr else ("পরিসরের ঠিক নিচে" if sc["mean_act"] < sc["mean_lo"] else "পরিসরের ওপরে")) + '</td></tr>')
        o.append(f'<tr><td>±১৫০ গ্রামের বাইরে হেড</td><td>প্রায় {num(sc["fail_fc"], 1)}টি</td><td>{bn(sc["fail_act"])}টি</td><td class="l">{"প্রত্যাশার চেয়ে কম" if sc["fail_act"] < sc["fail_fc"] else "প্রত্যাশার চেয়ে বেশি"}</td></tr>')
        o.append(f'<tr><td>হেডভিত্তিক গড় পরম ত্রুটি (<span class="lat">MAE</span>)</td><td>{num(sc["mae_g"], 1)} গ্রাম</td><td>—</td><td class="l">সরল নাইভ পদ্ধতিতে (আগের রিডিংই থাকবে) {num(sc["naive_mae"], 1)} গ্রাম</td></tr>')
        o.append(f'<tr><td>৮০% পরিসরের ভেতরে পড়া হেড</td><td>প্রত্যাশা ৮০%</td><td>{bn(sc["heads"])}টির {bn(sc["in_range"])}টি ({num(sc["in_range"] / sc["heads"] * 100, 0)}%)</td><td class="l"></td></tr></table></div>')
        verdict = ("রাউন্ডের গড় ভালোভাবে ধরা গেছে, কিন্তু আলাদা আলাদা হেডের ক্ষেত্রে মডেলটি সরল নাইভ পদ্ধতির চেয়ে ভালো করেনি। তাই এবার পূর্বাভাসের পদ্ধতি আবার যাচাই করে বেছে নেওয়া হয়েছে (নিচে)।"
                   if sc["mae_g"] > sc["naive_mae"] else "রাউন্ডের গড় ও হেডভিত্তিক পূর্বাভাস দুটোই সরল নাইভ পদ্ধতির চেয়ে ভালো ছিল।")
        o.append(f'<p>আগের পদ্ধতি: <span class="lat">{esc(sc["method"])}</span>। {verdict}</p></div>')

    # 7 new forecast
    M = R["models"]; sel = M[M.selected].iloc[0]
    o.append('<div class="card"><h3>৭. পরের পরীক্ষার পূর্বাভাস</h3>')
    acc_d = "<span class=lat>MAPE</span> " + num(sel.mape_net_pct, 2) + "% (নিট ওজনে) · দিক ঠিক " + num(sel.direction_hit_pct, 1) + "%"
    rng80 = "৮০% পরিসর " + num(fc["mean_lo"], 1, True) + " থেকে " + num(fc["mean_hi"], 1, True)
    o.append(f'<div class="tiles" style="margin-bottom:10px">{tile("পরের রাউন্ডের গড় ত্রুটি", num(fc["mean"], 1, True) + " গ্রাম", rng80)}'
             f'{tile("±১৫০ গ্রামের বাইরে প্রত্যাশিত হেড", "২৪টির " + num(fc["fail_heads"], 1) + "টি", "প্রতিটি হেডের সম্ভাবনার যোগফল")}'
             f'{tile("পদ্ধতির ত্রুটি (<span class=lat>RMSE</span>)", num(sel.rmse_g, 1) + " গ্রাম", acc_d)}</div>')
    o.append(f'<p><b>পদ্ধতি:</b> {METHOD_BN.get(fc["method"], esc(fc["method"]))}। সূত্র: <span class="lat">S<sub>t</sub> = α·x<sub>t</sub> + (1 − α)·S<sub>t−1</sub></span>; প্রতিটি হেডের নিজের রিডিংয়ের ওপর, '
             'নতুন রিডিং বেশি গুরুত্ব পায়। ±৩০০ গ্রামের সীমা একটি ভুল রিডিংকে পূর্বাভাস টেনে নিতে দেয় না।</p>')
    o.append(f'<p><b>প্রশিক্ষণ:</b> {bdate(R["rounds"].date.min())} – {bdate(ld)} ({num(len(R["c"]), 0)}টি পরীক্ষা, {bn(len(R["rounds"]))}টি রাউন্ড)। '
             f'<b>যাচাই:</b> শেষ ৮টি রাউন্ডে ({bdate(fc["first_test"], year=False)} – {bdate(fc["last_test"], year=False)}) প্রতিবার শুধু আগের তথ্য দিয়ে এক রাউন্ড আগের পূর্বাভাস, '
             f'মোট {bn(fc["n_test"])}টি হেড-পরীক্ষা; {bn(fc["n_methods"])}টি পদ্ধতির মধ্যে সবচেয়ে কম <span class="lat">RMSE</span>। পরিসর এসেছে যাচাইয়ের ভুলের ১০ম ও ৯০তম শতাংশক থেকে '
             f'({num(fc["q10"], 0, True)} ও {num(fc["q90"], 0, True)} গ্রাম)।</p>')
    o.append('<div class="tw"><table><tr><th class="l">পদ্ধতি</th><th><span class="lat">RMSE</span> (গ্রাম)</th><th><span class="lat">MAE</span> (গ্রাম)</th><th><span class="lat">MAPE</span> %</th><th>দিক ঠিক %</th><th>নাইভের চেয়ে ভালো %</th></tr>')
    for _, m in M.sort_values("rmse_g").iterrows():
        o.append(f'<tr{" class=sel" if m.selected else ""}><td>{METHOD_BN.get(m.model, esc(m.model))}{" ✓" if m.selected else ""}</td><td>{num(m.rmse_g, 1)}</td><td>{num(m.mae_g, 1)}</td><td>{num(m.mape_net_pct, 2)}</td><td>{num(m.direction_hit_pct, 1)}</td><td>{num(m.skill_vs_naive_pct, 1, True)}</td></tr>')
    o.append(f'</table></div><p class="note">সতর্কতা: সেরা পদ্ধতিও নাইভের চেয়ে মাত্র {num(sel.skill_vs_naive_pct, 1)}% ভালো; হেডভিত্তিক পূর্বাভাসকে অগ্রাধিকার ঠিক করার নির্দেশক হিসেবে দেখুন, নিশ্চিত ফল হিসেবে নয়। '
             '২৫ অক্টোবরের নিউরাল নেটওয়ার্ক (<span class="lat">LSTM</span>) এই হালনাগাদে নতুন করে প্রশিক্ষিত হয়নি; তার ফল স্লাইড ও লিখিত রিপোর্টে আছে।</p></div>')

    # 8 actions
    first = hd[hd.fail_chance_pct >= 50]
    o.append('<div class="card"><h3>৮. করণীয় (সুপারিশ)</h3><ol style="margin:0;padding-left:1.3em">')
    over_first = first[first.forecast_g > 0]["head"].astype(int).tolist(); under_first = first[first.forecast_g < 0]["head"].astype(int).tolist()
    if over_first: o.append(f'<li>হেড {blist(over_first)} আগে ক্যালিব্রেট করুন: পরের পরীক্ষায় +১৫০ গ্রাম পেরোনোর সম্ভাবনা ৫০%-এর বেশি।</li>')
    for _, r in R["unusual"].iterrows(): o.append(f'<li>হেড {bn(int(r["head"]))}: {bdate(r.date, year=False)}-এর কাগজের রেকর্ড মিলিয়ে দেখুন; রিডিং সঠিক হলে কম ভরার কারণ খুঁজুন।</li>')
    if under_first and not len(R["unusual"]): o.append(f'<li>হেড {blist(under_first)}: কম ভরার ঝুঁকি; পরের রাউন্ডে আলাদা করে দেখুন।</li>')
    for n, g in big.groupby("nominal"):
        if g.error_g.max() > 300: o.append(f'<li>{bn(int(n))} কেজির {num(g.error_g.max(), 0, True)} গ্রাম অতিরিক্ত ভরাট যোগ্য প্রকৌশলী দিয়ে পর্যালোচনা করুন।</li>')
    o.append('<li>চেক-ওয়েয়ারে প্রতিটি বাতিল (রিজেক্ট) সিলিন্ডারের লগ রাখুন, যাতে নমুনার বাইরের সিলিন্ডারও ধরা পড়ে।</li></ol></div>')

    # 9 what is unchanged
    gv = next((s for s in R["summary"] if s["item"].startswith("LPG over-delivered")), None)
    o.append('<div class="card"><h3>৯. যা এই হালনাগাদে বদলায়নি</h3><ul>')
    if gv: o.append(f'<li>অতিরিক্ত ভরাটে বিনামূল্যে যাওয়া এলপিজি: <b>{num(gv["value"], 1)} <span class="lat">MT</span></b> (৯৫% পরিসর {num(gv["low"], 1)}–{num(gv["high"], 1)}), ১ মার্চ – ২৫ অক্টোবর ২০২৬। '
                    'এর পরের উৎপাদনের তথ্য পাওয়া যায়নি, তাই হিসাব বাড়ানো হয়নি; নতুন উৎপাদন রিপোর্ট পেলে হালনাগাদ হবে।</li>')
    o.append('<li>স্লাইড ও লিখিত রিপোর্ট ২৫ অক্টোবর পর্যন্ত। ড্যাশবোর্ডের সব চার্ট ও টেবিল নতুন তথ্যে হালনাগাদ; শুধু নিউরাল নেটওয়ার্কের কারণ-বিশ্লেষণ ও <span class="lat">autoencoder/Isolation Forest</span> অংশ ২৫ অক্টোবর পর্যন্ত।</li></ul></div>')

    if updates:
        o.append('<details class="card"><summary>হালনাগাদের ইতিহাস</summary><ul>' + "".join(f'<li>{bdate(u["date"])}: {esc(u["text"]).translate(BN)}</li>' for u in reversed(updates)) + '</ul></details>')
    o.append('<p class="note">প্রতিটি সংখ্যা ওজন-পরীক্ষার কাঁচা ওজন থেকে নতুন করে হিসাব করা: ত্রুটি = (ভরাটের পরের ওজন − ট্যার − ১২ কেজি) × ১০০০। কোনো সংখ্যা অনুমান করে বসানো হয়নি।</p>')
    o.append('</div>')
    return "\n".join(o)

# ---------------------------------------------------------------- write
def setu(page, key, val):
    page2, n = re.subn(rf'(<(?:span|small) data-u="{key}">)(.*?)(</(?:span|small)>)', lambda m: m.group(1) + val + m.group(3), page, flags=re.S)
    assert n >= 1, key
    return page2

def write_all(page, R, a):
    D = R["datasets"]; ld = R["last_day"]; fc = R["fc"]; L = pd.Timestamp(ld)
    hub = json.load(open(HUBDATA, encoding="utf8"))
    updates = hub.setdefault("updates", [{"date": "2026-11-03", "text": "ওয়েবসাইট প্রকাশ: ছয়টি রিপোর্ট, তথ্য 25 অক্টোবর 2026 পর্যন্ত"}])
    hot = R["heads"][R["heads"].hot].sort_values("mean_g", ascending=False)["head"].astype(int).tolist()
    NR = R["new_rounds"]
    text = (f"ওজন-পরীক্ষার {len(NR)}টি নতুন রাউন্ড ({', '.join(ldate(d) for d in NR.date)}; {len(R['newc'])}টি সিলিন্ডার)। "
            f"2026-এর গড় অতিরিক্ত ভরাট {R['s6']['mean']:+.0f} গ্রাম; চিহ্নিত হেড {len(hot)}টি; পরের রাউন্ডের পূর্বাভাস {fc['mean']:+.0f} গ্রাম।") if len(NR) else "নতুন রাউন্ড নেই; হিসাব পুনর্যাচাই।"
    entry = {"date": a.date, "text": text, "through": ld, "key": "cal-" + ld, "open": "cal", "view": "update"}
    updates[:] = [u for u in updates if u.get("key") != entry["key"] and not (u.get("through") == ld and "key" not in u)] + [entry]
    updates.sort(key=lambda u: (u["date"], u.get("key", "")))

    data_json = json.dumps(D, ensure_ascii=False, default=float).replace("</", "<\\/")
    page = re.sub(r'(<script id="dash-data" type="application/json">)(.*?)(</script>)', lambda m: m.group(1) + data_json + m.group(3), page, count=1, flags=re.S)
    dl = f"{L.day} {L:%B}"; ds = f"{L.day} {L:%b}"
    page = setu(page, "day_long", dl); page = setu(page, "day_short", ds); page = setu(page, "nsheets", str(R["n_sheets"]))
    page = setu(page, "recent_label", R["recent_label"])
    page = setu(page, "fc_method", f"{esc(fc['method'])}, best of {fc['n_methods']} methods in the backtest")
    page = setu(page, "fc_when", f"next check after {dl}")
    page = setu(page, "bt_text", f"One round ahead on the last 8 rounds ({edate(fc['first_test'], '%-d %b')} – {edate(fc['last_test'])}), refitted each time; data {edate(R['rounds'].date.min())} – {edate(ld)}. "
                                 "MAPE is measured on net content. The 25 Oct neural network (LSTM) was not refitted in this update; its results are in the slides and written report.")
    page = setu(page, "up_tab", bdate(ld, True, False)); page = setu(page, "dash_tab", f"to {ds}")
    panel = render(R, a, [u for u in updates if u.get("key") != entry["key"] and u.get("open", "cal") == "cal"])
    page = re.sub(r"<!--UPDATE-->.*?<!--/UPDATE-->", lambda m: "<!--UPDATE-->" + panel + "<!--/UPDATE-->", page, count=1, flags=re.S)
    open(CAL, "w", encoding="utf8").write(page)

    # hub figures
    PBN = {"2024 Jun": "২০২৪ জুন", "2026 Jan–Mar": "২০২৬ জানু–মার্চ", "2026 May–Aug": "২০২৬ মে–আগ"}
    def pb(p):
        if p in PBN: return PBN[p]
        out = p
        for i2, m2 in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]): out = out.replace(m2, MONS[i2])
        return bn(out)
    hub["cal"] = [{"p": p["period"], "pb": pb(p["period"]), "m": round(p["mean_g"]), "cpk": round(p["cpk150"], 2)} for p in R["periods"]]
    hub["heads"] = [{"h": int(h["head"]), "m": round(h.mean_g, 1), "lo": round(h.ci_low_g, 3), "hot": bool(h.hot)} for _, h in R["heads"].sort_values("head").iterrows()]
    sel = R["models"][R["models"].selected].iloc[0]
    short = "EWMA" if fc["method"].startswith("EWMA") else fc["method"].split(" (")[0]
    hub.setdefault("tokens", {}).update({
        "asof": f"তথ্য 25 অক্টোবর 2026 পর্যন্ত · ওজন-পরীক্ষা {ldate(ld)} {L.year} পর্যন্ত",
        "updated": f"{ldate(a.date)} {pd.Timestamp(a.date).year}",
        "cal_mean26": f"{R['s6']['mean']:+.0f}", "cal_last": ldate(ld), "cal_max": f"{R['e'].max():+.0f}", "cal_n": f"{len(R['c']):,}",
        "cal_cpk": f"{R['sb']['cpk']:.2f} → {R['s6']['cpk']:.2f}", "cal_hot_n": str(len(hot)), "cal_hot_list": ", ".join(map(str, hot)),
        "cal_fc": f"{fc['mean']:+.0f}", "cal_fc_method": short, "cal_fc_mape": f"{sel.mape_net_pct:.2f}",
    })
    json.dump(hub, open(HUBDATA, "w", encoding="utf8"), ensure_ascii=False, indent=1)

    os.makedirs(f"{HERE}/history", exist_ok=True)
    hist = {"update_date": a.date, "data_through": ld, "previous_through": R["prev_last"], "new_rounds": NR[["round", "cylinders", "mean_g", "sd_g", "mean_out", "sd_out"]].to_dict("records"),
            "y2026": R["s6"], "latest": R["sl"], "latest_without_unusual": R["slx"], "hot_heads": hot, "previous_hot_heads": R["prev_hot"],
            "forecast": fc, "previous_forecast_score": R["score"], "excluded_rows": R["n_excl"], "changed_rounds": R["changed_rounds"]}
    json.dump(hist, open(f"{HERE}/history/{a.date}.json", "w", encoding="utf8"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: hist[k] for k in ("data_through", "previous_through", "hot_heads", "excluded_rows")}, ensure_ascii=False, default=float))
    print("forecast", round(fc["mean"], 1), round(fc["mean_lo"], 1), round(fc["mean_hi"], 1), fc["method"])

if __name__ == "__main__":
    main()
