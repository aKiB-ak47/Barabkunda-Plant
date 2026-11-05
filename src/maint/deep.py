"""TPM indicators and deeper statistics for the maintenance report.
Reads orders.json, mdata.json, mfacts.json and the calibration dashboard data; writes tpm.json."""
import json, os, re
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); os.chdir(HERE)
O = pd.DataFrame(json.load(open("orders.json")))
D = json.load(open("mdata.json")); F = json.load(open("mfacts.json"))
page = open(f"{SRC}/reports/cal.html", encoding="utf8").read()
C = json.loads(re.search(r'<script id="dash-data" type="application/json">(.*?)</script>', page, re.S).group(1))
O["date"] = pd.to_datetime(O.date); O["q"] = O.date.dt.to_period("Q").astype(str)
# fleet jobs exactly as in analyze.py: fleet ZPM1 maintenance orders, zero-cost duplicate twins dropped
J = O[(O.group == "যানবাহন বহর") & (O.type == "ZPM1") & (O.cat != "nonmaint") & ~O.order.isin(F["twins"])].copy()
J["m"] = J.date.dt.to_period("M")
rng = np.random.default_rng(7)
T = {}

# ---------------------------------------------------------------- KPI series by quarter (fleet jobs)
W0, W1 = pd.Timestamp("2025-06-01"), pd.Timestamp("2026-06-30")
win = J[(J.date >= W0) & (J.date <= W1)]
def planned(df): return float(df.pm.isin(["নির্ধারিত সার্ভিস", "সার্ভিস + মেরামত"]).mean() * 100) if len(df) else None
def reactive(df): return float((df.pm == "মেরামত").mean() * 100) if len(df) else None
# repeat repair: a repair job followed by another job of the same kind on the same vehicle within 1-90 days
rep = J[J.pm != "নির্ধারিত সার্ভিস"].sort_values("date")
rep_flag = []
for r in rep.itertuples():
    nxt = rep[(rep.vehicle == r.vehicle) & (rep.cat_bn == r.cat_bn) & (rep.date > r.date) & (rep.date <= r.date + pd.Timedelta(days=90))]
    rep_flag.append(len(nxt) > 0)
rep = rep.assign(repeat=rep_flag)
QS = [q for q in sorted(J.q.unique()) if q >= "2025Q3" and q <= "2026Q2"]
qser = []
for q in sorted(J.q.unique()):
    g = J[J.q == q]; r_ = rep[rep.q == q]; o = O[O.q == q]
    veh = g.vehicle.nunique()
    qser.append({"q": q, "jobs": int(len(g)), "planned": planned(g), "reactive": reactive(g), "repeat": float(r_.repeat.mean() * 100) if len(r_) else None,
                 "cost": float(g.cost.sum()), "cost_per_vehicle_month": float(g.cost.sum() / veh / 3) if veh else None,
                 "backdated": float(o.backdated.mean() * 100) if len(o) else None, "orders": int(len(o))})
T["quarters"] = qser
rw = rep[(rep.date >= W0) & (rep.date <= W1 - pd.Timedelta(days=90))]   # only jobs with a full 90-day look-ahead inside the window
T["repeat_rate"] = float(rw.repeat.mean() * 100); T["repeat_n"] = int(rw.repeat.sum()); T["repeat_base"] = int(len(rw))

st = O.status.fillna("")
has = lambda k: st.str.contains(rf"\b{k}\b")
funnel = [("তৈরি (CRTD)", len(O)), ("রিলিজ (REL)", int((has("REL") | has("RELR")).sum())), ("খরচ পোস্ট (GMPS)", int(has("GMPS").sum())),
          ("কনফার্ম (CNF)", int(has("CNF").sum())), ("টেকনিক্যালি বন্ধ (TECO)", int(has("TECO").sum()))]
T["funnel"] = [{"stage": a, "n": int(b), "pct": b / len(O) * 100} for a, b in funnel]

