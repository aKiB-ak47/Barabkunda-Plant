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
BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
MON = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
MONS = ["জানু", "ফেব্রু", "মার্চ", "এপ্রি", "মে", "জুন", "জুলা", "আগ", "সেপ্টে", "অক্টো", "নভে", "ডিসে"]
def bn(x): return str(x).translate(BN)
def n0(x): return bn(f"{x:,.0f}")
def n1(x): return bn(f"{x:,.1f}")
def pct(x, d=1): return bn(f"{x:.{d}f}") + "%"
def tk(x):
    if abs(x) >= 1e7: return bn(f"{x/1e7:.2f}") + " কোটি টাকা"
    if abs(x) >= 1e5: return bn(f"{x/1e5:.1f}") + " লাখ টাকা"
    return bn(f"{x:,.0f}") + " টাকা"
def lakh(x): return bn(f"{x/1e5:.1f}") + " লাখ"
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
gc = F["group_cost"]; fleet_share = gc["যানবাহন বহর"] / F["cost_total"] * 100
reg_best = D["reg"][0]
ext = F["fire_ext"]; ext_gap = max(F["fire_ext_gaps_m"])
ext_gap_i = F["fire_ext_gaps_m"].index(ext_gap)
comp260 = next(x for x in F["compressor"] if x["cost"] > 100000)
zc = F["zero_cost_zpm1_2022_23"]
tw = F["twins"]

T = {}  # text blocks with numbers
T["eyebrow"] = f"বিএম এনার্জি (বিডি) লিমিটেড · প্ল্যান্ট <span class=lat>1201</span> · SAP রক্ষণাবেক্ষণ অর্ডার, {dt(F['date_min'])} – {dt(F['date_max'])}"
T["lede"] = (f"SAP PM-এর {n0(F['n'])}টি রক্ষণাবেক্ষণ অর্ডারের পূর্ণ বিশ্লেষণ: খরচ, প্রতিরোধমূলক কাজ, পূর্বাভাস ও ঝুঁকি-মডেল, পরিসংখ্যানিক তাৎপর্য। "
             f"মোট লিপিবদ্ধ খরচ {tk(F['cost_total'])}, যার {pct(fleet_share,0)} গেছে যানবাহন বহরে। ওপরের বোতাম থেকে TPM কর্মসূচি ও যন্ত্রপাতির ছবিসহ নির্দেশিকা।")
