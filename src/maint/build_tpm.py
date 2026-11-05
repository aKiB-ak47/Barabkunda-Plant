"""HTML for the TPM programme view, the equipment guide view and the deeper-analytics section of the maintenance report."""
import html, re, math
import pandas as pd
import atlas_svg as A
from atlas_content import EQ, STAGES, WHO
import tpm_content as TC

BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
def bn(x): return str(x).translate(BN)
def n0(x): return bn(f"{x:,.0f}")
def n1(x): return bn(f"{x:,.1f}")
def pct(x, d=1): return bn(f"{x:.{d}f}") + "%"
def tk(x):
    if abs(x) >= 1e7: return bn(f"{x/1e7:.2f}") + " কোটি টাকা"
    if abs(x) >= 1e5: return bn(f"{x/1e5:.1f}") + " লাখ টাকা"
    return bn(f"{x:,.0f}") + " টাকা"
esc = lambda s: html.escape(str(s), quote=True)
LAT = lambda s: f"<span class=lat>{s}</span>"
FREQ_ORDER = [("প্রতি", "প্রতিবার/শিফট"), ("দৈনিক", "দৈনিক"), ("সাপ্তাহিক", "সাপ্তাহিক"), ("মাসিক", "মাসিক"), ("ত্রৈমাসিক", "ত্রৈমাসিক"), ("ষাণ্মাসিক", "ষাণ্মাসিক"), ("বার্ষিক", "বার্ষিক")]
def fbucket(f):
    for k, lab in FREQ_ORDER:
        if f.startswith(k) or (k == "প্রতি" and f.startswith("প্রতি ")): return lab
    return "অন্যান্য / প্রস্তুতকারক"