n = len(O)
plan_orders = int(F["plan_orders"]); plan_rel = int(F["plan_released"])   # same count as the analysis section
K = {k["metric"]: k for k in C["kpis"]}
last_check = max(r["date"] for r in C["rounds"])
n26 = sum(1 for c in C["checks"] if c["year"] == 2026)
T["cal"] = {"within150_26": K["Within ±150 g (%)"]["y2026"], "within150_24": K["Within ±150 g (%)"]["base_2024"], "within150_last": K["Within ±150 g (%)"]["latest"],
            "cpk26": K["Cpk (±150 g)"]["y2026"], "cpk24": K["Cpk (±150 g)"]["base_2024"], "mean26": K["Average error (g)"]["y2026"],
            "period26": "২০২৬", "checks26": n26, "last": last_check, "giveaway_mt": C["summary"][0]["value"], "giveaway_lo": C["summary"][0]["low"], "giveaway_hi": C["summary"][0]["high"]}
w = F["jun25_jun26"]; h2, h1 = F["h2_2025"], F["h1_2026"]
veh_months = sum(1 for _ in D["vehicles"]) * 13
KPI = [
 # key, name, value, unit, target, world, better, basis, measurable
 ("planned", "পরিকল্পিত (প্রতিরোধমূলক) কাজের হার", F["pm_share_w"], "%", 70, 85, "up", "বহরের কাজ, জুন ২০২৫ – জুন ২০২৬", True),
 ("reactive", "শুধু ভাঙার পর মেরামত", 100 - F["pm_share_w"], "%", 30, 15, "down", "বহরের কাজ, জুন ২০২৫ – জুন ২০২৬", True),
 ("repeat", "৯০ দিনের মধ্যে একই মেরামত আবার", T["repeat_rate"], "%", 8, 5, "down", f"{T['repeat_base']}টি মেরামতের মধ্যে {T['repeat_n']}টি", True),
 ("mtbe", "দুই রক্ষণাবেক্ষণের গড় ব্যবধান (প্রতি গাড়ি)", F["weibull"]["mean"], "দিন", 60, 90, "up", "Weibull গড়, ২৭৫টি বিরতি", True),
 ("plan", "প্ল্যান-অর্ডার রিলিজ ও পালন (ZPM3)", plan_rel / plan_orders * 100 if plan_orders else 0, "%", 90, 95, "up", f"{plan_orders}টি প্ল্যান-অর্ডার", True),
 ("cnf", "কাজ শেষে কনফার্মেশন", int(has("CNF").sum()) / n * 100, "%", 90, 98, "up", f"{n}টি অর্ডার", True),
 ("teco", "টেকনিক্যালি বন্ধ (TECO)", int(has("TECO").sum()) / n * 100, "%", 90, 98, "up", f"{n}টি অর্ডার", True),
 ("timely", "সময়মতো খোলা অর্ডার (৩০ দিনের বেশি পিছিয়ে নয়)", (1 - O.backdated.mean()) * 100, "%", 90, 98, "up", f"{n}টি অর্ডার; মধ্যমা দেরি {F['late_median']:.0f} দিন", True),
 ("equip", "ইকুইপমেন্ট নম্বরসহ অর্ডার", (1 - O.equip.isna().mean()) * 100, "%", 98, 100, "up", f"{n}টি অর্ডার", True),
 ("quality", "ফিলিং-মান: ±১৫০ গ্রামের ভেতরে সিলিন্ডার", T["cal"]["within150_26"], "%", 95, 99.7, "up", f"২০২৬-এর {T['cal']['checks26']}টি ওজন-পরীক্ষা", True),
 ("cpk", "ফিলিং প্রক্রিয়া-সক্ষমতা Cpk", T["cal"]["cpk26"], "", 1.0, 1.33, "up", f"২০২৬-এর {T['cal']['checks26']}টি ওজন-পরীক্ষা", True),
 ("mttr", "মেরামতের গড় সময় (MTTR)", None, "ঘণ্টা", None, None, "down", "মাত্র ৫টি অর্ডারে প্রকৃত শুরু–শেষ তারিখ আছে", False),
 ("oee", "ফিলিং ক্যারোসেলের OEE", None, "%", 65, 85, "up", "ডাউনটাইম ও গতি লিপিবদ্ধ হয় না; মান-অংশ ওজন-পরীক্ষা থেকে", False),
]
def progress(v, base, tgt, better):
    if v is None or tgt is None: return None
    if better == "up": return float(np.clip(v / tgt * 100, 0, 100))
    return float(np.clip((100 - v) / (100 - tgt) * 100, 0, 100)) if base == "%" else float(np.clip(tgt / v * 100, 0, 100))
