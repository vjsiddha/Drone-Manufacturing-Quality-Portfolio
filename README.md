# Drone Manufacturing Quality Engineering Portfolio

## Overview

Manufacturing quality teams face a common challenge:

How do you consistently build products that meet engineering requirements while minimizing defects, reducing rework, improving supplier performance, and preventing recurring quality issues?

Quality issues can originate at any stage of the product lifecycle:

- Design decisions introduce risk
- Suppliers deliver nonconforming parts
- Manufacturing processes drift out of control
- Inspection failures go unnoticed
- Root causes are poorly understood
- Corrective actions are not tracked effectively
- Quality data remains disconnected from decision-making

When these problems are not addressed systematically, organizations experience:

- Increased scrap and rework
- Reduced yield
- Supplier quality issues
- Longer production cycles
- Escalating cost of poor quality
- Repeated failures caused by unresolved root causes

This portfolio demonstrates a complete quality lifecycle designed to address these challenges.

The system follows a structured quality engineering workflow to:

1. Identify risks before failures occur
2. Detect nonconforming parts during inspection
3. Investigate and resolve quality incidents
4. Measure the effectiveness of corrective actions
5. Drive continuous improvement using quality data

---

# Quality Lifecycle

```text
Risk Identification
        ↓
Inspection & Verification
        ↓
Non-Conformance Management
        ↓
Root Cause Analysis
        ↓
Corrective & Preventive Action
        ↓
Quality Analytics
        ↓
Continuous Improvement
```

Each project represents a critical stage in this lifecycle.

---

# Repository Structure

```text
drone-manufacturing-quality-portfolio/
│
├── 01_risk_assessment_fmea/
├── 02_inspection_verification/
├── 03_quality_management_system/
├── 04_quality_analytics_dashboard/
│
├── assets/
│   ├── architecture/
│   ├── reports/
│   └── screenshots/
│
└── README.md
```

---

# Problem Statement

Quality engineers are responsible for ensuring that manufacturing systems produce parts and assemblies that consistently meet requirements.

In practice, this involves answering questions such as:

### Risk

What are the most critical ways a component could fail?

### Inspection

Are incoming parts actually meeting engineering requirements?

### Non-Conformance Management

What happens when a defect is discovered?

### Root Cause Analysis

Why did the defect occur?

### Corrective Action

How do we ensure the issue does not happen again?

### Quality Analytics

Are the corrective actions actually improving performance?

This portfolio addresses each of these questions through an integrated quality lifecycle.

---

# Project 1 — Risk Assessment (FMEA)

**Folder:** `01_risk_assessment_fmea/`

## Purpose

Quality issues are often discovered only after they reach production.

FMEA provides a structured approach for identifying potential failure modes before failures occur.

The objective is to understand:

- What could fail
- Why it could fail
- How severe the consequences would be
- How likely the failure is to occur
- How likely the failure is to be detected

By prioritizing risks early, controls can be implemented before quality issues reach production.

## Key Outcomes

- Identification of critical failure modes
- Quantified risk prioritization
- Recommended mitigation actions
- Reduction of overall system risk

## Deliverables

- 35 failure modes across 8 propulsion-related components
- Automated RPN calculations
- Risk ranking and prioritization
- Corrective action recommendations
- Before-and-after mitigation comparison
- Color-coded Excel workbook
- Summary reports and visualizations

---

# Project 2 — Inspection & Verification

**Folder:** `02_inspection_verification/`

## Purpose

Even with robust risk planning, parts must still be verified against engineering requirements.

Inspection systems are responsible for determining whether components conform to specifications.

This project automates that process using GD&T and dimensional inspection requirements.

## Challenges Addressed

- Manual inspection reviews are time consuming
- Large datasets are difficult to evaluate consistently
- Defects can be missed due to human error
- Documentation can become inconsistent

## Key Outcomes

- Automated pass/fail evaluation
- Standardized inspection logic
- Consistent verification against requirements
- Automatic generation of draft NCRs for failed features

## Deliverables

- Evaluation of 11 GD&T features
- True position analysis
- Flatness verification
- Parallelism verification
- Perpendicularity verification
- Profile verification
- Diameter validation
- Slot width validation
- Thickness validation
- PDF inspection reports
- CSV inspection results
- Markdown reports
- 89 automatically generated draft NCRs

