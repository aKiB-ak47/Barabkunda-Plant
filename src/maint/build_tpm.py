"""HTML for the TPM programme view, the equipment guide view and the deeper-analytics section of the maintenance report."""
import html, re, math
import pandas as pd
import atlas_svg as A
from atlas_content import EQ, STAGES, WHO
import tpm_content as TC

BN = str.maketrans("0123456789", "0123456789")
def bn(x): return str(x).translate(BN)
def n0(x): return bn(f"{x:,.0f}")
def n1(x): return bn(f"{x:,.1f}")
def pct(x, d=1): return bn(f"{x:.{d}f}") + "%"
def tk(x):
    if abs(x) >= 1e7: return "Tk " + bn(f"{x/1e7:.2f}") + " crore"
    if abs(x) >= 1e5: return "Tk " + bn(f"{x/1e5:.1f}") + " lakh"
    return "Tk " + bn(f"{x:,.0f}")
esc = lambda s: html.escape(str(s), quote=True)
LAT = lambda s: f"<span class=lat>{s}</span>"
FREQ_ORDER = [("Every", "Each time/shift"), ("Daily", "Daily"), ("Weekly", "Weekly"), ("Monthly", "Monthly"), ("Quarterly", "Quarterly"), ("Half-yearly", "Half-yearly"), ("Yearly", "Yearly")]
def fbucket(f):
    for k, lab in FREQ_ORDER:
        if f.startswith(k) or (k == "Every" and f.startswith("Every ")): return lab
    return "Other / manufacturer"