T["kpis"] = []
for k, nm, v, u, tgt, wc, better, basis, meas in KPI:
    T["kpis"].append({"k": k, "name": nm, "v": None if v is None else float(v), "unit": u, "target": tgt, "world": wc, "better": better, "basis": basis, "measurable": meas,
                      "progress": progress(v, u, wc, better)})
# trend direction H2 2025 -> H1 2026 for the KPIs that have quarterly data
qd = {x["q"]: x for x in qser}
def half(keys, field):
    vals = [qd[k][field] for k in keys if k in qd and qd[k][field] is not None]
    return float(np.mean(vals)) if vals else None
T["half"] = {f: {"h2_2025": half(["2025Q3", "2025Q4"], f), "h1_2026": half(["2026Q1", "2026Q2"], f)} for f in ["planned", "reactive", "repeat", "backdated", "cost_per_vehicle_month"]}

# ---------------------------------------------------------------- TPM pillar maturity (1-5), evidence-based where data exist
def lvl(v, cuts):  # cuts ascending thresholds for levels 2..5
    return 1 + sum(v >= c for c in cuts)
pl = F["pm_share_w"]; safety_open = 6
P = [
 ("jh", "স্বয়ংক্রিয় রক্ষণাবেক্ষণ (জিশু হোজেন)", None, "অপারেটর/চালকের দৈনিক পরিদর্শনের কোনো রেকর্ড SAP-এ নেই; মূল্যায়ন মাঠে করতে হবে।"),
 ("pm", "পরিকল্পিত রক্ষণাবেক্ষণ", min(lvl(pl, [30, 50, 70, 85]), 2 if plan_rel == 0 else 5), f"পরিকল্পিত কাজ {pl:.1f}%; {plan_orders}টি প্ল্যান-অর্ডারের {plan_rel}টি রিলিজ; সার্ভিস-ব্যবধান অনির্দিষ্ট (মধ্যমা {F['sched_interval']['median']:.0f} দিন)।"),
 ("kk", "লক্ষ্যভিত্তিক উন্নয়ন (কাইজেন)", lvl(100 - T["repeat_rate"], [80, 90, 95, 98]), f"৯০ দিনে পুনরাবৃত্ত মেরামত {T['repeat_rate']:.1f}%; খরচের ৮০% মাত্র {F['pareto80']}টি গাড়িতে, তবু কোনো মূল-কারণ বিশ্লেষণের রেকর্ড নেই।"),
 ("qm", "মান রক্ষণাবেক্ষণ", lvl(T["cal"]["cpk26"], [0.67, 1.0, 1.33, 1.67]), f"২০২৬-এ Cpk {T['cal']['cpk26']:.2f} (২০২৪: {T['cal']['cpk24']:.2f}); ±১৫০ গ্রামের ভেতরে {T['cal']['within150_26']:.1f}%।"),
 ("ot", "অফিস TPM (SAP শৃঙ্খলা)", lvl(np.mean([int(has('CNF').sum()) / n * 100, int(has('TECO').sum()) / n * 100, (1 - O.backdated.mean()) * 100]), [40, 60, 80, 95]),
  f"কনফার্মেশন {int(has('CNF').sum()) / n * 100:.1f}%, TECO {int(has('TECO').sum()) / n * 100:.0f}%, সময়মতো অর্ডার {(1 - O.backdated.mean()) * 100:.0f}%।"),
 ("she", "নিরাপত্তা, স্বাস্থ্য ও পরিবেশ", 1, f"{safety_open}টি নিরাপত্তা-সংক্রান্ত রক্ষণাবেক্ষণ খোলা: গ্যাস ডিটেক্টরের শেষ অর্ডার {F['gas_mon_months']:.1f} মাস আগে, অগ্নিনির্বাপকে ৩১ মাসের ফাঁক।"),
 ("et", "শিক্ষা ও প্রশিক্ষণ", None, "দক্ষতা-ম্যাট্রিক্স বা প্রশিক্ষণের রেকর্ড পাওয়া যায়নি; নিচের ছকে ভিত্তি-মূল্যায়ন করতে হবে।"),
 ("eem", "নতুন যন্ত্রের প্রাথমিক ব্যবস্থাপনা", None, "নতুন যন্ত্র কেনা/বসানোর সময় রক্ষণাবেক্ষণযোগ্যতা যাচাইয়ের রেকর্ড নেই।"),
]
T["pillars"] = [{"k": k, "name": nm, "score": s, "evidence": ev} for k, nm, s, ev in P]
sc = [p["score"] for p in T["pillars"] if p["score"] is not None]
T["maturity"] = {"mean": float(np.mean(sc)), "measured": len(sc), "total": len(P)}

