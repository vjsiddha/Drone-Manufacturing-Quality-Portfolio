# Drone Propulsion System FMEA — Summary Report

**Document:** Propulsion FMEA Rev A  
**Date:** 2026-06-04  
**Prepared by:** Quality Engineering  
**Scope:** Drone Autonomous Delivery Vehicle — Propulsion Subsystem

---

## 1. Scope

This FMEA analyzes 35 failure modes across 8 propulsion components:

| Component | Failure Modes Analyzed |
|-----------|----------------------|
| Battery Connector | 5 |
| Electronic Speed Controller | 5 |
| Fasteners | 2 |
| Motor | 5 |
| Motor Mount Bracket | 5 |
| Propeller | 5 |
| Thermal Interface Material | 2 |
| Wiring Harness | 6 |

---

## 2. Assumptions

- Analysis covers manufacturing and design-related failure modes.
- Scoring reflects current-state controls prior to corrective actions.
- Detection controls reflect inspection and end-of-line test capabilities as of 2026-06-04.
- RPN threshold for high-risk classification: **≥ 150**.

---

## 3. Scoring Methodology

- **RPN = Severity × Occurrence × Detection** (1–10 scale each)
- High risk: RPN ≥ 150
- Moderate risk: RPN 80–149
- Low risk: RPN < 80
- Target: All revised RPNs below 80 after corrective actions

---

## 4. Risk Summary

| Metric | Value |
|--------|-------|
| Total failure modes | 35 |
| High-risk items (RPN ≥ 150) | 8 |
| Average RPN (before) | 113.2 |
| Average RPN (after) | 37.7 |
| Average RPN reduction | 66.2% |
| Highest RPN | 225 (Bearing seizure) |

---

## 5. Top 10 Risks by RPN

| Rank | Component | Failure Mode | S | O | D | RPN |
|------|-----------|-------------|---|---|---|-----|
| 1 | Motor | Bearing seizure | 9 | 5 | 5 | **225** |
| 2 | Wiring Harness | Wire chafing | 9 | 4 | 5 | **180** |
| 3 | Motor Mount Bracket | Hole position out of tolerance | 7 | 5 | 5 | **175** |
| 4 | Electronic Speed Controller | Firmware mismatch | 8 | 5 | 4 | **160** |
| 5 | Propeller | Delamination | 8 | 4 | 5 | **160** |
| 6 | Wiring Harness | Connector not fully seated | 8 | 5 | 4 | **160** |
| 7 | Wiring Harness | Intermittent connection | 8 | 5 | 4 | **160** |
| 8 | Battery Connector | Loose contact | 8 | 4 | 5 | **160** |
| 9 | Electronic Speed Controller | Thermal shutdown | 9 | 4 | 4 | **144** |
| 10 | Electronic Speed Controller | Solder joint failure | 7 | 4 | 5 | **140** |

---

## 6. Highest-Risk Components

| Component | Avg RPN |
|-----------|---------|
| Motor | 133.2 |
| Wiring Harness | 127.5 |
| Electronic Speed Controller | 123.6 |
| Motor Mount Bracket | 105.6 |
| Propeller | 101.6 |
| Battery Connector | 100.2 |
| Fasteners | 98.0 |
| Thermal Interface Material | 90.0 |

---

## 7. Recommended Mitigations

Key themes across corrective actions:

1. **Barcode/scan verification** — Eliminate wrong-part installation errors at motor, propeller, ESC
2. **Inspection step additions** — CMM tightening, C-scan for CFRP, PMI for material lots
3. **Connector upgrades** — Polarized, locking connectors to prevent reverse polarity and signal loss
4. **Torque data logging** — Digital torque tools with automated pass/fail flagging
5. **Thermal management** — TIM standardization, ESC thermal margin increase, thermal cycle screens
6. **SPC on CNC fixtures** — Reduce dimensional variation on Motor Mount Bracket hole positions

---

## 8. Revised RPN Results

After implementing recommended actions, average RPN drops from **113.2** to **37.7** — a **66.2% reduction**.

Items still requiring monitoring (revised RPN > 50):
- **Bearing seizure** (Motor): Revised RPN = 81
- **Loose contact** (Battery Connector): Revised RPN = 72
- **Solder joint failure** (Electronic Speed Controller): Revised RPN = 63
- **Hole position out of tolerance** (Motor Mount Bracket): Revised RPN = 63
- **Thermal shutdown** (Electronic Speed Controller): Revised RPN = 54

---

## 9. Lessons Learned

- Connector design improvements (polarization, locking) have high leverage — low cost, high RPN reduction
- Wire routing and chafing protection are underspecified in current SOPs; high-severity, high-occurrence gap
- Material verification (PMI) gaps represent high-severity, low-detection risk that must be closed at receiving
- Firmware configuration control needs formal version-locking in build traveler

---

## 10. Connection to Manufacturing Quality

This FMEA directly feeds into:

- **Inspection Plans** — High-occurrence/high-severity items trigger increased AQL sampling
- **NCR System** — Identified failure modes become defect type library
- **Supplier Quality** — Supplier-related failures become Supplier Corrective Action Requests (SCARs)
- **End-of-Line Test** — Detection gaps (high D score) → new EOL test cases
- **GD&T Inspection** — Motor Mount Bracket dimensional failures → CMM inspection requirements

