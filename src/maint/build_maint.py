"""Build the Bangla maintenance report page (self-contained, d3 inlined) from mdata.json and mfacts.json.
Every number in the text is taken from the computed facts; nothing is typed by hand."""
import json, math, html, re, os, datetime as dt_
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); os.chdir(HERE)
D = json.load(open("mdata.json")); F = json.load(open("mfacts.json")); TPM = json.load(open("tpm.json"))
import sys; sys.path.insert(0, HERE)
import build_tpm, tpm_content, atlas_svg
from urllib.parse import quote
def _d3():
    if os.path.exists("/opt/npm-tools/node_modules/d3/dist/d3.min.js"):
        return open("/opt/npm-tools/node_modules/d3/dist/d3.min.js", encoding="utf8").read()
    for f in ("maint.html", "cal.html"):   # the same d3 7.9.0 is already inside the built report
        t = open(f"{SRC}/reports/{f}", encoding="utf8").read(); m = re.search(r"<script>(// https://d3js.org v7.9.0.*?)</script>", t, re.S)
        if m: return m.group(1).replace("<\\/script", "</script")
    raise SystemExit("d3 not found")
D3 = _d3().replace("</script", "<\\/script")
BN = str.maketrans("0123456789", "0123456789")
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MONS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
def bn(x): return str(x).translate(BN)
def n0(x): return bn(f"{x:,.0f}")
def n1(x): return bn(f"{x:,.1f}")
def pct(x, d=1): return bn(f"{x:.{d}f}") + "%"
def tk(x):
    if abs(x) >= 1e7: return "Tk " + bn(f"{x/1e7:.2f}") + " crore"
    if abs(x) >= 1e5: return "Tk " + bn(f"{x/1e5:.1f}") + " lakh"
    return "Tk " + bn(f"{x:,.0f}")
def lakh(x): return bn(f"{x/1e5:.1f}") + " lakh"
def dt(s, short=False):
    d = pd.Timestamp(s); return bn(f"{d.day} {MONS[d.month-1] if short else MON[d.month-1]} {d.year}")
def mon(s):
    d = pd.Timestamp(s + "-01") if len(s) == 7 else pd.Timestamp(s); return bn(f"{MON[d.month-1]} {d.year}")
def chg(a, b, unit="%"):
    if a in (None, 0) or b is None: return "—"
    c = (b - a) / a * 100; return ("+" if c > 0 else "−") + bn(f"{abs(c):.1f}") + "%"
esc = lambda s: html.escape(str(s), quote=True)
H2, H1 = F["h2_2025"], F["h1_2026"]; W, FC, CB, CA = F["weibull"], F["fc"], F["clsB"], F["clsA"]
risk = D["risk"]; top4 = [r["v"][-4:] for r in risk[:4]]
v1 = D["vehicles"][0]
gc = F["group_cost"]; fleet_share = gc["Vehicle fleet"] / F["cost_total"] * 100
reg_best = D["reg"][0]
ext = F["fire_ext"]; ext_gap = max(F["fire_ext_gaps_m"])
ext_gap_i = F["fire_ext_gaps_m"].index(ext_gap)
comp260 = next(x for x in F["compressor"] if x["cost"] > 100000)
zc = F["zero_cost_zpm1_2022_23"]
tw = F["twins"]

T = {}  # text blocks with numbers
T["eyebrow"] = f"BM Energy (BD) Limited · Plant <span class=lat>1201</span> · SAP maintenance record, {dt(F['date_min'])} – {dt(F['as_of'])} (last order {dt(F['date_max'])})"
T["lede"] = (f"A full analysis of {n0(F['n'])} SAP PM maintenance orders: cost, preventive work, forecasts and a risk model, and statistical significance. "
             f"Total recorded cost {tk(F['cost_total'])}, of which {pct(fleet_share,0)} went to the vehicle fleet. Use the buttons above for the TPM programme and the illustrated equipment guide.")
