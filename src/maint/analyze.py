"""Maintenance analytics on the cleaned SAP PM order list (orders.json).
Writes mdata.json (everything the report page draws) and mfacts.json (every number quoted in the text)."""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import json, math, re, warnings
import numpy as np, pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, GradientBoostingRegressor, IsolationForest
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, brier_score_loss, r2_score, silhouette_score, adjusted_rand_score
from sklearn.model_selection import KFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
warnings.filterwarnings("ignore")
TODAY = pd.Timestamp(os.environ.get("AS_OF", "2026-11-06"))   # date the SAP record runs to (not the date of the last order)
F, D = {}, {}
df = pd.DataFrame(json.load(open("orders.json")))
df["date"] = pd.to_datetime(df.date)
df["m"] = df.date.dt.to_period("M")
# zero-cost twins of a duplicated order are dropped from job counts (the costed copy stays)
pairs = df[df.dup_of.notna()][["order", "dup_of"]].astype(int).values.tolist()
cost_of = df.set_index("order").cost
TWINS = sorted({o for pr in pairs for o in pr if cost_of[o] == 0})
fleet = df[(df.group == "Vehicle fleet") & (df.type == "ZPM1") & (df.cat != "nonmaint") & ~df.order.isin(TWINS)].copy()
plant = df[df.group.isin(["Utilities (compressor, pump, power)", "Filling and handling", "Buildings, office and site", "Fire and safety", "Weighing (weighbridge)", "Marine and jetty"])].copy()
r1 = lambda x: None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 1)

# ======================= 1. profile and data quality
F["n"] = int(len(df)); F["types"] = df.type.value_counts().to_dict()
F["date_min"], F["date_max"] = str(df.date.min().date()), str(df.date.max().date()); F["as_of"] = str(TODAY.date())
F["order_min"], F["order_max"] = int(df.order.min()), int(df.order.max())
F["cost_total"] = float(df.cost.sum()); F["n_cost"] = int((df.cost > 0).sum())
F["gmps_n"] = int(df.has_gmps.sum()); F["gmps_with_cost"] = int((df.has_gmps & (df.cost > 0)).sum()); F["cost_without_gmps"] = int(((df.cost > 0) & ~df.has_gmps).sum())
F["teco"] = int(df.teco.sum()); F["cnf"] = int(df.cnf.sum()); F["actual_dates"] = int(df.a_start.notna().sum()); F["crtd"] = int(df.crtd.sum())
F["no_equip"] = int(df.equip.isna().sum()); F["trunc"] = int(df.trunc.sum()); F["backdated"] = int(df.backdated.sum())
F["late_median"] = float(df.late_days.median()); F["mismatch"] = df[df.mismatch][["order", "desc", "equip_vehicle", "vehicle"]].to_dict("records")
F["dups"] = df[df.dup_of.notna()][["order", "dup_of", "desc", "cost"]].to_dict("records"); F["twins"] = TWINS
F["lowconf"] = df[df.lowconf][["order", "desc", "cost"]].to_dict("records")
zpm1 = df[df.type == "ZPM1"]
mc = zpm1.groupby("m").size()
gap = [str(p) for p in pd.period_range("2024-07", "2025-05", freq="M") if mc.get(p, 0) == 0]
F["gap_months"] = gap; F["gap_orders"] = int(zpm1[(zpm1.m >= pd.Period("2024-07")) & (zpm1.m <= pd.Period("2025-05"))].shape[0])
F["zero_cost_zpm1_2022_23"] = [int(((zpm1.year <= 2023) & (zpm1.cost == 0)).sum()), int((zpm1.year <= 2023).sum())]
recent = zpm1[(zpm1.date >= pd.Timestamp("2026-07-01")) & (zpm1.date <= TODAY)]
F["recent_jul_oct"] = {"orders": int(len(recent)), "fleet_orders": int((recent.group == "Vehicle fleet").sum()), "cost": float(recent.cost.sum())}
# silent period: no order dated after the last one, although the record runs to TODAY
_last = df.date.max(); _d26 = df[(df.date >= pd.Timestamp("2026-01-01")) & (df.date <= pd.Timestamp("2026-09-30"))]
_rate = len(_d26) / 273.0; _days = int((TODAY - _last).days); _f26 = _d26[(_d26.group == "Vehicle fleet") & (_d26.type == "ZPM1")]
_dts = np.sort(df[(df.date >= pd.Timestamp("2026-01-01")) & (df.date <= _last)].date.unique()); _gaps = np.diff(_dts).astype("timedelta64[D]").astype(int)
F["silent"] = {"last": str(_last.date()), "days": _days, "rate_month": _rate * 30.44, "expected": _rate * _days, "p0": float(np.exp(-_rate * _days)),
               "fleet_expected": len(_f26) / 273.0 * _days, "max_gap_2026": int(_gaps.max()) if len(_gaps) else 0, "late_median": float(df[df.backdated].late_days.median()) if "late_days" in df else None}
