"""TPM programme content for Barabkunda LPG plant (Bangla). Numbers are filled in by build_maint.py from tpm.json."""

PILLARS = {
 "jh": dict(jp="Jishu Hozen", goal="Operators and drivers own their equipment: cleaning, inspecting, lubricating and tightening become a daily habit.",
            focus="Carousel filling heads, pumps and compressors, valve manifolds, every LPG-carrying vehicle (driver's daily check).",
            act=["Introduce a one-page CLIT checklist for each piece of equipment (below), signed every shift", "Pilot area: initial cleaning and defect-tag drive in the carousel and pump house", "A 10-minute daily vehicle check card for drivers (tyres, brakes, oil, battery, leaks)"],
            kpi="Daily checklist compliance; defect tags opened and closed each month", owner="Production Manager and Head of Transport"),
 "pm": dict(jp="Keikaku Hozen", goal="Maintenance before breakdown: time- or condition-based schedules, recurring plans in SAP, spares stocked in advance.",
            focus="A fixed service interval for every vehicle, the 15 idle air-compressor plan orders, condition monitoring of pumps and compressors (vibration, temperature).",
            act=["A ZPM3 maintenance plan in SAP for every piece of equipment and vehicle (per the schedule below)", "Vehicle service at fixed days or kilometres (start from the current median interval)", "Weekly planning meeting: confirm next week's jobs, parts and people"],
            kpi="Planned-work share, plan compliance, MTBF", owner="Head of Maintenance"),
 "kk": dict(jp="Kobetsu Kaizen", goal="Remove the major losses one by one with root-cause analysis (why-why, fishbone, PDCA).",
            focus="The most expensive vehicles, repeat repairs within 90 days, cylinder overfilling.",
            act=["Start with three projects from the kaizen board below, each with a team leader", "A one-page why-why analysis for every repeat repair", "Monthly kaizen review with savings recorded"],
            kpi="Repeat-repair rate, savings per project (Tk)", owner="Plant Manager"),
 "qm": dict(jp="Hinshitsu Hozen", goal="Control equipment conditions for zero defects: know which conditions cause wrong weight or leaks, and check exactly those conditions regularly.",
            focus="Filling-head weight accuracy (Cpk), check-scale, leak test, cylinder valves.",
            act=["Set the condition standard for each head per the quality-maintenance matrix below", "Calibrate the load cells and filling valves of the flagged heads first", "Update the X-bar/S chart after every weight check"],
            kpi="Cpk (target ≥ 1.33), % within ±150 g", owner="Quality control and maintenance"),
 "ot": dict(jp="Office TPM", goal="Accurate, timely maintenance paperwork and data flow: order first, confirmation and TECO right after the job.",
            focus="SAP PM orders: opened before the work, confirmation, TECO, catalogue codes, equipment numbers, one consistent vehicle number.",
            act=["Rule: order before the work starts; confirmation and TECO within 48 hours of completion", "Introduce catalogue codes for damage cause and job type", "Weekly SAP health report: open, back-dated and equipment-less orders"],
            kpi="Confirmation %, TECO %, orders on time %", owner="Maintenance planner and SAP team"),
 "she": dict(jp="Anzen Eisei Kankyo", goal="Zero accidents: safety equipment is never out of date; every job has a permit and a risk assessment.",
            focus="Gas detectors, fire extinguishers, deluge and fire pumps, PSVs, ESD, licences.",
            act=["Check the list of all safety equipment and its last test date (S1–S6 in this report)", "Permit-to-work, lock-out/tag-out and gas testing made mandatory", "Start near-miss reporting with a monthly review"],
            kpi="Out-of-date safety equipment (target zero), near-miss reports", owner="HSE Manager"),
 "et": dict(jp="Kyoiku Kunren", goal="Trained people for every task: skills matrix, one-point lessons (OPL) and competence certificates.",
            focus="LPG safety, valves and PSVs, pump seals, load-cell calibration, using SAP PM.",
            act=["Baseline assessment of everyone in the skills matrix below", "At least four one-point lessons (OPL) every month", "Two trained people for every critical task (no single point of dependence)"],
            kpi="Skills-matrix completion %, training hours", owner="HR and heads of department"),
 "eem": dict(jp="Shoki Kanri", goal="Make sure new equipment has an easy-to-maintain design and spares at the time it is bought and installed.",
            focus="New vehicles, pumps, filling heads, valves: specifications informed by past failure data.",
            act=["Pre-purchase checklist: spares availability, service support, life-cycle cost", "Use SAP cost history to put the most expensive parts into the specifications", "Early monitoring for the first 90 days after installation"],
            kpi="First-year breakdowns of new equipment", owner="Engineering and procurement"),
}