# ------------------------------------------------------------------ TPM view
def tpm_html(T, F, hubtok):
    K = {k["k"]: k for k in T["kpis"]}; cal = T["cal"]
    pil = {p["k"]: p for p in T["pillars"]}
    mat = T["maturity"]
    # hero
    out = [f'''<section class="blk first" id="tpm-top"><div class="tpm-hero">
<div><span class="eyebrow">Total Productive Maintenance · Barabkunda LPG Plant</span>
<h1>Zero breakdowns, zero defects, <em>zero accidents</em></h1>
<p class="lede">A complete TPM programme for Barabkunda, built on eight pillars and a 5S foundation. The current state of every pillar is measured from this plant's own maintenance and weight-check data; where data is missing, that is said plainly.</p>
<div class="zeros"><span><b>{pct(K["reactive"]["v"], 0)}</b> of jobs after a breakdown</span><span><b>{pct(100 - cal["within150_26"], 1)}</b> of cylinders outside the weight limit (2026)</span><span><b>6</b> safety maintenance items open</span></div>
<p class="prep">Prepared by: Akib Fateh · Barabkunda LPG Plant (CTG)</p></div>
<div class="matwrap"><div id="matGauge" class="matg"></div><p class="small">TPM maturity index: mean of {bn(mat["measured"])} measured pillars ({bn(mat["total"] - mat["measured"])} have no data). 1 = reactive, 3 = planned, 5 = world class.</p></div>
</div></section>''']
    # house
    out.append(f'''<section class="blk" id="tpm-house"><div class="sh"><span class="kick">The TPM house</span><h2>Eight pillars: where we stand</h2>
<p>Each pillar's colour shows its current level (1–5). Click a pillar to see its goal, evidence, first-90-day actions, KPIs and owners. How each level was scored is written in the pillar's evidence.</p></div>
<div class="housegrid"><div class="card"><div id="house"></div></div><div class="card pdetail" id="pdetail" aria-live="polite"></div></div></section>''')
    # KPI scorecard
    rows = []
    for k in T["kpis"]:
        v = k["v"]; u = k["unit"]
        val = "—" if v is None else (bn(f"{v:.2f}") if k["k"] == "cpk" else (n1(v) + ("%" if u == "%" else f" {u}")))
        tgt = "—" if k["target"] is None else (bn(f"{k['target']:g}") + ("%" if u == "%" else (f" {u}" if u else "")))
        wc = "—" if k["world"] is None else (bn(f"{k['world']:g}") + ("%" if u == "%" else (f" {u}" if u else "")))
        prog = k["progress"]
        st = "gap" if v is None else ("ok" if prog is not None and prog >= 90 else ("warn" if prog is not None and prog >= 50 else "bad"))
        stl = {"gap": "Not measured", "ok": "Near target", "warn": "Halfway", "bad": "Far off"}[st]
        bar = f'<div class="prog"><i style="width:{0 if prog is None else prog:.0f}%"></i></div><span class="small">{"" if prog is None else pct(prog, 0) + " of the way to world class"}</span>'
        rows.append(f'<div class="kc {st}" data-k="{k["k"]}"><div class="kh"><b>{k["name"]}</b><span class="chip {st}">{stl}</span></div><div class="kv">{val}</div>'
                    f'<div class="kt"><span>Plant target (3 years): <b>{tgt}</b></span><span>World class: <b>{wc}</b></span></div>{bar}<p class="small">{bn(k["basis"])}</p></div>')
    half = T["half"]
    def hv(f, d=1): a, b = half[f]["h2_2025"], half[f]["h1_2026"]; return "—" if a is None or b is None else f"{n1(a)} → {n1(b)}"
    out.append(f'''<section class="blk" id="tpm-kpi"><div class="sh"><span class="kick">KPIs and progress</span><h2>Where we stand against world class</h2>
<p>Each KPI's current value, a proposed three-year plant target and the world-class benchmark common in industry (Nakajima's 85% for OEE). The bar shows how much of the way to world class has been covered.
H2 2025 to H1 2026: planned work {hv("planned")}%, back-dated orders {hv("backdated")}%, repeat repairs {hv("repeat")}%.</p></div>
<div class="kgrid">{"".join(rows)}</div>
<div class="card" style="margin-top:16px"><h3>Quarterly trend and targets</h3><p class="small">Dashed line = proposed plant target. SAP has very few orders from mid-2024 to mid-2025, so those quarters are blank.</p><div class="spk" id="spk"></div></div>
</section>''')
    # losses + OEE
    give = f"{cal['giveaway_mt']:.1f}".translate(BN) + " t"
    fill = {"reactive": pct(K["reactive"]["v"], 0), "out150": pct(100 - cal["within150_26"], 1) + " (2026)", "backdated": pct(100 - K["timely"]["v"], 0),
            "top3": ", ".join(v[-4:] for v, _ in F["top3_vehicles"]).translate(BN), "give": give}
    lc = []
    for cat, nm, ex, src in TC.LOSSES:
        txt = ex.format(**fill)
        lc.append(f'<div class="lc {"data" if src == "data" else "gap"}"><span class="lcat">{cat}</span><b>{nm}</b><p>{txt}</p><span class="chip {"blue" if src == "data" else ""}">{"Measured from data" if src == "data" else "Not measured yet"}</span></div>')
    q = cal["within150_26"]
    out.append(f'''<section class="blk" id="tpm-loss"><div class="sh"><span class="kick">The 16 major losses</span><h2>Where the losses are</h2>
<p>Nakajima's 16 losses, written for an LPG bottling plant. Losses marked blue are measured from this site's own data; the rest need downtime and production logs.</p></div>
<div class="lgrid">{"".join(lc)}</div>
<div class="card oee" style="margin-top:16px"><div><h3>Filling carousel OEE</h3><p class="t small">OEE = availability × performance × quality. World class is 85% (90% × 95% × 99.9%).</p></div>
<div class="oeef"><div class="of"><span>Availability</span><b>?</b><em>needs a downtime log</em></div><span class="x">×</span><div class="of"><span>Performance</span><b>?</b><em>needs rated vs actual speed</em></div><span class="x">×</span>
<div class="of on"><span>Quality</span><b>{pct(q, 1)}</b><em>within ±150 g in {n0(cal["checks26"])} weight checks of 2026</em></div><span class="x">=</span><div class="of"><span>OEE</span><b>≤ {pct(q, 0)}</b><em>quality alone caps the maximum</em></div></div></div>
</section>''')
    # office TPM: SAP funnel
    out.append(f'''<section class="blk" id="tpm-sap"><div class="sh"><span class="kick">Office TPM</span><h2>Where SAP orders get stuck</h2>
<p>The full life cycle of a maintenance order: created → released → materials and cost → confirmation → technically closed. Almost all of Barabkunda's {n0(F["n"])} orders stop after cost posting, so downtime, time to repair (MTTR) and actual job dates cannot be measured.</p></div>
<div class="grid2"><div class="card"><h3>Order life cycle</h3><div class="chart" id="funnel"></div></div><div class="card"><h3>Share of back-dated orders, by quarter</h3><p class="small">Orders opened more than 30 days after the job date. Target ≤ 10%.</p><div class="chart" id="lateQ"></div></div></div></section>''')
    # autonomous maintenance + F-tag + 5S audit
    steps = "".join(f'<li><span class="sn">{bn(i + 1)}</span><div><b>{a}</b><p>{b}</p><span class="small">Exit criterion: {c}</span></div></li>' for i, (a, b, c) in enumerate(TC.AM_STEPS))
    tags = "".join(f'<div class="ftag" style="--c:{c}"><b>{a}</b><p>{b}</p></div>' for a, b, c in TC.FTAG)
    s5 = "".join(f'<div class="s5g"><b>{bn(i + 1)}. {nm}</b>' + "".join(f'<label class="s5q"><span>{q}</span><select data-s="{i}"><option value="0">0 none</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4 full</option></select></label>' for q in qs) + '</div>' for i, (nm, qs) in enumerate(TC.S5))
    out.append(f'''<section class="blk" id="tpm-am"><div class="sh"><span class="kick">Autonomous maintenance and 5S</span><h2>Operators and drivers: the first guardians of the equipment</h2>
<p>The seven steps of Jishu Hozen, a defect-tag system and a 5S audit you can score right here. Audit scores stay only in this browser; print and sign them for the record.</p></div>
<div class="grid2"><div class="card"><h3>Seven steps</h3><ol class="amst">{steps}</ol></div>
<div class="stack"><div class="card"><h3>Defect tags (F-tags)</h3><div class="ftags">{tags}</div><p class="small" style="margin-top:8px">Every tag goes in the logbook and as an SAP notification; weekly open/closed counts on the TPM board.</p></div>
<div class="card"><div class="cap"><b>5S audit</b><span id="s5score" class="s5score">0 / 60</span></div><div class="s5">{s5}</div><div class="btns" style="margin-top:10px"><button class="btn" id="s5reset">Clear</button><button class="btn" id="s5print">Print</button></div></div></div></div></section>''')
    # planned maintenance calendar (from the equipment guide + extra items)
    items = [(e["name"], e["id"], e["pm"]) for e in EQ] + [(nm, None, pm) for nm, _, pm in TC.EXTRA_PM]
    cols = [lab for _, lab in FREQ_ORDER] + ["Other / manufacturer"]
    trs = []
    for nm, eid, pm in items:
        cells = {c: [] for c in cols}
        for task, f, who, clit in pm:
            cells[fbucket(f)].append(f'<span class="tk w{who}" data-w="{who}" title="{esc(f)} · {WHO[who]} · {clit}"><i>{"/".join(clit)}</i>{task}</span>')
        link = f' <a class="eqlink" href="#eq-{eid}" data-eq="{eid}">Picture →</a>' if eid else ""
        trs.append(f'<tr><th scope="row">{nm}{link}</th>' + "".join(f'<td>{"".join(cells[c])}</td>' for c in cols) + '</tr>')
    whof = "".join(f'<button class="btn{" on" if k == "all" else ""}" data-who="{k}">{v}</button>' for k, v in [("all", "All"), ("O", "Operator/driver"), ("T", "Technician"), ("E", "Engineer"), ("V", "Contractor"), ("H", "HSE")])
    out.append(f'''<section class="blk" id="tpm-pm"><div class="sh"><span class="kick">Planned maintenance</span><h2>What to do on which equipment, how often, and who does it</h2>
<p>Clean (C), Lubricate (L), Inspect (I), Tighten (T): the CLIT standard and schedule for every piece of equipment in one table. This is the draft for the SAP maintenance plans (ZPM3). Manufacturer's instructions, licence conditions and the applicable codes (NFPA 10, 25, 58; LPG Rules 2004) take precedence. For review by a qualified engineer.</p></div>
<div class="vbar"><span class="small">Owner:</span><div class="btns" id="whoF">{whof}</div></div>
<div class="card"><div class="tw pmcal"><table><thead><tr><th>Equipment</th>{"".join(f"<th>{c}</th>" for c in cols)}</tr></thead><tbody>{"".join(trs)}</tbody></table></div></div></section>''')
    # quality maintenance matrix
    qm = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td></tr>" for a, b, c, d, e in TC.QM)
    hot = hubtok.get("cal_hot_list", "").translate(BN)
    out.append(f'''<section class="blk" id="tpm-qm"><div class="sh"><span class="kick">Quality maintenance</span><h2>Which conditions must be held for the right weight</h2>
<p>In 2026 the filling process Cpk is {bn(f"{cal['cpk26']:.2f}")} ({bn(f"{cal['cpk24']:.2f}")} in 2024; target ≥ 1.33), with average overfill +{n1(cal["mean26"])} g. Heads flagged in the weight checks: {hot}. To prevent defects, each condition below must be held at its set value.</p></div>
<div class="card"><div class="tw"><table><thead><tr><th>Quality characteristic</th><th>Equipment condition</th><th>Standard</th><th>Check method</th><th>How often</th></tr></thead><tbody>{qm}</tbody></table></div></div></section>''')
    # kaizen board
    rep_cost = T["repeat_cost"]; v1 = F["top3_vehicles"][0]
    projects = [
     ("Plan", "Reduce overfilling", f"An estimated {give} of LPG given away free in Mar–Oct 2026; Cpk {bn(f'{cal['cpk26']:.2f}')}.", "Cpk ≥ 1.33; mean error within ±20 g", "Quality control + maintenance", "q"),
     ("Plan", "Repeat repairs within 90 days", f"{pct(T['repeat_rate'], 0)} of {bn(T['repeat_base'])} repairs in Jun 2025 – Mar 2026 hit the same part again; repeat cost over all time {tk(rep_cost)}.", "Repeats ≤ 8%", "Head of Maintenance", "k"),
     ("Plan", f"Most expensive vehicle ({v1[0][-4:]})".translate(BN), f"{tk(v1[1])} in Jun 2025 – Jun 2026; repeated engine and clutch work.", "Find the root cause; replace-vs-repair costing", "Head of Transport", "k"),
     ("Plan", "SAP order discipline", f"Confirmation {pct(K['cnf']['v'], 1)}, TECO {pct(K['teco']['v'], 0)}, orders on time {pct(K['timely']['v'], 0)}.", "All three ≥ 90%", "Maintenance planner", "o"),
     ("Plan", "Safety-equipment validity", f"Last gas-detector order {n1(F['gas_mon_months'])} months ago; a 31-month gap in fire extinguishers.", "All safety equipment in date, with recurring plans in SAP", "HSE Manager", "s"),
     ("Plan", "Start the air-compressor plans", f"None of the {bn(F['plan_orders'])} plan orders released; a major outside repair on compressor 2.", "Plan compliance ≥ 95%", "Head of Maintenance", "p"),
    ]
    col = {"Plan": "Plan (P)", "Do": "Do (D)", "Check": "Check (C)", "Act": "Act / standardise (A)"}
    cards = {c: [] for c in col}
    for st, nm, base, tgt, own, pk in projects:
        cards[st].append(f'<div class="kz"><span class="chip">{TC.PILLARS[{"q": "qm", "k": "kk", "o": "ot", "s": "she", "p": "pm"}[pk]]["jp"]}</span><b>{nm}</b><p><span class="small">Baseline:</span> {base}</p><p><span class="small">Target:</span> {tgt}</p><p class="small">Owner: {own}</p></div>')
    out.append(f'''<section class="blk" id="tpm-kaizen"><div class="sh"><span class="kick">Focused improvement</span><h2>Kaizen board</h2>
<p>The first six projects, chosen from the data, each with a numeric baseline and target. All are now in the plan stage; each card moves one step a month.</p></div>
<div class="kanban">{"".join(f'<div class="kcol"><h4>{col[c]} <span class="small">{bn(len(cards[c]))}</span></h4>{"".join(cards[c]) or chr(10) + "<p class=small>None yet</p>"}</div>' for c in col)}</div></section>''')
    # skills matrix
    head = "".join(f"<th><span>{s}</span></th>" for s in TC.SKILLS)
    body = "".join(f"<tr><th scope=row>{r}</th>" + "".join(f'<td class="lv l{v}">{bn(v) if v else "—"}</td>' for v in TC.REQ[i]) + "</tr>" for i, r in enumerate(TC.ROLES))
    out.append(f'''<section class="blk" id="tpm-skill"><div class="sh"><span class="kick">Education and training</span><h2>Skills matrix: who needs to know how much</h2>
<p>The level each role needs (0 = not needed, 1 = knows, 2 = can do with help, 3 = can do alone, 4 = can teach). Put each person's current level beside it; the gaps become the training plan.</p></div>
<div class="card"><div class="tw"><table class="skill"><thead><tr><th>Role</th>{head}</tr></thead><tbody>{body}</tbody></table></div></div></section>''')
    # roadmap + governance
    gov = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in TC.GOV)
    raci = "".join(f"<tr><td>{r[0]}</td>" + "".join(f'<td class="rc">{x}</td>' for x in r[1:]) + "</tr>" for r in TC.RACI)
    out.append(f'''<section class="blk" id="tpm-road"><div class="sh"><span class="kick">Roadmap and governance</span><h2>36-month roadmap</h2>
<p>A proposed schedule from December 2026. Three months of preparation, then a pilot area (carousel and pump house), then the whole plant and fleet. Progress will be updated here every month.</p></div>
<div class="card"><div class="chart" id="gantt"></div></div>
<div class="grid2" style="margin-top:16px"><div class="card"><h3>Governance structure</h3><div class="tw"><table><thead><tr><th>Team</th><th>Members</th><th>Meeting</th><th>Responsibility</th></tr></thead><tbody>{gov}</tbody></table></div></div>
<div class="card"><h3>Responsibility chart (RACI)</h3><p class="small">R = Responsible, A = Accountable, C = Consulted, I = Informed</p><div class="tw"><table class="raci"><thead><tr><th>Task</th><th>Plant Manager</th><th>Maintenance</th><th>Production</th><th>HSE</th><th>Transport</th><th>Admin/SAP</th></tr></thead><tbody>{raci}</tbody></table></div></div></div></section>''')
    return "\n".join(out)

