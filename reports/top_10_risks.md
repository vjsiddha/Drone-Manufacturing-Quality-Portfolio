# Top 10 FMEA Risk Items
## Drone Propulsion System — Ranked by RPN

## Rank 1 — Bearing seizure

| | |
|---|---|
| Component | Motor |
| Risk Band | HIGH |
| RPN | 225 (S=9 × O=5 × D=5) |
| Failure Effect | Complete loss of motor rotation → vehicle crash |
| Potential Cause | Insufficient lubrication / contamination during assembly |
| Recommended Action | Add bearing inspection step at motor install; specify grease type in BOM |
| Owner | QE-Torres |
| Due Date | 2026-07-05 |
| Revised RPN | 81 — reduction of 144 points (64%) |
| Status | In Progress |

---

## Rank 2 — Wire chafing

| | |
|---|---|
| Component | Wiring Harness |
| Risk Band | HIGH |
| RPN | 180 (S=9 × O=4 × D=5) |
| Failure Effect | Short circuit → fire risk or power loss |
| Potential Cause | Inadequate routing protection in high-vibration zones |
| Recommended Action | Add grommets/abrasion sleeves at all frame contact points; add to inspection checklist |
| Owner | QE-Patel |
| Due Date | 2026-06-26 |
| Revised RPN | 54 — reduction of 126 points (70%) |
| Status | Open |

---

## Rank 3 — Hole position out of tolerance

| | |
|---|---|
| Component | Motor Mount Bracket |
| Risk Band | HIGH |
| RPN | 175 (S=7 × O=5 × D=5) |
| Failure Effect | Motor misalignment → vibration → fatigue |
| Potential Cause | Fixture wear; CNC program error |
| Recommended Action | Tighten AQL from 1.0 to 0.4 for hole position; add SPC on CNC fixture |
| Owner | QE-Torres |
| Due Date | 2026-06-26 |
| Revised RPN | 63 — reduction of 112 points (64%) |
| Status | In Progress |

---

## Rank 4 — Intermittent connection

| | |
|---|---|
| Component | Wiring Harness |
| Risk Band | HIGH |
| RPN | 160 (S=8 × O=5 × D=4) |
| Failure Effect | Random power loss → flight instability |
| Potential Cause | Vibration-induced fretting; poor crimp quality |
| Recommended Action | Add crimp pull-test to receiving inspection; specify vibration-resistant crimp termination |
| Owner | QE-Osei |
| Due Date | 2026-07-05 |
| Revised RPN | 48 — reduction of 112 points (70%) |
| Status | In Progress |

---

## Rank 5 — Loose contact

| | |
|---|---|
| Component | Battery Connector |
| Risk Band | HIGH |
| RPN | 160 (S=8 × O=4 × D=5) |
| Failure Effect | Intermittent power → erratic flight behavior |
| Potential Cause | Worn contact spring; incorrect mating cycle count exceeded |
| Recommended Action | Add mating cycle tracker to battery swap log; replace connectors at spec limit |
| Owner | QE-Patel |
| Due Date | 2026-06-26 |
| Revised RPN | 72 — reduction of 88 points (55%) |
| Status | Open |

---

## Rank 6 — Delamination

| | |
|---|---|
| Component | Propeller |
| Risk Band | HIGH |
| RPN | 160 (S=8 × O=4 × D=5) |
| Failure Effect | Loss of aerodynamic profile → thrust asymmetry |
| Potential Cause | CFRP layup defect; moisture ingress during storage |
| Recommended Action | Add C-scan to receiving AQL plan for CFRP propellers; improve storage spec |
| Owner | QE-Osei |
| Due Date | 2026-07-05 |
| Revised RPN | 48 — reduction of 112 points (70%) |
| Status | Open |

---

## Rank 7 — Firmware mismatch

| | |
|---|---|
| Component | Electronic Speed Controller |
| Risk Band | HIGH |
| RPN | 160 (S=8 × O=5 × D=4) |
| Failure Effect | Motor runs at wrong speed profile → unstable flight |
| Potential Cause | Firmware version not validated against motor/FC combination |
| Recommended Action | Lock firmware version in build traveler; add version check to EOL script |
| Owner | QE-Osei |
| Due Date | 2026-06-19 |
| Revised RPN | 32 — reduction of 128 points (80%) |
| Status | In Progress |

---

## Rank 8 — Connector not fully seated

| | |
|---|---|
| Component | Wiring Harness |
| Risk Band | HIGH |
| RPN | 160 (S=8 × O=5 × D=4) |
| Failure Effect | Intermittent power/signal → erratic motor behavior |
| Potential Cause | Assembly error; connector design requires high insertion force |
| Recommended Action | Add positive-lock connectors; add seating force verification to work instruction |
| Owner | QE-Torres |
| Due Date | 2026-06-19 |
| Revised RPN | 48 — reduction of 112 points (70%) |
| Status | In Progress |

---

## Rank 9 — Thermal shutdown

| | |
|---|---|
| Component | Electronic Speed Controller |
| Risk Band | MODERATE |
| RPN | 144 (S=9 × O=4 × D=4) |
| Failure Effect | Mid-flight power cutoff → crash |
| Potential Cause | Inadequate heatsinking; ambient temperature exceeded spec |
| Recommended Action | Add 10°C thermal margin to ESC mounting design; validate in thermal chamber |
| Owner | QE-Torres |
| Due Date | 2026-07-05 |
| Revised RPN | 54 — reduction of 90 points (62%) |
| Status | In Progress |

---

## Rank 10 — Solder joint failure

| | |
|---|---|
| Component | Electronic Speed Controller |
| Risk Band | MODERATE |
| RPN | 140 (S=7 × O=4 × D=5) |
| Failure Effect | Intermittent / complete power loss |
| Potential Cause | Poor wetting; thermal fatigue from power cycling |
| Recommended Action | Increase x-ray sample rate to 20%; add thermal cycle screen |
| Owner | QE-Nguyen |
| Due Date | 2026-06-26 |
| Revised RPN | 63 — reduction of 77 points (55%) |
| Status | Open |

---
