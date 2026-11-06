"""Clean the SAP PM order list: dates, vehicle identity (spelling variants unified),
asset group, work category, preventive/corrective class and data-quality flags. Output: orders.json"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import json, re, sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orders_raw import ROWS, LOWCONF

df = pd.DataFrame(ROWS, columns=["order", "type", "date", "equip", "desc", "status", "cost", "a_start", "a_finish"])
df["date"] = pd.to_datetime(df.date, format="%d.%m.%Y")
df["equip"] = df.equip.astype("Int64")
df["cost"] = df.cost.astype(float)
df["lowconf"] = df.order.isin(LOWCONF)

# ---------------- vehicle identity: registration number is unique by its last four digits
EQ = {8000003: "0732", 8000004: "0225", 8000005: "0226", 8000006: "0227", 8000007: "0228", 8000008: "0245", 8000009: "0246", 8000010: "0247",
      8000011: "0279", 8000012: "0280", 8000013: "0281", 8000014: "0284", 8000015: "0285", 8000016: "0286", 8000017: "0287", 8000018: "1263",
      8000019: "1264", 8000020: "0101", 8000021: "0102", 8000022: "0103", 8000027: "6797", 8000036: "0961", 8000037: "0957", 8000038: "0958",
      8000039: "0959", 8000040: "0960", 8000042: "3475", 8000043: "3476", 8000044: "3477", 8000045: "3478", 8000052: "0137", 8000053: "0138",
      8000054: "0139", 8000055: "0140", 8000056: "0141"}
def canon(n):
    if n in {"0225", "0226", "0227", "0228", "0245", "0246", "0247", "0279", "0280", "0281", "0284", "0285", "0286", "0287"}: return f"CM-DHA-61-{n}"
    if n in {"0101", "0102", "0103", "0137", "0138", "0139", "0140", "0141"}: return f"CM-DHA-11-{n}"
    if n in {"1263", "1264", "3475", "3476", "3477", "3478"}: return f"CM-SHA-11-{n}"
    if n == "6797": return "CM-CHA-11-6797"
    if n in {"0957", "0958", "0959", "0960", "0961", "0732"}: return f"CM-U-11-{n}"
    return None
SERIES = lambda v: (None if not isinstance(v, str) else "Dha-61 series (DHA-61)" if "-61-" in v else "Bobtail Dha-11 (0101–0103)" if v[-4:] in ("0101", "0102", "0103")
                    else "Dha-11 series (0137–0141)" if "DHA-11" in v else "Bobtail Sha-11 (1263–1264)" if v[-4:] in ("1263", "1264")
                    else "Sha-11 series (3475–3478)" if "SHA-11" in v else "Office car" if "6797" in v else "U-11 series")
KNOWN = set(EQ.values())
def desc_vehicles(d):
    hits = re.findall(r"(?<!\d)(?:61|11)\s*-\s*(\d{4})(?!\d)", d) + re.findall(r"(?<!\d)(6797|1264|0102|0101)(?!\d)", d)
    hits += re.findall(r"(?:^|\s|,)(1264|103|101)(?=\s|,|&|$)", d) if "Bobtail C.M Sha" in d else []
    out = []
    for h in hits:
        h = {"103": "0103", "101": "0101"}.get(h, h)
        if h in KNOWN and h not in out: out.append(h)
    return out
rows = []
for r in df.itertuples():
    dv = desc_vehicles(r.desc); ev = EQ.get(int(r.equip)) if pd.notna(r.equip) else None
    multi = len(dv) > 1
    if multi: veh, src = None, "Several vehicles"
    elif dv: veh, src = dv[0], "description"
    elif ev: veh, src = ev, "equipment number"
    elif re.search(r"office car", r.desc, re.I): veh, src = "6797", "description"
    else: veh, src = None, ""
    mismatch = bool(dv and ev and not multi and dv[0] != ev)
    # 'CM-Sha-11-0247' : no such Sha-11 vehicle; the equipment (0247) is the vehicle and the text is a typo
    if r.order == 4010264: veh, mismatch, src = "0247", False, "equipment number (typo in description)"
    rows.append(dict(vehicle=canon(veh) if veh else None, veh_src=src, equip_vehicle=canon(ev) if ev else None, mismatch=mismatch, multi_vehicle=multi,
                     desc_regs=re.findall(r"C\.?\s?M[\s\.\-]*(?:DhA|DHA|DA|Sha|SHA|SH|Cha|CHA|U)?[\s\-\.]*\d{2}\s*-\s*\d{2,4}|(?<![\w-])\d{2}-\d{4}", r.desc)))
df = pd.concat([df, pd.DataFrame(rows)], axis=1)
df["series"] = df.vehicle.map(SERIES)

# ---------------- asset group and work category
def group(r):
    d = r.desc.lower()
    if r.type == "ZPMD" or "renewal" in d or "license" in d or "licence" in d: return "Renewals and licences"
    if isinstance(r.vehicle, str) or r.multi_vehicle or "bobtail" in d or "office car" in d: return "Vehicle fleet"
    if re.search(r"fire|extingu|extengu|gas monitor|walkie", d): return "Fire and safety"
    if re.search(r"filling|carousel|pusher|conveyor|sealing|steam machine|fm 3|pv valve|tanker point|chain", d): return "Filling and handling"
    if re.search(r"air com|compressor|submersible|pump|generat|diesel gen|dynamo|radiator cooling|solar|wash machine|of lp", d): return "Utilities (compressor, pump, power)"
    if re.search(r"weigh|bridge scale|bsti", d): return "Weighing (weighbridge)"
    if re.search(r"buoy|offshore|boat|jetty", d): return "Marine and jetty"
    return "Buildings, office and site"
df["group"] = df.apply(group, axis=1)

CATS = [  # (key, Bangla label, pattern) in priority order; first match is the main system
    ("tyre", "Tyres", r"\btyres?\b|\btire\b"),
    ("overhaul", "Engine overhaul and block", r"overhaul|engine block|engine & denting"),
    ("clutch", "Clutch, gearbox and drive", r"clutch|clautch|claustch|pressure\s*plate|prassure|fly ?wheel|gear|syncron|cutting shaft|cross|differential|pinion|center bearing|padel|knuckel"),
    ("brake", "Brakes", r"brake|break|booster|boster|hub drum"),
    ("susp", "Chassis, springs and suspension", r"spring|chassis|chessis|hanger|shock|absorver|u bolt|base plate|bace plate|tie ?rod|leaf|bush|tension rod|plainsheet|steel ma[jz]on"),
    ("steer", "Steering and servo", r"steering|servo"),
    ("fuel", "Fuel system", r"fuel|diesel tank|dizzel|nozzle|nozzel|accelerator|stainer|water separator|turbo"),
    ("cool", "Cooling (radiator, water, fan)", r"radiator|water pump|cooling water|fan|belt tensoner|ac pump"),
    ("elec", "Electrical (battery, lights, wiring)", r"battery|alternator|self assy|light|led\b|bulb|wir|electric|switch|horn|wiper|weiper|meter board|sensor|flasher|magnet|signal|self contact"),
    ("air", "Air system and diaphragm", r"air cylinder|air compressor head|diaphragm|diaphogram|air pipe|valve crane|hose"),
    ("body", "Body, cabin and paint", r"dent|paint|door|glass|seat|cabin|bonat|lock|welding|silencer"),
    ("hyd", "Hydraulics and bobtail pump", r"hydraulic|hyd\.|jack|bobtail|pump maintenance|motor rewin|ex pulsar"),
    ("service", "Oil, filters and routine service", r"oil|filter|mobil|grease|measuring|general maint|servic"),
]
SCHED = r"sched|schd|shedule|schudule|sche\.|\bsch\.|schedual|scheduled|schedule"
def cat(r):
    d = r.desc.lower()
    if r.group != "Vehicle fleet":
        return ("plant", r.group)
    for k, lab, pat in CATS:
        if re.search(pat, d): return (k, lab)
    if "trip rent" in d: return ("nonmaint", "Not maintenance (hire)")
    if re.search(SCHED, d) or "maint" in d: return ("sched", "Scheduled service (no detail)")
    return ("other", "Other")
cc = df.apply(cat, axis=1, result_type="expand"); df["cat"], df["cat_bn"] = cc[0], cc[1]
def pmclass(r):
    d = r.desc.lower()
    if r.type == "ZPMD" or "renewal" in d: return "Renewal"
    if r.type == "ZPM3" or "MSPT" in r.status: return "Planned preventive (plan)"
    s = bool(re.search(SCHED, d)); svc = bool(re.search(r"oil|filter|grease|mobil", d)) and not re.search(r"pump|plate|clutch|radiator|seal", d)
    corr = r["cat"] not in ("sched", "service", "plant") or bool(re.search(r"repai|replace|new|change|rewin|making|denting|overhaul", d))
    if (s or svc) and not corr: return "Scheduled service"
    if (s or svc) and corr: return "Service + repair"
    return "Repair"
df["pm"] = df.apply(pmclass, axis=1)

# ---------------- data-quality flags
df["has_gmps"] = df.status.str.contains("GMPS")
df["teco"] = df.status.str.contains("TECO|CLSD")
df["cnf"] = df.status.str.contains("CNF")
df["crtd"] = df.status.str.startswith("CRTD")
df["trunc"] = df.desc.str.len().ge(39) & ~df.desc.str.rstrip().str.endswith((".", ")"))
# recorded well after the work date: basic start date more than 30 days before the latest date already entered on an earlier-numbered order of the same type
df = df.sort_values("order").reset_index(drop=True)
df["runmax"] = df.groupby("type").date.cummax().groupby(df.type).shift().fillna(df.date)
df["late_days"] = (df.runmax - df.date).dt.days.clip(lower=0)
df["backdated"] = df.late_days > 30
# possible duplicates: same vehicle (or same text for plant), same main category, within 45 days
df["dup_of"] = None
key = df.vehicle.fillna(df.desc.str.lower().str[:25])
for i, r in df.iterrows():
    if r.type != "ZPM1": continue
    prev = df[(df.index < i) & (key == key[i]) & (df["cat"] == r["cat"]) & (df.type == r.type) & ((r.date - df.date).abs().dt.days <= (21 if r["cat"] == "sched" else 45))]
    same = prev[prev.desc.str.lower().str.replace(r"[^a-z0-9]", "", regex=True).str[:22] == re.sub(r"[^a-z0-9]", "", r.desc.lower())[:22]]
    if len(same): df.at[i, "dup_of"] = int(same.order.iloc[-1])
df["ym"] = df.date.dt.to_period("M").astype(str)
df["year"] = df.date.dt.year
out = df.drop(columns=["runmax"]).copy()
out["date"] = out.date.dt.strftime("%Y-%m-%d")
out["equip"] = out.equip.astype(object).where(out.equip.notna(), None)
json.dump(out.to_dict("records"), open("orders.json", "w"), ensure_ascii=False, default=lambda x: None if pd.isna(x) else (int(x) if isinstance(x, (np.integer,)) else float(x) if isinstance(x, np.floating) else bool(x) if isinstance(x, np.bool_) else str(x)))
print(len(out), "orders")
print(out.group.value_counts().to_string()); print(out[out.group == "Vehicle fleet"].cat_bn.value_counts().to_string()); print(out.pm.value_counts().to_string())
print("mismatch", out[out.mismatch][["order", "desc", "equip_vehicle", "vehicle"]].to_string())
print("dups", out[out.dup_of.notna()][["order", "dup_of", "desc", "cost"]].to_string())
print("backdated", int(out.backdated.sum()), "trunc", int(out.trunc.sum()))
print("vehicles", out.vehicle.nunique(), sorted(out.vehicle.dropna().unique()))