def tpm_data():
    return {"pillars": {k: {kk: vv for kk, vv in v.items()} for k, v in TC.PILLARS.items()}, "roadmap": TC.ROADMAP}

# ------------------------------------------------------------------ equipment guide view
def atlas_html(orders):
    O = pd.DataFrame(orders)
    plant = O[~O.group.isin(["Vehicle fleet", "Renewals and licences"])]
    chips = "".join(f'<button class="btn{" on" if k == "all" else ""}" data-st="{k}">{v}</button>' for k, v in [("all", "All equipment"), *STAGES.items()])
    cards = []
    for e in EQ:
        m = plant[plant.desc.fillna("").str.upper().str.contains(e["sap"], regex=True)]
        sap = (f'<p class="small">Related plant orders in SAP: <b>{bn(len(m))}</b>, cost {tk(m.cost.sum())}.</p><ul class="saplist">'
               + "".join(f'<li><span class=lat>{int(r.order)}</span> · {bn(pd.Timestamp(r.date).strftime("%d.%m.%Y"))} · {esc(r.desc)} · {tk(r.cost) if r.cost else "zero cost"}</li>' for r in m.sort_values("date", ascending=False).head(6).itertuples()) + "</ul>"
               if len(m) else '<p class="small">No plant maintenance order was found in SAP under this equipment name: either no work was done, or it was written under another name.</p>')
        parts = "".join(f'<li data-p="{i + 1}"><span class="pn">{bn(i + 1)}</span><div><b>{a}</b><span>{b}</span></div></li>' for i, (a, b) in enumerate(e["parts"]))
        fail = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in e["fail"])
        pm = "".join(f'<tr><td>{a}</td><td>{f}</td><td><span class="who w{w}">{WHO[w]}</span></td><td class="lat">{"/".join(c)}</td></tr>' for a, f, w, c in e["pm"])
        lpg = "".join(f"<li>{x}</li>" for x in e["lpg"])
        saf = '<span class="chip bad">Safety-critical</span>' if e.get("safety") else ""
        cards.append(f'''<article class="eq" id="eq-{e["id"]}" data-st="{e["stage"]}" data-name="{esc(e["name"] + " " + e["en"])}">
<header><div><h3>{e["name"]}</h3><span class="en">{e["en"]}</span></div><div class="eqchips"><span class="chip blue">{STAGES[e["stage"]]}</span>{saf}</div></header>
<div class="eqbody"><figure class="eqfig">{getattr(A, e["id"])()}<figcaption>Hover over or tap a part name: that part lights up in the drawing.</figcaption></figure>
<div class="eqinfo"><dl><dt>What it does</dt><dd>{e["what"]}</dd><dt>Where in the plant</dt><dd>{e["where"]}</dd><dt>How it works</dt><dd>{e["how"]}</dd></dl>
<h4>Parts</h4><ol class="parts">{parts}</ol></div></div>
<div class="eqmore"><details><summary>Special requirements for LPG</summary><ul class="lpg">{lpg}</ul></details>
<details><summary>Common failures and symptoms</summary><div class="tw"><table><thead><tr><th>Failure</th><th>What you see</th></tr></thead><tbody>{fail}</tbody></table></div></details>
<details open><summary>Maintenance (CLIT) and KPIs</summary><div class="tw"><table><thead><tr><th>Task</th><th>How often</th><th>Who</th><th>Type</th></tr></thead><tbody>{pm}</tbody></table></div><p class="small" style="margin-top:6px">KPI to track: {e["kpi"]}</p></details>
<details><summary>SAP history</summary>{sap}</details></div></article>''')
    return f'''<section class="blk first" id="atlas-top"><span class="eyebrow">LPG distribution equipment · Barabkunda</span>
<h1>From tanker to cylinder: <em>every piece of equipment</em>, illustrated</h1>
<p class="lede">{bn(len(EQ))} pieces of equipment, from the storage spheres, non-return valves and butterfly valves to safety valves, pumps, filling heads, gas detectors and fire protection: what each does, what is inside, how it fails, and who maintains what, how often.</p>
<p class="prep">Prepared by: Akib Fateh · Barabkunda LPG Plant (CTG) · All drawings are explanatory, not to scale. Maintenance schedules are for review by a qualified engineer; manufacturer's instructions and licence conditions take precedence.</p></section>
<section class="blk" id="atlas-flow"><div class="sh"><span class="kick">Flow diagram</span><h2>Where each piece of equipment sits</h2><p>From tanker unloading to storage, pumps, carousel, check-scale and dispatch, with the fire-water network below. Click any symbol to go to that equipment's full description.</p></div>
<div class="card pidwrap">{A.pid()}</div></section>
<section class="blk" id="atlas-list"><div class="sh"><span class="kick">Equipment guide</span><h2>{bn(len(EQ))} pieces of equipment</h2></div>
<div class="vbar"><div class="btns" id="stF">{chips}</div><input type="search" id="eqQ" placeholder="Search: NRV, valve, pump…" aria-label="Search equipment"></div>
<div class="eqlist">{"".join(cards)}</div></section>'''