# Nakajima's 16 major losses adapted to an LPG bottling plant. src: 'data' = measured in this site, 'gap' = not yet measured
LOSSES = [
 ("Equipment", "Breakdowns", "Repair after breakdown: {reactive} of fleet jobs", "data"),
 ("Equipment", "Set-up and adjustment", "Changing cylinder size (12/35/45 kg), adjusting the head set-weight", "gap"),
 ("Equipment", "Part/tool changes", "Filling-head seals, pump vanes, tyres, brake kits", "data"),
 ("Equipment", "Start-up losses", "The first cylinders of each head weigh wrong at the start of a shift", "gap"),
 ("Equipment", "Minor stops and idling", "Cylinders jamming on the conveyor, heads slow to seat", "gap"),
 ("Equipment", "Reduced speed", "Worn pump vanes slow the filling; carousel running below rated speed", "gap"),
 ("Equipment", "Defects and rework", "Cylinders rejected for weight or leaks: {out150} outside ±150 g", "data"),
 ("Equipment", "Planned shutdowns", "Shutdowns and annual maintenance", "gap"),
 ("People", "Management losses", "Waiting for parts or approval; back-dated orders {backdated}", "data"),
 ("People", "Motion losses", "Walking to find parts and tools: reduced by 5S", "gap"),
 ("People", "Line-organisation losses", "Uneven staffing across shifts", "gap"),
 ("People", "Transport and logistics", "Vehicles stuck in the workshop: the 3 highest-cost vehicles {top3}", "data"),
 ("People", "Measurement and adjustment", "Weighing-equipment calibration drift; repeated head adjustment", "data"),
 ("Materials and energy", "Yield loss (overfilling)", "An estimated {give} of LPG given away free in Mar–Oct 2026", "data"),
 ("Materials and energy", "Energy losses", "Air leaks make the compressor run longer; inefficient pumps", "gap"),
 ("Materials and energy", "Tools and dies", "Early replacement of tyres and batteries", "data"),
]

AM_STEPS = [
 ("Initial cleaning", "Cleaning is inspection: find leaks, cracks and loose bolts under the dirt and attach defect tags.", "Start with the carousel and pump house; every tag on the list."),
 ("Remove sources of contamination and hard-to-reach places", "Stop oil, dust or gas from seeping out; make cleaning and inspection easy.", "Every source fixed and cleaning time halved."),
 ("Provisional standards for cleaning, lubrication and inspection", "What, how, how often, who: a one-page CLIT standard.", "A CLIT card hung on every piece of equipment."),
 ("General inspection", "Teach operators the parts and functions of the equipment (bolts, oil, air, electricity, pressure), then inspect.", "A one-point lesson and test for each topic."),
 ("Autonomous inspection", "Operators run their own checklists; duties split against the maintenance team's checklist.", "Checklist compliance ≥ 95%."),
 ("Standardisation", "Workplace management: fixed places for parts, tools and information; visual controls (colours, markings).", "≥ 80% in the 5S audit."),
 ("Autonomous management", "Operator teams set their own targets, measure losses and run small kaizens.", "Monthly team kaizen."),
]

# extra planned-maintenance items not drawn in the equipment guide
EXTRA_PM = [
 ("LPG-carrying vehicles", "fleet", [("Driver's daily check: tyres, brakes, oil, water, battery, lights, leaks, fire extinguisher", "Daily", "O", "CLIT"), ("Scheduled service: engine oil, filters, grease, brakes", "Fixed kilometres or days", "T", "L"),
                                     ("Tyre pressure and tread, wheel nuts", "Weekly", "T", "IT"), ("Renew explosives licence, fitness and route permit", "Before expiry", "H", "I")]),
 ("Air compressors and dryer", "plant", [("Oil level, drain, pressure, temperature", "Daily", "O", "LI"), ("Clean the air filter", "Weekly", "T", "C"), ("Change oil and separator", "By running hours", "T", "L"),
                                        ("Receiver safety valve and pressure-vessel inspection", "Yearly", "E", "I")]),
 ("Diesel generator", "plant", [("Oil, coolant, battery, fuel", "Weekly", "O", "LI"), ("Run on load", "Monthly", "T", "I"), ("Change oil and filters", "By running hours", "T", "L")]),
 ("Electrical panels and earthing", "plant", [("Flameproof box covers and glands", "Monthly", "T", "IT"), ("Thermal imaging", "Half-yearly", "E", "I"), ("Earthing and bonding resistance measurement", "Yearly", "E", "I")]),

 ("Weighbridge", "plant", [("Zero and clean", "Daily", "O", "C"), ("BSTI verification", "Yearly", "V", "I")]),
]

ROADMAP = [  # (step, phase, start month offset, duration months)
 ("1. Top-management announcement", "Preparation", 0, 1), ("2. Training and awareness", "Preparation", 0, 3), ("3. TPM committee and promotion office", "Preparation", 1, 1),
 ("4. Policy and targets (this report's KPIs)", "Preparation", 1, 2), ("5. Master plan", "Preparation", 2, 1), ("6. Formal kick-off", "Kick-off", 3, 1),
 ("7. Pilot area: carousel and pump house", "Implementation", 3, 9), ("8. Autonomous maintenance (steps 1–4)", "Implementation", 4, 14), ("9. Planned maintenance and SAP plans", "Implementation", 3, 12),
 ("10. Quality maintenance (weight accuracy)", "Implementation", 4, 12), ("11. Skills development and OPL", "Implementation", 3, 18), ("12. Early equipment management and office TPM", "Implementation", 6, 12),
 ("13. Full roll-out and higher targets", "Consolidation", 18, 18),
]