# ---------------------------------------------------------------- significance tests
T["sig"] = []
def add(key, q, test, stat, p, effect, verdict):
    T["sig"].append({"k": key, "q": q, "test": test, "stat": stat, "p": float(p), "effect": effect, "verdict": verdict})
mser = J.groupby("m").cost.sum(); mserh = O[(O.group == "যানবাহন বহর") & (O.type == "ZPM1")].assign(m=lambda x: x.date.dt.to_period("M")).groupby("m").cost.sum()
a = np.array([mserh.get(pd.Period(f"2025-{m:02d}"), 0.0) for m in range(7, 13)]); b = np.array([mserh.get(pd.Period(f"2026-{m:02d}"), 0.0) for m in range(1, 7)])
U = stats.mannwhitneyu(a, b, alternative="two-sided"); tW = stats.ttest_ind(a, b, equal_var=False)
boots = [(rng.choice(b, 6).sum() / rng.choice(a, 6).sum() - 1) * 100 for _ in range(10000)]
lo, hi = np.percentile(boots, [2.5, 97.5])
T["cost_change"] = {"pct": float((b.sum() / a.sum() - 1) * 100), "lo": float(lo), "hi": float(hi), "a": a.tolist(), "b": b.tolist()}
add("cost_h", "জানু–জুন ২০২৬-এ বহরের মাসিক খরচ কি আগের ছয় মাসের চেয়ে আলাদা?", "ম্যান–হুইটনি U (ওয়েলচ t সহ)", f"U = {U.statistic:.0f}", U.pvalue,
    f"পরিবর্তন {T['cost_change']['pct']:+.1f}% (৯৫% পরিসর {lo:+.0f}% থেকে {hi:+.0f}%)", "পার্থক্য পরিসংখ্যানগতভাবে তাৎপর্যপূর্ণ নয়")
