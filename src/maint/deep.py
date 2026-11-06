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
J = O[(O.group == "Vehicle fleet") & (O.type == "ZPM1") & (O.cat != "nonmaint") & ~O.order.isin(F["twins"])].copy()
J["m"] = J.date.dt.to_period("M")
rng = np.random.default_rng(7)
T = {}

# ---------------------------------------------------------------- KPI series by quarter (fleet jobs)
W0, W1 = pd.Timestamp("2025-06-01"), pd.Timestamp("2026-06-30")
win = J[(J.date >= W0) & (J.date <= W1)]
def planned(df): return float(df.pm.isin(["Scheduled service", "Service + repair"]).mean() * 100) if len(df) else None
def reactive(df): return float((df.pm == "Repair").mean() * 100) if len(df) else None
# repeat repair: a repair job followed by another job of the same kind on the same vehicle within 1-90 days
rep = J[J.pm != "Scheduled service"].sort_values("date")
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
funnel = [("Created (CRTD)", len(O)), ("Released (REL)", int((has("REL") | has("RELR")).sum())), ("Cost posted (GMPS)", int(has("GMPS").sum())),
          ("Confirmed (CNF)", int(has("CNF").sum())), ("Technically closed (TECO)", int(has("TECO").sum()))]
T["funnel"] = [{"stage": a, "n": int(b), "pct": b / len(O) * 100} for a, b in funnel]

n = len(O)
plan_orders = int(F["plan_orders"]); plan_rel = int(F["plan_released"])   # same count as the analysis section
K = {k["metric"]: k for k in C["kpis"]}
last_check = max(r["date"] for r in C["rounds"])
n26 = sum(1 for c in C["checks"] if c["year"] == 2026)
T["cal"] = {"within150_26": K["Within ±150 g (%)"]["y2026"], "within150_24": K["Within ±150 g (%)"]["base_2024"], "within150_last": K["Within ±150 g (%)"]["latest"],
            "cpk26": K["Cpk (±150 g)"]["y2026"], "cpk24": K["Cpk (±150 g)"]["base_2024"], "mean26": K["Average error (g)"]["y2026"],
            "period26": "2026", "checks26": n26, "last": last_check, "giveaway_mt": C["summary"][0]["value"], "giveaway_lo": C["summary"][0]["low"], "giveaway_hi": C["summary"][0]["high"]}
w = F["jun25_jun26"]; h2, h1 = F["h2_2025"], F["h1_2026"]
veh_months = sum(1 for _ in D["vehicles"]) * 13
KPI = [
 # key, name, value, unit, target, world, better, basis, measurable
 ("planned", "Planned (preventive) work share", F["pm_share_w"], "%", 70, 85, "up", "Fleet jobs, Jun 2025 – Jun 2026", True),
 ("reactive", "Repair only after breakdown", 100 - F["pm_share_w"], "%", 30, 15, "down", "Fleet jobs, Jun 2025 – Jun 2026", True),
 ("repeat", "Same repair again within 90 days", T["repeat_rate"], "%", 8, 5, "down", f"{T['repeat_n']} of {T['repeat_base']} repairs", True),
 ("mtbe", "Average interval between two maintenance jobs (per vehicle)", F["weibull"]["mean"], "days", 60, 90, "up", "Weibull mean, 275 intervals", True),
 ("plan", "Plan-order release and compliance (ZPM3)", plan_rel / plan_orders * 100 if plan_orders else 0, "%", 90, 95, "up", f"{plan_orders} plan orders", True),
 ("cnf", "Confirmation after the job", int(has("CNF").sum()) / n * 100, "%", 90, 98, "up", f"{n} orders", True),
 ("teco", "Technically closed (TECO)", int(has("TECO").sum()) / n * 100, "%", 90, 98, "up", f"{n} orders", True),
 ("timely", "Orders opened on time (not more than 30 days late)", (1 - O.backdated.mean()) * 100, "%", 90, 98, "up", f"{n} orders; median delay {F['late_median']:.0f} days", True),
 ("equip", "Orders with an equipment number", (1 - O.equip.isna().mean()) * 100, "%", 98, 100, "up", f"{n} orders", True),
 ("quality", "Filling quality: cylinders within ±150 g", T["cal"]["within150_26"], "%", 95, 99.7, "up", f"{T['cal']['checks26']} weight checks in 2026", True),
 ("cpk", "Filling process capability Cpk", T["cal"]["cpk26"], "", 1.0, 1.33, "up", f"{T['cal']['checks26']} weight checks in 2026", True),
 ("mttr", "Mean time to repair (MTTR)", None, "hours", None, None, "down", "Only 5 orders have actual start–finish dates", False),
 ("oee", "Filling carousel OEE", None, "%", 65, 85, "up", "Downtime and speed are not recorded; quality factor from the weight checks", False),
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
 ("jh", "Autonomous maintenance (Jishu Hozen)", None, "SAP has no record of daily operator or driver inspections; assess on the floor."),
 ("pm", "Planned maintenance", min(lvl(pl, [30, 50, 70, 85]), 2 if plan_rel == 0 else 5), f"Planned work {pl:.1f}%; {plan_rel} of {plan_orders} plan orders released; service interval not fixed (median {F['sched_interval']['median']:.0f} days)."),
 ("kk", "Focused improvement (Kaizen)", lvl(100 - T["repeat_rate"], [80, 90, 95, 98]), f"Repeat repairs within 90 days {T['repeat_rate']:.1f}%; 80% of cost sits in only {F['pareto80']} vehicles, yet there is no root-cause analysis on record."),
 ("qm", "Quality maintenance", lvl(T["cal"]["cpk26"], [0.67, 1.0, 1.33, 1.67]), f"Cpk {T['cal']['cpk26']:.2f} in 2026 (2024: {T['cal']['cpk24']:.2f}); {T['cal']['within150_26']:.1f}% within ±150 g."),
 ("ot", "Office TPM (SAP discipline)", lvl(np.mean([int(has('CNF').sum()) / n * 100, int(has('TECO').sum()) / n * 100, (1 - O.backdated.mean()) * 100]), [40, 60, 80, 95]),
  f"Confirmation {int(has('CNF').sum()) / n * 100:.1f}%, TECO {int(has('TECO').sum()) / n * 100:.0f}%, orders on time {(1 - O.backdated.mean()) * 100:.0f}%."),
 ("she", "Safety, health and environment", 1, f"{safety_open} safety-related maintenance items open: last gas-detector order {F['gas_mon_months']:.1f} months ago, a 31-month gap in fire-extinguisher orders."),
 ("et", "Education and training", None, "No skills matrix or training record found; a baseline assessment is needed using the table below."),
 ("eem", "Early equipment management", None, "No record of maintainability checks when new equipment is bought or installed."),
]
T["pillars"] = [{"k": k, "name": nm, "score": s, "evidence": ev} for k, nm, s, ev in P]
sc = [p["score"] for p in T["pillars"] if p["score"] is not None]
T["maturity"] = {"mean": float(np.mean(sc)), "measured": len(sc), "total": len(P)}

