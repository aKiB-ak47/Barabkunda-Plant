"""Build the public website (index.html at the repository root) from src/.
    python3 -I src/build_site.py
Inputs: src/hub/hub.src.html (page template), src/hub/hubdata.json (chart data and {{tokens}}),
src/hub/head_meta.html (search-engine tags), src/reports/*.html (the two self-contained reports)."""
import base64, datetime as dt, json, os, re

SRC = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SRC)
REPORTS = ["cal", "maint"]
src = open(f"{SRC}/hub/hub.src.html", encoding="utf8").read()
hub = json.load(open(f"{SRC}/hub/hubdata.json", encoding="utf8"))
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
ldate = lambda s: f"{int(s[8:])} {MON[int(s[5:7]) - 1]} {s[:4]}"
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
ups = sorted(hub.get("updates", []), key=lambda u: (u["date"], u.get("key", "")))   # kept for the record; not shown on the site
# figures shared with the report pages: TPM maturity, equipment count, value of over-filled LPG, round means for the mini chart
tpm = json.load(open(f"{SRC}/maint/tpm.json", encoding="utf8"))
calpage = open(f"{SRC}/reports/cal.html", encoding="utf8").read()
C = json.loads(re.search(r'<script id="dash-data" type="application/json">(.*?)</script>', calpage, re.S).group(1))
PRICE_KG = 2060.0 / 12   # BERC retail price of a 12 kg cylinder, November 2026 (same value as src/cal/deep_cal.py)
hub.setdefault("tokens", {}).update({"tpm_mat": f"{tpm['maturity']['mean']:.1f}", "eq_n": str(len(re.findall(r'<article class="eq" id="eq-', open(f"{SRC}/reports/maint.html", encoding="utf8").read()))),
                                     "cal_give": f"{C['summary'][0]['value'] * 1000 * PRICE_KG / 1e5:.0f}"})
MS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
hub["calr"] = [{"l": f"{int(r['date'][8:])} {MS[int(r['date'][5:7]) - 1]} {r['date'][2:4]}", "m": round(r["mean_g"], 1)} for r in sorted(C["rounds"], key=lambda r: r["date"])]
hub["cpk"] = [{"l": p["pb"], "v": p["cpk"]} for p in hub.get("cal", [])]
T = hub["tokens"]
cpk24, cpk26 = [s.strip() for s in T["cal_cpk"].split("→")]
TC = tpm["cal"]
_g = C["summary"][0]
T.update({"cal_w24": f"{TC['within150_24']:.0f}", "cal_give_lo": f"{_g['low'] * 1000 * PRICE_KG / 1e5:.0f}", "cal_give_hi": f"{_g['high'] * 1000 * PRICE_KG / 1e5:.0f}",
          "maint_maxgap": str(json.load(open(f"{SRC}/maint/mfacts.json", encoding="utf8"))["silent"]["max_gap_2026"])})
T.update({"cal_cpk24": cpk24, "cal_cpk26": cpk26, "cal_within": f"{TC['within150_26']:.0f}",
          "asof": f"Weight checks to {ldate(TC['last'])} · maintenance record to {T['maint_asof']}", "updated": ldate(ups[-1]["date"]) if ups else T.get("updated", "")})