# ------------------------------------------------------------------ deeper analytics section (analytics view)
def deep_html(T):
    sig = "".join(f'<tr><td>{s["q"]}</td><td>{s["test"]}<br><span class="small lat">{s["stat"]}</span></td><td class="num"><span class="pv {"sig" if s["p"] < 0.05 else ("mid" if s["p"] < 0.1 else "ns")}">p {"< 0.001" if s["p"] < 0.001 else "= " + bn(f"{s["p"]:.3f}")}</span></td><td>{s["effect"].translate(BN)}</td><td><b>{s["verdict"].translate(BN)}</b></td></tr>' for s in T["sig"])
    cc = T["cost_change"]; ct = T["cost_type"]; cm = T["cm"]
    prec = cm["tp"] / (cm["tp"] + cm["fp"]) * 100 if cm["tp"] + cm["fp"] else 0; rec = cm["tp"] / (cm["tp"] + cm["fn"]) * 100 if cm["tp"] + cm["fn"] else 0
    return f'''<section class="blk" id="deep"><div class="sh"><span class="kick">Significance, error, cost and progress</span><h2>How reliable the numbers are, and where the money went</h2>
<p>A statistical test behind every major claim, the error of every model, the sources of the cost change and quarterly progress. p &lt; 0.05 = significant; 0.05–0.10 = weak evidence; above that, the difference could be chance.</p></div>
<div class="card"><h3>Statistical significance</h3><div class="tw"><table class="sigt"><thead><tr><th>Question</th><th>Test</th><th class="num">p-value</th><th>Effect size and range</th><th>Verdict</th></tr></thead><tbody>{sig}</tbody></table></div></div>
<div class="grid2" style="margin-top:16px">
<div class="card"><h3>Cost bridge: H2 2025 → H1 2026</h3><p class="small">Fleet cost went from {tk(T["waterfall"]["start"])} to {tk(T["waterfall"]["end"])} ({("+" if cc["pct"] > 0 else "−") + bn(f"{abs(cc['pct']):.1f}")}%), and which job types pushed it up or down. Bootstrap 95% range {bn(f"{cc['lo']:+.0f}")}% to {bn(f"{cc['hi']:+.0f}")}%: month-to-month swings are so large that the overall change is not certain.</p><div class="chart" id="cWater"></div></div>
<div class="card"><h3>Cost by quarter</h3><p class="small">Fleet, plant and renewals shown separately. Grey = quarters with almost no orders in SAP; the last quarter is still incomplete.</p><div class="chart" id="cCostQ"></div></div>
<div class="card"><h3>Cost per job by job type</h3><p class="small">Jobs with a cost, Jun 2025 – Jun 2026. Repair-only has a low median because it includes many small repairs, but its large count makes it big in total cost.</p><div class="chart" id="cCostType"></div></div>
<div class="card"><h3>Forecast error, month by month</h3><p class="small">Forecasts made each month of January–June 2026 from earlier data only (chosen method and naive) against actual. Bar height = error.</p><div class="chart" id="cFcErr"></div></div>
<div class="card"><h3>How trustworthy the risk model is</h3><p class="small">Predicted probability (x) against what actually happened (y), in five bins. Close to the diagonal means the probabilities can be trusted.</p><div class="chart" id="cCal"></div></div>
<div class="card"><h3>What the model caught in the test months</h3><p class="small">Flagging the {bn(cm["k"])} riskiest vehicle-months (as many as the major repairs that actually happened).</p>
<div class="cm"><div class="cmc tp"><b>{bn(cm["tp"])}</b><span>Caught</span></div><div class="cmc fp"><b>{bn(cm["fp"])}</b><span>False alarm</span></div><div class="cmc fn"><b>{bn(cm["fn"])}</b><span>Missed</span></div><div class="cmc tn"><b>{bn(cm["tn"])}</b><span>Correctly clear</span></div></div>
<p class="small" style="margin-top:10px">Precision {pct(prec, 0)}, recall {pct(rec, 0)}; random picking would give a precision of {pct(cm["k"] / (cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"]) * 100, 0)}.</p></div>
</div>
<div class="card" style="margin-top:16px"><h3>Progress: key KPIs by quarter</h3><p class="small">Dashed line = proposed plant target. Green dot = moving toward the target, red = moving away (against the previous quarter).</p><div class="spk" id="spk2"></div></div>
</section>'''