F["h1_2026_monthly_orders"] = float(zpm1[(zpm1.m >= pd.Period("2026-01")) & (zpm1.m <= pd.Period("2026-06"))].shape[0] / 6)
# registration spelling variants per vehicle (written forms in the description)
var = {}
for r in df.itertuples():
    if isinstance(r.vehicle, str):
        for w in r.desc_regs or []:
            w = re.sub(r"\s+", " ", w.strip())
            var.setdefault(r.vehicle, {}); var[r.vehicle][w] = var[r.vehicle].get(w, 0) + 1
F["reg_variants_total"] = int(sum(len(v) for v in var.values())); F["reg_vehicles"] = len(var)
D["reg_variants"] = sorted([{"v": k, "forms": sorted(v.items(), key=lambda x: -x[1])} for k, v in var.items()], key=lambda x: -len(x["forms"]))
WORDS = {"schedule": r"\b(sched\w*|schd\.?|shedule|schudule|schedual|sche\.|sch\.)", "diaphragm": r"diaph\w*", "absorber": r"absor\w*",
         "clutch": r"\b(clutch|clautch|claustch)\b", "nozzle": r"\bnozz\w*", "wiring": r"\b(wireing|wrieing|wiring)\b", "maintenance": r"\b(maint\w*|maintenace|maintence|naintenance|maintenan)\b",
         "replace": r"\b(replace|repalace)\b", "extinguisher": r"\b(extingu\w*|extengu\w*)\b", "diesel": r"\b(diesel|dizzel)\b", "chassis": r"\b(chassis|chessis)\b", "servicing": r"\b(servic\w*|servercing)\b"}
sp = []
for k, pat in WORDS.items():
    forms = {}
    for d in df.desc:
        for mm in re.finditer(pat, d, re.I): forms[mm.group(0)] = forms.get(mm.group(0), 0) + 1
    sp.append({"word": k, "forms": sorted(forms.items(), key=lambda x: -x[1])})
D["spell"] = sp; F["spell_forms"] = int(sum(len(s["forms"]) for s in sp))

# ======================= 2. cost history
D["monthly"] = []
for p in pd.period_range(df.m.min(), TODAY.to_period("M"), freq="M"):
    s = df[df.m == p]
    D["monthly"].append({"m": str(p), "n": int(len(s)), "cost": float(s.cost.sum()),
                         "fleet": float(s[s.group == "Vehicle fleet"].cost.sum()), "plant": float(s[s.group.isin(plant.group.unique())].cost.sum()),
                         "renew": float(s[s.group == "Renewals and licences"].cost.sum()), "fleet_n": int(((s.group == "Vehicle fleet") & (s.type == "ZPM1")).sum())})
yr = df.groupby("year").agg(n=("order", "size"), cost=("cost", "sum")).reset_index()
D["yearly"] = yr.to_dict("records")
def per(a, b):
    s = df[(df.date >= a) & (df.date <= b)]; f = s[(s.group == "Vehicle fleet") & (s.type == "ZPM1")]
    fc = f[f.cost > 0]
    return {"cost": float(s.cost.sum()), "fleet_cost": float(f.cost.sum()), "plant_cost": float(s[s.group.isin(plant.group.unique())].cost.sum()), "fleet_jobs": int(len(f)),
            "cost_per_job": float(fc.cost.mean()) if len(fc) else None, "sched_share": float(f.pm.isin(["Scheduled service", "Service + repair"]).mean() * 100) if len(f) else None,
            "vehicles": int(f.vehicle.nunique()), "top_cat": f.groupby("cat_bn").cost.sum().sort_values(ascending=False).head(3).round(0).to_dict()}
F["h2_2025"] = per("2025-07-01", "2025-12-31"); F["h1_2026"] = per("2026-01-01", "2026-06-30")
F["jun25_jun26"] = per("2025-06-01", "2026-06-30"); F["mar24"] = per("2024-03-01", "2024-03-31")
F["group_cost"] = df.groupby("group").cost.sum().sort_values(ascending=False).to_dict()
F["top_orders"] = df.sort_values("cost", ascending=False).head(15)[["order", "date", "desc", "vehicle", "group", "cost"]].assign(date=lambda x: x.date.dt.strftime("%Y-%m-%d")).to_dict("records")

