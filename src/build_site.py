"""Build the public website (index.html at the repository root) from src/.
    python3 -I src/build_site.py
Inputs: src/hub/hub.src.html (page template), src/hub/hubdata.json (chart data and {{tokens}}),
src/hub/head_meta.html (search-engine tags), src/reports/*.html (the two self-contained reports)."""
import base64, datetime as dt, json, os, re
from bs4 import BeautifulSoup, NavigableString, Comment

SRC = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(SRC)
REPORTS = ["cal", "maint"]
src = open(f"{SRC}/hub/hub.src.html", encoding="utf8").read()
hub = json.load(open(f"{SRC}/hub/hubdata.json", encoding="utf8"))
MON = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
ldate = lambda s: f"{int(s[8:])} {MON[int(s[5:7]) - 1]} {s[:4]}"
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
ups = sorted(hub.get("updates", []), key=lambda u: (u["date"], u.get("key", "")))
if ups:
    last = ups[-1]["date"]; cur_, old_ = [u for u in ups if u["date"] == last], [u for u in ups if u["date"] != last]
    btn = lambda u: f' <button class="go main sm" data-open="{u["open"]}"' + (f' data-view="{u["view"]}"' if u.get("view") else "") + '>দেখুন <span class="arr">→</span></button>' if u.get("open") else ""
    strip = (f'<div class="upd" id="latest"><span class="when">সর্বশেষ হালনাগাদ · {ldate(last)}</span><div class="what">'
             + "".join(f'<div class="ln"><span>{esc(u["text"])}</span>{btn(u)}</div>' for u in reversed(cur_)) + "</div>"
             + (f'<details class="old"><summary>আগের হালনাগাদ</summary><ul>' + "".join(f"<li>{ldate(u['date'])}: {esc(u['text'])}</li>" for u in reversed(old_)) + "</ul></details>" if old_ else "") + "</div>")
    hub.setdefault("tokens", {})["update_strip"] = strip
# figures shared with the report pages: TPM maturity, equipment count, value of over-filled LPG, round means for the mini chart
tpm = json.load(open(f"{SRC}/maint/tpm.json", encoding="utf8"))
calpage = open(f"{SRC}/reports/cal.html", encoding="utf8").read()
C = json.loads(re.search(r'<script id="dash-data" type="application/json">(.*?)</script>', calpage, re.S).group(1))
PRICE_KG = 2060.0 / 12   # BERC retail price of a 12 kg cylinder, November 2026 (same value as src/cal/deep_cal.py)
hub.setdefault("tokens", {}).update({"tpm_mat": f"{tpm['maturity']['mean']:.1f}", "eq_n": str(len(re.findall(r'<article class="eq" id="eq-', open(f"{SRC}/reports/maint.html", encoding="utf8").read()))),
                                     "cal_give": f"{C['summary'][0]['value'] * 1000 * PRICE_KG / 1e5:.0f}"})
MS = ["জানু", "ফেব্রু", "মার্চ", "এপ্রি", "মে", "জুন", "জুলা", "আগ", "সেপ্টে", "অক্টো", "নভে", "ডিসে"]
hub["calr"] = [{"l": f"{int(r['date'][8:])} {MS[int(r['date'][5:7]) - 1]} {r['date'][2:4]}", "m": round(r["mean_g"], 1)} for r in sorted(C["rounds"], key=lambda r: r["date"])]
hub["cpk"] = [{"l": p["pb"], "v": p["cpk"]} for p in hub.get("cal", [])]
T = hub["tokens"]
cpk24, cpk26 = [s.strip() for s in T["cal_cpk"].split("→")]
TC = tpm["cal"]
_g = C["summary"][0]
T.update({"cal_w24": f"{TC['within150_24']:.0f}", "cal_give_lo": f"{_g['low'] * 1000 * PRICE_KG / 1e5:.0f}", "cal_give_hi": f"{_g['high'] * 1000 * PRICE_KG / 1e5:.0f}",
          "maint_maxgap": str(json.load(open(f"{SRC}/maint/mfacts.json", encoding="utf8"))["silent"]["max_gap_2026"])})
T.update({"cal_cpk24": cpk24, "cal_cpk26": cpk26, "cal_within": f"{TC['within150_26']:.0f}",
          "asof": f"ওজন-পরীক্ষা {ldate(TC['last'])} · রক্ষণাবেক্ষণ রেকর্ড {T['maint_asof']} পর্যন্ত", "updated": ldate(ups[-1]["date"]) if ups else T.get("updated", "")})