---

# Project 3 — Quality Management System

**Folder:** `03_quality_management_system/`

## Purpose

Finding a defect is only the beginning of the quality process.

The next challenge is determining:

- What should happen to affected material?
- What caused the issue?
- How can recurrence be prevented?

This project manages the entire lifecycle of a quality incident.

## Challenges Addressed

- Inconsistent NCR documentation
- Delayed investigations
- Missing root cause analysis
- Untracked corrective actions
- Repeated failures caused by ineffective CAPAs

## Key Outcomes

- Structured NCR workflow
- Root cause analysis using 5 Why and Fishbone methods
- CAPA management
- 8D problem solving reports
- Verification and closure tracking

## Deliverables

### NCR Management

- NCR Creation
- Severity Classification
- Aging Tracking
- Disposition Management
- Ownership Assignment

### Root Cause Analysis

- 5 Why Analysis
- Fishbone Analysis

Categories:

- Manpower
- Machine
- Method
- Material
- Measurement
- Environment

### CAPA Management

- Corrective Action Tracking
- Preventive Action Tracking
- Due Date Management
- Verification Tracking
- Closure Verification

### 8D Problem Solving

- D1 Team Formation
- D2 Problem Description
- D3 Containment
- D4 Root Cause Analysis
- D5 Corrective Action
- D6 Implementation
- D7 Prevention
- D8 Closure

---

# Project 4 — Quality Analytics Dashboard

**Folder:** `04_quality_analytics_dashboard/`

## Purpose

Quality systems generate large amounts of data.

Without visibility into trends and performance metrics, it becomes difficult to determine whether improvement efforts are actually working.

This project consolidates quality information into a single operational view.

## Challenges Addressed

- Disconnected quality metrics
- Limited visibility into supplier performance
- Difficulty identifying recurring issues
- Poor tracking of quality improvement initiatives

## Key Outcomes

- First Pass Yield monitoring
- Defect trend analysis
- Supplier performance evaluation
- NCR and CAPA tracking
- Cost of Poor Quality visibility
- Continuous improvement monitoring

## Deliverables

- Executive KPI dashboard
- Defect Pareto analysis
- Supplier scorecards
- Production station performance analysis
- NCR analytics dashboard
- 10,000-record synthetic manufacturing dataset

---

# End-to-End Workflow Example

## Step 1

A high-risk failure mode is identified during FMEA analysis.

```text
Hole Position Out-of-Tolerance
```

Risk controls are recommended.

## Step 2

A batch of parts is inspected.

The inspection system determines:

```text
Measured Value: 0.28 mm
Tolerance:      0.20 mm
```

Result:

```text
FAIL
```

A draft NCR is automatically generated.

## Step 3

The quality management system receives the NCR.

The investigation process includes:

- Containment
- Disposition
- Root Cause Analysis
- Corrective Action
- Preventive Action
- Verification

Root cause is identified and corrective actions are implemented.

## Step 4

Quality metrics are monitored through the dashboard.

The team can observe whether:

- Defect rates decrease
- Yield improves
- Supplier performance improves
- NCR closure times decrease
- Corrective actions remain effective

---

# Quality Engineering Concepts Demonstrated

## Risk Management

- Failure Modes and Effects Analysis (FMEA)
- Risk Priority Number (RPN)
- Preventive Quality Engineering

## Inspection & Verification

- GD&T
- Dimensional Inspection
- Acceptance Criteria
- Verification & Validation

## Quality Management

- NCR Management
- CAPA
- 5 Why Analysis
- Fishbone Analysis
- 8D Problem Solving

## Manufacturing Quality

- Supplier Quality
- First Pass Yield
- Scrap & Rework Analysis
- Cost of Poor Quality
- Continuous Improvement

---

# System Objective

The objective of this portfolio is to demonstrate how quality information flows through an entire manufacturing lifecycle:

```text
Potential Risk
      ↓
Inspection Failure
      ↓
Non-Conformance
      ↓
Root Cause
      ↓
Corrective Action
      ↓
Performance Monitoring
      ↓
Continuous Improvement
```

Rather than treating quality activities as isolated tasks, the portfolio connects them into a single system where risk assessment, inspection, investigation, corrective action, and analytics work together to improve product quality and process performance.
