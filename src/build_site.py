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
ups = sorted(hub.get("updates", []), key=lambda u: (u["date"], u.get("key", "")))
if ups:
    last = ups[-1]["date"]; cur_, old_ = [u for u in ups if u["date"] == last], [u for u in ups if u["date"] != last]
    btn = lambda u: f' <button class="go main sm" data-open="{u["open"]}"' + (f' data-view="{u["view"]}"' if u.get("view") else "") + '>View <span class="arr">→</span></button>' if u.get("open") else ""
    strip = (f'<div class="upd" id="latest"><span class="when">Latest update · {ldate(last)}</span><div class="what">'
             + "".join(f'<div class="ln"><span>{esc(u["text"])}</span>{btn(u)}</div>' for u in reversed(cur_)) + "</div>"
             + (f'<details class="old"><summary>Earlier updates</summary><ul>' + "".join(f"<li>{ldate(u['date'])}: {esc(u['text'])}</li>" for u in reversed(old_)) + "</ul></details>" if old_ else "") + "</div>")
    hub.setdefault("tokens", {})["update_strip"] = strip
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
for k, v in hub.get("tokens", {}).items(): src = src.replace("{{" + k + "}}", v)
left = re.findall(r"\{\{\w+\}\}", src)
assert not left, f"unfilled tokens: {left}"
data = {k: v for k, v in hub.items() if k != "tokens"}
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