GOV = [
 ("TPM steering committee", "Plant Manager (chair), heads of department", "Monthly", "Targets, resources, progress review"),
 ("TPM promotion office", "One coordinator (full- or part-time)", "Weekly", "Coordinates pillar teams, updates KPIs, audits"),
 ("Pillar teams (8)", "A team leader and 4–6 members each", "Weekly", "Plan and carry out the pillar's work"),
 ("Small groups (operators/drivers)", "Each shift or vehicle team", "15 minutes daily", "Checklists, defect tags, small kaizens"),
]

RACI = [  # activity, Plant Mgr, Maintenance, Production, HSE, Transport, Admin/SAP
 ("Daily CLIT checklist", "I", "C", "A/R", "I", "R", "—"), ("SAP maintenance plans and schedules", "A", "R", "C", "C", "C", "C"),
 ("Opening orders, confirmation, TECO", "I", "A/R", "C", "—", "R", "C"), ("Testing safety equipment", "A", "R", "C", "R", "—", "—"),
 ("Weight accuracy and calibration", "A", "R", "R", "—", "—", "—"), ("Licence renewals", "A", "—", "—", "C", "R", "R"),
 ("Kaizen projects", "A", "R", "R", "C", "R", "C"), ("Skills matrix and training", "A", "R", "R", "R", "R", "C"),
]

S5 = [
 ("Sort", ["Unneeded parts and tools have been removed", "Old valves, hoses and cylinders separately marked", "A red-tag area exists and is emptied regularly"]),
 ("Set in order", ["Every tool and part has a fixed, labelled place", "Fire extinguishers and ESD buttons clearly marked and unobstructed", "Flow direction and colour codes on pipes and valves"]),
 ("Shine", ["No oil, dust or gas stains on equipment", "Defects are looked for and tagged during cleaning", "No oil or water on the floor"]),
 ("Standardise", ["A CLIT card on every piece of equipment", "Normal ranges marked green/red on gauges", "One-point lessons posted at the workplace"]),
 ("Sustain", ["A monthly 5S audit is done and the results posted", "Defects from the previous audit closed", "Everyone knows and follows the rules"]),
]

SKILLS = ["LPG safety and permits", "Valves and PSVs", "Pumps and seals", "Compressors", "Filling heads and load cells", "Gas detectors and ESD", "Fire fighting", "Vehicle maintenance", "SAP PM"]
ROLES = ["Filling operator", "Pump/compressor operator", "Maintenance technician", "Electrical technician", "Driver", "Shift supervisor", "Maintenance planner"]
# required level 0-4 per role x skill
REQ = [
 [3, 1, 1, 0, 3, 2, 2, 0, 1], [3, 2, 3, 3, 1, 2, 2, 0, 1], [3, 4, 4, 3, 3, 2, 2, 1, 2], [3, 1, 1, 1, 2, 4, 2, 1, 1],
 [3, 1, 0, 0, 0, 1, 2, 3, 0], [4, 3, 2, 2, 3, 3, 3, 1, 3], [3, 3, 3, 3, 3, 3, 2, 2, 4],
]

QM = [  # quality characteristic -> condition, standard, check, frequency
 ("Net weight 12 kg (±150 g)", "Load-cell zero and span", "Deviation on test weight ≤ 20 g", "Certified weight", "Every shift"),
 ("Net weight 12 kg (±150 g)", "Filling-valve closing time", "In-flight compensation updated", "Cylinder weight vs set-weight", "Daily"),
 ("Net weight 12 kg (±150 g)", "Correct tare weight", "Tare stamped on the cylinder is legible", "Visual", "Every cylinder"),
 ("Net weight 12 kg (±150 g)", "LPG temperature and density", "Changes recorded", "Thermometer/density", "Every shift"),
 ("No leaks", "Filling-head seals", "No visible wear", "Visual and leak detector", "Weekly"),
 ("No leaks", "Cylinder-valve O-rings", "No bubbles in the leak test", "Water bath/electronic", "Every cylinder"),
 ("Check-scale accuracy", "Check-scale calibration", "BSTI certificate valid; correct on test weight", "Certified weight", "Every shift / yearly"),
]

FTAG = [("Blue tag", "Operator can fix it (cleaning, loose bolt, label)", "#4c9bff"),
        ("Red tag", "Maintenance team needed (leak, crack, vibration, broken gauge)", "#ff5a5f"),
        ("Yellow tag", "Safety risk: report immediately (gas smell, unusable extinguisher)", "#ffc46b")]