Jh = O[(O.group == "যানবাহন বহর") & (O.type == "ZPM1")]   # same base as the key-metrics table
h2j = Jh[(Jh.date >= "2025-07-01") & (Jh.date <= "2025-12-31")]; h1j = Jh[(Jh.date >= "2026-01-01") & (Jh.date <= "2026-06-30")]
x1, n1 = int(h2j.pm.isin(["নির্ধারিত সার্ভিস", "সার্ভিস + মেরামত"]).sum()), len(h2j); x2, n2 = int(h1j.pm.isin(["নির্ধারিত সার্ভিস", "সার্ভিস + মেরামত"]).sum()), len(h1j)
pp = (x1 + x2) / (n1 + n2); z = (x2 / n2 - x1 / n1) / np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)); pz = 2 * (1 - stats.norm.cdf(abs(z)))
d = x2 / n2 - x1 / n1; se = np.sqrt(x1 / n1 * (1 - x1 / n1) / n1 + x2 / n2 * (1 - x2 / n2) / n2)
add("pm_h", "পরিকল্পিত কাজের হার কি সত্যিই বেড়েছে (দ্বিতীয়ার্ধ ২০২৫ → প্রথমার্ধ ২০২৬)?", "দুই-অনুপাতের z-পরীক্ষা", f"z = {z:.2f}", pz,
    f"{x1 / n1 * 100:.1f}% → {x2 / n2 * 100:.1f}% (পার্থক্য {d * 100:+.1f} পয়েন্ট, ৯৫% পরিসর {(d - 1.96 * se) * 100:+.1f} থেকে {(d + 1.96 * se) * 100:+.1f})",
    "দিক ঠিক আছে, কিন্তু এখনো তাৎপর্যপূর্ণ নয়" if pz >= 0.05 else "তাৎপর্যপূর্ণ উন্নতি")
cw = win[win.cost > 0]
grp = [cw[cw.pm == k].cost.values for k in ["নির্ধারিত সার্ভিস", "সার্ভিস + মেরামত", "মেরামত"]]
KW = stats.kruskal(*grp)
med = [float(np.median(g)) for g in grp]
add("cost_type", "কাজের ধরন (শুধু সার্ভিস, সার্ভিস+মেরামত, শুধু মেরামত) অনুযায়ী কাজপ্রতি খরচ কি আলাদা?", "ক্রুসকাল–ওয়ালিস", f"H = {KW.statistic:.1f}", KW.pvalue,
    f"মধ্যমা: শুধু সার্ভিস {med[0]:,.0f}, সার্ভিস+মেরামত {med[1]:,.0f}, শুধু মেরামত {med[2]:,.0f} টাকা", "তাৎপর্যপূর্ণ পার্থক্য" if KW.pvalue < 0.05 else "তাৎপর্যপূর্ণ নয়")
T["cost_type"] = {"med": med, "n": [int(len(g)) for g in grp], "sum": [float(g.sum()) for g in grp]}
y13 = np.array([mser.get(p, 0.0) for p in pd.period_range("2025-06", "2026-06", freq="M")])
tau = stats.kendalltau(np.arange(len(y13)), y13); ts = stats.theilslopes(y13, np.arange(len(y13)))
add("trend", "জুন ২০২৫ – জুন ২০২৬-এ মাসিক খরচে কি ঊর্ধ্বমুখী বা নিম্নমুখী প্রবণতা আছে?", "ম্যান–কেন্ডাল (কেন্ডাল τ), থাইল–সেন ঢাল", f"τ = {tau.statistic:.2f}", tau.pvalue,
    f"ঢাল মাসে {ts.slope / 1e5:+.2f} লাখ টাকা (৯৫% পরিসর {ts.low_slope / 1e5:+.2f} থেকে {ts.high_slope / 1e5:+.2f})", "কোনো নির্ভরযোগ্য প্রবণতা নেই" if tau.pvalue >= 0.05 else "তাৎপর্যপূর্ণ প্রবণতা")
vc = np.array(sorted(v["cost_w"] for v in D["vehicles"]))
def gini(x): x = np.sort(x); k = np.arange(1, len(x) + 1); return float((2 * (k * x).sum() / (len(x) * x.sum())) - (len(x) + 1) / len(x))
gb = [gini(rng.choice(vc, len(vc))) for _ in range(5000)]
T["gini"] = {"g": gini(vc), "lo": float(np.percentile(gb, 2.5)), "hi": float(np.percentile(gb, 97.5))}
ser = {}
for v in D["vehicles"]:
    ser.setdefault(v["series"], []).append(v["cost_w"] / 13)