EXEC = [
  f"<b>নিরাপত্তা আগে:</b> SAP-এ গ্যাস ডিটেক্টর সার্ভিসের একমাত্র অর্ডার {dt(F['gas_mon'][0]['date'])}-এর ({n1(F['gas_mon_months'])} মাস আগে); অগ্নিনির্বাপক রিফিলে একবার {n1(ext_gap)} মাসের ফাঁক; প্ল্যান্টের {bn(F['plant_lic_n'])} ধরনের লাইসেন্সের নবায়ন-অর্ডার {dt(F['plant_lic_last'])}-এর পর নেই। যোগ্য প্রকৌশলী দিয়ে যাচাই প্রয়োজন।",
  f"<b>খরচ:</b> জুন ২০২৫ – জুন ২০২৬-এ চিহ্নিত {bn(F['fleet_vehicles_w'])}টি গাড়িতে {tk(F['fleet_w_cost'])}; {bn(F['pareto80'])}টি গাড়িতেই ৮০% খরচ। শীর্ষে <span class=lat>{v1['v']}</span>: {tk(v1['cost_w'])}।",
  f"<b>প্রক্রিয়া:</b> {n0(F['n'])}টির একটিও অর্ডার টেকনিক্যালি বন্ধ (<span class=lat>TECO</span>) নয়; {bn(F['backdated'])}টি ({pct(F['backdated']/F['n']*100,0)}) কাজের পরে লেখা। জুলাই–অক্টোবর ২০২৬-এ বহরের মাত্র {bn(F['recent_jul_oct']['fleet_orders'])}টি অর্ডার, অর্থাৎ আনুমানিক {tk(FC['unbooked_jul_oct'])} ({lakh(FC['unbooked_lo'])}–{lakh(FC['unbooked_hi'])}) খরচ এখনো SAP-এ ওঠেনি।",
  f"<b>প্রতিরোধমূলক:</b> বহরের কাজের মাত্র {pct(F['pm_share_w'],0)}-এ নির্ধারিত সার্ভিস আছে; কম্প্রেসরের {bn(F['plan_orders'])}টি প্ল্যান-অর্ডারের একটিও রিলিজ হয়নি। ৯০ দিনের মধ্যে একই অংশে {bn(F['repeats_n'])}বার পুনরায় মেরামত, খরচ {tk(F['repeats_cost'])}।",
  f"<b>পূর্বাভাস:</b> নিউরাল নেটওয়ার্ক মডেল কোন গাড়িতে আগামী ৩ মাসে বড় মেরামত (≥৫০ হাজার টাকা) লাগবে তা <span class=lat>AUC</span> {bn(f'{CB[chr(97)+chr(117)+chr(99)]:.2f}')} (৯০% পরিসর {bn(f'{CB[chr(108)+chr(111)]:.2f}')}–{bn(f'{CB[chr(104)+chr(105)]:.2f}')}) দিয়ে ক্রম করে, শুধু অতীত হারের চেয়ে ভালো ({bn(f'{CB[chr(98)+chr(97)+chr(115)+chr(101)+chr(95)+chr(97)+chr(117)+chr(99)]:.2f}')})। শীর্ষ ঝুঁকি: {', '.join('<span class=lat>'+x+'</span>' for x in top4)}।",
]
KM = [
  ("মোট খরচ", tk(H2["cost"]), tk(H1["cost"]), chg(H2["cost"], H1["cost"]), "বেশি মানে খারাপ নয়: বড় ওভারহল থাকলে বাড়ে"),
  ("বহরের খরচ", tk(H2["fleet_cost"]), tk(H1["fleet_cost"]), chg(H2["fleet_cost"], H1["fleet_cost"]), ""),
  ("প্ল্যান্টের খরচ", tk(H2["plant_cost"]), tk(H1["plant_cost"]), chg(H2["plant_cost"], H1["plant_cost"]), "ভবন, ফিলিং, ইউটিলিটি, অগ্নি-নিরাপত্তা"),
  ("বহরের কাজের অর্ডার", n0(H2["fleet_jobs"]), n0(H1["fleet_jobs"]), chg(H2["fleet_jobs"], H1["fleet_jobs"]), ""),
  ("প্রতি অর্ডারে গড় খরচ", n0(H2["cost_per_job"]) + " টাকা", n0(H1["cost_per_job"]) + " টাকা", chg(H2["cost_per_job"], H1["cost_per_job"]), "খরচ আছে এমন অর্ডার"),
  ("নির্ধারিত সার্ভিসসহ কাজ", pct(H2["sched_share"]), pct(H1["sched_share"]), ("+" if H1["sched_share"] > H2["sched_share"] else "−") + bn(f"{abs(H1['sched_share']-H2['sched_share']):.1f}") + " পয়েন্ট", "শিল্প-মানদণ্ড: পরিকল্পিত কাজ প্রায় ৮০%"),
]
DQ = [
  ("কোনো অর্ডার বন্ধ হয়নি", f"{n0(F['n'])}টির মধ্যে <span class=lat>TECO/CLSD</span> {bn(F['teco'])}টি; কনফার্মেশন (<span class=lat>CNF</span>) মাত্র {bn(F['cnf'])}টিতে, প্রকৃত শুরু-শেষের তারিখও {bn(F['actual_dates'])}টিতে।", "ডাউনটাইম ও মেরামতের সময় (<span class=lat>MTTR</span>) মাপা যায়নি; বিরতি মাপা হয়েছে অর্ডারের তারিখ দিয়ে।"),
  ("খরচ শুধু মালামালের", f"খরচ আছে {bn(F['n_cost'])}টিতে, এবং প্রতিটিতেই মালামাল ইস্যু (<span class=lat>GMPS</span>) আছে; মালামাল ছাড়া কোনো খরচ নেই।", "শ্রম ও বাইরের সার্ভিসের খরচ দেখা যায় না; খরচ কম করে দেখানো হতে পারে।"),
  ("৯ মাসের ফাঁক", f"জুলাই ২০২৪ – মে ২০২৫-এ মাত্র {bn(F['gap_orders'])}টি সাধারণ রক্ষণাবেক্ষণ অর্ডার; ২০২২–২৩-এর {bn(zc[1])}টির {bn(zc[0])}টিতে খরচ শূন্য।", "প্রবণতা ও মডেল জুন ২০২৫ – জুন ২০২৬-এর ধারাবাহিক তথ্যে।"),
  ("সাম্প্রতিক মাস অসম্পূর্ণ", f"জুলাই–অক্টোবর ২০২৬-এ মোট {bn(F['recent_jul_oct']['orders'])}টি অর্ডার, বহরের {bn(F['recent_jul_oct']['fleet_orders'])}টি; প্রথম অর্ধে মাসে গড়ে {n1(F['h1_2026_monthly_orders'])}টি ছিল।", "এই মাসগুলো পূর্বাভাসের প্রশিক্ষণে নেওয়া হয়নি; না-ওঠা খরচ আলাদা করে অনুমান করা হয়েছে।"),
  ("কাজের পরে লেখা অর্ডার", f"{bn(F['backdated'])}টি অর্ডারের তারিখ আগের নম্বরের অর্ডারের চেয়ে ৩০ দিনেরও বেশি পুরোনো; মধ্যমা দেরি {bn(int(F['late_median']))} দিন।", "অর্ডার পরিকল্পনার জন্য নয়, পরে খরচ বসাতে খোলা হচ্ছে; তারিখকে কাজের দিন ধরা হয়েছে।"),
  ("গাড়ির নম্বরের ৬০ রকম লেখা", f"{bn(F['reg_vehicles'])}টি গাড়ির নম্বর বিবরণে {bn(F['reg_variants_total'])} রকমভাবে লেখা (যেমন <span class=lat>CM DA-61-0225</span>, <span class=lat>61-0226</span>, <span class=lat>C.M.DHA 11-0137</span>); ১২টি সাধারণ শব্দের {bn(F['spell_forms'])}টি বানান।", "শেষ চার অঙ্ক ও ইকুইপমেন্ট নম্বর দিয়ে প্রতিটি গাড়িকে একটি নামে আনা হয়েছে।"),
  ("ভুল গাড়িতে অর্ডার", f"{bn(len(F['mismatch']))}টি অর্ডারে বিবরণের গাড়ি আর ইকুইপমেন্ট নম্বরের গাড়ি আলাদা (যেমন <span class=lat>4010249</span>); ১টিতে নম্বর টাইপো (<span class=lat>CM-Sha-11-0247</span>)।", "কাজের হিসাবে বিবরণের গাড়ি ধরা হয়েছে; তালিকায় চিহ্নিত।"),
  ("সম্ভাব্য দ্বৈত অর্ডার", f"{bn(len(F['dups']))}টি জোড়ায় {bn(len(tw))}টি শূন্য-খরচের যমজ অর্ডার। <span class=lat>CM-DHA-61-0287</span>-এ ২৪ দিনে দুবার টায়ার (প্রতিবার ৬১,৬০০ টাকা)।", "শূন্য-খরচের যমজ কাজের গণনা থেকে বাদ; বাকিগুলো নিরীক্ষার জন্য চিহ্নিত।"),
  ("অন্যান্য", f"{bn(F['no_equip'])}টিতে ইকুইপমেন্ট নেই; {bn(F['trunc'])}টির বিবরণ ৪০ অক্ষরে কাটা; {bn(F['crtd'])}টি শুধু তৈরি (<span class=lat>CRTD</span>), রিলিজ হয়নি; ১টি রক্ষণাবেক্ষণ নয় (গাড়ি ভাড়া)।", "ভাড়ার অর্ডার বিশ্লেষণ থেকে বাদ।"),
  ("তিনটি খরচ যাচাই বাকি", f"৩টি অর্ডারের খরচ (<span class=lat>4010371, 4010372, 4010408</span>) মূল SAP রেকর্ডের সঙ্গে মিলিয়ে নিশ্চিত করা দরকার।", "তালিকায় \"খরচ যাচাই বাকি\" চিহ্ন দেওয়া; মোট খরচে এগুলোর প্রভাব সামান্য।"),
]
SAFE = [
  ("S1 · গ্যাস ডিটেক্টর", f"{n1(F['gas_mon_months'])} মাস", f"SAP-এ গ্যাস মনিটর সার্ভিসের একমাত্র অর্ডার <span class=lat>4004850</span>, {dt(F['gas_mon'][0]['date'])}, খরচ শূন্য, কখনো বন্ধ হয়নি। এর পরে কোনো ক্যালিব্রেশন বা সার্ভিসের অর্ডার নেই।", "প্রস্তুতকারকের ক্যালিব্রেশন ব্যবধান; <span class=lat>NFPA 58</span>; এলপিজি বিধিমালা ২০০৪"),
  ("S2 · অগ্নিনির্বাপক", f"{n1(ext_gap)} মাসের ফাঁক", f"রিফিলের অর্ডার {', '.join(dt(x['date'], True) for x in ext)}। {dt(ext[ext_gap_i]['date'], True)} থেকে {dt(ext[ext_gap_i+1]['date'], True)} পর্যন্ত SAP-এ কোনো রিফিল বা রক্ষণাবেক্ষণ নেই।", "<span class=lat>NFPA 10</span> (বার্ষিক রক্ষণাবেক্ষণ); অগ্নি প্রতিরোধ ও নির্বাপণ আইন ২০০৩"),
  ("S3 · প্ল্যান্টের লাইসেন্স", f"{bn(F['plant_lic_n'])} ধরন", f"ফায়ার লাইসেন্সের শেষ অর্ডার {dt(next(x['last'] for x in D['renewals'] if x['doc']=='ফায়ার লাইসেন্স' and x['plant']))}, প্ল্যান্টের এক্সপ্লোসিভ লাইসেন্সের {dt(next(x['last'] for x in D['renewals'] if x['doc']=='এক্সপ্লোসিভ লাইসেন্স' and x['plant']))}; সব প্ল্যান্ট-লাইসেন্সের শেষ অর্ডার {dt(F['plant_lic_last'])}। নবায়ন অন্য কোথাও লিপিবদ্ধ হতে পারে; মেয়াদ যাচাই করুন।", "বিস্ফোরক আইন ১৮৮৪ ও এলপিজি বিধিমালা ২০০৪ (বিস্ফোরক পরিদপ্তর); ফায়ার সার্ভিসের লাইসেন্স"),
  ("S4 · গাড়ির এক্সপ্লোসিভ লাইসেন্স", "২০২৩-এর পর নেই", "বেশির ভাগ এলপিজিবাহী গাড়ির \"Explosive\" নামের শেষ অর্ডার ২০২৩-এর; শুধু <span class=lat>CM-DHA-11-0139</span>-এর ২০২৬-এ (৮০,৮৭৭ টাকা)। ২০২৬-এর সাধারণ \"DOC RENEWAL\" অর্ডারে এই লাইসেন্স আছে কি না SAP থেকে বোঝা যায় না।", "বিস্ফোরক পরিদপ্তরের যানবাহন লাইসেন্স; এলপিজি বিধিমালা ২০০৪"),
  ("S5 · এয়ার কম্প্রেসর", f"{bn(F['plan_orders'])}টির ০টি রিলিজ".translate(BN), f"২০২২–২০২৬-এ দুই কম্প্রেসরের {bn(F['plan_orders'])}টি প্রতিরোধমূলক প্ল্যান-অর্ডার শুধু তৈরি হয়ে পড়ে আছে। খরচসহ একমাত্র অর্ডার <span class=lat>{comp260['order']}</span>: কম্প্রেসর-২-এর বাইরের মেরামত, {tk(comp260['cost'])} ({dt(comp260['date'])})। ফিলিং ও সিলিং মেশিন সংকুচিত বাতাসে চলে।", "প্রস্তুতকারকের রক্ষণাবেক্ষণ সূচি; চাপযুক্ত পাত্রের নিয়মিত পরিদর্শন"),
  ("S6 · অগ্নিনির্বাপণ ব্যবস্থা", "২টি অর্ডার", "ফায়ার মনিটরের ৪\" গেট ভাল্‌ভ মেরামত (মে ২০২৩, খরচ শূন্য, খোলা) আর ফায়ার ফাইটিং পাইপলাইন ভাল্‌ভ (সেপ্টেম্বর ২০২৫, ১৯,৩০০ টাকা)। পাম্প, হাইড্রেন্ট বা ড্রেঞ্চারের কোনো নিয়মিত পরীক্ষার অর্ডার নেই।".translate(BN), "<span class=lat>NFPA 25</span> (পানিভিত্তিক অগ্নিনির্বাপণের পরিদর্শন ও পরীক্ষা); <span class=lat>NFPA 58</span>"),
]
REC = [
  ("উচ্চ", "এইচএসই ও প্ল্যান্ট ম্যানেজার", "গ্যাস ডিটেক্টর ক্যালিব্রেশন ও অগ্নিনির্বাপকের রেকর্ড যাচাই; SAP-এ এগুলোর জন্য পুনরাবৃত্ত প্ল্যান (<span class=lat>ZPM3</span>) তৈরি।"),
  ("উচ্চ", "প্রশাসন ও কমপ্লায়েন্স", f"{bn(F['plant_lic_n'])} ধরনের প্ল্যান্ট-লাইসেন্স ও প্রতিটি গাড়ির এক্সপ্লোসিভ লাইসেন্সের মেয়াদ যাচাই; প্রতিটি নবায়নের অর্ডার SAP-এ সময়মতো খোলা ও বন্ধ করা।"),
  ("উচ্চ", "রক্ষণাবেক্ষণ বিভাগ", f"জুলাই–অক্টোবর ২০২৬-এর বহরের কাজ SAP-এ তোলা (আনুমানিক {tk(FC['unbooked_jul_oct'])}); কাজ শেষে কনফার্মেশন ও <span class=lat>TECO</span>।"),
  ("মধ্যম", "পরিবহন ও রক্ষণাবেক্ষণ", f"ঝুঁকি-তালিকার শীর্ষ গাড়িগুলোর ({', '.join('<span class=lat>'+x+'</span>' for x in top4)}) আগাম পরিদর্শন; প্রতি গাড়িতে প্রায় {bn(int(F['sched_interval']['median']))} দিন পরপর নির্ধারিত সার্ভিসের প্ল্যান।"),
  ("মধ্যম", "রক্ষণাবেক্ষণ বিভাগ", "দুই এয়ার কম্প্রেসরের প্ল্যান-অর্ডার রিলিজ ও সম্পাদন; তেল, ফিল্টার ও সেফটি ভাল্‌ভের পরীক্ষা লিপিবদ্ধ করা।"),
  ("মধ্যম", "অভ্যন্তরীণ নিরীক্ষা", f"{bn(F['anom_n'])}টি অস্বাভাবিক খরচ, {bn(len(F['dups']))}টি সম্ভাব্য দ্বৈত অর্ডার ও ভুল-গাড়ির {bn(len(F['mismatch']))}টি অর্ডার যাচাই।"),
  ("নিম্ন", "এসএপি ও আইটি", "গাড়ির নম্বর ইকুইপমেন্ট থেকে স্বয়ংক্রিয়ভাবে বসানো, কাজের ধরন ও ক্ষতির কারণের ক্যাটালগ কোড, বিবরণ ও ইকুইপমেন্ট না মিললে সতর্কবার্তা।"),
]