# plant map: one entry per area, every figure taken from the SAP orders, the maintenance facts and the weight checks
F = json.load(open(f"{SRC}/maint/mfacts.json", encoding="utf8"))
O = [r for r in json.load(open(f"{SRC}/maint/orders.json", encoding="utf8")) if r["cat"] == "plant"]
def hits(pat, rows=O): return sorted([r for r in rows if re.search(pat, r["desc"].upper())], key=lambda r: r["date"])
def lastd(rows): return ldate(rows[-1]["date"]) if rows else "none"
hose, store = hits(r"TANKER POINT|HOSE|LOADING ARM|UNLOAD"), hits(r"SPHERE|STORAGE TANK|LPG TANK|BULLET|SAFETY VALVE|RELIEF|\bPSV\b|LEVEL|ROTO|SPRAY|DELUGE")
esd = hits(r"\bESD\b|SHUT.?DOWN|EMERGENCY")
firepump = hits(r"FIRE PUMP|JOCKEY|HYDRANT|DIESEL PUMP|FIRE WATER")
pumps, lpgpump = hits(r"\bPUMP\b"), [r for r in hits(r"\bPUMP\b") if not re.search(r"SUBMERSIBLE|WATER", r["desc"].upper())]
air = hits(r"AIR COM|AIR COMPRESSOR"); air_rel = [r for r in air if "REL" in r["status"].split()]
fill = hits(r"FILLING (MACHINE|HALL|HEAD)|CAROUSEL|CONVEYOR")
scale = hits(r"SCALE|WEIGH")
ext = sorted(F["fire_ext"], key=lambda r: r["date"]); gasm = sorted(F["gas_mon"], key=lambda r: r["date"]); fsys = sorted(F["fire_sys"], key=lambda r: r["date"])
give_mt = C["summary"][0]["value"]
hub["zones"] = [
    {"k": "receipt", "short": "Receipt", "t": "LPG receipt: jetty and tanker bay", "s": "a", "x": 330, "y": 352,
     "d": "LPG from ships and tankers reaches the spheres through loading hoses, breakaway couplings, strainers and emergency shutdown (ESD) valves. A burst hose or a coupling coming apart is the biggest risk here.",
     "f": [f"SAP orders for hoses or the tanker point: {len(hose)}, last on {lastd(hose)}", f"Orders for ESD valves or emergency-shutdown tests: {len(esd)}",
           "A proposed schedule for hose pressure tests and ESD function tests is in the TPM programme"],
     "b": [["Loading hose", "maint", "eq-breakaway"], ["ESD valve", "maint", "eq-esdv"], ["Flow diagram", "maint", "atlas-flow"]]},
    {"k": "storage", "short": "Storage spheres", "t": "LPG storage spheres (4)", "s": "r" if not store else "a", "x": 795, "y": 236,
     "d": "Four spherical pressure vessels hold all the plant's bulk LPG. Each sphere's safety valves (PSV), level gauge, pressure gauge, excess flow valve and water-spray system are the last line of defence.",
     "f": [f"SAP orders for spheres, PSVs, level gauges or water spray: {len(store)}", "So SAP holds no record of periodic sphere inspection or PSV testing; any paper records should be entered in SAP",
           "For review by a qualified engineer (NFPA 58; LPG Rules 2004)"],
     "b": [["View spheres", "maint", "eq-sphere"], ["Safety valve", "maint", "eq-psv"], ["Excess flow valve", "maint", "eq-efv"]]},
    {"k": "fire", "short": "Fire protection", "t": "Fire protection: water tank, pumps and extinguishers", "s": "r", "x": 457, "y": 300,
     "d": "The fire-water tank, fire pumps, hydrants, monitors and the spheres' water spray together form the fire defence, with dry-powder extinguishers in every area.",
     "f": [f"Longest gap between fire-extinguisher refill orders {max(F['fire_ext_gaps_m']):.0f} months; last refill {lastd(ext)}",
           f"Orders for fire-fighting lines or monitors: {len(fsys)}, last on {lastd(fsys)}", f"Orders for fire-pump or hydrant tests: {len(firepump)} (NFPA 25 requires regular testing)"],
     "b": [["Fire extinguisher", "maint", "eq-extinguisher"], ["Water-spray system", "maint", "eq-deluge"], ["Renewal calendar", "maint", "renew"]]},
    {"k": "gas", "short": "Gas detector", "t": "Fixed gas detector", "s": "r", "x": 665, "y": 330,
     "d": "Detectors in the sphere area, pump house and filling shed measure LPG in the air (as % of LEL) and sound the alarm. Without calibration a sensor can slowly go blind.",
     "f": [f"Last service order: {lastd(gasm)}", f"No calibration record for {F['gas_mon_months']:.0f} months", "Bump tests and calibration are needed on the manufacturer's schedule"],
     "b": [["Gas detector", "maint", "eq-detector"], ["TPM schedule", "maint", "tpm-pm"]]},
    {"k": "pump", "short": "Pump house", "t": "Pump and compressor house", "s": "a", "x": 1074, "y": 404,
     "d": "LPG pumps send liquid gas from the spheres to the filling shed; air compressors drive the filling machines and pneumatic valves. Mechanical seals, bearings and NRVs wear most here.",
     "f": [f"SAP orders for LPG pumps: {len(lpgpump)}; all {len(pumps)} pump orders are for submersible water pumps" if not lpgpump else f"SAP orders for LPG pumps: {len(lpgpump)}, last on {lastd(lpgpump)}",
           f"{len(air)} scheduled air-compressor orders created, {len(air_rel)} released", "A daily check of pump vibration, temperature and seal leaks is in the TPM programme"],
     "b": [["LPG pump", "maint", "eq-pump"], ["NRV", "maint", "eq-nrv_swing"], ["Butterfly valve", "maint", "eq-butterfly"]]},
    {"k": "filling", "short": "Filling carousel", "t": "Filling carousel and filling heads", "s": "r", "x": 680, "y": 450,
     "d": "Each filling head on the rotating carousel weighs and fills a cylinder. When a head overfills, the customer gets gas free and the cylinder has less room for thermal expansion.",
     "f": [f"2026 average overfill {T['cal_mean26']} g; highest single cylinder {T['cal_max']} g", f"{T['cal_hot_n']} flagged heads: {T['cal_hot_list']}",
           f"About {give_mt:.1f} t of LPG over-delivered, 1 Mar – 25 Oct 2026 (≈ Tk {T['cal_give']} lakh, upper bound)", f"SAP orders for filling machines and carousel: {len(fill)}, last on {lastd(fill)}"],
     "b": [["Weight accuracy", "cal", "update"], ["By head", "cal", "dash"], ["Filling head", "maint", "eq-filler"]]},
    {"k": "check", "short": "Check-scale", "t": "Check-scale and quality control", "s": "a", "x": 852, "y": 452,
     "d": "Every cylinder is weighed again after filling and set aside if outside the limit. Regular sample checks show how accurate the filling heads are.",
     "f": [f"Within ±150 g: {TC['within150_24']:.0f}% in 2024, {TC['within150_26']:.0f}% in 2026, {TC['within150_last']:.0f}% in the latest round", f"Process capability Cpk: from {cpk24} to {cpk26} (target ≥ 1.33)",
           f"{T['cal_n']} weight checks in all; SAP orders for scales: {len(scale)}, last on {lastd(scale)}"],
     "b": [["Deep analysis", "cal", "deep"], ["Check-scale", "maint", "eq-checkscale"], ["Slides", "cal", "slides"]]},
    {"k": "dispatch", "short": "Dispatch and fleet", "t": "Dispatch and vehicle fleet", "s": "a", "x": 1040, "y": 478,
     "d": "Filled cylinders go by truck to distributors. The vehicle fleet is the largest part of maintenance cost, and keeping every vehicle's explosives licence valid is a legal requirement.",
     "f": [f"Fleet planned-work share {F['pm_share_w']:.0f}% (world class 85%)", f"{F['pareto80']} of {F['fleet_vehicles_w']} vehicles take 80% of the cost",
           f"Record to {T['maint_asof']}; {F['silent']['days']} silent days since the last order, an estimated Tk {T['maint_unbooked']} lakh of work not yet in SAP"],
     "b": [["Vehicle fleet", "maint", "fleet"], ["Renewal calendar", "maint", "renew"], ["Forecast", "maint", "predict"]]},
]

