# How to update

Prepared by: Akib Fateh. When new data arrives, the reports and site are refreshed with the steps below; at the end `index.html` is rebuilt.

## 1. Cylinder weight checks

```
python3 -I src/cal/update_cal.py <weight-check workbook.xlsx> --date YYYY-MM-DD
python3 -I src/build_site.py
```

Adds the new rounds: safety, data quality, comparison with the previous period, head-by-head table, forecast and its validation, the "Deep analysis" tab (significance, error sources, cost, progress), and the landing-page figures. `build_site.py` then recalculates every red flag.

## 2. Maintenance (SAP PM orders)

New orders go in the `ROWS` list of `src/maint/orders_raw.py` (same order: order, type, date, equipment, description, status, cost, actual start, actual finish). An Excel export from SAP (IW38/IW39) is best.

```
python3 -I src/maint/prep.py
AS_OF=YYYY-MM-DD python3 -I src/maint/analyze.py
python3 -I src/maint/deep.py
UPDATE_DATE=YYYY-MM-DD python3 -I src/maint/build_maint.py
python3 -I src/build_site.py
```

`AS_OF` = the date the record is taken to run to (normally today). The silent period from the last order to `AS_OF` is not treated as "no work": unbooked work and cost are estimated from the 2026 order rate and the usual delay in entering orders into SAP.

## Rules

- Every number is calculated from the data; any assumption is written down.
- Safety items first, "For review by a qualified engineer" (NFPA 10, 25, 58; LPG Rules 2004).
- Data-quality issues first; comparison with the previous period and with targets.
- Forecasts state the method, training period, accuracy (MAPE/RMSE) and range.
- All text on the site is in British English.
- Red flags (`src/build_site.py`) are recalculated on every build from the report data: each has a severity (red or amber), the current value, its limit, the reason and the report sections where it is shown.

## Folders

| Path | Contents |
|---|---|
| `index.html` | The published site (generated file; do not edit by hand) |
| `assets/` | Plant image (1280 to 3840 px) and BM LP GAS logo (background, header, watermark and footer of the landing page and both reports) |
| `src/build_site.py` | Builds `index.html` from the landing page and the two reports |
| `src/hub/` | Landing-page template and figures |
| `src/reports/` | The two report pages |
| `src/cal/` | Weight-check update and deep analysis |
| `src/maint/` | Maintenance: orders, analysis, TPM, equipment guide, page builder |

## Mobile app

- Data updates need no new app: the app opens the live site and saves a copy for offline use (`sw.js`).
- To change the app itself: edit `app/android/`, raise `VERSION_NAME` in `app/android/version.properties` and push. The "Android app" workflow builds an unsigned app on the `app-build` branch; sign it with the plant's key (kept privately) into `download/BM-Barabkunda-Plant.apk`, run `src/build_site.py` and push. The "Android app check" workflow then installs it on an emulator and saves screenshots on the `app-check` branch.
- Installable-website files: `manifest.webmanifest`, `sw.js`, `assets/app/`.
