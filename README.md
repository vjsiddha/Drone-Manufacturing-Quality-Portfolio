# Drone Manufacturing Quality Engineering Portfolio

A connected 4-project system simulating a complete manufacturing quality lifecycle for an autonomous delivery drone. Each project represents a real workflow stage — risk assessment, dimensional inspection, non-conformance management, and quality analytics — and feeds data into the next.

---

## The Problem This Solves

Manufacturing quality teams struggle to connect their tools. FMEA lives in a spreadsheet. Inspection data sits in a CMM export. NCRs are tracked in email. Metrics are pulled manually into PowerPoint the night before a review.

This portfolio builds the integrated system that replaces that workflow.

---

## System Architecture

```
FMEA (Project 1)
Identifies high-risk failure modes → defines what to inspect for
        ↓
GD&T Inspection System (Project 2)
Measures parts against engineering requirements → auto-generates NCRs on failure
        ↓
NCR / CAPA System (Project 3)
Manages investigation, root cause, corrective action, and closure
        ↓
Quality Analytics Dashboard (Project 4)
Tracks FPY, defect trends, supplier scores, NCR aging, and COPQ
```

---

## Projects

### 01 — Drone Propulsion System FMEA
`01_risk_assessment_fmea/`

Hybrid design + process FMEA covering 8 propulsion components and 35 failure modes. Outputs color-coded Excel workbook with RPN scoring, top-10 risk ranking, and before/after mitigation comparison.

**Key numbers:** 35 failure modes · avg RPN 113 → 38 after mitigation · 66% risk reduction

**Skills:** FMEA · RPN · Risk prioritization · Corrective action planning

---

### 02 — Automated GD&T Inspection System
`02_inspection_verification/`

Python inspection engine that reads CMM-style measurement data, evaluates 11 GD&T features against engineering requirements, determines part disposition, and auto-generates draft NCRs for every failure. Built as a 5-page Streamlit app.

**Key numbers:** 11 features · 50 parts · 5 lots · 89 draft NCRs auto-generated · LOT-203 bad-lot scenario included

**Skills:** GD&T · True position math · Flatness/parallelism/perpendicularity · Automated reporting · Python

---

### 03 — NCR / CAPA Management System
`03_quality_management_system/`

Full non-conformance lifecycle tool. Imports draft NCRs from the inspection system, supports disposition workflow, 5-Why and fishbone RCA, CAPA tracking, and generates 8D reports. Backed by SQLite. Built as an 8-page Streamlit app.

**Key numbers:** 60 seeded NCRs · 20 CAPAs · Full 8D report generation · Closure blocked unless all required fields complete

**Skills:** NCR management · CAPA · 5-Why · Fishbone · 8D · Disposition workflow · SQLite

---

### 04 — Manufacturing Quality Dashboard
`04_quality_analytics_dashboard/`

Executive-facing Streamlit dashboard tracking production quality across 10,000+ synthetic records. Five pages covering KPIs, defect Pareto, supplier scorecards, station performance, and NCR analytics. Includes Cpk.

**Key numbers:** 10,000 inspection records · 3,000 production records · 500 NCRs · 10 suppliers scored A–D

**Skills:** FPY · Cpk · Defect Pareto · Supplier quality · COPQ · Streamlit · Plotly · Pandas

---

## Running the Projects

Each project is self-contained. Install dependencies and run:

```bash
# Project 1 — FMEA (generates Excel + markdown reports)
cd 01_risk_assessment_fmea
pip install -r requirements.txt
python generate_fmea.py

# Project 2 — GD&T Inspection (Streamlit app)
cd 02_inspection_verification
pip install -r requirements.txt
python generate_measurements.py
streamlit run app.py

# Project 3 — NCR/CAPA System (Streamlit app)
cd 03_quality_management_system
pip install -r requirements.txt
python seed_data.py
streamlit run app.py

# Project 4 — Quality Dashboard (Streamlit app)
cd 04_quality_analytics_dashboard
pip install -r requirements.txt
python generate_data.py
streamlit run app.py
```

---

## Key Quality Engineering Concepts Demonstrated

| Concept | Where |
|---------|-------|
| FMEA / RPN | Project 1 |
| GD&T (position, flatness, parallelism, perpendicularity, profile) | Project 2 |
| True position formula: `2√(dx² + dy²)` | Project 2 |
| NCR disposition workflow | Project 3 |
| 5-Why root cause analysis | Project 3 |
| Fishbone (Ishikawa) analysis | Project 3 |
| 8D problem solving | Project 3 |
| First Pass Yield | Projects 3, 4 |
| Cpk process capability | Project 4 |
| Supplier scorecard (A–D grading) | Project 4 |
| Cost of Poor Quality | Project 4 |
| Defect Pareto | Project 4 |

---