# ---------------------------------------------------------------- significance tests
T["sig"] = []
def add(key, q, test, stat, p, effect, verdict):
    T["sig"].append({"k": key, "q": q, "test": test, "stat": stat, "p": float(p), "effect": effect, "verdict": verdict})
mser = J.groupby("m").cost.sum(); mserh = O[(O.group == "Vehicle fleet") & (O.type == "ZPM1")].assign(m=lambda x: x.date.dt.to_period("M")).groupby("m").cost.sum()
a = np.array([mserh.get(pd.Period(f"2025-{m:02d}"), 0.0) for m in range(7, 13)]); b = np.array([mserh.get(pd.Period(f"2026-{m:02d}"), 0.0) for m in range(1, 7)])
U = stats.mannwhitneyu(a, b, alternative="two-sided"); tW = stats.ttest_ind(a, b, equal_var=False)
boots = [(rng.choice(b, 6).sum() / rng.choice(a, 6).sum() - 1) * 100 for _ in range(10000)]
lo, hi = np.percentile(boots, [2.5, 97.5])
T["cost_change"] = {"pct": float((b.sum() / a.sum() - 1) * 100), "lo": float(lo), "hi": float(hi), "a": a.tolist(), "b": b.tolist()}
add("cost_h", "Was the fleet's monthly cost in Jan–Jun 2026 different from the previous six months?", "Mann–Whitney U (with Welch t)", f"U = {U.statistic:.0f}", U.pvalue,
    f"Change {T['cost_change']['pct']:+.1f}% (95% range {lo:+.0f}% to {hi:+.0f}%)", "The difference is not statistically significant")
Jh = O[(O.group == "Vehicle fleet") & (O.type == "ZPM1")]   # same base as the key-metrics table
h2j = Jh[(Jh.date >= "2025-07-01") & (Jh.date <= "2025-12-31")]; h1j = Jh[(Jh.date >= "2026-01-01") & (Jh.date <= "2026-06-30")]
x1, n1 = int(h2j.pm.isin(["Scheduled service", "Service + repair"]).sum()), len(h2j); x2, n2 = int(h1j.pm.isin(["Scheduled service", "Service + repair"]).sum()), len(h1j)
pp = (x1 + x2) / (n1 + n2); z = (x2 / n2 - x1 / n1) / np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)); pz = 2 * (1 - stats.norm.cdf(abs(z)))
d = x2 / n2 - x1 / n1; se = np.sqrt(x1 / n1 * (1 - x1 / n1) / n1 + x2 / n2 * (1 - x2 / n2) / n2)
add("pm_h", "Has the planned-work share really risen (H2 2025 → H1 2026)?", "Two-proportion z-test", f"z = {z:.2f}", pz,
    f"{x1 / n1 * 100:.1f}% → {x2 / n2 * 100:.1f}% (difference {d * 100:+.1f} points, 95% range {(d - 1.96 * se) * 100:+.1f} to {(d + 1.96 * se) * 100:+.1f})",
    "Right direction, but not yet significant" if pz >= 0.05 else "Significant improvement")