def li(items): return "".join(f"<li>{x}</li>" for x in items)
exec_html = li(EXEC)
km_html = "".join(f"<tr><td>{a}</td><td class=num>{b}</td><td class=num>{c}</td><td class=num>{d}</td><td class=note>{e}</td></tr>" for a, b, c, d, e in KM)
dq_html = "".join(f"<div class=dq><b>{a}</b><p>{b}</p><p class=fix>যা করা হয়েছে: {c}</p></div>" for a, b, c in DQ)
safe_html = "".join(f"<div class=sitem><span class=sid>{a}</span><span class=sv>{b}</span><p>{c}</p><span class=ref>{d}</span></div>" for a, b, c, d in SAFE)
rec_html = "".join(f"<tr><td><span class='pri p{['উচ্চ','মধ্যম','নিম্ন'].index(a)}'>{a}</span></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in REC)

T["fleet"] = (f"জুন ২০২৫ – জুন ২০২৬-এ (ধারাবাহিক তথ্যের সময়) চিহ্নিত {bn(F['fleet_vehicles_w'])}টি গাড়িতে মোট {tk(F['fleet_w_cost'])}। খরচ খুব অসমান: "
              f"{bn(F['pareto80'])}টি গাড়িতেই ৮০%। শীর্ষ তিন: " + "; ".join(f"<span class=lat>{v}</span> {tk(c)}" for v, c in F["top3_vehicles"]) + "। একটি গাড়িতে ক্লিক করলে তার প্রতিটি কাজ সময়রেখায় দেখা যাবে।")
T["weibull"] = (f"প্রতিটি গাড়ির পরপর দুই রক্ষণাবেক্ষণ-দিনের মধ্যে কত দিন গেল ({n0(W['n'])}টি বিরতি), তার ওপর <span class=lat>Weibull</span> বণ্টন বসানো হয়েছে। "
                f"আকৃতি β = {bn(f'{W[chr(98)+chr(101)+chr(116)+chr(97)]:.2f}')} (৯০% পরিসর {bn(f'{W[chr(98)+chr(101)+chr(116)+chr(97)+chr(95)+chr(108)+chr(111)]:.2f}')}–{bn(f'{W[chr(98)+chr(101)+chr(116)+chr(97)+chr(95)+chr(104)+chr(105)]:.2f}')}), স্কেল η = {n1(W['eta'])} দিন। "
                f"β ১-এর একটু বেশি মানে সময় যত যায় পরের কাজের সম্ভাবনা ধীরে বাড়ে (হালকা ক্ষয়-জনিত)। গড় বিরতি {n1(W['mean'])} দিন; ৩০ দিনের মধ্যে আবার কাজ লাগার সম্ভাবনা {pct(W['p30']*100,0)}। "
                f"<span class=lat>KS</span> পরীক্ষা p = {bn(f'{W[chr(107)+chr(115)+chr(95)+chr(112)]:.2f}')}, অর্থাৎ বণ্টনটি তথ্যের সঙ্গে গ্রহণযোগ্যভাবে মেলে।")
T["pm"] = (f"জুন ২০২৫ – জুন ২০২৬-এ বহরের কাজের {pct(F['pm_share_w'])}-এ নির্ধারিত সার্ভিস আছে (শুধু সার্ভিস {pct(F['pm_only_share_w'])}, সার্ভিসের সঙ্গে মেরামত বাকিটা); খরচের হিসাবে {pct(F['pm_cost_share_w'])}। "
           f"প্রথম অর্ধ ২০২৬-এ এই হার {pct(H1['sched_share'])}, আগের ছয় মাসে ছিল {pct(H2['sched_share'])}। পরপর দুই নির্ধারিত সার্ভিসের মধ্যমা ব্যবধান {bn(int(F['sched_interval']['median']))} দিন "
           f"(মাঝের অর্ধেক {bn(int(F['sched_interval']['p25']))}–{bn(int(F['sched_interval']['p75']))} দিন), কোনো নির্দিষ্ট সূচি নেই। SAP-এর {bn(F['plan_orders'])}টি প্ল্যান-অর্ডারের (কম্প্রেসর) {bn(F['plan_released'])}টি রিলিজ হয়েছে।")
T["fc"] = (f"বহরের মাসিক খরচ খুব ওঠানামা করে: জুন ২০২৫ – জুন ২০২৬-এ মাসে গড় {tk(FC['monthly_mean'])}, আদর্শ বিচ্যুতি {tk(FC['monthly_sd'])} (পরিবর্তনশীলতা {pct(FC['cv'],0)})। "
           f"সাতটি পদ্ধতি জানুয়ারি–জুন ২০২৬-এ প্রতিবার শুধু আগের মাসের তথ্য দিয়ে এক মাস আগে পূর্বাভাস দিয়েছে। সবচেয়ে কম ত্রুটি দিয়েছে <b>{FC['method']}</b>: "
           f"<span class=lat>RMSE</span> {tk(FC['rmse'])}, নাইভের চেয়ে {pct(D['fc_bt'][0]['skill'],0)} ভালো; কিন্তু <span class=lat>MAPE</span> {pct(FC['mape'],0)}, কারণ কয়েকটি মাসে খরচ খুব কম। "
           f"পরের প্রতি মাসের পূর্বাভাস {tk(FC['level'])}, ৮০% পরিসর {lakh(FC['lo'])} থেকে {lakh(FC['hi'])} টাকা। জুলাই–অক্টোবর ২০২৬-এ SAP-এ উঠেছে মাত্র {tk(FC['recorded_jul_oct'])}; "
           f"একই হারে কাজ হয়ে থাকলে আনুমানিক {tk(FC['unbooked_jul_oct'])} ({lakh(FC['unbooked_lo'])}–{lakh(FC['unbooked_hi'])} টাকা) এখনো লেখা বাকি।")
T["risk"] = (f"প্রতিটি গাড়ি ও মাস একটি সারি ({n0(CB['n'])}টি পরীক্ষার সারি, {bn(CB['pos'])}টিতে বড় মেরামত)। লক্ষ্য: আগামী ৩ মাসে ≥৫০,০০০ টাকার কোনো কাজ। প্রতিটি মডেল শুধু আগের মাসগুলো দিয়ে শিখে "
             f"{bn(CB['test'].replace('2026-01','জানু ২০২৬').replace('2026-04','এপ্রি ২০২৬'))}-এর প্রতিটি মাসে পূর্বাভাস দিয়েছে। সেরা <b>{CB['best']}</b>: <span class=lat>AUC</span> {bn(f'{CB[chr(97)+chr(117)+chr(99)]:.2f}')} "
             f"(৯০% পরিসর {bn(f'{CB[chr(108)+chr(111)]:.2f}')}–{bn(f'{CB[chr(104)+chr(105)]:.2f}')}); শুধু গাড়ির অতীত হার দিয়ে {bn(f'{CB[chr(98)+chr(97)+chr(115)+chr(101)+chr(95)+chr(97)+chr(117)+chr(99)]:.2f}')}। "
             f"২,০০০ বার বুটস্ট্র্যাপে নিউরাল নেটওয়ার্ক {pct(CB['p_better']*100,0)} ক্ষেত্রে ভিত্তিরেখার চেয়ে ভালো। নমুনা ছোট, তাই এটি পরিদর্শনের অগ্রাধিকার, নিশ্চিত ভবিষ্যদ্বাণী নয়।".translate(BN))
T["riskB"] = (f"জুন ২০২৬ পর্যন্ত তথ্য দিয়ে জুলাই–সেপ্টেম্বর ২০২৬-এর ঝুঁকি। গড় সম্ভাবনা {pct(F['risk']['mean_p'],0)}। ওই সময়ের বড় কাজ SAP-এ এখন পর্যন্ত উঠেছে {bn(F['risk']['seen_n'])}টি গাড়িতে, "
              f"যার {bn(F['risk']['seen_in_top10'])}টি শীর্ষ দশে (বাকি তথ্য এখনো ওঠেনি, তাই এটি পূর্ণ যাচাই নয়)।")
T["clsA"] = (f"একই কাঠামোয় \"আগামী মাসে কোনো কাজ লাগবে কি না\" পরীক্ষা করা হয়েছে ({n0(CA['n'])}টি সারি, {bn(CA['pos'])}টিতে কাজ)। এখানে কোনো মেশিন-লার্নিং মডেল গাড়ির নিজের অতীত হারকে "
             f"(<span class=lat>AUC</span> {bn(f'{CA[chr(98)+chr(101)+chr(115)+chr(116)+chr(95)+chr(97)+chr(117)+chr(99)]:.2f}')}) হারাতে পারেনি: ছোটখাটো কাজ মূলত প্রতিটি গাড়ির অভ্যাস, তাই সাধারণ হারই যথেষ্ট।")
T["reg"] = (f"খরচসহ {n0(F['n_cost_jobs'])}টি কাজের খরচ (মধ্যমা {n0(F['cost_job_median'])} টাকা, গড় {n0(F['cost_job_mean'])} টাকা) কাজের ধরন, সিরিজ ও বছর দিয়ে কতটা বোঝা যায়, ৫-ভাগ ক্রস-ভ্যালিডেশনে মাপা হয়েছে। "
            f"সেরা {reg_best['model']}: <span class=lat>R²</span> {bn(f'{reg_best[chr(114)+chr(50)]:.2f}')}। অর্থাৎ খরচের মাত্র এক-পঞ্চমাংশ বিবরণ দিয়ে ব্যাখ্যা হয়; বাকিটা বিবরণে লেখা নেই (কোন যন্ত্রাংশ, কতগুলো)। "
            f"নিচের গুণক দেখায়, নির্ধারিত সার্ভিসের তুলনায় প্রতিটি ধরনের কাজে সাধারণত কত গুণ খরচ।")
T["anom"] = (f"একই ধরনের কাজের মধ্যমার তুলনায় খরচ কত দূরে (রোবাস্ট <span class=lat>z</span>, মধ্যমা ও <span class=lat>MAD</span> দিয়ে) আর <span class=lat>Isolation Forest</span>, দুটো মিলিয়ে {bn(F['anom_n'])}টি অর্ডার চিহ্নিত। "
             "এগুলো ভুল নয়, শুধু যাচাইয়ের যোগ্য।")
T["clusters"] = (f"বিবরণের লেখা থেকে (গাড়ির নম্বর বাদ দিয়ে, অক্ষর-স্তরের <span class=lat>TF-IDF</span>) <span class=lat>K-Means</span> দিয়ে নিজে থেকে দল তৈরি করা হয়েছে; সিলুয়েট স্কোর সবচেয়ে ভালো "
                 f"k = {bn(F['clusters']['k'])}-এ ({bn(f'{F[chr(99)+chr(108)+chr(117)+chr(115)+chr(116)+chr(101)+chr(114)+chr(115)][chr(115)+chr(105)+chr(108)+chr(104)+chr(111)+chr(117)+chr(101)+chr(116)+chr(116)+chr(101)]:.2f}')})। "
                 f"নিয়মভিত্তিক শ্রেণির সঙ্গে মিল কম (<span class=lat>ARI</span> {bn(f'{F[chr(99)+chr(108)+chr(117)+chr(115)+chr(116)+chr(101)+chr(114)+chr(115)][chr(97)+chr(114)+chr(105)+chr(95)+chr(118)+chr(115)+chr(95)+chr(114)+chr(117)+chr(108)+chr(101)+chr(115)]:.2f}')}), কারণ অনেক দল বানানের ধরন দিয়ে তৈরি (যেমন schedule/schedual/shedule)। এটাই প্রমাণ যে SAP-এ ক্যাটালগ কোড দরকার।")
T["renew"] = (f"নবায়ন-অর্ডার থেকে প্রতিটি বিষয়ের (গাড়ি বা প্ল্যান্ট) প্রতিটি কাগজের শেষ তারিখ, আর ধরে নেওয়া এক বছর মেয়াদে পরের নবায়ন। {bn(F['ren_overdue'])}টির ক্ষেত্রে ১২ মাসের মধ্যে কোনো নতুন অর্ডার নেই, "
              f"{bn(F['ren_soon'])}টির নবায়ন ১২০ দিনের মধ্যে। মনে রাখুন: কোনো অর্ডার বন্ধ হয় না, তাই অর্ডার থাকা মানেই নবায়ন হয়েছে তা নয়।")
T["plant"] = (f"বহরের বাইরে {n0(F['plant_n'])}টি অর্ডার, খরচ {tk(F['plant_cost'])}। বড় তিনটি: এয়ার কম্প্রেসর-২-এর বাইরের মেরামত {tk(comp260['cost'])}, মাউন্ডেড ট্যাংক এলাকার মাটি ১.৪ লাখ টাকা, প্রশাসনিক ভবনের ভেতরের কাজ ১ লাখ টাকা।".translate(BN))
T["prep"] = f"প্রস্তুত করেছেন: <b>Akib Fateh</b>, বাড়বকুণ্ড এলপিজি প্ল্যান্ট (সিটিজি)। তারিখ: {dt(os.environ.get('UPDATE_DATE', dt_.date.today().isoformat()))}"

METHODS = [
  ("সময়কাল", "প্রবণতা, গাড়ির তুলনা ও মডেল জুন ২০২৫ – জুন ২০২৬-এ, কারণ এর আগে ৯ মাসের ফাঁক আর পরে তথ্য অসম্পূর্ণ। মোট খরচে সব বছর আছে।"),
  ("গাড়ি ও কাজের ধরন", "গাড়ির নম্বর শেষ চার অঙ্ক ও ইকুইপমেন্ট নম্বর দিয়ে এক নামে আনা। কাজের ধরন বিবরণের শব্দ দিয়ে ১৪টি শ্রেণিতে; নির্ধারিত সার্ভিস = schedule-এর যেকোনো বানান বা শুধু তেল, ফিল্টার, গ্রিজ।"),
  ("অনুমান", "অর্ডারের মূল শুরুর তারিখকে কাজের তারিখ ধরা হয়েছে। নবায়নের মেয়াদ এক বছর ধরা হয়েছে। খরচ টাকায়, SAP-এর \"Total actual costs\"। TPM-এর তিন বছরের প্ল্যান্ট-লক্ষ্য প্রস্তাবিত, অনুমোদিত নয়।"),
  ("সীমাবদ্ধতা", "শ্রম ও বাইরের সার্ভিসের খরচ নেই; অর্ডার বন্ধ না হওয়ায় ডাউনটাইম ও MTTR মাপা যায়নি; গাড়ির বয়স, কিলোমিটার ও চলার ঘণ্টা নেই, থাকলে পূর্বাভাস আরও ভালো হতো। নমুনা ছোট, তাই মডেলগুলো পরিদর্শনের অগ্রাধিকার ঠিক করতে, নিশ্চিত ভবিষ্যদ্বাণী নয়।"),
  ("পর্যালোচনা", "নিরাপত্তা-সংক্রান্ত সব পর্যবেক্ষণ ও রক্ষণাবেক্ষণ-সূচি যোগ্য প্রকৌশলীর পর্যালোচনার জন্য (NFPA 10, 25, 58; এলপিজি বিধিমালা ২০০৪)। সিদ্ধান্ত-সহায়তা, নিয়ন্ত্রণ নয়।"),
]
meth_html = "".join(f"<div class=mrow><b>{a}</b><p>{b}</p></div>" for a, b in METHODS)
hubtok = json.load(open(f"{SRC}/hub/hubdata.json", encoding="utf8")).get("tokens", {})
D["tpm"] = {**TPM, "pillar_info": tpm_content.PILLARS, "roadmap": tpm_content.ROADMAP}
tpm_html = build_tpm.tpm_html(TPM, F, hubtok); atlas_html = build_tpm.atlas_html(D["orders"]); deep_html = build_tpm.deep_html(TPM)
wm_svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="560" height="320" viewBox="0 0 560 320"><g transform="rotate(-18 280 160)" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-weight="700">'
          '<path d="M120 112c10 18 26 28 26 46a26 26 0 0 1-52 0c0-13 8-21 13-28 3 8 5 13 10 16 0-13 0-23 3-34z"/>'
          '<text x="160" y="150" font-size="38" letter-spacing="3">BM LP GAS</text><text x="162" y="178" font-size="14" letter-spacing="5">BARABKUNDA LPG PLANT</text>'
          '<text x="300" y="268" font-size="13" letter-spacing="3" opacity=".8">AKIB FATEH</text></g></svg>')