# ======================= 3. fleet: vehicles, categories, intervals
W0, W1 = pd.Timestamp("2025-06-01"), pd.Timestamp("2026-06-30")   # window with consistent recording
fw = fleet[(fleet.date >= W0) & (fleet.date <= W1) & fleet.vehicle.notna()]
V = []
for v, g in fleet[fleet.vehicle.notna()].groupby("vehicle"):
    gw = fw[fw.vehicle == v]
    days = sorted(gw.date.dt.normalize().unique()); iv = np.diff(days).astype("timedelta64[D]").astype(int) if len(days) > 1 else np.array([])
    ren = df[(df.vehicle == v) & (df.group == "Renewals and licences")]
    V.append({"v": v, "series": g.series.iloc[0], "jobs": int(len(g)), "jobs_w": int(len(gw)), "cost": float(g.cost.sum()), "cost_w": float(gw.cost.sum()),
              "corr_w": int((gw.pm == "Repair").sum()), "sched_w": int(gw.pm.isin(["Scheduled service", "Service + repair"]).sum()),
              "mtbe": r1(iv.mean()) if len(iv) else None, "last": str(g.date.max().date()), "top": gw.groupby("cat_bn").cost.sum().idxmax() if len(gw) and gw.cost.sum() > 0 else None,
              "max_job": float(g.cost.max()), "renew_last": str(ren.date.max().date()) if len(ren) else None})
V = sorted(V, key=lambda x: -x["cost_w"]); D["vehicles"] = V
tot = sum(x["cost_w"] for x in V); cum = 0; n80 = None
for i, x in enumerate(V):
    cum += x["cost_w"]; x["cum"] = cum / tot * 100 if tot else 0
    if n80 is None and x["cum"] >= 80: n80 = i + 1
F["fleet_w_cost"] = tot; F["pareto80"] = n80; F["fleet_vehicles_w"] = int(sum(1 for x in V if x["jobs_w"] > 0))
F["top3_vehicles"] = [(x["v"], x["cost_w"]) for x in V[:3]]
cat = fw.groupby("cat_bn").agg(jobs=("order", "size"), cost=("cost", "sum"), med=("cost", "median"), mx=("cost", "max")).sort_values("cost", ascending=False).reset_index()
D["cats"] = cat.to_dict("records")
ser = fw.groupby("series").agg(vehicles=("vehicle", "nunique"), jobs=("order", "size"), cost=("cost", "sum")).reset_index()
ser["cost_per_vehicle_month"] = ser.cost / ser.vehicles / 13
D["series"] = ser.sort_values("cost_per_vehicle_month", ascending=False).to_dict("records")
D["fleet_jobs"] = fleet[fleet.vehicle.notna()][["order", "date", "vehicle", "desc", "cat_bn", "pm", "cost"]].assign(date=lambda x: x.date.dt.strftime("%Y-%m-%d")).to_dict("records")
# repeat repairs: same vehicle, same main system (not routine service), within 90 days
rep = []
for v, g in fw[~fw.cat.isin(["sched", "service", "other"])].sort_values("date").groupby("vehicle"):
    for c, gg in g.groupby("cat_bn"):
        dd = gg.date.tolist(); oo = gg.order.tolist(); cs = gg.cost.tolist()
        for i in range(1, len(dd)):
            if 0 < (dd[i] - dd[i - 1]).days <= 90: rep.append({"v": v, "cat": c, "first": str(dd[i - 1].date()), "second": str(dd[i].date()), "days": int((dd[i] - dd[i - 1]).days), "cost2": float(cs[i]), "o1": int(oo[i - 1]), "o2": int(oo[i])})
D["repeats"] = sorted(rep, key=lambda x: x["days"]); F["repeats_n"] = len(rep); F["repeats_cost"] = float(sum(x["cost2"] for x in rep))
# Weibull on time between maintenance days, pooled over vehicles
ivs = []
for v, g in fw.groupby("vehicle"):
    days = sorted(g.date.dt.normalize().unique())
    ivs += [int(x) for x in np.diff(days).astype("timedelta64[D]").astype(int) if x > 0]
ivs = np.array(ivs, float)
c, loc, scale = stats.weibull_min.fit(ivs, floc=0)
rng = np.random.default_rng(7); bs = []
for _ in range(400):
    s = rng.choice(ivs, len(ivs)); cc_, _, ss_ = stats.weibull_min.fit(s, floc=0); bs.append((cc_, ss_))
bs = np.array(bs)
ks = stats.kstest(ivs, "weibull_min", args=(c, 0, scale))
F["weibull"] = {"n": int(len(ivs)), "beta": float(c), "beta_lo": float(np.percentile(bs[:, 0], 5)), "beta_hi": float(np.percentile(bs[:, 0], 95)), "eta": float(scale),
                "eta_lo": float(np.percentile(bs[:, 1], 5)), "eta_hi": float(np.percentile(bs[:, 1], 95)), "mean": float(scale * math.gamma(1 + 1 / c)), "median_obs": float(np.median(ivs)),
                "ks_p": float(ks.pvalue), "p30": float(stats.weibull_min.cdf(30, c, 0, scale))}
