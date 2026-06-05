# FMEA Summary Report
## Drone Propulsion System — Rev A

| | |
|---|---|
| Document | Propulsion FMEA Rev A |
| Date | 2026-06-05 |
| Prepared by | Quality Engineering |
| Scope | Autonomous Delivery Drone — Propulsion Subsystem |
| RPN Formula | Severity × Occurrence × Detection (1–10 scale) |

---

## 1. Scope

35 failure modes analysed across 8 propulsion components.

| Component | Failure Modes |
|-----------|--------------|
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

- Analysis covers both design-intent and manufacturing-process failure modes.
- All scores reflect current-state controls — no proposed mitigations applied.
- RPN threshold for high-risk classification: 150.
- Detection controls reference inspection and EOL test capabilities as of 2026-06-05.

---

## 3. Scoring Methodology

RPN = Severity × Occurrence × Detection

| Band | RPN Range | Action Required |
|------|-----------|----------------|
| High | ≥ 150 | Immediate corrective action |
| Moderate | 80–149 | Action plan required |
| Low | < 80 | Monitor; no immediate action |

---

## 4. Risk Summary

| | |
|---|---|
| Total failure modes | 35 |
| High-risk items (RPN ≥ 150) | 8 |
| Average RPN — before | 113.2 |
| Average RPN — after | 37.7 |
| Average RPN reduction | 66.2% |
| Highest RPN | 225 — Bearing seizure |

---

## 5. Top 10 Risks by RPN

| Rank | Component | Failure Mode | S | O | D | RPN |
|------|-----------|-------------|---|---|---|-----|
| 1 | Motor | Bearing seizure | 9 | 5 | 5 | 225 |
| 2 | Wiring Harness | Wire chafing | 9 | 4 | 5 | 180 |
| 3 | Motor Mount Bracket | Hole position out of tolerance | 7 | 5 | 5 | 175 |
| 4 | Electronic Speed Controller | Firmware mismatch | 8 | 5 | 4 | 160 |
| 5 | Propeller | Delamination | 8 | 4 | 5 | 160 |
| 6 | Wiring Harness | Connector not fully seated | 8 | 5 | 4 | 160 |
| 7 | Wiring Harness | Intermittent connection | 8 | 5 | 4 | 160 |
| 8 | Battery Connector | Loose contact | 8 | 4 | 5 | 160 |
| 9 | Electronic Speed Controller | Thermal shutdown | 9 | 4 | 4 | 144 |
| 10 | Electronic Speed Controller | Solder joint failure | 7 | 4 | 5 | 140 |

---

## 6. Risk by Component

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

Six themes emerged across corrective actions:

- Barcode scan verification at assembly — eliminates wrong-part installation at motor, propeller, and ESC stations
- AQL tightening and CMM SPC — closes dimensional gaps on Motor Mount Bracket hole positions
- Connector upgrades — polarized and locking connectors eliminate reverse polarity and signal-loss risk
- Digital torque logging — real-time pass/fail capture replaces manual torque audit
- Thermal management — TIM shim templates, ESC margin increase, thermal cycle qualification screen
- PMI at receiving — closes material verification gap on high-severity, low-detection bracket lots

---

## 8. Revised RPN Results

Average RPN reduced from 113.2 to 37.7 — a 66.2% reduction across the subsystem.

Items still above RPN 50 after mitigation:

- Bearing seizure (Motor): revised RPN 81
- Loose contact (Battery Connector): revised RPN 72
- Solder joint failure (Electronic Speed Controller): revised RPN 63
- Hole position out of tolerance (Motor Mount Bracket): revised RPN 63
- Thermal shutdown (Electronic Speed Controller): revised RPN 54

---

## 9. Lessons Learned

- Connector design changes (polarization, locking retention) deliver high RPN reduction at low implementation cost
- Wire routing and chafing protection gaps are underspecified in current SOPs — high-severity, high-occurrence risk
- PMI gaps at receiving represent a high-severity, low-detection condition that cannot be deferred
- Firmware version control requires formal configuration locking in the build traveler, not just release notes review

---

## 10. Connection to Manufacturing Quality

| Downstream System | How This FMEA Feeds It |
|------------------|------------------------|
| Inspection Plans | High S×O items trigger increased AQL sampling rates |
| NCR Defect Library | Failure modes become standardised defect type categories |
| Supplier Quality | Supplier-caused failures generate SCARs |
| EOL Test Cases | High-detection-score items become new automated EOL checks |
| GD&T Inspection | Bracket dimensional failures define CMM feature requirements |

---
*Generated 2026-06-05 — Drone Manufacturing Quality Engineering*
