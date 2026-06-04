# Top 10 FMEA Risk Items

*Ranked by RPN — Drone Propulsion System — Rev A — 2026-06-04*

---

## 🔴 Rank 1 — Bearing seizure

**Component:** Motor  
**RPN:** 225 (S=9 × O=5 × D=5)  
**Effect:** Complete loss of motor rotation → vehicle crash  
**Cause:** Insufficient lubrication / contamination during assembly  
**Recommended Action:** Add bearing inspection step at motor install; specify grease type in BOM  
**Owner:** QE-Torres | **Due:** 2026-07-04  
**Revised RPN:** 81 → reduction of 144 points (64%)

---

## 🔴 Rank 2 — Wire chafing

**Component:** Wiring Harness  
**RPN:** 180 (S=9 × O=4 × D=5)  
**Effect:** Short circuit → fire risk or power loss  
**Cause:** Inadequate routing protection in high-vibration zones  
**Recommended Action:** Add grommets/abrasion sleeves at all frame contact points; add to inspection checklist  
**Owner:** QE-Patel | **Due:** 2026-06-25  
**Revised RPN:** 54 → reduction of 126 points (70%)

---

## 🔴 Rank 3 — Hole position out of tolerance

**Component:** Motor Mount Bracket  
**RPN:** 175 (S=7 × O=5 × D=5)  
**Effect:** Motor misalignment → vibration → fatigue  
**Cause:** Fixture wear; CNC program error  
**Recommended Action:** Tighten AQL from 1.0 to 0.4 for hole position; add SPC on CNC fixture  
**Owner:** QE-Torres | **Due:** 2026-06-25  
**Revised RPN:** 63 → reduction of 112 points (64%)

---

## 🔴 Rank 4 — Firmware mismatch

**Component:** Electronic Speed Controller  
**RPN:** 160 (S=8 × O=5 × D=4)  
**Effect:** Motor runs at wrong speed profile → unstable flight  
**Cause:** Firmware version not validated against motor/FC combination  
**Recommended Action:** Lock firmware version in build traveler; add version check to EOL script  
**Owner:** QE-Osei | **Due:** 2026-06-18  
**Revised RPN:** 32 → reduction of 128 points (80%)

---

## 🔴 Rank 5 — Delamination

**Component:** Propeller  
**RPN:** 160 (S=8 × O=4 × D=5)  
**Effect:** Loss of aerodynamic profile → thrust asymmetry  
**Cause:** CFRP layup defect; moisture ingress during storage  
**Recommended Action:** Add C-scan to receiving AQL plan for CFRP propellers; improve storage spec  
**Owner:** QE-Osei | **Due:** 2026-07-04  
**Revised RPN:** 48 → reduction of 112 points (70%)

---

## 🔴 Rank 6 — Connector not fully seated

**Component:** Wiring Harness  
**RPN:** 160 (S=8 × O=5 × D=4)  
**Effect:** Intermittent power/signal → erratic motor behavior  
**Cause:** Assembly error; connector design requires high insertion force  
**Recommended Action:** Add positive-lock connectors; add seating force verification to work instruction  
**Owner:** QE-Torres | **Due:** 2026-06-18  
**Revised RPN:** 48 → reduction of 112 points (70%)

---

## 🔴 Rank 7 — Intermittent connection

**Component:** Wiring Harness  
**RPN:** 160 (S=8 × O=5 × D=4)  
**Effect:** Random power loss → flight instability  
**Cause:** Vibration-induced fretting; poor crimp quality  
**Recommended Action:** Add crimp pull-test to receiving inspection; specify vibration-resistant crimp termination  
**Owner:** QE-Osei | **Due:** 2026-07-04  
**Revised RPN:** 48 → reduction of 112 points (70%)

---

## 🔴 Rank 8 — Loose contact

**Component:** Battery Connector  
**RPN:** 160 (S=8 × O=4 × D=5)  
**Effect:** Intermittent power → erratic flight behavior  
**Cause:** Worn contact spring; incorrect mating cycle count exceeded  
**Recommended Action:** Add mating cycle tracker to battery swap log; replace connectors at spec limit  
**Owner:** QE-Patel | **Due:** 2026-06-25  
**Revised RPN:** 72 → reduction of 88 points (55%)

---

## 🟡 Rank 9 — Thermal shutdown

**Component:** Electronic Speed Controller  
**RPN:** 144 (S=9 × O=4 × D=4)  
**Effect:** Mid-flight power cutoff → crash  
**Cause:** Inadequate heatsinking; ambient temperature exceeded spec  
**Recommended Action:** Add 10°C thermal margin to ESC mounting design; validate in thermal chamber  
**Owner:** QE-Torres | **Due:** 2026-07-04  
**Revised RPN:** 54 → reduction of 90 points (62%)

---

## 🟡 Rank 10 — Solder joint failure

**Component:** Electronic Speed Controller  
**RPN:** 140 (S=7 × O=4 × D=5)  
**Effect:** Intermittent / complete power loss  
**Cause:** Poor wetting; thermal fatigue from power cycling  
**Recommended Action:** Increase x-ray sample rate to 20%; add thermal cycle screen  
**Owner:** QE-Nguyen | **Due:** 2026-06-25  
**Revised RPN:** 63 → reduction of 77 points (55%)

---