D["weibull"] = {"hist": np.histogram(ivs, bins=np.arange(0, ivs.max() + 15, 15))[0].tolist(), "edges": np.arange(0, ivs.max() + 15, 15).tolist(),
                "curve": [[float(x), float(stats.weibull_min.pdf(x, c, 0, scale) * len(ivs) * 15)] for x in np.linspace(1, ivs.max(), 80)]}

# ======================= 4. preventive vs corrective
q = fleet[fleet.date >= pd.Timestamp("2024-01-01")].copy(); q["q"] = q.date.dt.to_period("Q").astype(str)
pmq = q.groupby(["q", "pm"]).size().unstack(fill_value=0)
D["pm_q"] = [{"q": i, **{k: int(v) for k, v in r.items()}} for i, r in pmq.iterrows()]
F["pm_share_w"] = float(fw.pm.isin(["Scheduled service", "Service + repair"]).mean() * 100); F["pm_only_share_w"] = float((fw.pm == "Scheduled service").mean() * 100)
F["pm_cost_share_w"] = float(fw[fw.pm.isin(["Scheduled service", "Service + repair"])].cost.sum() / fw.cost.sum() * 100)
plan = df[(df.type == "ZPM3") | df.status.str.contains("MSPT")]
F["plan_orders"] = int(len(plan)); F["plan_released"] = int((~plan.status.str.startswith("CRTD")).sum())
F["plan_list"] = plan[["order", "type", "date", "desc", "status"]].assign(date=lambda x: x.date.dt.strftime("%Y-%m-%d")).to_dict("records")
# observed interval between scheduled services per vehicle (median), to propose a plan interval
sint = []
for v, g in fw[fw.pm.isin(["Scheduled service", "Service + repair"])].groupby("vehicle"):
    dd = sorted(g.date.unique())
    if len(dd) >= 2: sint += list(np.diff(dd).astype("timedelta64[D]").astype(int))
sint = np.array([x for x in sint if x > 0])
F["sched_interval"] = {"n": int(len(sint)), "median": float(np.median(sint)), "p25": float(np.percentile(sint, 25)), "p75": float(np.percentile(sint, 75))}

# ======================= 5. safety and compliance evidence in SAP
def last(pat, g=None):
    s = df[df.desc.str.contains(pat, case=False, regex=True)]
    return s.sort_values("date")[["order", "date", "desc", "status", "cost"]].assign(date=lambda x: x.date.dt.strftime("%Y-%m-%d")).to_dict("records")
F["fire_ext"] = last(r"extingu|extengu"); F["gas_mon"] = last(r"gas monitor"); F["fire_sys"] = last(r"fire monitor|fire fighting")
F["weigh"] = last(r"weigh|bridge scale|bsti"); F["compressor"] = last(r"air com|air compressor 0|air compressor -")
ext_d = pd.to_datetime([x["date"] for x in F["fire_ext"]]); F["fire_ext_gaps_m"] = [round(x / 30.44, 1) for x in np.diff(ext_d.values).astype("timedelta64[D]").astype(int)]
F["gas_mon_months"] = round((TODAY - pd.Timestamp(F["gas_mon"][-1]["date"])).days / 30.44, 1)

# ======================= 6. renewals calendar
ren = df[df.group == "Renewals and licences"].copy()
def doc(d):
    dl = d.lower()
    for k, lab in [("explosive", "Explosives licence"), ("insurance", "Insurance"), ("tax token", "Tax token"), ("fitness", "Fitness"), ("fire license", "Fire licence"),
                   ("factory", "Factory licence"), ("trade", "Trade licence"), ("environmental clearance", "Environmental clearance"), ("jetty environment", "Jetty environmental licence"),
                   ("erc", "ERC licence"), ("bsti", "BSTI"), ("import registration", "Import registration"), ("bpc", "BPC renewal fee"), ("biwta", "BIWTA NOC"),
                   ("ministry", "Energy Ministry permission"), ("isps", "ISPS Code certificate"), ("chamber", "Chamber membership"), ("holding tax", "Holding tax")]:
        if k in dl: return lab
    return "Vehicle papers"
ren["doc"] = ren.desc.map(doc); ren["subject"] = ren.vehicle.fillna("Plant 1201")
# insurance / tax token / fitness orders carry the vehicle only in the equipment number
ren.loc[ren.vehicle.isna() & ren.equip_vehicle.notna(), "subject"] = ren.equip_vehicle
cal = []
for (s, d), g in ren.groupby(["subject", "doc"]):
    lastd = g.date.max(); nxt = lastd + pd.DateOffset(years=1)
    status = "Expired — no new order in SAP" if nxt < TODAY else ("Within 120 days" if nxt <= TODAY + pd.Timedelta(days=120) else "Later")
    cal.append({"subject": s, "doc": d, "orders": int(len(g)), "last": str(lastd.date()), "next": str(nxt.date()), "status": status, "plant": s == "Plant 1201"})