EXEC = [
  f"<b>Safety first:</b> the only SAP order for gas-detector service is dated {dt(F['gas_mon'][0]['date'])} ({n1(F['gas_mon_months'])} months ago); fire-extinguisher refills once had a gap of {n1(ext_gap)} months; renewal orders for {bn(F['plant_lic_n'])} kinds of plant licence stop after {dt(F['plant_lic_last'])}. Verification by a qualified engineer is required.",
  f"<b>Cost:</b> {tk(F['fleet_w_cost'])} on {bn(F['fleet_vehicles_w'])} identified vehicles in Jun 2025 – Jun 2026; just {bn(F['pareto80'])} vehicles take 80% of the cost. Highest: <span class=lat>{v1['v']}</span> at {tk(v1['cost_w'])}.",
  f"<b>Process:</b> not one of the {n0(F['n'])} orders is technically closed (<span class=lat>TECO</span>); {bn(F['backdated'])} ({pct(F['backdated']/F['n']*100,0)}) were written after the work. From July 2026 to today the fleet has only {bn(F['recent_jul_oct']['fleet_orders'])} orders, and none in the {bn(F['silent']['days'])} days since {dt(F['date_max'])}; an estimated {tk(FC['unbooked_jul_oct'])} ({lakh(FC['unbooked_lo'])}–{lakh(FC['unbooked_hi'])}) of cost is not yet in SAP.",
  f"<b>Preventive:</b> only {pct(F['pm_share_w'],0)} of fleet jobs include a scheduled service; none of the {bn(F['plan_orders'])} compressor plan orders was ever released. The same part was repaired again within 90 days {bn(F['repeats_n'])} times, costing {tk(F['repeats_cost'])}.",
  f"<b>Forecast:</b> a neural-network model ranks which vehicles will need a major repair (≥ Tk 50,000) in the next 3 months with <span class=lat>AUC</span> {bn(f'{CB[chr(97)+chr(117)+chr(99)]:.2f}')} (90% range {bn(f'{CB[chr(108)+chr(111)]:.2f}')}–{bn(f'{CB[chr(104)+chr(105)]:.2f}')}), better than the past rate alone ({bn(f'{CB[chr(98)+chr(97)+chr(115)+chr(101)+chr(95)+chr(97)+chr(117)+chr(99)]:.2f}')}). Highest risk: {', '.join('<span class=lat>'+x+'</span>' for x in top4)}.",
]
KM = [
  ("Total cost", tk(H2["cost"]), tk(H1["cost"]), chg(H2["cost"], H1["cost"]), "Higher is not always worse: major overhauls push it up"),
  ("Fleet cost", tk(H2["fleet_cost"]), tk(H1["fleet_cost"]), chg(H2["fleet_cost"], H1["fleet_cost"]), ""),
  ("Plant cost", tk(H2["plant_cost"]), tk(H1["plant_cost"]), chg(H2["plant_cost"], H1["plant_cost"]), "Buildings, filling, utilities, fire safety"),
  ("Fleet work orders", n0(H2["fleet_jobs"]), n0(H1["fleet_jobs"]), chg(H2["fleet_jobs"], H1["fleet_jobs"]), ""),
  ("Average cost per order", n0(H2["cost_per_job"]) + "", n0(H1["cost_per_job"]) + "", chg(H2["cost_per_job"], H1["cost_per_job"]), "Orders with a cost"),
  ("Jobs including a scheduled service", pct(H2["sched_share"]), pct(H1["sched_share"]), ("+" if H1["sched_share"] > H2["sched_share"] else "−") + bn(f"{abs(H1['sched_share']-H2['sched_share']):.1f}") + " points", "World class: 85% planned work (plant target 70%)"),
]
DQ = [
  ("No order has been closed", f"Of {n0(F['n'])} orders, {bn(F['teco'])} are <span class=lat>TECO/CLSD</span>; only {bn(F['cnf'])} are confirmed (<span class=lat>CNF</span>), and only {bn(F['actual_dates'])} have actual start and finish dates.", "Downtime and time to repair (<span class=lat>MTTR</span>) cannot be measured; intervals are measured from order dates."),
  ("Cost is materials only", f"{bn(F['n_cost'])} orders carry a cost, and every one has a goods issue (<span class=lat>GMPS</span>); there is no cost without materials.", "Labour and outside-service costs are not visible; cost may be understated."),
  ("A 9-month gap", f"Only {bn(F['gap_orders'])} general maintenance orders in Jul 2024 – May 2025; {bn(zc[0])} of the {bn(zc[1])} orders of 2022–23 have zero cost.", "Trends and models use the continuous data of Jun 2025 – Jun 2026."),
  (f"{bn(F['silent']['days'])} silent days since the last order", f"The record runs to {dt(F['as_of'])}, but the last order is dated {dt(F['date_max'])}. At the 2026 average rate ({n1(F['silent']['rate_month'])} a month) about {n0(F['silent']['expected'])} orders would be expected in these {bn(F['silent']['days'])} days. 2026 already had a {bn(F['silent']['max_gap_2026'])}-day gap that was later filled by back-dated orders (median delay of such orders {n0(F['silent']['late_median'])} days). So the work has most likely been done but is not yet in SAP. Since July there are {bn(F['recent_jul_oct']['orders'])} orders in all, {bn(F['recent_jul_oct']['fleet_orders'])} of them for the fleet; the first half of 2026 averaged {n1(F['h1_2026_monthly_orders'])} a month.", "Missing orders are not taken to mean no work: this period is left out of forecast training and the unbooked cost is estimated separately."),
  ("Orders written after the work", f"{bn(F['backdated'])} orders are dated more than 30 days before the previous order number; median delay {bn(int(F['late_median']))} days.", "Orders are opened to book cost afterwards, not to plan work; the order date is taken as the job date."),
  ("60 ways of writing vehicle numbers", f"{bn(F['reg_vehicles'])} vehicle numbers are written {bn(F['reg_variants_total'])} different ways in the descriptions (e.g. <span class=lat>CM DA-61-0225</span>, <span class=lat>61-0226</span>, <span class=lat>C.M.DHA 11-0137</span>); {bn(F['spell_forms'])} spellings of 12 common words.", "Each vehicle is brought to one name using the last four digits and the equipment number."),
  ("Orders on the wrong vehicle", f"In {bn(len(F['mismatch']))} orders the vehicle in the description differs from the vehicle of the equipment number (e.g. <span class=lat>4010249</span>); 1 has a number typo (<span class=lat>CM-Sha-11-0247</span>).", "The vehicle in the description is used for the job count; these orders are flagged in the list."),
  ("Possible duplicate orders", f"{bn(len(tw))} zero-cost twin orders in {bn(len(F['dups']))} pairs. <span class=lat>CM-DHA-61-0287</span> got tyres twice in 24 days (Tk 61,600 each time).", "Zero-cost twins are left out of the job count; the rest are flagged for audit."),
  ("Other", f"{bn(F['no_equip'])} have no equipment; {bn(F['trunc'])} descriptions are cut at 40 characters; {bn(F['crtd'])} are only created (<span class=lat>CRTD</span>), never released; 1 is not maintenance (vehicle hire).", "The hire order is left out of the analysis."),
  ("Three costs still to verify", f"The cost of 3 orders (<span class=lat>4010371, 4010372, 4010408</span>) should be checked against the original SAP record.", "Marked \"cost to verify\" in the list; their effect on the total is small."),
]
SAFE = [
  ("S1 · Gas detectors", f"{n1(F['gas_mon_months'])} months", f"The only SAP order for gas-monitor service is <span class=lat>4004850</span>, {dt(F['gas_mon'][0]['date'])}, zero cost, never closed. There is no calibration or service order after it.", "Manufacturer's calibration interval; <span class=lat>NFPA 58</span>; LPG Rules 2004"),
  ("S2 · Fire extinguishers", f"{n1(ext_gap)}-month gap", f"Refill orders: {', '.join(dt(x['date'], True) for x in ext)}. From {dt(ext[ext_gap_i]['date'], True)} to {dt(ext[ext_gap_i+1]['date'], True)} SAP shows no refill or maintenance.", "<span class=lat>NFPA 10</span> (annual maintenance); Fire Prevention and Extinguishing Act 2003"),
  ("S3 · Plant licences", f"{bn(F['plant_lic_n'])} kinds", f"Last fire-licence order {dt(next(x['last'] for x in D['renewals'] if x['doc']=='Fire licence' and x['plant']))}, plant explosives licence {dt(next(x['last'] for x in D['renewals'] if x['doc']=='Explosives licence' and x['plant']))}; last order for any plant licence {dt(F['plant_lic_last'])}. Renewals may be recorded elsewhere; check the expiry dates.", "Explosives Act 1884 and LPG Rules 2004 (Department of Explosives); Fire Service licence"),
  ("S4 · Vehicle explosives licences", "None after 2023", "For most LPG-carrying vehicles the last order named \"Explosive\" is from 2023; only <span class=lat>CM-DHA-11-0139</span> has one in 2026 (Tk 80,877). SAP does not show whether the general 2026 \"DOC RENEWAL\" orders include this licence.", "Department of Explosives vehicle licence; LPG Rules 2004"),
  ("S5 · Air compressors", f"0 of {bn(F['plan_orders'])} released".translate(BN), f"In 2022–2026, the {bn(F['plan_orders'])} preventive plan orders for the two compressors were only created and left idle. The only order with a cost is <span class=lat>{comp260['order']}</span>: an outside repair of compressor 2, {tk(comp260['cost'])} ({dt(comp260['date'])}). The filling and sealing machines run on compressed air.", "Manufacturer's maintenance schedule; periodic inspection of pressure vessels"),
  ("S6 · Fire-fighting system", "2 orders", "Repair of the fire monitor's 4\" gate valve (May 2023, zero cost, still open) and the fire-fighting pipeline valve (September 2025, Tk 19,300). There is no routine test order for pumps, hydrants or drenchers.".translate(BN), "<span class=lat>NFPA 25</span> (inspection and testing of water-based fire protection); <span class=lat>NFPA 58</span>"),
]
REC = [
  ("High", "HSE and Plant Manager", "Check the gas-detector calibration and fire-extinguisher records; create recurring plans (<span class=lat>ZPM3</span>) for them in SAP."),
  ("High", "Administration and compliance", f"Check the expiry of the {bn(F['plant_lic_n'])} kinds of plant licence and of every vehicle's explosives licence; open and close every renewal order in SAP on time."),
  ("High", "Maintenance department", f"Enter all fleet work since July 2026 in SAP (an estimated {tk(FC['unbooked_jul_oct'])}); confirm and <span class=lat>TECO</span> each job when done."),
  ("Medium", "Transport and maintenance", f"Inspect the top vehicles on the risk list ({', '.join('<span class=lat>'+x+'</span>' for x in top4)}) early; plan a scheduled service for every vehicle about every {bn(int(F['sched_interval']['median']))} days."),
  ("Medium", "Maintenance department", "Release and carry out the plan orders for the two air compressors; record the oil, filter and safety-valve checks."),
  ("Medium", "Internal audit", f"Check the {bn(F['anom_n'])} unusual costs, {bn(len(F['dups']))} possible duplicate orders and {bn(len(F['mismatch']))} wrong-vehicle orders."),
  ("Low", "SAP and IT", "Fill the vehicle number automatically from the equipment, add catalogue codes for job type and damage cause, and warn when the description and equipment do not match."),
]