# plant map: one entry per area, every figure taken from the SAP orders, the maintenance facts and the weight checks
F = json.load(open(f"{SRC}/maint/mfacts.json", encoding="utf8"))
O = [r for r in json.load(open(f"{SRC}/maint/orders.json", encoding="utf8")) if r["cat"] == "plant"]
def hits(pat, rows=O): return sorted([r for r in rows if re.search(pat, r["desc"].upper())], key=lambda r: r["date"])
def lastd(rows): return ldate(rows[-1]["date"]) if rows else "নেই"
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
    {"k": "receipt", "short": "গ্রহণ", "t": "এলপিজি গ্রহণ: জেটি ও ট্যাংকার বে", "s": "a", "x": 330, "y": 352,
     "d": "জাহাজ ও ট্যাংকার থেকে এলপিজি লোডিং হোস, ব্রেকঅ্যাওয়ে কাপলিং, স্ট্রেইনার ও জরুরি শাটডাউন (ESD) ভালভ পেরিয়ে স্ফিয়ারে যায়। হোস ফাটা বা কাপলিং খুলে যাওয়াই এখানে সবচেয়ে বড় ঝুঁকি।",
     "f": [f"হোস বা ট্যাংকার পয়েন্টের SAP অর্ডার: {len(hose)}টি, শেষটি {lastd(hose)}", f"ESD ভালভ বা জরুরি শাটডাউন পরীক্ষার অর্ডার: {len(esd)}টি",
           "হোসের চাপ-পরীক্ষা ও ESD কার্যকারিতা-পরীক্ষার প্রস্তাবিত সূচি TPM কর্মসূচিতে"],
     "b": [["লোডিং হোস", "maint", "eq-breakaway"], ["ESD ভালভ", "maint", "eq-esdv"], ["প্রবাহ-চিত্র", "maint", "atlas-flow"]]},
    {"k": "storage", "short": "স্টোরেজ স্ফিয়ার", "t": "এলপিজি স্টোরেজ স্ফিয়ার (৪টি)", "s": "r" if not store else "a", "x": 795, "y": 236,
     "d": "চারটি গোলাকার চাপ-পাত্রে প্ল্যান্টের সব বাল্ক এলপিজি থাকে। প্রতিটি স্ফিয়ারের সেফটি ভালভ (PSV), লেভেল গেজ, চাপমাপক, এক্সেস ফ্লো ভালভ আর পানি-স্প্রে ব্যবস্থাই শেষ প্রতিরক্ষা।",
     "f": [f"স্ফিয়ার, PSV, লেভেল গেজ বা পানি-স্প্রের SAP অর্ডার: {len(store)}টি", "অর্থাৎ স্ফিয়ারের নির্ধারিত পরিদর্শন বা PSV পরীক্ষার কোনো রেকর্ড SAP-এ নেই; কাগজের রেকর্ড থাকলে তা SAP-এ তোলা দরকার",
           "যোগ্য প্রকৌশলীর পর্যালোচনার জন্য (NFPA 58; এলপিজি বিধিমালা ২০০৪)"],
     "b": [["স্ফিয়ার দেখুন", "maint", "eq-sphere"], ["সেফটি ভালভ", "maint", "eq-psv"], ["এক্সেস ফ্লো ভালভ", "maint", "eq-efv"]]},
    {"k": "fire", "short": "অগ্নি-সুরক্ষা", "t": "অগ্নি-সুরক্ষা: পানির ট্যাংক, পাম্প ও নির্বাপক", "s": "r", "x": 457, "y": 300,
     "d": "ফায়ার-ওয়াটার ট্যাংক, ফায়ার পাম্প, হাইড্রেন্ট, মনিটর ও স্ফিয়ারের পানি-স্প্রে মিলে আগুন ঠেকানোর ব্যবস্থা; সঙ্গে প্রতিটি এলাকায় শুকনো পাউডারের অগ্নিনির্বাপক।",
     "f": [f"অগ্নিনির্বাপক রিফিলের অর্ডারের মাঝে সর্বোচ্চ ফাঁক {max(F['fire_ext_gaps_m']):.0f} মাস; শেষ রিফিল {lastd(ext)}",
           f"ফায়ার-ফাইটিং লাইন বা মনিটরের অর্ডার: {len(fsys)}টি, শেষটি {lastd(fsys)}", f"ফায়ার পাম্প বা হাইড্রেন্ট পরীক্ষার অর্ডার: {len(firepump)}টি (NFPA 25 নিয়মিত পরীক্ষা চায়)"],
     "b": [["অগ্নিনির্বাপক", "maint", "eq-extinguisher"], ["পানি-স্প্রে ব্যবস্থা", "maint", "eq-deluge"], ["নবায়ন ক্যালেন্ডার", "maint", "renew"]]},
    {"k": "gas", "short": "গ্যাস ডিটেক্টর", "t": "স্থায়ী গ্যাস ডিটেক্টর", "s": "r", "x": 665, "y": 330,
     "d": "স্ফিয়ার, পাম্প হাউস ও ফিলিং শেডে বসানো ডিটেক্টর বাতাসে এলপিজির মাত্রা (LEL-এর শতাংশ) মাপে এবং অ্যালার্ম বাজায়। ক্যালিব্রেশন ছাড়া সেন্সর ধীরে ধীরে অন্ধ হয়ে যেতে পারে।",
     "f": [f"শেষ সার্ভিস-অর্ডার: {lastd(gasm)}", f"{F['gas_mon_months']:.0f} মাস ধরে ক্যালিব্রেশনের কোনো রেকর্ড নেই", "বাম্প-পরীক্ষা ও ক্যালিব্রেশন প্রস্তুতকারকের সূচি অনুযায়ী দরকার"],
     "b": [["গ্যাস ডিটেক্টর", "maint", "eq-detector"], ["TPM সূচি", "maint", "tpm-pm"]]},
    {"k": "pump", "short": "পাম্প হাউস", "t": "পাম্প ও কম্প্রেসর হাউস", "s": "a", "x": 1074, "y": 404,
     "d": "স্ফিয়ার থেকে এলপিজি পাম্প তরল গ্যাস ফিলিং শেডে পাঠায়; এয়ার কম্প্রেসর ফিলিং মেশিন ও নিউমেটিক ভালভ চালায়। মেকানিক্যাল সিল, বিয়ারিং আর NRV এখানে সবচেয়ে বেশি ক্ষয় হয়।",
     "f": [f"এলপিজি পাম্পের SAP অর্ডার: {len(lpgpump)}টি; পাম্পের {len(pumps)}টি অর্ডারের সবই সাবমার্সিবল পানির পাম্পের" if not lpgpump else f"এলপিজি পাম্পের SAP অর্ডার: {len(lpgpump)}টি, শেষটি {lastd(lpgpump)}",
           f"এয়ার কম্প্রেসরের নির্ধারিত অর্ডার {len(air)}টি তৈরি হয়েছে, রিলিজ হয়েছে {len(air_rel)}টি", "পাম্পের কম্পন, তাপমাত্রা ও সিল-ফুটো দেখার দৈনিক তালিকা TPM কর্মসূচিতে"],
     "b": [["এলপিজি পাম্প", "maint", "eq-pump"], ["NRV", "maint", "eq-nrv_swing"], ["বাটারফ্লাই ভালভ", "maint", "eq-butterfly"]]},
    {"k": "filling", "short": "ফিলিং কারুসেল", "t": "ফিলিং কারুসেল ও ফিলিং হেড", "s": "r", "x": 680, "y": 450,
     "d": "ঘূর্ণায়মান কারুসেলের প্রতিটি ফিলিং হেড ওজন মেপে সিলিন্ডার ভরে। কোনো হেড বেশি ভরলে গ্রাহক বিনামূল্যে গ্যাস পান, আর সিলিন্ডারে তাপে প্রসারণের জায়গা কমে।",
     "f": [f"২০২৬-এর গড় অতিরিক্ত ভরাট {T['cal_mean26']} গ্রাম; একক সিলিন্ডারে সর্বোচ্চ {T['cal_max']} গ্রাম", f"চিহ্নিত হেড {T['cal_hot_n']}টি: {T['cal_hot_list']}",
           f"১ মার্চ – ২৫ অক্টোবর ২০২৬-এ অতিরিক্ত গেছে প্রায় {give_mt:.1f} টন এলপিজি (≈ {T['cal_give']} লাখ টাকা, ঊর্ধ্বসীমা)", f"ফিলিং মেশিন ও কারুসেলের SAP অর্ডার {len(fill)}টি, শেষটি {lastd(fill)}"],
     "b": [["ওজন-নির্ভুলতা", "cal", "update"], ["হেড অনুযায়ী", "cal", "dash"], ["ফিলিং হেড", "maint", "eq-filler"]]},
    {"k": "check", "short": "চেক-স্কেল", "t": "চেক-স্কেল ও মান-নিয়ন্ত্রণ", "s": "a", "x": 852, "y": 452,
     "d": "ভরার পর প্রতিটি সিলিন্ডার আবার ওজন হয়; সীমার বাইরে গেলে আলাদা করা হয়। নিয়মিত নমুনা-পরীক্ষা দেখায় ফিলিং হেডগুলো কতটা নির্ভুল।",
     "f": [f"±১৫০ গ্রামের ভেতরে: ২০২৪-এ {TC['within150_24']:.0f}%, ২০২৬-এ {TC['within150_26']:.0f}%, সর্বশেষ রাউন্ডে {TC['within150_last']:.0f}%", f"প্রক্রিয়া-সক্ষমতা Cpk: {cpk24} থেকে {cpk26} (লক্ষ্য ≥ ১.৩৩)",
           f"মোট {T['cal_n']}টি ওজন-পরীক্ষা; স্কেলের SAP অর্ডার {len(scale)}টি, শেষটি {lastd(scale)}"],
     "b": [["গভীর বিশ্লেষণ", "cal", "deep"], ["চেক-স্কেল", "maint", "eq-checkscale"], ["স্লাইড", "cal", "slides"]]},
    {"k": "dispatch", "short": "ডিসপ্যাচ ও বহর", "t": "ডিসপ্যাচ ও গাড়ির বহর", "s": "a", "x": 1040, "y": 478,
     "d": "ভরা সিলিন্ডার ট্রাকে করে পরিবেশকের কাছে যায়। গাড়ির বহরই রক্ষণাবেক্ষণ খরচের বড় অংশ, আর প্রতিটি গাড়ির এক্সপ্লোসিভ লাইসেন্স সচল রাখা আইনি বাধ্যবাধকতা।",
     "f": [f"বহরের পরিকল্পিত কাজের হার {F['pm_share_w']:.0f}% (বিশ্বমান ৮৫%)", f"{F['fleet_vehicles_w']}টি গাড়ির মধ্যে {F['pareto80']}টিতে মোট খরচের ৮০%",
           f"রেকর্ড {T['maint_asof']} পর্যন্ত; শেষ অর্ডারের পর {F['silent']['days']} দিন নীরব, আনুমানিক {T['maint_unbooked']} লাখ টাকার কাজ SAP-এ ওঠেনি"],
     "b": [["যানবাহন বহর", "maint", "fleet"], ["নবায়ন ক্যালেন্ডার", "maint", "renew"], ["পূর্বাভাস", "maint", "predict"]]},
]
for k, v in hub.get("tokens", {}).items(): src = src.replace("{{" + k + "}}", v)
left = re.findall(r"\{\{\w+\}\}", src)
assert not left, f"unfilled tokens: {left}"
data = {k: v for k, v in hub.items() if k != "tokens"}
src = src.replace("__HUBDATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))

# Bangla digits in visible text (not in scripts, styles, code or Latin-marked spans)
soup = BeautifulSoup(src, "html.parser")
BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
CODE = re.compile(r"((?:NFPA|ISO|API|ASTM|IEC)\s?[A-Z]?\d+(?:[,/]\s?\d+)*)")
def keep(node):
    p = node.parent
    while p is not None and p.name:
        if p.name in ("script", "style", "title"): return True
        if {"lat", "code", "vars"} & set(p.get("class") or []): return True
        p = p.parent
    return False
for t in soup.find_all(string=True):
    if isinstance(t, Comment) or keep(t): continue
    new = "".join(seg if i % 2 else seg.translate(BN) for i, seg in enumerate(CODE.split(str(t))))   # keep code numbers (NFPA 58, ISO 10691) in Latin digits
    if new != str(t): t.replace_with(NavigableString(new))
hub_html = str(soup)

reps = {k: open(f"{SRC}/reports/{k}.html", encoding="utf8").read() for k in REPORTS}
payload = "".join(f'<script type="application/octet-stream" id="rep-{k}">{base64.b64encode(v.encode()).decode()}</script>\n' for k, v in reps.items())
meta = open(f"{SRC}/hub/head_meta.html", encoding="utf8").read()
i = hub_html.index("</style>") + len("</style>")
doc = ('<!doctype html>\n<html lang="bn">\n<head>\n' + meta + '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n'
       + hub_html[:i] + "\n</head>\n<body>\n" + hub_html[i:] + "\n" + payload + "</body>\n</html>\n")
open(f"{ROOT}/index.html", "w", encoding="utf8").write(doc)

today = dt.date.today().isoformat()
sm = open(f"{ROOT}/sitemap.xml", encoding="utf8").read()
open(f"{ROOT}/sitemap.xml", "w", encoding="utf8").write(re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{today}</lastmod>", sm))
print("index.html", round(len(doc.encode()) / 1e6, 2), "MB")