cal = sorted(cal, key=lambda x: x["next"]); D["renewals"] = cal
F["ren_overdue"] = sum(1 for x in cal if x["status"].startswith("Expired")); F["ren_soon"] = sum(1 for x in cal if x["status"].startswith("Within"))
F["plant_lic_last"] = max(x["last"] for x in cal if x["plant"]); F["plant_lic_n"] = sum(1 for x in cal if x["plant"])

# ======================= 7. forecasting: fleet monthly cost
months = pd.period_range("2025-06", "2026-06", freq="M")
y = np.array([fleet[fleet.m == p].cost.sum() for p in months], float)
def f_naive(h): return h[-1]
def f_mean(h): return h.mean()
def f_ma3(h): return h[-3:].mean()
def f_ewma(a):
    def f(h):
        s = h[0]
        for x in h[1:]: s = a * x + (1 - a) * s
        return s
    return f
def f_trend(h): t = np.arange(len(h)); b = np.polyfit(t, h, 1); return b[0] * len(h) + b[1]
def f_mlp(h):
    if len(h) < 6: return h.mean()
    X = np.array([h[i - 3:i] for i in range(3, len(h))]); Y = h[3:]
    sc = h.mean(); m = MLPRegressor(hidden_layer_sizes=(6,), alpha=1.0, max_iter=5000, random_state=0).fit(X / sc, Y / sc)
    return float(m.predict((h[-3:] / sc).reshape(1, -1))[0] * sc)
METH = {"Same as last month (naive)": f_naive, "Average to date": f_mean, "3-month moving average": f_ma3, "EWMA α 0.3": f_ewma(0.3), "EWMA α 0.5": f_ewma(0.5),
        "Linear trend (regression)": f_trend, "Neural network (MLP, 3 lags)": f_mlp}
bt = []; res = {}; pts = {}
for name, fn in METH.items():
    e = []
    for k in range(7, len(y)):   # predict Jan..Jun 2026 one month ahead, using only earlier months
        e.append((y[k], fn(y[:k])))
    e = np.array(e); err = e[:, 0] - e[:, 1]; res[name] = err; pts[name] = e
    bt.append({"model": name, "rmse": float(np.sqrt((err ** 2).mean())), "mae": float(np.abs(err).mean()), "mape": float((np.abs(err) / e[:, 0]).mean() * 100)})
bt = sorted(bt, key=lambda x: x["rmse"]); best = bt[0]["model"]
naive_rmse = next(b["rmse"] for b in bt if b["model"].startswith("Same as last month"))
for b in bt: b["skill"] = (1 - b["rmse"] / naive_rmse) * 100; b["sel"] = b["model"] == best
D["fc_bt"] = bt
D["fc_pts"] = [{"m": str(months[k]), "y": float(pts[best][i, 0]), "p": float(pts[best][i, 1]), "naive": float(pts["Same as last month (naive)"][i, 1])} for i, k in enumerate(range(7, len(y)))]
lvl = METH[best](y); sd = float(np.std(res[best], ddof=1))
fc_months = pd.period_range("2026-07", "2027-04", freq="M")
D["fc"] = {"hist": [{"m": str(p), "v": float(v)} for p, v in zip(months, y)],
           "recorded_after": [{"m": str(p), "v": float(fleet[fleet.m == p].cost.sum())} for p in pd.period_range("2026-07", TODAY.to_period("M"), freq="M")],
           "fwd": [{"m": str(p), "v": float(lvl), "lo": float(max(0, lvl - 1.2816 * sd)), "hi": float(lvl + 1.2816 * sd)} for p in fc_months]}
rec_jul_oct = sum(x["v"] for x in D["fc"]["recorded_after"]); el = (TODAY - pd.Timestamp("2026-07-01")).days / 30.44   # months elapsed since 1 July
F["fc"] = {"method": best, "level": float(lvl), "lo": float(max(0, lvl - 1.2816 * sd)), "hi": float(lvl + 1.2816 * sd), "rmse": bt[0]["rmse"], "mape": bt[0]["mape"],
           "train": "Jun 2025 – Jun 2026", "test": "Jan – Jun 2026", "recorded_jul_oct": rec_jul_oct, "expected_jul_oct": float(lvl * el), "elapsed_months": float(el),
           "unbooked_jul_oct": float(lvl * el - rec_jul_oct), "unbooked_lo": float(max(0, lvl * el - 1.2816 * sd * np.sqrt(el) - rec_jul_oct)), "unbooked_hi": float(lvl * el + 1.2816 * sd * np.sqrt(el) - rec_jul_oct), "resid_sd": sd, "monthly_mean": float(y.mean()), "monthly_sd": float(y.std(ddof=1)), "cv": float(y.std(ddof=1) / y.mean() * 100)}

