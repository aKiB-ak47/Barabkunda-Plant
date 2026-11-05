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
