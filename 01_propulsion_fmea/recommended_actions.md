# FMEA Recommended Actions

*35 total actions — Drone Propulsion FMEA Rev A — 2026-06-04*

## Actions by Owner

### QE-Brooks

| ID | Component | Failure Mode | Action | Due Date | Status |
|----|-----------|-------------|--------|----------|--------|
| 5 | Motor | Incorrect motor installed | Implement barcode scan verification at motor installation station | 2026-06-14 | Complete |
| 10 | Electronic Speed Controller | Incorrect calibration | Add mandatory calibration step with pass/fail criteria to build traveler | 2026-06-11 | Complete |
| 14 | Propeller | Loose attachment | Use torque-indicating fasteners; add torque verification to build record | 2026-06-11 | Complete |
| 19 | Motor Mount Bracket | Fastener interface wear | Specify thread insert (Helicoil) for high-cycle fastener interfaces | 2026-07-04 | Open |
| 24 | Wiring Harness | Insulation damage | Add insulation damage to receiving inspection AQL; improve packaging spec | 2026-06-25 | Open |
| 29 | Battery Connector | Reverse polarity risk | Replace with asymmetric keyed connector to physically prevent reverse polarity | 2026-06-11 | Complete |
| 34 | Thermal Interface Material | Dry-out / delamination over thermal cycles | Upgrade to phase-change TIM; add thermal cycle qualification test | 2026-07-04 | Open |

### QE-Nguyen

| ID | Component | Failure Mode | Action | Due Date | Status |
|----|-----------|-------------|--------|----------|--------|
| 3 | Motor | Winding insulation failure | Require 100% hi-pot test at supplier; add thermal shock screen | 2026-06-18 | In Progress |
| 9 | Electronic Speed Controller | Solder joint failure | Increase x-ray sample rate to 20%; add thermal cycle screen | 2026-06-25 | Open |
| 15 | Propeller | Surface damage | Add foam-lined storage trays; inspect immediately before installation | 2026-06-18 | Open |
| 18 | Motor Mount Bracket | Flatness failure | Add stress-relief annealing step to manufacturing router | 2026-06-25 | Complete |
| 23 | Wiring Harness | Incorrect pinout | Add polarized connector shrouds; implement spin-direction check in EOL software | 2026-06-14 | Complete |
| 28 | Battery Connector | Thermal damage | Uprate connector to next ampacity class; add thermal fuse in line | 2026-06-18 | In Progress |
| 33 | Thermal Interface Material | Incorrect thickness applied | Add shim template for TIM application; add thickness check with feeler gauge | 2026-06-18 | Open |

### QE-Osei

| ID | Component | Failure Mode | Action | Due Date | Status |
|----|-----------|-------------|--------|----------|--------|
| 6 | Electronic Speed Controller | Firmware mismatch | Lock firmware version in build traveler; add version check to EOL script | 2026-06-18 | In Progress |
| 12 | Propeller | Delamination | Add C-scan to receiving AQL plan for CFRP propellers; improve storage spec | 2026-07-04 | Open |
| 20 | Motor Mount Bracket | Incorrect material lot | Add 100% PMI scan at receiving inspection for motor mount brackets | 2026-06-18 | In Progress |
| 25 | Wiring Harness | Intermittent connection | Add crimp pull-test to receiving inspection; specify vibration-resistant crimp termination | 2026-07-04 | In Progress |
| 30 | Battery Connector | Contamination at contact surface | Add connector cap/plug until mating; add cleaning step to assembly SOP | 2026-06-25 | Open |
| 35 | Wiring Harness | Over-length wire routing | Add wire length to BOM; add wire-to-prop clearance check to EOL inspection | 2026-06-11 | In Progress |

### QE-Patel

| ID | Component | Failure Mode | Action | Due Date | Status |
|----|-----------|-------------|--------|----------|--------|
| 2 | Motor | Rotor imbalance | Implement dynamic balance check at motor receiving inspection | 2026-06-25 | In Progress |
| 8 | Electronic Speed Controller | Signal loss | Add locking connector on ESC signal line; vibration test at system level | 2026-06-25 | In Progress |
| 13 | Propeller | Incorrect pitch installed | Add pitch laser-etch marking; implement scan-to-verify at assembly | 2026-06-14 | Complete |
| 17 | Motor Mount Bracket | Crack at mounting feature | Add stress-relief radius to design; specify 7075-T6 only in BOM | 2026-06-18 | In Progress |
| 22 | Wiring Harness | Wire chafing | Add grommets/abrasion sleeves at all frame contact points; add to inspection checklist | 2026-06-25 | Open |
| 27 | Battery Connector | Loose contact | Add mating cycle tracker to battery swap log; replace connectors at spec limit | 2026-06-25 | Open |
| 32 | Fasteners | Wrong fastener grade installed | Implement kitting by job traveler; add grade stamp requirement to fastener spec | 2026-06-25 | Open |

### QE-Torres

| ID | Component | Failure Mode | Action | Due Date | Status |
|----|-----------|-------------|--------|----------|--------|
| 1 | Motor | Bearing seizure | Add bearing inspection step at motor install; specify grease type in BOM | 2026-07-04 | Open |
| 4 | Motor | Motor overheating | Add thermal derating curve to motor spec; test at max load | 2026-07-19 | Open |
| 7 | Electronic Speed Controller | Thermal shutdown | Add 10°C thermal margin to ESC mounting design; validate in thermal chamber | 2026-07-04 | In Progress |
| 11 | Propeller | Crack | Add dye-penetrant inspection to receiving; torque limiter on installation tool | 2026-06-18 | In Progress |
| 16 | Motor Mount Bracket | Hole position out of tolerance | Tighten AQL from 1.0 to 0.4 for hole position; add SPC on CNC fixture | 2026-06-25 | In Progress |
| 21 | Wiring Harness | Connector not fully seated | Add positive-lock connectors; add seating force verification to work instruction | 2026-06-18 | In Progress |
| 26 | Battery Connector | Voltage drop | Add contact resistance measurement to receiving AQL | 2026-06-18 | In Progress |
| 31 | Fasteners | Under-torque on critical joint | Add digital torque tool with data logging; flag out-of-spec torques in real time | 2026-06-18 | In Progress |


## Summary

- Total actions: **35**
- Complete: **7**
- In Progress: **15**
- Open: **13**
