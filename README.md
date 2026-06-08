# AeroQMS – Quality Detective

AeroQMS is an integrated manufacturing quality investigation platform for a drone manufacturing environment. It helps quality engineers move from a suspected issue to evidence review, formal investigation, corrective action, and verification.

Instead of acting like four separate dashboards, AeroQMS connects the full quality lifecycle:

```text
Risk Intelligence → Evidence Review → Case Management → Verification & Monitoring
```

---

## What This Project Is

AeroQMS simulates a real Quality Management System used by manufacturing and quality engineering teams.

It combines:

- FMEA risk analysis
- GD&T inspection verification
- NCR and CAPA management
- Root cause analysis
- Supplier quality feedback
- SPC and production analytics

The system is positioned as a **Quality Detective** assistant: a tool that helps engineers investigate quality problems using connected manufacturing data.

---

## Why This Is Needed

Quality engineers often work with disconnected systems:

- FMEA files are stored separately from inspection records
- Inspection failures are manually converted into NCRs
- NCRs and CAPAs are tracked in separate tools
- Supplier issues are hard to connect to production defects
- SPC data is reviewed after the fact instead of being tied to investigations

This makes it difficult to answer important questions quickly:

- Where did the issue start?
- Was this risk already known?
- What evidence proves the failure?
- Does this require an NCR or CAPA?
- What corrective action was taken?
- Did the process actually improve?

AeroQMS solves this by connecting each step into one investigation workflow.

---

## What It Solves

AeroQMS helps quality teams:

- Identify high-risk failure modes before production
- Evaluate inspection evidence against engineering requirements
- Generate draft NCRs from failed GD&T features
- Manage investigation cases through containment, RCA, CAPA, and closure
- Track supplier quality issues
- Monitor process health using FPY, defect rate, Cp, Cpk, and SPC trends
- Verify whether corrective actions were effective

---

## How It Works

A user starts with a quality concern, such as:

```text
Hole position failure on MMB-001, LOT-203
```

AeroQMS guides the user through the investigation:

```text
1. Risk Intelligence
   Review FMEA risks, RPN scores, known failure modes, and mitigation plans.

2. Evidence Review
   Run GD&T inspection checks, analyze true position error, review failed features,
   and generate draft NCR records.

3. Case Management
   Import draft NCRs, open investigation cases, assign containment, perform RCA,
   create CAPAs, and generate 8D reports.

4. Verification & Monitoring
   Review production KPIs, supplier quality, SPC charts, Cp/Cpk, and improvement trends
   to verify whether the fix worked.
```

---

## System Architecture

```text
AeroQMS – Quality Detective
│
├── app.py
│   └── Main Streamlit application and Quality Detective homepage
│
├── modules/
│   │
│   ├── fmea/
│   │   └── Risk Intelligence Center
│   │       ├── FMEA table
│   │       ├── RPN calculations
│   │       ├── Top risk ranking
│   │       ├── Mitigation planner
│   │       └── FMEA reports
│   │
│   ├── inspection/
│   │   └── Evidence Review Center
│   │       ├── GD&T inspection engine
│   │       ├── True position calculations
│   │       ├── Failure analysis
│   │       ├── Inspection report generation
│   │       └── Draft NCR generation
│   │
│   ├── ncr_capa/
│   │   └── Case Management Center
│   │       ├── NCR database
│   │       ├── Draft NCR import
│   │       ├── Case detail and disposition
│   │       ├── CAPA creation
│   │       ├── 5 Why analysis
│   │       ├── Fishbone analysis
│   │       ├── 8D reports
│   │       └── Supplier feedback reports
│   │
│   ├── dashboard/
│   │   └── Verification & Monitoring Center
│   │       ├── Production analytics
│   │       ├── Supplier scorecards
│   │       ├── NCR/CAPA analytics
│   │       ├── SPC monitoring
│   │       ├── Cp/Cpk analysis
│   │       └── Continuous improvement tracking
│   │
│   └── common/
│       ├── shared paths
│       └── shared UI helpers
│
├── data/
│   ├── propulsion_fmea.csv
│   ├── propulsion_fmea.xlsx
│   ├── inspection_requirements.yaml
│   ├── sample_measurements.csv
│   ├── inspection_results.csv
│   ├── draft_ncrs.csv
│   ├── ncr_capa.db
│   ├── ncr_records.csv
│   ├── production_records.csv
│   ├── inspection_records.csv
│   ├── suppliers.csv
│   ├── parts.csv
│   └── spc_measurements.csv
│
└── reports/
    ├── inspection_report.md
    ├── fmea_summary_report.md
    ├── top_10_risks.md
    ├── recommended_actions.md
    ├── ncr_reports/
    ├── capa_reports/
    └── dashboard_exports/
```

---

## Data Flow

```text
FMEA risk data
      ↓
Risk Intelligence Center
      ↓
Inspection requirements and measurement data
      ↓
Evidence Review Center
      ↓
Failed features generate draft NCRs
      ↓
Case Management Center
      ↓
NCRs trigger RCA, CAPA, supplier feedback, and 8D reports
      ↓
Verification & Monitoring Center
      ↓
SPC, FPY, defect rate, supplier quality, and CAPA effectiveness are reviewed
```

---

## Main Features

### Risk Intelligence Center

- FMEA risk register
- Severity, occurrence, detection scoring
- RPN calculation
- Top risk prioritization
- Risk heatmaps
- Mitigation tracking
- Risk reports

### Evidence Review Center

- GD&T inspection evaluation
- True position error calculation
- Feature-level pass/fail results
- Failure analysis by feature, lot, and GD&T type
- Technical evidence tables
- Inspection report generation
- Draft NCR generation

### Case Management Center

- NCR creation and tracking
- Draft NCR import from inspection failures
- Case detail and disposition updates
- CAPA creation
- Root cause analysis
- 5 Why analysis
- Fishbone analysis
- 8D report generation
- Supplier case feedback reports

### Verification & Monitoring Center

- First Pass Yield tracking
- Defect rate tracking
- Scrap and rework analytics
- Supplier quality scorecards
- NCR/CAPA analytics
- SPC control charts
- Cp and Cpk calculations
- Continuous improvement backlog

---

## Quality Engineering Concepts Demonstrated

- FMEA
- RPN
- GD&T inspection
- True position calculation
- NCR management
- CAPA management
- Root Cause Analysis
- 5 Why
- Fishbone diagram logic
- 8D reporting
- Supplier quality management
- SPC
- Cp/Cpk
- First Pass Yield
- Scrap and rework tracking
- Continuous improvement

---

## How To Run The Project

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Drone-Manufacturing-Quality-Portfolio.git
cd Drone-Manufacturing-Quality-Portfolio
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate
```

```bash
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit app

```bash
streamlit run app.py
```

### 5. Open the local app

Streamlit will provide a local URL similar to:

```text
http://localhost:8501
```

---

## Project Purpose

This project demonstrates how quality engineering workflows can be connected into a single digital platform.

AeroQMS shows how manufacturing quality teams can move beyond disconnected spreadsheets and dashboards toward an integrated system that supports investigation, traceability, corrective action, and continuous improvement.