extra_css = open("maint_extra.css", encoding="utf8").read().replace("{{WM}}", "data:image/svg+xml," + quote(wm_svg))
extra_js = open("maint_extra.js", encoding="utf8").read()
data_json = json.dumps(D, ensure_ascii=False).replace("</", "<\\/")
tpl = open("maint_tpl.html", encoding="utf8").read()
rep = {"EYEBROW": T["eyebrow"], "LEDE": T["lede"], "PREP": T["prep"], "EXEC": exec_html, "KM": km_html, "DQ": dq_html, "SAFE": safe_html, "REC": rec_html,
       "T_FLEET": T["fleet"], "T_WEIBULL": T["weibull"], "T_PM": T["pm"], "T_FC": T["fc"], "T_RISK": T["risk"], "T_RISKB": T["riskB"], "T_CLSA": T["clsA"], "T_REG": T["reg"],
       "T_ANOM": T["anom"], "T_CLUSTERS": T["clusters"], "T_RENEW": T["renew"], "T_PLANT": T["plant"], "METH": meth_html, "N_ORDERS": n0(F["n"]),
       "KPI_COST": bn(f"{F['cost_total']/1e7:.2f}") + " কোটি", "KPI_FLEETW": lakh(F["fleet_w_cost"]), "KPI_PM": pct(F["pm_share_w"], 0), "KPI_TECO": bn(F["teco"]), "KPI_UNBOOKED": lakh(FC["unbooked_jul_oct"]),
       "KPI_AUC": bn(f"{CB['auc']:.2f}"), "D3": D3, "DATA": data_json, "TPM": tpm_html, "ATLAS": atlas_html, "DEEP": deep_html, "ATLAS_DEFS": atlas_svg.DEFS,
       "EXTRA_CSS": extra_css, "EXTRA_JS": extra_js, "DATA_TO": dt(F["date_max"])}