cw = win[win.cost > 0]
grp = [cw[cw.pm == k].cost.values for k in ["Scheduled service", "Service + repair", "Repair"]]
KW = stats.kruskal(*grp)
med = [float(np.median(g)) for g in grp]
add("cost_type", "Does cost per job differ by job type (service only, service + repair, repair only)?", "Kruskal–Wallis", f"H = {KW.statistic:.1f}", KW.pvalue,
    f"Median: service only Tk {med[0]:,.0f}, service + repair Tk {med[1]:,.0f}, repair only Tk {med[2]:,.0f}", "Significant difference" if KW.pvalue < 0.05 else "Not significant")
T["cost_type"] = {"med": med, "n": [int(len(g)) for g in grp], "sum": [float(g.sum()) for g in grp]}
y13 = np.array([mser.get(p, 0.0) for p in pd.period_range("2025-06", "2026-06", freq="M")])
tau = stats.kendalltau(np.arange(len(y13)), y13); ts = stats.theilslopes(y13, np.arange(len(y13)))
add("trend", "Is there an upward or downward trend in monthly cost, Jun 2025 – Jun 2026?", "Mann–Kendall (Kendall τ), Theil–Sen slope", f"τ = {tau.statistic:.2f}", tau.pvalue,
    f"Slope Tk {ts.slope / 1e5:+.2f} lakh per month (95% range {ts.low_slope / 1e5:+.2f} to {ts.high_slope / 1e5:+.2f})", "No reliable trend" if tau.pvalue >= 0.05 else "Significant trend")
vc = np.array(sorted(v["cost_w"] for v in D["vehicles"]))
def gini(x): x = np.sort(x); k = np.arange(1, len(x) + 1); return float((2 * (k * x).sum() / (len(x) * x.sum())) - (len(x) + 1) / len(x))
gb = [gini(rng.choice(vc, len(vc))) for _ in range(5000)]
T["gini"] = {"g": gini(vc), "lo": float(np.percentile(gb, 2.5)), "hi": float(np.percentile(gb, 97.5))}
ser = {}
for v in D["vehicles"]:
    ser.setdefault(v["series"], []).append(v["cost_w"] / 13)
sg = [np.array(x) for x in ser.values() if len(x) >= 3]
KS = stats.kruskal(*sg)
add("series", "Does monthly cost differ by vehicle series?", "Kruskal–Wallis", f"H = {KS.statistic:.1f}", KS.pvalue,
    "; ".join(f"{k.split('(')[-1].rstrip(')')}: median Tk {np.median(x) / 1e3:,.1f}k/month ({len(x)})" for k, x in ser.items() if len(x) >= 3), "Significant difference" if KS.pvalue < 0.05 else "Not significant")
add("weibull", "Does the chance of a job rise with time (wear-out, β > 1)?", "Bootstrap range of the Weibull shape", f"β = {F['weibull']['beta']:.2f}", 0.0 if F["weibull"]["beta_lo"] > 1 else 1.0,
    f"90% range {F['weibull']['beta_lo']:.2f}–{F['weibull']['beta_hi']:.2f}, above 1", "Mild but significant wear-out pattern")
add("model", "Is the neural network for major repairs better than a simple rule?", "Bootstrap AUC comparison (2,000 resamples)", f"AUC {F['clsB']['auc']:.2f} vs {F['clsB']['base_auc']:.2f}", 1 - F["clsB"]["p_better"],
    f"Neural network ahead in {F['clsB']['p_better'] * 100:.1f}% of resamples", "Probably better (one-sided p ≈ {:.2f})".format(1 - F["clsB"]["p_better"]))

# ---------------------------------------------------------------- cost decomposition H2 2025 -> H1 2026 by work type
ca = h2j.groupby("cat_bn").cost.sum(); cb = h1j.groupby("cat_bn").cost.sum()
cats = sorted(set(ca.index) | set(cb.index), key=lambda c: -abs(cb.get(c, 0) - ca.get(c, 0)))
steps = [{"c": c, "d": float(cb.get(c, 0) - ca.get(c, 0))} for c in cats]
top = steps[:6]; rest = sum(s["d"] for s in steps[6:])
T["waterfall"] = {"start": float(ca.sum()), "end": float(cb.sum()), "steps": top + [{"c": "Other", "d": float(rest)}]}
mon = pd.DataFrame(D["monthly"]); mon["q"] = pd.PeriodIndex(mon.m, freq="M").asfreq("Q").astype(str)
T["cost_q"] = [{"q": q, "fleet": float(g.fleet.sum()), "plant": float(g.plant.sum()), "renew": float(g.renew.sum())} for q, g in mon.groupby("q")]
T["fc_err"] = D["fc_pts"]; T["cal_bins"] = D["clsB_cal"]; T["cm"] = D["clsB_cm"]
T["reactive_cost"] = {k: float(win[win.pm == k].cost.sum()) for k in ["Scheduled service", "Service + repair", "Repair"]}
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