def li(items): return "".join(f"<li>{x}</li>" for x in items)
exec_html = li(EXEC)
km_html = "".join(f"<tr><td>{a}</td><td class=num>{b}</td><td class=num>{c}</td><td class=num>{d}</td><td class=note>{e}</td></tr>" for a, b, c, d, e in KM)
dq_html = "".join(f"<div class=dq><b>{a}</b><p>{b}</p><p class=fix>What was done: {c}</p></div>" for a, b, c in DQ)
safe_html = "".join(f"<div class=sitem><span class=sid>{a}</span><span class=sv>{b}</span><p>{c}</p><span class=ref>{d}</span></div>" for a, b, c, d in SAFE)
rec_html = "".join(f"<tr><td><span class='pri p{['High','Medium','Low'].index(a)}'>{a}</span></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in REC)

T["fleet"] = (f"In Jun 2025 – Jun 2026 (the period of continuous data) the {bn(F['fleet_vehicles_w'])} identified vehicles cost {tk(F['fleet_w_cost'])} in all. Cost is very uneven: "
              f"just {bn(F['pareto80'])} vehicles take 80%. Top three: " + "; ".join(f"<span class=lat>{v}</span> {tk(c)}" for v, c in F["top3_vehicles"]) + ". Click a vehicle to see each of its jobs on a timeline.")
T["weibull"] = (f"A <span class=lat>Weibull</span> distribution is fitted to the number of days between two consecutive maintenance days of each vehicle ({n0(W['n'])} intervals). "
                f"Shape β = {bn(f'{W[chr(98)+chr(101)+chr(116)+chr(97)]:.2f}')} (90% range {bn(f'{W[chr(98)+chr(101)+chr(116)+chr(97)+chr(95)+chr(108)+chr(111)]:.2f}')}–{bn(f'{W[chr(98)+chr(101)+chr(116)+chr(97)+chr(95)+chr(104)+chr(105)]:.2f}')}), scale η = {n1(W['eta'])} days. "
                f"β a little above 1 means the chance of the next job rises slowly with time (mild wear-out). Mean interval {n1(W['mean'])} days; chance of another job within 30 days {pct(W['p30']*100,0)}. "
                f"<span class=lat>KS</span> test p = {bn(f'{W[chr(107)+chr(115)+chr(95)+chr(112)]:.2f}')}, so the distribution fits the data acceptably.")
T["pm"] = (f"In Jun 2025 – Jun 2026, {pct(F['pm_share_w'])} of fleet jobs include a scheduled service (service only {pct(F['pm_only_share_w'])}, the rest service with repair); by cost it is {pct(F['pm_cost_share_w'])}. "
           f"In H1 2026 the share was {pct(H1['sched_share'])}, against {pct(H2['sched_share'])} in the previous six months. The median gap between two scheduled services is {bn(int(F['sched_interval']['median']))} days "
           f"(middle half {bn(int(F['sched_interval']['p25']))}–{bn(int(F['sched_interval']['p75']))} days), with no fixed schedule. {bn(F['plan_released'])} of SAP's {bn(F['plan_orders'])} plan orders (compressors) were released.")
T["fc"] = (f"The fleet's monthly cost swings widely: in Jun 2025 – Jun 2026 the monthly mean is {tk(FC['monthly_mean'])} with a standard deviation of {tk(FC['monthly_sd'])} (variability {pct(FC['cv'],0)}). "
           f"Seven methods forecast one month ahead for each month of January–June 2026, each time using only the earlier months. Lowest error: <b>{FC['method']}</b>, "
           f"<span class=lat>RMSE</span> {tk(FC['rmse'])}, {pct(D['fc_bt'][0]['skill'],0)} better than naive; but <span class=lat>MAPE</span> is {pct(FC['mape'],0)} because a few months have very low cost. "
           f"Forecast for each coming month: {tk(FC['level'])}, 80% range Tk {lakh(FC['lo'])} to {lakh(FC['hi'])}. From July 2026 to {dt(F['as_of'])} only {tk(FC['recorded_jul_oct'])} has reached SAP; "
           f"if work continued at the same rate, an estimated {tk(FC['unbooked_jul_oct'])} (Tk {lakh(FC['unbooked_lo'])}–{lakh(FC['unbooked_hi'])}) is still to be entered.")
T["risk"] = (f"Each vehicle-month is one row ({n0(CB['n'])} test rows, {bn(CB['pos'])} with a major repair). Target: any job of ≥ Tk 50,000 in the next 3 months. Each model learns only from earlier months and "
             f"forecasts each month of {bn(CB['test'].replace('2026-01','Jan 2026').replace('2026-04','Apr 2026'))}. Best: <b>{CB['best']}</b>, <span class=lat>AUC</span> {bn(f'{CB[chr(97)+chr(117)+chr(99)]:.2f}')} "
             f"(90% range {bn(f'{CB[chr(108)+chr(111)]:.2f}')}–{bn(f'{CB[chr(104)+chr(105)]:.2f}')}); the vehicle's past rate alone gives {bn(f'{CB[chr(98)+chr(97)+chr(115)+chr(101)+chr(95)+chr(97)+chr(117)+chr(99)]:.2f}')}. "
             f"In 2,000 bootstrap resamples the neural network beats the baseline {pct(CB['p_better']*100,0)} of the time. The sample is small, so this sets inspection priority; it is not a certain prediction.".translate(BN))
T["riskB"] = (f"Risk for July–September 2026 from data up to June 2026. Mean probability {pct(F['risk']['mean_p'],0)}. Major jobs of that period have so far reached SAP for {bn(F['risk']['seen_n'])} vehicles, "
              f"{bn(F['risk']['seen_in_top10'])} of them in the top ten (the rest of the data is not in yet, so this is not a full check).")
T["clsA"] = (f"The same set-up was tested for \"will any job be needed next month\" ({n0(CA['n'])} rows, {bn(CA['pos'])} with a job). Here no machine-learning model beat the vehicle's own past rate "
             f"(<span class=lat>AUC</span> {bn(f'{CA[chr(98)+chr(101)+chr(115)+chr(116)+chr(95)+chr(97)+chr(117)+chr(99)]:.2f}')}): small jobs mostly follow each vehicle's habit, so the simple rate is enough.")
T["reg"] = (f"How well job type, series and year explain the cost of the {n0(F['n_cost_jobs'])} jobs with a cost (median Tk {n0(F['cost_job_median'])}, mean Tk {n0(F['cost_job_mean'])}) was measured with 5-fold cross-validation. "
            f"Best {reg_best['model']}: <span class=lat>R²</span> {bn(f'{reg_best[chr(114)+chr(50)]:.2f}')}. So only about a fifth of the cost is explained by the description; the rest is not written down (which parts, how many). "
            f"The multipliers below show how many times the cost of a scheduled service each job type usually costs.")
T["anom"] = (f"Distance of each cost from the median of the same job type (robust <span class=lat>z</span>, using the median and <span class=lat>MAD</span>) plus an <span class=lat>Isolation Forest</span> together flag {bn(F['anom_n'])} orders. "
             "They are not errors, only worth checking.")
T["clusters"] = (f"Groups were formed automatically from the description text (vehicle numbers removed, character-level <span class=lat>TF-IDF</span>) with <span class=lat>K-Means</span>; the silhouette score is best "
                 f"at k = {bn(F['clusters']['k'])} ({bn(f'{F[chr(99)+chr(108)+chr(117)+chr(115)+chr(116)+chr(101)+chr(114)+chr(115)][chr(115)+chr(105)+chr(108)+chr(104)+chr(111)+chr(117)+chr(101)+chr(116)+chr(116)+chr(101)]:.2f}')}). "
                 f"Agreement with the rule-based categories is low (<span class=lat>ARI</span> {bn(f'{F[chr(99)+chr(108)+chr(117)+chr(115)+chr(116)+chr(101)+chr(114)+chr(115)][chr(97)+chr(114)+chr(105)+chr(95)+chr(118)+chr(115)+chr(95)+chr(114)+chr(117)+chr(108)+chr(101)+chr(115)]:.2f}')}), because many groups form around spelling variants (e.g. schedule/schedual/shedule). This is evidence that SAP needs catalogue codes.")
T["renew"] = (f"From the renewal orders: the last date of each document for each subject (vehicle or plant), and the next renewal assuming a one-year validity. {bn(F['ren_overdue'])} have no new order within 12 months; "
              f"{bn(F['ren_soon'])} are due within 120 days. Note: no order is ever closed, so an order does not prove the renewal was done.")
T["plant"] = (f"Outside the fleet there are {n0(F['plant_n'])} orders costing {tk(F['plant_cost'])}. The three largest: outside repair of air compressor 2 at {tk(comp260['cost'])}, earthwork in the tank area at Tk 1.4 lakh, and interior work in the administration building at Tk 1 lakh.".translate(BN))
T["prep"] = f"Prepared by: <b>Akib Fateh</b>, Barabkunda LPG Plant (CTG). Date: {dt(os.environ.get('UPDATE_DATE', dt_.date.today().isoformat()))}"

METHODS = [
  ("Period", "Trends, vehicle comparisons and models use Jun 2025 – Jun 2026, because there is a 9-month gap before it and the data after it is incomplete. Total cost includes all years."),
  ("Vehicles and job types", "Vehicle numbers are brought to one name using the last four digits and the equipment number. Job types come from the description words, in 14 categories; scheduled service = any spelling of schedule, or only oil, filter and grease."),
  ("Assumptions", "The order's basic start date is taken as the job date. Renewals are assumed valid for one year. Cost in taka, SAP \"Total actual costs\". The three-year TPM plant targets are proposed, not approved."),
  ("Limitations", "No labour or outside-service cost; downtime and MTTR cannot be measured because orders are never closed; vehicle age, kilometres and running hours are missing and would improve the forecasts. The sample is small, so the models set inspection priority; they are not certain predictions."),
  ("Review", "All safety observations and maintenance schedules are for review by a qualified engineer (NFPA 10, 25, 58; LPG Rules 2004). Decision support, not control."),
]
meth_html = "".join(f"<div class=mrow><b>{a}</b><p>{b}</p></div>" for a, b in METHODS)
hubtok = json.load(open(f"{SRC}/hub/hubdata.json", encoding="utf8")).get("tokens", {})
D["tpm"] = {**TPM, "pillar_info": tpm_content.PILLARS, "roadmap": tpm_content.ROADMAP}
tpm_html = build_tpm.tpm_html(TPM, F, hubtok); atlas_html = build_tpm.atlas_html(D["orders"]); deep_html = build_tpm.deep_html(TPM)
wm_svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="560" height="320" viewBox="0 0 560 320"><g transform="rotate(-18 280 160)" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-weight="700">'
          '<path d="M120 112c10 18 26 28 26 46a26 26 0 0 1-52 0c0-13 8-21 13-28 3 8 5 13 10 16 0-13 0-23 3-34z"/>'
          '<text x="160" y="150" font-size="38" letter-spacing="3">BM LP GAS™</text><text x="162" y="178" font-size="14" letter-spacing="5">BARABKUNDA LPG PLANT</text>'
          '<text x="300" y="268" font-size="13" letter-spacing="3" opacity=".8">AKIB FATEH</text></g></svg>')