# ======================= 8. vehicle-month panel: predictive models
vehs = sorted(fw.vehicle.unique())
mons = pd.period_range("2025-06", "2026-07", freq="M")
def panel(th, h):
    rows = []
    for v in vehs:
        g = fleet[fleet.vehicle == v]
        for p in mons:
            fut = g[(g.m >= p) & (g.m < p + h)]; past = g[(g.m < p) & (g.date >= W0)]; past3 = g[(g.m < p) & (g.m >= p - 3)]
            nm = max(1, (p - pd.Period("2025-06")).n); lastj = past.m.max() if len(past) else None
            rows.append({"v": v, "m": p, "y": int((fut.cost >= th).any()) if th > 0 else int(len(fut) > 0), "rate": len(past) / nm, "crate": float(np.log1p(past.cost.sum() / nm)),
                         "jobs3": int(len(past3)), "cost3": float(np.log1p(past3.cost.sum())), "since": float((p - lastj).n) if lastj is not None else 12.0,
                         "big6": int(((g.m < p) & (g.m >= p - 6) & (g.cost >= 50000)).sum()), "s61": int("-61-" in v)})
    return pd.DataFrame(rows)
FE = ["rate", "crate", "jobs3", "cost3", "since", "big6", "s61"]
NAMES = {"rate": "Average monthly job rate (since Jun 2025)", "crate": "Average monthly cost", "jobs3": "Jobs in last 3 months", "cost3": "Cost in last 3 months",
         "since": "Months since last job", "big6": "Major repair in 6 months (≥ Tk 50k)", "s61": "Dha-61 series vehicle or not"}
class MLPEns:
    def __init__(self, n=10): self.n = n
    def fit(self, X, y):
        self.m = [make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(8,), alpha=1.0, max_iter=5000, random_state=s)).fit(X, y) for s in range(self.n)]; return self
    def predict_proba(self, X):
        p = np.mean([m.predict_proba(X)[:, 1] for m in self.m], axis=0); return np.c_[1 - p, p]
MODELS = {"Logistic regression": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=3000)),
          "Random forest": lambda: RandomForestClassifier(n_estimators=300, max_depth=3, min_samples_leaf=8, random_state=0),
          "Gradient boosting": lambda: GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, random_state=0),
          "Neural network (MLP, mean of 10)": lambda: MLPEns(10)}
EV = {}
def evaluate(P, h):
    test = [t for t in pd.period_range("2026-01", "2026-06", freq="M") if t + h - 1 <= pd.Period("2026-06")]
    out, preds = [], {}
    for name, mk in {**MODELS, "Baseline: vehicle's past rate": None}.items():
        ys, ps, top = [], [], []
        for t in test:
            tr = P[(P.m >= pd.Period("2025-09")) & (P.m + h - 1 < t)]; te = P[P.m == t]
            p_ = te.rate.values if mk is None else mk().fit(tr[FE].values, tr.y.values).predict_proba(te[FE].values)[:, 1]
            ys += list(te.y); ps += list(p_); top.append(te.assign(p=p_).sort_values("p", ascending=False).head(5).y.mean())
        ys, ps = np.array(ys), np.array(ps); preds[name] = ps
        out.append({"model": name, "auc": float(roc_auc_score(ys, ps)), "brier": float(brier_score_loss(ys, np.clip(ps, 0, 1))), "top5": float(np.mean(top) * 100)})
    rng = np.random.default_rng(0); A = {k: [] for k in preds}
    for _ in range(2000):
        i = rng.integers(0, len(ys), len(ys))
        if ys[i].min() == ys[i].max(): continue
        for k in preds: A[k].append(roc_auc_score(ys[i], preds[k][i]))
    for o in out: o["lo"], o["hi"] = float(np.percentile(A[o["model"]], 5)), float(np.percentile(A[o["model"]], 95))
    out = sorted(out, key=lambda x: -x["auc"]); out[0]["sel"] = True
    EV[h] = (ys, preds)
    return out, len(ys), int(ys.sum()), test, A
# (a) any job next month
Pa = panel(0, 1); clsA, nA, posA, _, _ = evaluate(Pa, 1)
D["clsA"] = clsA; F["clsA"] = {"n": nA, "pos": posA, "best": clsA[0]["model"], "best_auc": clsA[0]["auc"]}
# (b) a major repair (>= 50,000 BDT) within the next 3 months
Pb = panel(50000, 3); clsB, nB, posB, testB, AB = evaluate(Pb, 3)
best_c = clsB[0]["model"]; base_n = "Baseline: vehicle's past rate"
F["clsB"] = {"n": nB, "pos": posB, "best": best_c, "auc": clsB[0]["auc"], "lo": clsB[0]["lo"], "hi": clsB[0]["hi"],
             "base_auc": next(c["auc"] for c in clsB if c["model"] == base_n), "p_better": float(np.mean(np.array(AB[best_c]) > np.array(AB[base_n]))),
             "test": f"{testB[0]} – {testB[-1]}"}
