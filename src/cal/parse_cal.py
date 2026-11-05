"""Read the Cylinder Weight Calibration workbook into one row per check-weighed cylinder.
error_g = (after - tare - nominal) * 1000, recomputed from raw weights (sheet totals are not trusted:
column meanings changed between 2024 and 2026). Sheet name is the date (date cells are often wrong)."""
import re, sys, json, datetime as dt
import openpyxl, pandas as pd

SKIP = {"for amzad vai", "agm report"}

def sheet_date(name):
    m = re.match(r"\s*(\d{1,2})-(\d{1,2})-(\d{2,4})\s*$", name)
    if not m: return None
    d, mo, y = map(int, m.groups()); y = y + 2000 if y < 100 else y
    return dt.date(y, mo, d)

def nominal_above(ws, r, c):
    for rr in range(r - 1, max(0, r - 4), -1):
        for cc in range(max(1, c - 3), c + 10):
            v = ws.cell(rr, cc).value
            if isinstance(v, str):
                m = re.search(r"(\d{2})\s*kg", v, re.I)
                if m: return int(m.group(1))
    return None

def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def read(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    rows, issues = [], []
    for name in wb.sheetnames:
        if name.strip().lower() in SKIP: continue
        d = sheet_date(name)
        if d is None: issues.append(("sheet name not a date", name)); continue
        ws = wb[name]
        cell_date = ws.cell(3, 2).value
        blocks = []
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                v = ws.cell(r, c).value
                if isinstance(v, str) and v.strip().lower().startswith("tare weight"):
                    blocks.append((r, c))
        n12 = 0
        for (r, c) in blocks:
            nom = nominal_above(ws, r, c) or 12
            cols = {}
            for cc in range(c, min(ws.max_column, c + 12) + 1):
                h = ws.cell(r, cc).value
                if not isinstance(h, str): continue
                hl = h.lower()
                if hl.startswith("tare") and "tare" not in cols: cols["tare"] = cc
                elif "before" in hl and "before" not in cols: cols["before"] = cc
                elif "after" in hl and "after" not in cols: cols["after"] = cc
                elif "machine" in hl and "machine" not in cols: cols["machine"] = cc; break
            if nom == 12: n12 += 1
            blk = n12 if nom == 12 else 1
            rr = r + 1
            while rr <= ws.max_row:
                sl = ws.cell(rr, c - 1).value
                if sl is None or isinstance(sl, str): break
                t, b, a = (num(ws.cell(rr, cols[k]).value) if k in cols else None for k in ("tare", "before", "after"))
                mach = num(ws.cell(rr, cols["machine"]).value) if "machine" in cols else None
                rows.append({"sheet": name, "date": d.isoformat(), "block": blk, "nominal": nom, "sl": int(num(sl) or 0),
                             "head": int(mach) if mach else int(num(sl) or 0), "tare_kg": t, "before_kg": b, "after_kg": a})
                rr += 1
        if cell_date is not None and hasattr(cell_date, "date") and cell_date.date() != d:
            issues.append(("date cell differs from sheet name", f"{name.strip()}: cell {cell_date.date()}"))
    df = pd.DataFrame(rows)
    # round label, matching the earlier report: '04 Jun 24', with (1)/(2) when a sheet has two 12 kg rounds
    multi = df[df.nominal == 12].groupby("date").block.nunique()
    def label(r):
        base = dt.date.fromisoformat(r.date).strftime("%d %b %y")
        return f"{base} ({r.block})" if r.nominal == 12 and multi.get(r.date, 1) > 1 else base
    df["round"] = df.apply(label, axis=1)
    df["net_kg"] = df.after_kg - df.tare_kg
    df["error_g"] = ((df.net_kg - df.nominal) * 1000).round(1)
    df["leftover_g"] = ((df.before_kg - df.tare_kg) * 1000).round(1)
    bad = df.tare_kg.isna() | df.after_kg.isna() | (df.tare_kg <= 0) | (df.after_kg <= 0) | (df.after_kg < df.tare_kg) | (df.error_g.abs() > 1000) | (df.leftover_g < -300)  # empty weight >300 g below tare = misread tare
    df["valid"] = ~bad
    return df, issues

if __name__ == "__main__":
    df, issues = read(sys.argv[1])
    df.to_json(sys.argv[2], orient="records", force_ascii=False, indent=0)
    json.dump(issues, open(sys.argv[2].replace(".json", "_issues.json"), "w"), ensure_ascii=False, indent=1)
    print(len(df), "rows;", int(df.valid.sum()), "valid;", len(issues), "issues")