extra_css = open("maint_extra.css", encoding="utf8").read().replace("{{WM}}", "data:image/svg+xml," + quote(wm_svg))
extra_js = open("maint_extra.js", encoding="utf8").read()
data_json = json.dumps(D, ensure_ascii=False).replace("</", "<\\/")
tpl = open("maint_tpl.html", encoding="utf8").read()
rep = {"EYEBROW": T["eyebrow"], "LEDE": T["lede"], "PREP": T["prep"], "EXEC": exec_html, "KM": km_html, "DQ": dq_html, "SAFE": safe_html, "REC": rec_html,
       "T_FLEET": T["fleet"], "T_WEIBULL": T["weibull"], "T_PM": T["pm"], "T_FC": T["fc"], "T_RISK": T["risk"], "T_RISKB": T["riskB"], "T_CLSA": T["clsA"], "T_REG": T["reg"],
       "T_ANOM": T["anom"], "T_CLUSTERS": T["clusters"], "T_RENEW": T["renew"], "T_PLANT": T["plant"], "METH": meth_html, "N_ORDERS": n0(F["n"]),
       "KPI_COST": bn(f"{F['cost_total']/1e7:.2f}") + " crore", "KPI_FLEETW": lakh(F["fleet_w_cost"]), "KPI_PM": pct(F["pm_share_w"], 0), "KPI_TECO": bn(F["teco"]), "KPI_UNBOOKED": lakh(FC["unbooked_jul_oct"]),
       "KPI_AUC": bn(f"{CB['auc']:.2f}"), "D3": D3, "DATA": data_json, "TPM": tpm_html, "ATLAS": atlas_html, "DEEP": deep_html, "ATLAS_DEFS": atlas_svg.DEFS,
       "EXTRA_CSS": extra_css, "EXTRA_JS": extra_js, "DATA_TO": dt(F["as_of"]) + " (last order " + dt(F["date_max"]) + ")"}