D["clsB"] = clsB
ysB, prB = EV[3]; pb_ = np.clip(prB[best_c], 0, 1); qs = np.quantile(pb_, [0, .2, .4, .6, .8, 1])
D["clsB_cal"] = [{"lo": float(qs[i]), "hi": float(qs[i + 1]), "pred": float(pb_[(pb_ >= qs[i]) & ((pb_ < qs[i + 1]) | (i == 4))].mean() * 100),
                  "obs": float(ysB[(pb_ >= qs[i]) & ((pb_ < qs[i + 1]) | (i == 4))].mean() * 100), "n": int(((pb_ >= qs[i]) & ((pb_ < qs[i + 1]) | (i == 4))).sum())} for i in range(5)]
kB = int(ysB.sum()); flag = np.zeros(len(pb_), bool); flag[np.argsort(-pb_)[:kB]] = True
D["clsB_cm"] = {"tp": int((flag & (ysB == 1)).sum()), "fp": int((flag & (ysB == 0)).sum()), "fn": int((~flag & (ysB == 1)).sum()), "tn": int((~flag & (ysB == 0)).sum()), "k": kB}
trB = Pb[(Pb.m >= pd.Period("2025-09")) & (Pb.m <= pd.Period("2026-04"))]; teB = Pb[Pb.m == pd.Period("2026-07")]
mk = MODELS.get(best_c)
fin = mk().fit(trB[FE].values, trB.y.values) if mk else None
pj = fin.predict_proba(teB[FE].values)[:, 1] if fin else teB.rate.values
seen = fleet[(fleet.date >= "2026-07-01") & (fleet.date <= "2026-09-30") & (fleet.cost >= 50000)].groupby("vehicle").cost.max()
rk = teB.assign(p=pj).sort_values("p", ascending=False)
D["risk"] = [{"v": r.v, "p": float(r.p * 100), "rate": float(r.rate), "since": float(r.since), "jobs3": int(r.jobs3), "big6": int(r.big6), "seen": float(seen.get(r.v, 0))} for r in rk.itertuples()]
F["risk"] = {"n": int(len(rk)), "seen_n": int(len(seen)), "seen_in_top10": int(sum(1 for r in D["risk"][:10] if r["seen"] > 0)), "mean_p": float(pj.mean() * 100)}
# permutation importance of the chosen model on the test months
trI = Pb[(Pb.m >= pd.Period("2025-09")) & (Pb.m + 2 < pd.Period("2026-01"))]; teI = Pb[Pb.m.isin(testB)]
mI = (mk or (lambda: None))()
if mI is not None:
    mI.fit(trI[FE].values, trI.y.values); b0 = roc_auc_score(teI.y, mI.predict_proba(teI[FE].values)[:, 1]); rs = np.random.default_rng(1); imp = []
    for fcol in FE:
        dr = []
        for _ in range(25):
            X = teI[FE].copy(); X[fcol] = rs.permutation(X[fcol].values); dr.append(b0 - roc_auc_score(teI.y, mI.predict_proba(X.values)[:, 1]))
        imp.append({"f": NAMES[fcol], "drop": float(np.mean(dr))})
    D["imp"] = sorted(imp, key=lambda x: -x["drop"]); F["imp_base_auc"] = float(b0)

# ======================= 9. what drives the cost of a job (regression)
cj = fleet[(fleet.cost > 0) & fleet.vehicle.notna()].copy()
X = pd.get_dummies(cj[["cat_bn", "series", "pm"]], dtype=float); X["year"] = cj.year - 2024
yl = np.log(cj.cost.values)
REG = {"Ridge regression (log cost)": lambda: Ridge(alpha=1.0), "Gradient boosting": lambda: GradientBoostingRegressor(n_estimators=200, max_depth=2, learning_rate=0.05, random_state=0),
       "Neural network (MLP 16)": lambda: make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(16,), alpha=1.0, max_iter=5000, random_state=0))}
reg = []
kf = KFold(5, shuffle=True, random_state=0)
for name, mk in {**REG, "Baseline: overall median": None}.items():
    pr = np.zeros(len(yl))
    for a, b in kf.split(X):
        pr[b] = np.median(yl[a]) if mk is None else mk().fit(X.values[a], yl[a]).predict(X.values[b])
    reg.append({"model": name, "r2": float(r2_score(yl, pr)), "mae_bdt": float(np.median(np.abs(np.exp(pr) - cj.cost.values))), "within2x": float((np.abs(pr - yl) <= math.log(2)).mean() * 100)})