# ---------------------------------------------------------------- red flags for management
# Every flag is computed from the same records as the reports: weight checks (C), maintenance facts (F), TPM KPIs and the risk list.
MD = json.load(open(f"{SRC}/maint/mdata.json", encoding="utf8"))
K = {k["metric"]: k for k in C["kpis"]}; KP = {k["k"]: k for k in tpm["kpis"]}
rnd = sorted(C["rounds"], key=lambda r: r["date"]); r26 = [r for r in rnd if r["year"] == 2026]; rl = rnd[-1]
in_both = sum(1 for r in r26 if not r["mean_out"] and not r["sd_out"])
hot = [h for h in C["heads"] if h["ci_low_g"] > 0 and h["mean_g"] > 40]
fail50 = sorted([h for h in C["heads"] if h["fail_chance_pct"] >= 50], key=lambda h: -h["fail_chance_pct"])
nxt = next(x for x in C["summary"] if x["item"].startswith("Next check average error")); heads_out = next(x for x in C["summary"] if x["item"].startswith("Heads expected outside"))
sel = next(m for m in C["models"] if m["selected"])
big = min(C["sizes"], key=lambda z: z["within150_pct"]); bigmax = max(z["max_over_g"] for z in C["sizes"])
fmt = lambda v, d=1: f"{v:,.{d}f}"
sg = lambda v, d=0: ("+" if v > 0 else "−" if v < 0 else "") + f"{abs(v):,.{d}f}"
risky = [r for r in MD["risk"] if r["p"] >= 30]
lic_m = (dt.date.fromisoformat(F["as_of"]) - dt.date.fromisoformat(F["plant_lic_last"])).days / 30.44
FL = [
 # safety
 dict(sev="red", cat="Safety", title="Gas detectors: no calibration on record", now=f"{F['gas_mon_months']:.1f} months since the last service order", limit="Manufacturer's interval, usually 3–6 months", why="An uncalibrated sensor can show zero with gas present; the plant would get no LPG-leak alarm or automatic shutdown.", code="NFPA 58; LPG Rules 2004", rep="maint", view="eq-detector", secs=["safety", "eq-detector", "tpm-kpi"]),
 dict(sev="red", cat="Safety", title="Storage spheres: no inspection or safety-valve test on record", now=f"{len(store)} SAP orders for spheres, PSVs, level gauges or water spray", limit="Periodic inspection and PSV test per licence (PSV usually yearly)", why="The four spheres hold all the bulk LPG; the safety valves, level alarms and water spray are the last line of defence against a BLEVE.", code="NFPA 58; Explosives Act 1884; LPG Rules 2004", rep="maint", view="eq-sphere", secs=["safety", "eq-sphere", "eq-psv"]),
 dict(sev="red", cat="Safety", title="Fire extinguishers: long gap in maintenance", now=f"{max(F['fire_ext_gaps_m']):.0f}-month gap between refill orders", limit="Annual maintenance (12 months)", why="Extinguishers that are not maintained may not discharge when a fire starts.", code="NFPA 10", rep="maint", view="eq-extinguisher", secs=["safety", "eq-extinguisher"]),
 dict(sev="red", cat="Safety", title="Fire pumps and hydrants: no test on record", now=f"{len(firepump)} test orders in SAP", limit="Weekly pump run; yearly full-flow test", why="The fire-water system cools the spheres in a fire; an untested pump may not start.", code="NFPA 25", rep="maint", view="eq-deluge", secs=["safety", "eq-deluge"]),
 dict(sev="red", cat="Safety", title="Overfilled 12 kg cylinders", now=f"{K['Over by more than 150 g (%)']['y2026']:.1f}% of 12 kg cylinders over +150 g in 2026; highest +{max(f['value'] for f in C['flags'] if f['id'] == 'S1'):.0f} g", limit="Tolerance ±150 g (target: no cylinder over)", why="An overfilled cylinder has less vapour space for thermal expansion of the liquid.", code="NFPA 58; ISO 10691", rep="cal", view="update", secs=["tp-update", "tp-dash", "eq-filler"]),
 dict(sev="red", cat="Safety", title="Larger cylinders filled up to +800 g", now=f"{big['size']}: only {big['within150_pct']:.0f}% within ±150 g; highest +{bigmax:.0f} g across 20, 35 and 45 kg", limit="Tolerance ±150 g", why="20, 35 and 45 kg cylinders show the same overfilling as the 12 kg line.", code="NFPA 58", rep="cal", view="update", secs=["tp-update"]),
 dict(sev="red", cat="Procedure", title="No record of check-weigher rejects", now="Rejected cylinders are not logged", limit="Every out-of-tolerance cylinder logged and set aside", why="Without a reject log nobody can prove that out-of-limit cylinders are stopped before dispatch.", code="ISO 10691", rep="maint", view="eq-checkscale", secs=["tp-update", "eq-checkscale"]),
 dict(sev="red", cat="Licences", title=f"{F['plant_lic_n']} kinds of plant licence without a renewal order", now=f"Last renewal order {ldate(F['plant_lic_last'])} ({lic_m:.0f} months ago)", limit="Renewal before expiry (normally yearly)", why="Operating with an expired explosives, fire or factory licence is a legal risk for the whole plant.", code="Explosives Act 1884; LPG Rules 2004", rep="maint", view="renew", secs=["safety", "renew"]),
 dict(sev="red", cat="Licences", title="Renewal calendar: documents overdue", now=f"{F['ren_overdue']} documents with no new order in 12 months; {F['ren_soon']} due within 120 days", limit="No document past its renewal date", why="Vehicle explosives licences, fitness and tax tokens must be valid to carry LPG on public roads.", code="LPG Rules 2004", rep="maint", view="renew", secs=["renew", "fleet"]),
 dict(sev="red", cat="Procedure", title="Air-compressor maintenance plans never released", now=f"{F['plan_released']} of {F['plan_orders']} plan orders released", limit="Plan compliance ≥ 95%", why="Compressed air drives the filling machines and holds the ESD valves open; a dry, clean supply is a safety matter.", code="Manufacturer's schedule", rep="maint", view="pm", secs=["pm", "safety", "tpm-pm"]),
 # weight accuracy
 dict(sev="red", cat="Weight accuracy", title="Filling process capability far below target", now=f"Cpk {cpk26} in 2026 (2024: {cpk24})", limit="Cpk ≥ 1.33", why="The filling process cannot hold ±150 g reliably; overfill and underfill will keep occurring.", code="", rep="cal", view="deep", secs=["tp-deep", "tp-update", "tp-dash", "tpm-qm", "tpm-kpi"]),
 dict(sev="red", cat="Weight accuracy", title="Too few cylinders within ±150 g", now=f"{K['Within ±150 g (%)']['y2026']:.1f}% in 2026; latest round {K['Within ±150 g (%)']['latest']:.1f}%", limit="Target 95% (2024: " + f"{K['Within ±150 g (%)']['base_2024']:.1f}%)", why="Roughly one cylinder in six is outside tolerance.", code="", rep="cal", view="deep", secs=["tp-deep", "tp-dash"]),
 dict(sev="red", cat="Weight accuracy", title="Rounds outside the control limits", now=f"Only {in_both} of {len(r26)} rounds in 2026 inside both limits", limit="All rounds inside the 2024 control limits", why="The filling process is no longer stable compared with June 2024; a cause must be found.", code="", rep="cal", view="update", secs=["tp-update", "tp-dash", "tp-deep"]),
 dict(sev="red", cat="Weight accuracy", title="Spread in the latest round beyond its limit", now=f"SD {rl['sd_g']:.0f} g on {ldate(rl['date'])}", limit=f"SD limit {rl['sd_ucl']:.0f} g", why="Cylinder-to-cylinder scatter is more than twice the limit.", code="", rep="cal", view="update", secs=["tp-update"]),
 dict(sev="red", cat="Weight accuracy", title=f"{T['cal_hot_n']} filling heads overfill consistently", now="Heads " + T["cal_hot_list"], limit="No head with a significant bias", why="These heads need calibration first; their load cells or valve timing have drifted.", code="", rep="cal", view="dash", secs=["tp-dash", "tp-update", "eq-filler"]),
 dict(sev="red", cat="Cost", title="LPG given away by overfilling", now=f"≈ Tk {T['cal_give']} lakh, 1 March – 25 October 2026", limit="Zero over-delivery", why=f"About {C['summary'][0]['value']:.1f} t of LPG (95% range Tk {T['cal_give_lo']}–{T['cal_give_hi']} lakh at retail price, an upper bound).", code="", rep="cal", view="deep", secs=["tp-deep"]),
 # forecasts
 dict(sev="red", cat="Forecast", title="Next round forecast above the control limit", now=f"{sg(nxt['value'], 1)} g (80% range {sg(nxt['low'])} to {sg(nxt['high'])} g)", limit=f"Upper control limit {sg(rl['mean_ucl'])} g", why="Without action the next weight check is expected to fail its mean limit.", code="", rep="cal", view="update", secs=["tp-update", "tp-dash"]),
 dict(sev="red", cat="Forecast", title="Heads likely to leave ±150 g at the next check", now=f"{len(fail50)} heads with ≥ 50% chance (" + ", ".join(str(h["head"]) for h in fail50[:8]) + f"); {heads_out['value']:.1f} expected in total", limit="At most one head", why="Calibrate these heads before the next round.", code="", rep="cal", view="dash", secs=["tp-update", "tp-dash"]),
 dict(sev="amber", cat="Forecast", title="Weight forecast only slightly better than naive", now=f"RMSE {sel['rmse_g']:.1f} g; {sel['skill_vs_naive_pct']:.1f}% better than repeating the last reading", limit="Clearly better than naive (≥ 10%)", why="Use the head forecasts to set priorities, not as certain results.", code="", rep="cal", view="update", secs=["tp-update"]),
 dict(sev="amber", cat="Forecast", title="Monthly maintenance-cost forecast is unreliable", now=f"MAPE {F['fc']['mape']:.0f}%, RMSE Tk {F['fc']['rmse'] / 1e5:.1f} lakh a month", limit="MAPE ≤ 25%", why="Monthly cost swings too much for a dependable forecast; budget on the range, not the point value.", code="", rep="maint", view="predict", secs=["predict"]),
 dict(sev="amber", cat="Forecast", title="Maintenance work not yet entered in SAP", now=f"{F['silent']['days']} days without an order; ≈ Tk {T['maint_unbooked']} lakh unbooked since July", limit=f"Orders entered within days (2026 average {F['silent']['rate_month']:.0f} a month)", why="Cost and job counts since July are understated until the backlog is entered.", code="", rep="maint", view="dq", secs=["dq", "cost", "summary"]),
 # predictive models
 dict(sev="amber", cat="Predictive model", title=f"{len(risky)} vehicles at high risk of a major repair", now=", ".join(f"{r['v'][-7:]} ({r['p']:.0f}%)" for r in risky[:4]), limit="Risk below 30% (fleet mean " + f"{F['risk']['mean_p']:.0f}%)", why=f"Neural-network risk model, AUC {F['clsB']['auc']:.2f} (90% range {F['clsB']['lo']:.2f}–{F['clsB']['hi']:.2f}); inspect these vehicles first.", code="", rep="maint", view="predict", secs=["predict", "fleet"]),
 dict(sev="amber", cat="Predictive model", title="Next-month job model no better than a simple rule", now=f"Best is the vehicle's past rate (AUC {F['clsA']['best_auc']:.2f})", limit="A model clearly better than the baseline", why="Small jobs follow each vehicle's habit; record kilometres and running hours to improve prediction.", code="", rep="maint", view="predict", secs=["predict"]),
 # procedure and SAP
 dict(sev="red", cat="Procedure", title="No maintenance order has ever been closed", now=f"TECO {F['teco']} of {F['n']} orders; confirmed {F['cnf']}", limit="≥ 90% confirmed and closed", why="Downtime and repair time cannot be measured, and nobody can see which jobs are really finished.", code="", rep="maint", view="dq", secs=["dq", "tpm-sap", "tpm-kpi"]),
 dict(sev="red", cat="Procedure", title="Orders written after the work", now=f"{F['backdated']} of {F['n']} orders ({F['backdated'] / F['n'] * 100:.0f}%) back-dated", limit="≤ 10% (order before the work starts)", why="Orders are used to book cost afterwards, not to plan and control work.", code="", rep="maint", view="dq", secs=["dq", "tpm-sap"]),
 dict(sev="amber", cat="Procedure", title="Orders without an equipment number", now=f"{F['no_equip']} orders ({F['no_equip'] / F['n'] * 100:.1f}%)", limit="≤ 2%", why="Cost cannot be traced to a machine or vehicle.", code="", rep="maint", view="dq", secs=["dq"]),
 # fleet and cost
 dict(sev="red", cat="Fleet and cost", title="Most fleet work is repair after breakdown", now=f"Planned work {F['pm_share_w']:.1f}% of fleet jobs", limit="World class 85% (plant target 70%)", why="Breakdown repairs cost more and take vehicles off the road without warning.", code="", rep="maint", view="pm", secs=["pm", "fleet", "tpm-kpi"]),
 dict(sev="red", cat="Fleet and cost", title="Same repair again within 90 days", now=f"{KP['repeat']['v']:.1f}% of repairs ({tpm['repeat_n']} of {tpm['repeat_base']}); repeat cost Tk {F['repeats_cost'] / 1e5:.1f} lakh", limit="≤ 8% (world class 5%)", why="Repairs fix symptoms, not causes; root-cause analysis is missing.", code="", rep="maint", view="fleet", secs=["fleet", "tpm-kaizen", "tpm-kpi"]),
 dict(sev="amber", cat="Fleet and cost", title="Vehicles come back for work every month", now=f"Mean interval between jobs {F['weibull']['mean']:.0f} days", limit="Plant target 60 days (world class 90)", why=f"Chance of another job within 30 days is {F['weibull']['p30'] * 100:.0f}% (Weibull β {F['weibull']['beta']:.2f}).", code="", rep="maint", view="pm", secs=["pm"]),
 # data quality
 dict(sev="amber", cat="Data quality", title="Orders to audit", now=f"{len(F['dups'])} possible duplicates, {len(F['mismatch'])} on the wrong vehicle, {len(F['lowconf'])} costs to verify, {F['anom_n']} unusual costs", limit="None", why="These distort cost per vehicle and should be corrected in SAP.", code="", rep="maint", view="all", secs=["dq", "predict"]),
 dict(sev="amber", cat="Data quality", title="Weight-check records need tightening", now=next(f for f in C["flags"] if f["id"] == "D6")["finding"] + "; tare recorded to 0.1 kg; no checks in April or August", limit="Every round checked and recorded to 10 g", why="Gaps and rounding hide the true filling error.", code="", rep="cal", view="update", secs=["tp-update"]),
]
for i, f in enumerate(FL): f["id"] = f"F{i + 1:02d}"
hub["flags"] = FL
T.update({"flags_n": str(len(FL)), "flags_red": str(sum(f["sev"] == "red" for f in FL)), "flags_amber": str(sum(f["sev"] == "amber" for f in FL))})
for k, v in hub.get("tokens", {}).items(): src = src.replace("{{" + k + "}}", v)
left = re.findall(r"\{\{\w+\}\}", src)
assert not left, f"unfilled tokens: {left}"
data = {k: v for k, v in hub.items() if k in ("calr", "cpk", "maint", "zones", "flags")}   # only what the page draws; the update log is not published
src = src.replace("__HUBDATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))

hub_html = src

reps = {k: open(f"{SRC}/reports/{k}.html", encoding="utf8").read() for k in REPORTS}
payload = "".join(f'<script type="application/octet-stream" id="rep-{k}">{base64.b64encode(v.encode()).decode()}</script>\n' for k, v in reps.items())
meta = open(f"{SRC}/hub/head_meta.html", encoding="utf8").read()
i = hub_html.index("</style>") + len("</style>")
doc = ('<!doctype html>\n<html lang="en">\n<head>\n' + meta + '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n'
       + hub_html[:i] + "\n</head>\n<body>\n" + hub_html[i:] + "\n" + payload + "</body>\n</html>\n")
open(f"{ROOT}/index.html", "w", encoding="utf8").write(doc)

today = dt.date.today().isoformat()
sm = open(f"{ROOT}/sitemap.xml", encoding="utf8").read()
open(f"{ROOT}/sitemap.xml", "w", encoding="utf8").write(re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{today}</lastmod>", sm))
print("index.html", round(len(doc.encode()) / 1e6, 2), "MB")