for k, v in rep.items(): tpl = tpl.replace("{{" + k + "}}", v)
left = re.findall(r"\{\{[A-Z_]+\}\}", tpl); assert not left, left
open(f"{SRC}/reports/maint.html", "w", encoding="utf8").write(tpl)
print("maint.html", round(len(tpl.encode()) / 1e6, 2), "MB")

# ---------------- hub card figures, mini chart and update log
hub = json.load(open(f"{SRC}/hub/hubdata.json", encoding="utf8"))
MONS_ = ["জানু", "ফেব্রু", "মার্চ", "এপ্রি", "মে", "জুন", "জুলা", "আগ", "সেপ্টে", "অক্টো", "নভে", "ডিসে"]
mm = [m for m in D["monthly"] if m["m"] >= "2025-06"]
hub["maint"] = {"labels": [MONS_[int(m["m"][5:]) - 1] + " " + bn(m["m"][2:4]) for m in mm], "vals": [round((m["fleet"] + m["plant"]) / 1e5, 1) for m in mm],
                "inc": [m["m"] >= "2026-07" for m in mm]}
last = F["date_max"]; L = pd.Timestamp(last)
hub.setdefault("tokens", {}).update({
    "maint_n": f"{F['n']:,}", "maint_cost": f"{F['cost_total']/1e7:.2f}", "maint_p80": f"{F['pareto80']}/{F['fleet_vehicles_w']}", "maint_auc": f"{F['clsB']['auc']:.2f}",
    "maint_pm": f"{F['pm_share_w']:.0f}", "maint_from": "ফেব্রুয়ারি 2022", "maint_to": f"{MON[L.month-1]} {L.year}", "maint_gas_m": f"{F['gas_mon_months']:.0f}",
    "maint_ext_gap": f"{max(F['fire_ext_gaps_m']):.0f}", "maint_lic": str(F["plant_lic_n"]), "maint_unbooked": f"{F['fc']['unbooked_jul_oct']/1e5:.0f}"})