reg = sorted(reg, key=lambda x: -x["r2"]); D["reg"] = reg
rr = Ridge(alpha=1.0).fit(X.values, yl); coefs = dict(zip(X.columns, rr.coef_))
base_cat = "cat_bn_Scheduled service (no detail)"
D["cat_effect"] = sorted([{"c": k.replace("cat_bn_", ""), "x": float(math.exp(v - coefs.get(base_cat, 0)))} for k, v in coefs.items() if k.startswith("cat_bn_")], key=lambda x: -x["x"])
F["n_cost_jobs"] = int(len(cj)); F["cost_job_median"] = float(cj.cost.median()); F["cost_job_mean"] = float(cj.cost.mean())

# ======================= 10. unusual costs (anomaly detection)
cj["lc"] = np.log(cj.cost); med = cj.groupby("cat_bn").lc.transform("median"); mad = cj.groupby("cat_bn").lc.transform(lambda s: np.median(np.abs(s - s.median())) or 0.5)
cj["rz"] = 0.6745 * (cj.lc - med) / mad
iso = IsolationForest(n_estimators=300, contamination=0.05, random_state=0).fit(np.c_[cj.lc, cj.rz])
cj["iso"] = iso.predict(np.c_[cj.lc, cj.rz]) == -1
an = cj[(cj.rz >= 2.5) | cj.iso].sort_values("rz", ascending=False)
D["anom"] = an[["order", "date", "vehicle", "desc", "cat_bn", "cost", "rz", "iso"]].assign(date=lambda x: x.date.dt.strftime("%Y-%m-%d"), med=lambda x: np.exp(med[x.index])).head(14).to_dict("records")
F["anom_n"] = int(len(an))

# ======================= 11. text mining: clusters of work descriptions (unsupervised)
txt = fleet.desc.str.lower().str.replace(r"c\.?\s?m[\s\.\-]*\w*[\s\-\.]*\d{2}\s*-\s*\d{2,4}|\d{2}-\d{4}|\d+", " ", regex=True).str.replace(r"[^a-z ]", " ", regex=True)
tv = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True); Xt = tv.fit_transform(txt)
best_k, best_s, best_lab = None, -1, None
for k in range(6, 15):
    lab = KMeans(k, n_init=10, random_state=0).fit_predict(Xt); s = silhouette_score(Xt, lab, metric="cosine")
    if s > best_s: best_k, best_s, best_lab = k, s, lab
wv = TfidfVectorizer(stop_words=["of", "and", "the", "new", "maint", "maintenance", "servicing", "service", "ser", "serv", "work", "others", "other", "change", "with"], min_df=2)
Xw = wv.fit_transform(txt); terms = np.array(wv.get_feature_names_out())
cl = []
for k in range(best_k):
    idx = np.where(best_lab == k)[0]; cent = np.asarray(Xw[idx].mean(axis=0)).ravel()
    sims = (Xt[idx] @ np.asarray(Xt[idx].mean(axis=0)).ravel()); ex = fleet.desc.values[idx[int(np.argmax(sims))]]
    cl.append({"k": int(k), "n": int(len(idx)), "cost": float(fleet.cost.values[idx].sum()), "terms": terms[cent.argsort()[::-1][:5]].tolist(), "example": ex})
D["clusters"] = sorted(cl, key=lambda x: -x["n"])
F["clusters"] = {"k": int(best_k), "silhouette": float(best_s), "ari_vs_rules": float(adjusted_rand_score(fleet.cat.values, best_lab))}

# ======================= 12. plant equipment and the order list for the page
D["plant"] = plant.sort_values("date")[["order", "type", "date", "desc", "group", "status", "cost"]].assign(date=lambda x: x.date.dt.strftime("%Y-%m-%d")).to_dict("records")
F["plant_cost"] = float(plant.cost.sum()); F["plant_n"] = int(len(plant))
D["orders"] = df[["order", "type", "date", "equip", "vehicle", "desc", "status", "cost", "group", "cat_bn", "pm", "backdated", "mismatch", "dup_of", "lowconf", "a_start", "a_finish"]] \
    .assign(date=lambda x: x.date.dt.strftime("%Y-%m-%d")).to_dict("records")
F["groups"] = df.group.value_counts().to_dict(); F["fleet_n"] = int(len(fleet)); F["vehicles_n"] = int(df.vehicle.nunique())

def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating, float)): return None if math.isnan(o) else round(float(o), 4)
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, (pd.Period,)): return str(o)
    if o is pd.NaT: return None
    return o
json.dump(clean(D), open("mdata.json", "w"), ensure_ascii=False)
json.dump(clean(F), open("mfacts.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(clean({k: F[k] for k in F if k not in ("plan_list", "top_orders", "mismatch", "dups", "fire_ext", "gas_mon", "fire_sys", "weigh", "compressor", "lowconf")}), ensure_ascii=False, indent=0)[:9000])