# ------------------------------------------------------------------ TPM view
def tpm_html(T, F, hubtok):
    K = {k["k"]: k for k in T["kpis"]}; cal = T["cal"]
    pil = {p["k"]: p for p in T["pillars"]}
    mat = T["maturity"]
    # hero
    out = [f'''<section class="blk first" id="tpm-top"><div class="tpm-hero">
<div><span class="eyebrow">টোটাল প্রোডাক্টিভ মেইনটেন্যান্স · বাড়বকুণ্ড এলপিজি প্ল্যান্ট</span>
<h1>শূন্য ভাঙন, শূন্য ত্রুটি, <em>শূন্য দুর্ঘটনা</em></h1>
<p class="lede">আটটি স্তম্ভ ও ৫এস ভিত্তির ওপর বাড়বকুণ্ডের জন্য পূর্ণ TPM কর্মসূচি। প্রতিটি স্তম্ভের বর্তমান অবস্থা এই প্ল্যান্টের নিজের রক্ষণাবেক্ষণ ও ওজন-পরীক্ষার তথ্য দিয়ে মাপা; যেখানে তথ্য নেই সেখানে তা স্পষ্ট বলা আছে।</p>
<div class="zeros"><span><b>{pct(K["reactive"]["v"], 0)}</b> কাজ ভাঙার পরে</span><span><b>{pct(100 - cal["within150_26"], 1)}</b> সিলিন্ডার ওজন-সীমার বাইরে (২০২৬)</span><span><b>৬টি</b> নিরাপত্তা-রক্ষণাবেক্ষণ খোলা</span></div>
<p class="prep">প্রস্তুত করেছেন: Akib Fateh · বাড়বকুণ্ড এলপিজি প্ল্যান্ট (সিটিজি)</p></div>
<div class="matwrap"><div id="matGauge" class="matg"></div><p class="small">TPM পরিপক্বতা সূচক: {bn(mat["measured"])}টি মাপা স্তম্ভের গড় ({bn(mat["total"] - mat["measured"])}টির তথ্য নেই)। ১ = প্রতিক্রিয়াশীল, ৩ = পরিকল্পিত, ৫ = বিশ্বমান।</p></div>
</div></section>''']
    # house
    out.append(f'''<section class="blk" id="tpm-house"><div class="sh"><span class="kick">TPM ঘর</span><h2>আটটি স্তম্ভ: কোথায় আছি</h2>
<p>প্রতিটি স্তম্ভের রং তার বর্তমান স্তর (১–৫)। স্তম্ভে ক্লিক করলে লক্ষ্য, প্রমাণ, প্রথম ৯০ দিনের কাজ, সূচক ও দায়িত্ব দেখাবে। স্তর মাপার নিয়ম প্রতিটি স্তম্ভের প্রমাণে লেখা।</p></div>
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
        stl = {"gap": "মাপা হয় না", "ok": "লক্ষ্যের কাছে", "warn": "অর্ধেক পথে", "bad": "অনেক দূরে"}[st]
        bar = f'<div class="prog"><i style="width:{0 if prog is None else prog:.0f}%"></i></div><span class="small">{"" if prog is None else "বিশ্বমানের " + pct(prog, 0) + " পথ"}</span>'
        rows.append(f'<div class="kc {st}" data-k="{k["k"]}"><div class="kh"><b>{k["name"]}</b><span class="chip {st}">{stl}</span></div><div class="kv">{val}</div>'
                    f'<div class="kt"><span>প্ল্যান্ট-লক্ষ্য (৩ বছর): <b>{tgt}</b></span><span>বিশ্বমান: <b>{wc}</b></span></div>{bar}<p class="small">{bn(k["basis"])}</p></div>')
    half = T["half"]
    def hv(f, d=1): a, b = half[f]["h2_2025"], half[f]["h1_2026"]; return "—" if a is None or b is None else f"{n1(a)} → {n1(b)}"
    out.append(f'''<section class="blk" id="tpm-kpi"><div class="sh"><span class="kick">সূচক ও অগ্রগতি</span><h2>বিশ্বমানের তুলনায় আমরা কোথায়</h2>
<p>প্রতিটি সূচকের বর্তমান মান, প্রস্তাবিত তিন বছরের প্ল্যান্ট-লক্ষ্য আর শিল্পে প্রচলিত বিশ্বমানের মানদণ্ড (OEE-এর ৮৫% নাকাজিমার)। দণ্ড দেখায় বিশ্বমানের দিকে কতটা পথ পেরোনো হয়েছে।
দ্বিতীয়ার্ধ ২০২৫ থেকে প্রথমার্ধ ২০২৬: পরিকল্পিত কাজ {hv("planned")}%, পিছিয়ে খোলা অর্ডার {hv("backdated")}%, পুনরাবৃত্ত মেরামত {hv("repeat")}%।</p></div>
<div class="kgrid">{"".join(rows)}</div>
<div class="card" style="margin-top:16px"><h3>ত্রৈমাসিক প্রবণতা ও লক্ষ্য</h3><p class="small">ড্যাশ রেখা = প্রস্তাবিত প্ল্যান্ট-লক্ষ্য। ২০২৪-এর মাঝামাঝি থেকে ২০২৫-এর মাঝামাঝি পর্যন্ত SAP-এ খুব কম অর্ডার, তাই সেই ত্রৈমাসিকগুলো ফাঁকা।</p><div class="spk" id="spk"></div></div>
</section>''')
    # losses + OEE
    give = f"{cal['giveaway_mt']:.1f}".translate(BN) + " টন"
    fill = {"reactive": pct(K["reactive"]["v"], 0), "out150": pct(100 - cal["within150_26"], 1) + " (২০২৬)", "backdated": pct(100 - K["timely"]["v"], 0),
            "top3": ", ".join(v[-4:] for v, _ in F["top3_vehicles"]).translate(BN), "give": give}
    lc = []
    for cat, nm, ex, src in TC.LOSSES:
        txt = ex.format(**fill)
        lc.append(f'<div class="lc {"data" if src == "data" else "gap"}"><span class="lcat">{cat}</span><b>{nm}</b><p>{txt}</p><span class="chip {"blue" if src == "data" else ""}">{"তথ্যে মাপা" if src == "data" else "এখনো মাপা হয় না"}</span></div>')
    q = cal["within150_26"]
    out.append(f'''<section class="blk" id="tpm-loss"><div class="sh"><span class="kick">১৬টি বড় ক্ষতি</span><h2>ক্ষতি কোথায় হচ্ছে</h2>
<p>নাকাজিমার ১৬টি ক্ষতিকে এলপিজি বটলিং প্ল্যান্টের ভাষায় সাজানো। নীল চিহ্নের ক্ষতি এই সাইটের তথ্যেই মাপা; বাকিগুলো মাপতে ডাউনটাইম ও উৎপাদন-লগ লাগবে।</p></div>
<div class="lgrid">{"".join(lc)}</div>
<div class="card oee" style="margin-top:16px"><div><h3>ফিলিং ক্যারোসেলের OEE</h3><p class="t small">OEE = প্রাপ্যতা × কার্যক্ষমতা × মান। বিশ্বমান ৮৫% (৯০% × ৯৫% × ৯৯.৯%)।</p></div>
<div class="oeef"><div class="of"><span>প্রাপ্যতা</span><b>?</b><em>ডাউনটাইম লগ দরকার</em></div><span class="x">×</span><div class="of"><span>কার্যক্ষমতা</span><b>?</b><em>নির্ধারিত বনাম প্রকৃত গতি দরকার</em></div><span class="x">×</span>
<div class="of on"><span>মান</span><b>{pct(q, 1)}</b><em>২০২৬-এর {n0(cal["checks26"])}টি ওজন-পরীক্ষায় ±১৫০ গ্রামের ভেতরে</em></div><span class="x">=</span><div class="of"><span>OEE</span><b>≤ {pct(q, 0)}</b><em>মান-অংশই সর্বোচ্চ সীমা টেনে ধরে</em></div></div></div>
</section>''')
    # office TPM: SAP funnel
    out.append(f'''<section class="blk" id="tpm-sap"><div class="sh"><span class="kick">অফিস TPM</span><h2>SAP অর্ডার কোথায় আটকে থাকে</h2>
<p>একটি রক্ষণাবেক্ষণ অর্ডারের পূর্ণ জীবনচক্র: তৈরি → রিলিজ → মালামাল ও খরচ → কনফার্মেশন → টেকনিক্যালি বন্ধ। বাড়বকুণ্ডের {n0(F["n"])}টি অর্ডারের প্রায় সবই খরচ-পোস্টের পরে থেমে আছে; ফলে ডাউনটাইম, মেরামতের সময় (MTTR) ও প্রকৃত কাজের তারিখ মাপা যায় না।</p></div>
<div class="grid2"><div class="card"><h3>অর্ডারের জীবনচক্র</h3><div class="chart" id="funnel"></div></div><div class="card"><h3>পিছিয়ে খোলা অর্ডারের হার, প্রতি ত্রৈমাসিকে</h3><p class="small">কাজের তারিখের চেয়ে ৩০ দিনেরও বেশি পরে খোলা অর্ডার। লক্ষ্য ≤১০%।</p><div class="chart" id="lateQ"></div></div></div></section>''')
    # autonomous maintenance + F-tag + 5S audit
    steps = "".join(f'<li><span class="sn">{bn(i + 1)}</span><div><b>{a}</b><p>{b}</p><span class="small">সমাপ্তির মানদণ্ড: {c}</span></div></li>' for i, (a, b, c) in enumerate(TC.AM_STEPS))
    tags = "".join(f'<div class="ftag" style="--c:{c}"><b>{a}</b><p>{b}</p></div>' for a, b, c in TC.FTAG)
    s5 = "".join(f'<div class="s5g"><b>{bn(i + 1)}. {nm}</b>' + "".join(f'<label class="s5q"><span>{q}</span><select data-s="{i}"><option value="0">০ নেই</option><option value="1">১</option><option value="2">২</option><option value="3">৩</option><option value="4">৪ পুরো</option></select></label>' for q in qs) + '</div>' for i, (nm, qs) in enumerate(TC.S5))
    out.append(f'''<section class="blk" id="tpm-am"><div class="sh"><span class="kick">স্বয়ংক্রিয় রক্ষণাবেক্ষণ ও ৫এস</span><h2>অপারেটর ও চালক: যন্ত্রের প্রথম রক্ষক</h2>
<p>জিশু হোজেনের সাত ধাপ, ত্রুটি-ট্যাগ ব্যবস্থা আর এখানেই করা যায় এমন ৫এস নিরীক্ষা। নিরীক্ষার স্কোর শুধু এই ব্রাউজারে থাকে; প্রিন্ট করে স্বাক্ষর করে রাখুন।</p></div>
<div class="grid2"><div class="card"><h3>সাত ধাপ</h3><ol class="amst">{steps}</ol></div>
<div class="stack"><div class="card"><h3>ত্রুটি-ট্যাগ (F-tag)</h3><div class="ftags">{tags}</div><p class="small" style="margin-top:8px">প্রতিটি ট্যাগ লগবুকে ও SAP নোটিফিকেশনে; সাপ্তাহিক খোলা-বন্ধ গণনা TPM বোর্ডে।</p></div>
<div class="card"><div class="cap"><b>৫এস নিরীক্ষা</b><span id="s5score" class="s5score">০ / ৬০</span></div><div class="s5">{s5}</div><div class="btns" style="margin-top:10px"><button class="btn" id="s5reset">মুছে দিন</button><button class="btn" id="s5print">প্রিন্ট</button></div></div></div></div></section>''')
    # planned maintenance calendar (from the equipment guide + extra items)
    items = [(e["name"], e["id"], e["pm"]) for e in EQ] + [(nm, None, pm) for nm, _, pm in TC.EXTRA_PM]
    cols = [lab for _, lab in FREQ_ORDER] + ["অন্যান্য / প্রস্তুতকারক"]
    trs = []
    for nm, eid, pm in items:
        cells = {c: [] for c in cols}
        for task, f, who, clit in pm:
            cells[fbucket(f)].append(f'<span class="tk w{who}" data-w="{who}" title="{esc(f)} · {WHO[who]} · {clit}"><i>{"/".join(clit)}</i>{task}</span>')
        link = f' <a class="eqlink" href="#eq-{eid}" data-eq="{eid}">ছবি →</a>' if eid else ""
        trs.append(f'<tr><th scope="row">{nm}{link}</th>' + "".join(f'<td>{"".join(cells[c])}</td>' for c in cols) + '</tr>')
    whof = "".join(f'<button class="btn{" on" if k == "all" else ""}" data-who="{k}">{v}</button>' for k, v in [("all", "সবাই"), ("O", "অপারেটর/চালক"), ("T", "টেকনিশিয়ান"), ("E", "প্রকৌশলী"), ("V", "বাইরের সংস্থা"), ("H", "এইচএসই")])
    out.append(f'''<section class="blk" id="tpm-pm"><div class="sh"><span class="kick">পরিকল্পিত রক্ষণাবেক্ষণ</span><h2>কোন যন্ত্রে কী, কত দিন পরপর, কে করবেন</h2>
<p>পরিষ্কার (C), তেল-গ্রিজ (L), পরিদর্শন (I), টাইট (T): প্রতিটি যন্ত্রের CLIT মান ও সূচি, এক ছকে। এটিই SAP-এর রক্ষণাবেক্ষণ প্ল্যানের (ZPM3) খসড়া। প্রস্তুতকারকের নির্দেশ, লাইসেন্সের শর্ত ও প্রযোজ্য কোড (NFPA 10, 25, 58; এলপিজি বিধিমালা ২০০৪) প্রাধান্য পাবে। যোগ্য প্রকৌশলীর পর্যালোচনার জন্য।</p></div>
<div class="vbar"><span class="small">দায়িত্ব:</span><div class="btns" id="whoF">{whof}</div></div>
<div class="card"><div class="tw pmcal"><table><thead><tr><th>যন্ত্র</th>{"".join(f"<th>{c}</th>" for c in cols)}</tr></thead><tbody>{"".join(trs)}</tbody></table></div></div></section>''')
    # quality maintenance matrix
    qm = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td></tr>" for a, b, c, d, e in TC.QM)
    hot = hubtok.get("cal_hot_list", "").translate(BN)
    out.append(f'''<section class="blk" id="tpm-qm"><div class="sh"><span class="kick">মান রক্ষণাবেক্ষণ</span><h2>সঠিক ওজনের জন্য কোন অবস্থা ঠিক রাখতে হবে</h2>
<p>২০২৬-এ ফিলিং প্রক্রিয়ার Cpk {bn(f"{cal['cpk26']:.2f}")} (২০২৪-এ {bn(f"{cal['cpk24']:.2f}")}; লক্ষ্য ≥১.৩৩), গড় অতিরিক্ত ভরাট +{n1(cal["mean26"])} গ্রাম। ওজন-পরীক্ষায় চিহ্নিত হেড: {hot}। ত্রুটি ঠেকাতে নিচের প্রতিটি অবস্থা নির্দিষ্ট মানে রাখতে হবে।</p></div>
<div class="card"><div class="tw"><table><thead><tr><th>মানের বৈশিষ্ট্য</th><th>যন্ত্রের অবস্থা</th><th>মান</th><th>যাচাই-পদ্ধতি</th><th>কত দিন পরপর</th></tr></thead><tbody>{qm}</tbody></table></div></div></section>''')
    # kaizen board
    rep_cost = T["repeat_cost"]; v1 = F["top3_vehicles"][0]
    projects = [
     ("Plan", "অতিরিক্ত ভরাট কমানো", f"মার্চ–অক্টোবর ২০২৬-এ আনুমানিক {give} এলপিজি বিনামূল্যে; Cpk {bn(f'{cal['cpk26']:.2f}')}।", "Cpk ≥ ১.৩৩; গড় ত্রুটি ±২০ গ্রামের মধ্যে", "মান নিয়ন্ত্রণ + রক্ষণাবেক্ষণ", "q"),
     ("Plan", "৯০ দিনের মধ্যে পুনরাবৃত্ত মেরামত", f"জুন ২০২৫ – মার্চ ২০২৬-এর {bn(T['repeat_base'])}টি মেরামতের {pct(T['repeat_rate'], 0)} আবার একই অংশে; সব সময়ের পুনরাবৃত্তির খরচ {tk(rep_cost)}।", "পুনরাবৃত্তি ≤ ৮%", "রক্ষণাবেক্ষণ প্রধান", "k"),
     ("Plan", f"সবচেয়ে ব্যয়বহুল গাড়ি ({v1[0][-4:]})".translate(BN), f"জুন ২০২৫ – জুন ২০২৬-এ {tk(v1[1])}; ইঞ্জিন ও ক্লাচে বারবার কাজ।", "মূল-কারণ বের করে বদল বনাম মেরামতের হিসাব", "পরিবহন প্রধান", "k"),
     ("Plan", "SAP অর্ডার শৃঙ্খলা", f"কনফার্মেশন {pct(K['cnf']['v'], 1)}, TECO {pct(K['teco']['v'], 0)}, সময়মতো অর্ডার {pct(K['timely']['v'], 0)}।", "তিনটিই ≥ ৯০%", "রক্ষণাবেক্ষণ পরিকল্পনাকারী", "o"),
     ("Plan", "নিরাপত্তা-যন্ত্রের মেয়াদ", f"গ্যাস ডিটেক্টরের শেষ অর্ডার {n1(F['gas_mon_months'])} মাস আগে; অগ্নিনির্বাপকে ৩১ মাসের ফাঁক।", "সব নিরাপত্তা-যন্ত্র মেয়াদের মধ্যে, SAP-এ পুনরাবৃত্ত প্ল্যান", "এইচএসই ব্যবস্থাপক", "s"),
     ("Plan", "এয়ার কম্প্রেসরের প্ল্যান চালু", f"{bn(F['plan_orders'])}টি প্ল্যান-অর্ডারের একটিও রিলিজ হয়নি; কম্প্রেসর-২-এ বাইরের বড় মেরামত।", "প্ল্যান-পালন ≥ ৯৫%", "রক্ষণাবেক্ষণ প্রধান", "p"),
    ]
    col = {"Plan": "পরিকল্পনা (P)", "Do": "বাস্তবায়ন (D)", "Check": "যাচাই (C)", "Act": "মানকরণ (A)"}
    cards = {c: [] for c in col}
    for st, nm, base, tgt, own, pk in projects:
        cards[st].append(f'<div class="kz"><span class="chip">{TC.PILLARS[{"q": "qm", "k": "kk", "o": "ot", "s": "she", "p": "pm"}[pk]]["jp"]}</span><b>{nm}</b><p><span class="small">ভিত্তি:</span> {base}</p><p><span class="small">লক্ষ্য:</span> {tgt}</p><p class="small">দায়িত্ব: {own}</p></div>')
    out.append(f'''<section class="blk" id="tpm-kaizen"><div class="sh"><span class="kick">লক্ষ্যভিত্তিক উন্নয়ন</span><h2>কাইজেন বোর্ড</h2>
<p>তথ্য থেকে বেছে নেওয়া প্রথম ছয়টি প্রকল্প, প্রতিটির ভিত্তি-মান ও লক্ষ্য সংখ্যায়। সব প্রকল্প এখন পরিকল্পনা-ধাপে; প্রতি মাসে কার্ড এক ধাপ এগোবে।</p></div>
<div class="kanban">{"".join(f'<div class="kcol"><h4>{col[c]} <span class="small">{bn(len(cards[c]))}</span></h4>{"".join(cards[c]) or chr(10) + "<p class=small>এখনো নেই</p>"}</div>' for c in col)}</div></section>''')
    # skills matrix
    head = "".join(f"<th><span>{s}</span></th>" for s in TC.SKILLS)
    body = "".join(f"<tr><th scope=row>{r}</th>" + "".join(f'<td class="lv l{v}">{bn(v) if v else "—"}</td>' for v in TC.REQ[i]) + "</tr>" for i, r in enumerate(TC.ROLES))
    out.append(f'''<section class="blk" id="tpm-skill"><div class="sh"><span class="kick">শিক্ষা ও প্রশিক্ষণ</span><h2>দক্ষতা-ম্যাট্রিক্স: কার কতটা জানা দরকার</h2>
<p>প্রতিটি ভূমিকার জন্য প্রয়োজনীয় স্তর (০ = দরকার নেই, ১ = জানেন, ২ = সাহায্যে করতে পারেন, ৩ = একা করতে পারেন, ৪ = শেখাতে পারেন)। প্রত্যেক কর্মীর বর্তমান স্তর এর পাশে বসিয়ে ঘাটতি থেকে প্রশিক্ষণ-পরিকল্পনা।</p></div>
<div class="card"><div class="tw"><table class="skill"><thead><tr><th>ভূমিকা</th>{head}</tr></thead><tbody>{body}</tbody></table></div></div></section>''')
    # roadmap + governance
    gov = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in TC.GOV)
    raci = "".join(f"<tr><td>{r[0]}</td>" + "".join(f'<td class="rc">{x}</td>' for x in r[1:]) + "</tr>" for r in TC.RACI)
    out.append(f'''<section class="blk" id="tpm-road"><div class="sh"><span class="kick">বাস্তবায়ন-পথ ও পরিচালনা</span><h2>৩৬ মাসের রোডম্যাপ</h2>
<p>ডিসেম্বর ২০২৬ থেকে প্রস্তাবিত সময়সূচি। প্রস্তুতি তিন মাস, তারপর পরীক্ষামূলক এলাকা (ক্যারোসেল ও পাম্প হাউস), তারপর পুরো প্ল্যান্ট ও বহর। অগ্রগতি প্রতি মাসে এখানে হালনাগাদ হবে।</p></div>
<div class="card"><div class="chart" id="gantt"></div></div>
<div class="grid2" style="margin-top:16px"><div class="card"><h3>পরিচালনা-কাঠামো</h3><div class="tw"><table><thead><tr><th>দল</th><th>সদস্য</th><th>সভা</th><th>দায়িত্ব</th></tr></thead><tbody>{gov}</tbody></table></div></div>
<div class="card"><h3>দায়িত্ব-ছক (RACI)</h3><p class="small">R = করেন, A = জবাবদিহি, C = পরামর্শ, I = জানানো হয়</p><div class="tw"><table class="raci"><thead><tr><th>কাজ</th><th>প্ল্যান্ট ম্যানেজার</th><th>রক্ষণাবেক্ষণ</th><th>উৎপাদন</th><th>এইচএসই</th><th>পরিবহন</th><th>প্রশাসন/SAP</th></tr></thead><tbody>{raci}</tbody></table></div></div></div></section>''')
    return "\n".join(out)

def tpm_data():
    return {"pillars": {k: {kk: vv for kk, vv in v.items()} for k, v in TC.PILLARS.items()}, "roadmap": TC.ROADMAP}

# ------------------------------------------------------------------ equipment guide view
def atlas_html(orders):
    O = pd.DataFrame(orders)
    plant = O[~O.group.isin(["যানবাহন বহর", "নবায়ন ও লাইসেন্স"])]
    chips = "".join(f'<button class="btn{" on" if k == "all" else ""}" data-st="{k}">{v}</button>' for k, v in [("all", "সব যন্ত্র"), *STAGES.items()])
    cards = []
    for e in EQ:
        m = plant[plant.desc.fillna("").str.upper().str.contains(e["sap"], regex=True)]
        sap = (f'<p class="small">SAP-এ প্ল্যান্টের সংশ্লিষ্ট অর্ডার: <b>{bn(len(m))}টি</b>, খরচ {tk(m.cost.sum())}।</p><ul class="saplist">'
               + "".join(f'<li><span class=lat>{int(r.order)}</span> · {bn(pd.Timestamp(r.date).strftime("%d.%m.%Y"))} · {esc(r.desc)} · {tk(r.cost) if r.cost else "খরচ শূন্য"}</li>' for r in m.sort_values("date", ascending=False).head(6).itertuples()) + "</ul>"
               if len(m) else '<p class="small">SAP-এ এই যন্ত্রের নামে প্ল্যান্টের কোনো রক্ষণাবেক্ষণ অর্ডার পাওয়া যায়নি: হয় কাজ হয়নি, নয়তো অন্য নামে লেখা।</p>')
        parts = "".join(f'<li data-p="{i + 1}"><span class="pn">{bn(i + 1)}</span><div><b>{a}</b><span>{b}</span></div></li>' for i, (a, b) in enumerate(e["parts"]))
        fail = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in e["fail"])
        pm = "".join(f'<tr><td>{a}</td><td>{f}</td><td><span class="who w{w}">{WHO[w]}</span></td><td class="lat">{"/".join(c)}</td></tr>' for a, f, w, c in e["pm"])
        lpg = "".join(f"<li>{x}</li>" for x in e["lpg"])
        saf = '<span class="chip bad">নিরাপত্তা-গুরুত্বপূর্ণ</span>' if e.get("safety") else ""
        cards.append(f'''<article class="eq" id="eq-{e["id"]}" data-st="{e["stage"]}" data-name="{esc(e["name"] + " " + e["en"])}">
<header><div><h3>{e["name"]}</h3><span class="en">{e["en"]}</span></div><div class="eqchips"><span class="chip blue">{STAGES[e["stage"]]}</span>{saf}</div></header>
<div class="eqbody"><figure class="eqfig">{getattr(A, e["id"])()}<figcaption>অংশের নামের ওপর মাউস রাখুন বা ছুঁয়ে দেখুন: ছবিতে সেই অংশ জ্বলে উঠবে।</figcaption></figure>
<div class="eqinfo"><dl><dt>কাজ</dt><dd>{e["what"]}</dd><dt>প্ল্যান্টে কোথায়</dt><dd>{e["where"]}</dd><dt>কীভাবে কাজ করে</dt><dd>{e["how"]}</dd></dl>
<h4>অংশসমূহ</h4><ol class="parts">{parts}</ol></div></div>
<div class="eqmore"><details><summary>এলপিজির জন্য বিশেষ প্রয়োজন</summary><ul class="lpg">{lpg}</ul></details>
<details><summary>সাধারণ ত্রুটি ও লক্ষণ</summary><div class="tw"><table><thead><tr><th>ত্রুটি</th><th>যা দেখা যায়</th></tr></thead><tbody>{fail}</tbody></table></div></details>
<details open><summary>রক্ষণাবেক্ষণ (CLIT) ও সূচক</summary><div class="tw"><table><thead><tr><th>কাজ</th><th>কত দিন পরপর</th><th>কে</th><th>ধরন</th></tr></thead><tbody>{pm}</tbody></table></div><p class="small" style="margin-top:6px">মাপার সূচক: {e["kpi"]}</p></details>
<details><summary>SAP-এর ইতিহাস</summary>{sap}</details></div></article>''')
    return f'''<section class="blk first" id="atlas-top"><span class="eyebrow">এলপিজি বিতরণ ব্যবস্থার যন্ত্রপাতি · বাড়বকুণ্ড</span>
<h1>ট্যাংকার থেকে সিলিন্ডার: <em>প্রতিটি যন্ত্র</em>, ছবিসহ</h1>
<p class="lede">নন-রিটার্ন ভালভ, বাটারফ্লাই ভালভ থেকে সেফটি ভালভ, পাম্প, ফিলিং হেড, গ্যাস ডিটেক্টর ও অগ্নি-নিরাপত্তা পর্যন্ত {bn(len(EQ))}টি যন্ত্র: কী কাজ করে, ভেতরে কী আছে, কীভাবে নষ্ট হয়, আর কে কত দিন পরপর কী রক্ষণাবেক্ষণ করবেন।</p>
<p class="prep">প্রস্তুত করেছেন: Akib Fateh · বাড়বকুণ্ড এলপিজি প্ল্যান্ট (সিটিজি) · সব ছবি ব্যাখ্যামূলক, মাপ অনুযায়ী নয়। রক্ষণাবেক্ষণের সময়সূচি যোগ্য প্রকৌশলীর পর্যালোচনার জন্য; প্রস্তুতকারকের নির্দেশ ও লাইসেন্সের শর্ত প্রাধান্য পাবে।</p></section>
<section class="blk" id="atlas-flow"><div class="sh"><span class="kick">প্রবাহ-চিত্র</span><h2>কোন যন্ত্র কোথায় বসে</h2><p>ট্যাংকার আনলোড থেকে মজুত, পাম্প, ক্যারোসেল, চেক-স্কেল ও বিতরণ; নিচে অগ্নি-নিরাপত্তার পানি-নেটওয়ার্ক। যেকোনো চিহ্নে ক্লিক করলে সেই যন্ত্রের পূর্ণ বিবরণে যাবে।</p></div>
<div class="card pidwrap">{A.pid()}</div></section>
<section class="blk" id="atlas-list"><div class="sh"><span class="kick">যন্ত্র-নির্দেশিকা</span><h2>{bn(len(EQ))}টি যন্ত্র</h2></div>
<div class="vbar"><div class="btns" id="stF">{chips}</div><input type="search" id="eqQ" placeholder="খুঁজুন: NRV, valve, পাম্প…" aria-label="যন্ত্র খুঁজুন"></div>
<div class="eqlist">{"".join(cards)}</div></section>'''

# ------------------------------------------------------------------ deeper analytics section (analytics view)
def deep_html(T):
    sig = "".join(f'<tr><td>{s["q"]}</td><td>{s["test"]}<br><span class="small lat">{s["stat"]}</span></td><td class="num"><span class="pv {"sig" if s["p"] < 0.05 else ("mid" if s["p"] < 0.1 else "ns")}">p {"< ০.০০১" if s["p"] < 0.001 else "= " + bn(f"{s["p"]:.3f}")}</span></td><td>{s["effect"].translate(BN)}</td><td><b>{s["verdict"].translate(BN)}</b></td></tr>' for s in T["sig"])
    cc = T["cost_change"]; ct = T["cost_type"]; cm = T["cm"]
    prec = cm["tp"] / (cm["tp"] + cm["fp"]) * 100 if cm["tp"] + cm["fp"] else 0; rec = cm["tp"] / (cm["tp"] + cm["fn"]) * 100 if cm["tp"] + cm["fn"] else 0
    return f'''<section class="blk" id="deep"><div class="sh"><span class="kick">তাৎপর্য, ত্রুটি, খরচ ও অগ্রগতি</span><h2>সংখ্যাগুলো কতটা নির্ভরযোগ্য, আর টাকা কোথায় গেল</h2>
<p>প্রতিটি বড় দাবির পেছনে পরিসংখ্যানিক পরীক্ষা, প্রতিটি মডেলের ত্রুটি, খরচের পরিবর্তনের উৎস আর ত্রৈমাসিক অগ্রগতি। p &lt; ০.০৫ = তাৎপর্যপূর্ণ; ০.০৫–০.১০ = দুর্বল প্রমাণ; এর বেশি = পার্থক্যটি দৈবও হতে পারে।</p></div>
<div class="card"><h3>পরিসংখ্যানিক তাৎপর্য</h3><div class="tw"><table class="sigt"><thead><tr><th>প্রশ্ন</th><th>পরীক্ষা</th><th class="num">p-মান</th><th>প্রভাবের মাপ ও পরিসর</th><th>সিদ্ধান্ত</th></tr></thead><tbody>{sig}</tbody></table></div></div>
<div class="grid2" style="margin-top:16px">
<div class="card"><h3>খরচের সেতু: দ্বিতীয়ার্ধ ২০২৫ → প্রথমার্ধ ২০২৬</h3><p class="small">বহরের খরচ {tk(T["waterfall"]["start"])} থেকে {tk(T["waterfall"]["end"])} ({("+" if cc["pct"] > 0 else "−") + bn(f"{abs(cc['pct']):.1f}")}%)। কোন ধরনের কাজ বাড়াল বা কমাল। বুটস্ট্র্যাপ ৯৫% পরিসর {bn(f"{cc['lo']:+.0f}")}% থেকে {bn(f"{cc['hi']:+.0f}")}%: মাসে মাসে ওঠানামা এত বেশি যে মোট পরিবর্তনটি নিশ্চিত নয়।</p><div class="chart" id="cWater"></div></div>
<div class="card"><h3>প্রতি ত্রৈমাসিকে খরচ</h3><p class="small">বহর, প্ল্যান্ট ও নবায়ন আলাদা। ধূসর = SAP-এ প্রায় অর্ডার নেই এমন ত্রৈমাসিক; শেষ ত্রৈমাসিক এখনো অসম্পূর্ণ।</p><div class="chart" id="cCostQ"></div></div>
<div class="card"><h3>কাজের ধরন অনুযায়ী কাজপ্রতি খরচ</h3><p class="small">খরচসহ কাজ, জুন ২০২৫ – জুন ২০২৬। শুধু-মেরামতের মধ্যমা কম কারণ এতে অনেক ছোট মেরামত; কিন্তু সংখ্যায় বেশি বলে মোট খরচে বড়।</p><div class="chart" id="cCostType"></div></div>
<div class="card"><h3>পূর্বাভাসের ত্রুটি, মাসে মাসে</h3><p class="small">জানুয়ারি–জুন ২০২৬-এ প্রতি মাসে আগের তথ্য দিয়ে দেওয়া পূর্বাভাস (নির্বাচিত পদ্ধতি ও নাইভ) বনাম প্রকৃত। দণ্ডের উচ্চতা = ত্রুটি।</p><div class="chart" id="cFcErr"></div></div>
<div class="card"><h3>ঝুঁকি-মডেলের বিশ্বাসযোগ্যতা</h3><p class="small">মডেল যত সম্ভাবনা বলেছে (x) বনাম আসলে যত ঘটেছে (y), পাঁচ ভাগে। কর্ণরেখার কাছে থাকলে সম্ভাবনাগুলো বিশ্বাসযোগ্য।</p><div class="chart" id="cCal"></div></div>
<div class="card"><h3>পরীক্ষার মাসগুলোতে মডেল কতটা ধরল</h3><p class="small">সবচেয়ে ঝুঁকিপূর্ণ {bn(cm["k"])}টি গাড়ি-মাস চিহ্নিত করলে (যত বড় মেরামত আসলে ঘটেছে তত)।</p>
<div class="cm"><div class="cmc tp"><b>{bn(cm["tp"])}</b><span>ঠিক ধরা</span></div><div class="cmc fp"><b>{bn(cm["fp"])}</b><span>ভুল সতর্কতা</span></div><div class="cmc fn"><b>{bn(cm["fn"])}</b><span>মিস</span></div><div class="cmc tn"><b>{bn(cm["tn"])}</b><span>ঠিক বাদ</span></div></div>
<p class="small" style="margin-top:10px">যথার্থতা (precision) {pct(prec, 0)}, ধরার হার (recall) {pct(rec, 0)}; এলোমেলো বাছাইয়ে যথার্থতা হতো {pct(cm["k"] / (cm["tp"] + cm["fp"] + cm["fn"] + cm["tn"]) * 100, 0)}।</p></div>
</div>
<div class="card" style="margin-top:16px"><h3>অগ্রগতি: প্রতি ত্রৈমাসিকে মূল সূচক</h3><p class="small">ড্যাশ রেখা = প্রস্তাবিত প্ল্যান্ট-লক্ষ্য। সবুজ বিন্দু = লক্ষ্যের দিকে, লাল = উল্টো দিকে (আগের ত্রৈমাসিকের তুলনায়)।</p><div class="spk" id="spk2"></div></div>
</section>'''