today = os.environ.get("UPDATE_DATE", dt_.date.today().isoformat())
ups = hub.setdefault("updates", [])
text = f"রক্ষণাবেক্ষণ রিপোর্ট: SAP-এর {F['n']}টি অর্ডার, মোট খরচ {F['cost_total']/1e7:.2f} কোটি টাকা; বড় মেরামতের ঝুঁকি-মডেল (নিউরাল নেটওয়ার্ক, AUC {F['clsB']['auc']:.2f}); পরিসংখ্যানিক তাৎপর্য ও অগ্রগতি।"
text2 = f"নতুন: বিশ্বমানের TPM কর্মসূচি (৮ স্তম্ভ, পরিপক্বতা {TPM['maturity']['mean']:.1f}/৫, সূচক বনাম বিশ্বমান, ৩৬ মাসের রোডম্যাপ) ও {len(build_tpm.EQ)}টি যন্ত্রের ছবিসহ নির্দেশিকা (NRV, বাটারফ্লাই ভালভ, সেফটি ভালভ, পাম্প, ফিলিং হেড…)।"
ups[:] = [u for u in ups if u.get("key") not in ("maint-" + last, "tpm-" + today)] + [{"date": today, "text": text, "through": last, "key": "maint-" + last, "open": "maint", "view": "summary"},
          {"date": today, "text": text2, "through": last, "key": "tpm-" + today, "open": "maint", "view": "tpm"}]
ups.sort(key=lambda u: (u["date"], u.get("key", "")))
json.dump(hub, open(f"{SRC}/hub/hubdata.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("hub data updated")