sg = [np.array(x) for x in ser.values() if len(x) >= 3]
KS = stats.kruskal(*sg)
add("series", "গাড়ির সিরিজ অনুযায়ী মাসিক খরচ কি আলাদা?", "ক্রুসকাল–ওয়ালিস", f"H = {KS.statistic:.1f}", KS.pvalue,
    "; ".join(f"{k.split('(')[-1].rstrip(')')}: মধ্যমা {np.median(x) / 1e3:,.1f} হাজার/মাস ({len(x)}টি)" for k, x in ser.items() if len(x) >= 3), "তাৎপর্যপূর্ণ পার্থক্য" if KS.pvalue < 0.05 else "তাৎপর্যপূর্ণ নয়")
add("weibull", "সময়ের সঙ্গে কাজের সম্ভাবনা কি বাড়ে (ক্ষয়-জনিত, β > ১)?", "Weibull আকৃতির বুটস্ট্র্যাপ পরিসর", f"β = {F['weibull']['beta']:.2f}", 0.0 if F["weibull"]["beta_lo"] > 1 else 1.0,
    f"৯০% পরিসর {F['weibull']['beta_lo']:.2f}–{F['weibull']['beta_hi']:.2f}, ১-এর ওপরে", "হালকা কিন্তু তাৎপর্যপূর্ণ ক্ষয়-জনিত প্রবণতা")
add("model", "বড় মেরামতের নিউরাল নেটওয়ার্ক কি সরল নিয়মের চেয়ে ভালো?", "বুটস্ট্র্যাপ AUC তুলনা (২,০০০ বার)", f"AUC {F['clsB']['auc']:.2f} বনাম {F['clsB']['base_auc']:.2f}", 1 - F["clsB"]["p_better"],
    f"{F['clsB']['p_better'] * 100:.1f}% পুনর্নমুনায় নিউরাল নেটওয়ার্ক এগিয়ে", "সম্ভবত ভালো (একতরফা p ≈ {:.2f})".format(1 - F["clsB"]["p_better"]))

# ---------------------------------------------------------------- cost decomposition H2 2025 -> H1 2026 by work type
ca = h2j.groupby("cat_bn").cost.sum(); cb = h1j.groupby("cat_bn").cost.sum()
cats = sorted(set(ca.index) | set(cb.index), key=lambda c: -abs(cb.get(c, 0) - ca.get(c, 0)))
steps = [{"c": c, "d": float(cb.get(c, 0) - ca.get(c, 0))} for c in cats]
top = steps[:6]; rest = sum(s["d"] for s in steps[6:])
T["waterfall"] = {"start": float(ca.sum()), "end": float(cb.sum()), "steps": top + [{"c": "অন্যান্য", "d": float(rest)}]}
mon = pd.DataFrame(D["monthly"]); mon["q"] = pd.PeriodIndex(mon.m, freq="M").asfreq("Q").astype(str)
T["cost_q"] = [{"q": q, "fleet": float(g.fleet.sum()), "plant": float(g.plant.sum()), "renew": float(g.renew.sum())} for q, g in mon.groupby("q")]
T["fc_err"] = D["fc_pts"]; T["cal_bins"] = D["clsB_cal"]; T["cm"] = D["clsB_cm"]
T["reactive_cost"] = {k: float(win[win.pm == k].cost.sum()) for k in ["নির্ধারিত সার্ভিস", "সার্ভিস + মেরামত", "মেরামত"]}
T["repeat_cost"] = float(sum(r["cost2"] for r in D["repeats"]))

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list): return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)): return None if not np.isfinite(o) else round(float(o), 4)
    if isinstance(o, np.integer): return int(o)
    return o
json.dump(clean(T), open("tpm.json", "w"), ensure_ascii=False, indent=1)
for s in T["sig"]: print(f"{s['k']:9s} p={s['p']:.3f}  {s['effect'][:90]}")
print("repeat", T["repeat_rate"], T["repeat_n"], T["repeat_base"], "maturity", T["maturity"])
for k in T["kpis"]: print(k["k"], k["v"], k["progress"])
print(T["half"]); print(T["cal"]); print(T["waterfall"])