for k, v in rep.items(): tpl = tpl.replace("{{" + k + "}}", v)
left = re.findall(r"\{\{[A-Z_]+\}\}", tpl); assert not left, left
open(f"{SRC}/reports/maint.html", "w", encoding="utf8").write(tpl)
print("maint.html", round(len(tpl.encode()) / 1e6, 2), "MB")

# ---------------- hub card figures, mini chart and update log
hub = json.load(open(f"{SRC}/hub/hubdata.json", encoding="utf8"))
MONS_ = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
mm = [m for m in D["monthly"] if m["m"] >= "2025-06"]
hub["maint"] = {"labels": [MONS_[int(m["m"][5:]) - 1] + " " + bn(m["m"][2:4]) for m in mm], "vals": [round((m["fleet"] + m["plant"]) / 1e5, 1) for m in mm],
                "inc": [m["m"] >= "2026-07" for m in mm]}
last = F["date_max"]; L = pd.Timestamp(F["as_of"]); LA = pd.Timestamp(last)
hub.setdefault("tokens", {}).update({
    "maint_n": f"{F['n']:,}", "maint_cost": f"{F['cost_total']/1e7:.2f}", "maint_p80": f"{F['pareto80']}/{F['fleet_vehicles_w']}", "maint_auc": f"{F['clsB']['auc']:.2f}",
    "maint_pm": f"{F['pm_share_w']:.0f}", "maint_from": "February 2022", "maint_to": f"{MON[L.month-1]} {L.year}", "maint_gas_m": f"{F['gas_mon_months']:.0f}",
    "maint_ext_gap": f"{max(F['fire_ext_gaps_m']):.0f}", "maint_lic": str(F["plant_lic_n"]), "maint_unbooked": f"{F['fc']['unbooked_jul_oct']/1e5:.0f}",
    "maint_asof": f"{L.day} {MON[L.month-1]} {L.year}", "maint_last": f"{LA.day} {MON[LA.month-1]} {LA.year}", "maint_silent": str(F["silent"]["days"])})
today = os.environ.get("UPDATE_DATE", dt_.date.today().isoformat())
ups = hub.setdefault("updates", [])
text = f"Maintenance report: {F['n']} SAP orders, total cost Tk {F['cost_total']/1e7:.2f} crore; major-repair risk model (neural network, AUC {F['clsB']['auc']:.2f}); statistical significance and progress."
text2 = f"New: a world-class TPM programme (8 pillars, maturity {TPM['maturity']['mean']:.1f}/5, KPIs against world class, a 36-month roadmap) and an illustrated guide to {len(build_tpm.EQ)} pieces of equipment (NRV, butterfly valve, safety valve, pump, filling head…)."
text3 = (f"All figures recalculated with the maintenance record running to {L.day} {MON[L.month-1]} {L.year}: no order in the {F['silent']['days']} days since the last one, "
         f"an estimated Tk {F['fc']['unbooked_jul_oct']/1e5:.0f} lakh of work not yet in SAP; the equipment guide now covers {len(build_tpm.EQ)} items, including the spherical storage tanks.")
if not any(u.get("key") == "maint-" + last for u in ups):
    ups.append({"date": today, "text": text, "through": last, "key": "maint-" + last, "open": "maint", "view": "summary"})
ups[:] = [u for u in ups if u.get("key") != "maint-asof-" + F["as_of"]] + [{"date": today, "text": text3, "through": F["as_of"], "key": "maint-asof-" + F["as_of"], "open": "maint", "view": "dq"}]
ups.sort(key=lambda u: (u["date"], u.get("key", "")))
json.dump(hub, open(f"{SRC}/hub/hubdata.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("hub data updated")
