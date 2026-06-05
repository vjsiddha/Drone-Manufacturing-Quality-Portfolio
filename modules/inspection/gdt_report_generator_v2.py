"""
report_generator.py — GD&T Inspection System
Clean, professional markdown reports. No emoji. Clear hierarchy.
"""

import pandas as pd
from datetime import date


def _divider():
    return "\n---\n"


def _meta_table(rows: list[tuple]) -> str:
    lines = ["| | |", "|---|---|"]
    for k, v in rows:
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def generate_markdown_report(engine, results: list, output_path: str) -> str:
    stats   = engine.summary_stats(results)
    df      = engine.results_to_dataframe(results)
    today   = date.today().isoformat()
    reqs    = engine.requirements

    # ── Header ────────────────────────────────────────────────────────────────
    lines = [
        f"# Inspection Report",
        f"## {engine.part_number} — {engine.part_name}",
        f"",
        _meta_table([
            ("Part Number",    engine.part_number),
            ("Part Name",      engine.part_name),
            ("Revision",       engine.revision),
            ("Material",       reqs.get("material", "—")),
            ("Supplier",       engine.supplier),
            ("Criticality",    reqs.get("criticality", "—")),
            ("Report Date",    today),
            ("Lots Inspected", ", ".join(sorted(stats["lots_inspected"]))),
            ("Parts Inspected",stats["total_parts"]),
        ]),
        _divider(),
    ]

    # ── Results summary ───────────────────────────────────────────────────────
    pass_pct = stats["part_fpy_pct"]
    lines += [
        "## Results Summary",
        "",
        _meta_table([
            ("Parts Passed",        f"{stats['passed']} / {stats['total_parts']} ({pass_pct}%)"),
            ("Parts Failed",        stats["failed"]),
            ("MRB Review Required", stats["mrb_review"]),
            ("Feature-Level FPY",   f"{stats['feature_fpy_pct']}%"),
            ("Most Failed Feature",  stats["worst_feature"]),
        ]),
        "",
    ]

    # Overall verdict banner
    if stats["failed"] > 0:
        lines += [
            "> **LOT VERDICT: FAIL** — One or more parts contain critical feature failures.",
            "> Engineering disposition required before material can be released.",
            "",
        ]
    elif stats["mrb_review"] > 0:
        lines += [
            "> **LOT VERDICT: MRB REVIEW** — No critical failures. Non-critical or borderline conditions require engineering review.",
            "",
        ]
    else:
        lines += [
            "> **LOT VERDICT: PASS** — All parts conform to engineering requirements.",
            "",
        ]

    lines.append(_divider())

    # ── Feature-level summary ─────────────────────────────────────────────────
    feat_summary = (
        df.groupby(["feature_id","feature_name","gdandt_type","criticality","tolerance"])
        .agg(
            total=("result","count"),
            passed=("result", lambda x: (x=="PASS").sum()),
            failed=("result", lambda x: (x=="FAIL").sum()),
            borderline=("result", lambda x: (x=="BORDERLINE").sum()),
            avg_dev=("deviation","mean"),
        )
        .round(4).reset_index()
    )
    feat_summary["fpy_pct"] = (feat_summary["passed"] / feat_summary["total"] * 100).round(1)
    feat_summary = feat_summary.sort_values("failed", ascending=False)

    lines += [
        "## Feature Performance",
        "",
        "| Feature | GD&T Type | Criticality | Tolerance | Pass | Fail | Borderline | FPY | Avg Dev |",
        "|---------|-----------|-------------|-----------|------|------|------------|-----|---------|",
    ]
    for _, row in feat_summary.iterrows():
        status = "FAIL" if row["failed"] > 0 else ("BORDERLINE" if row["borderline"] > 0 else "PASS")
        lines.append(
            f"| {row['feature_name']} | {row['gdandt_type']} | {row['criticality']} "
            f"| {row['tolerance']} mm | {row['passed']} | {row['failed']} "
            f"| {row['borderline']} | {row['fpy_pct']}% | {row['avg_dev']} mm |"
        )

    lines.append(_divider())

    # ── Part-level results ────────────────────────────────────────────────────
    lines += [
        "## Part-Level Results",
        "",
        "| Serial | Lot | Disposition | Critical Fails | Non-Critical | Borderline |",
        "|--------|-----|-------------|----------------|--------------|------------|",
    ]
    for part in results:
        lines.append(
            f"| {part.part_serial_number} | {part.lot_number} | {part.disposition} "
            f"| {len(part.critical_failures)} | {len(part.non_critical_failures)} "
            f"| {len(part.borderline_items)} |"
        )

    lines.append(_divider())

    # ── Failed feature detail ─────────────────────────────────────────────────
    failed_df = df[df["result"] == "FAIL"].copy()
    lines += ["## Failed Feature Detail", ""]

    if failed_df.empty:
        lines.append("No failures detected.")
    else:
        lines += [
            "| Serial | Lot | Feature | Type | Measured | Nominal | Tolerance | Deviation | Margin |",
            "|--------|-----|---------|------|----------|---------|-----------|-----------|--------|",
        ]
        for _, row in failed_df.iterrows():
            nom = f"{row['nominal_value']} mm" if pd.notna(row["nominal_value"]) else "—"
            lines.append(
                f"| {row['part_serial_number']} | {row['lot_number']} | {row['feature_name']} "
                f"| {row['gdandt_type']} | {row['measured_value']} mm | {nom} "
                f"| ±{row['tolerance']} mm | {row['deviation']} mm | {row['margin']} mm |"
            )

    lines.append(_divider())

    # ── Datums and requirements reference ─────────────────────────────────────
    lines += [
        "## Engineering Requirements Reference",
        "",
        "**Datum Structure**",
        "",
    ]
    for datum, desc in reqs.get("datums", {}).items():
        lines.append(f"- Datum {datum}: {desc}")

    lines += [
        "",
        "**Feature Requirements**",
        "",
        "| Feature ID | GD&T Type | Tolerance | Datum | Criticality |",
        "|------------|-----------|-----------|-------|-------------|",
    ]
    for feat in reqs.get("features", []):
        lines.append(
            f"| {feat['feature_id']} | {feat['gdandt_type']} "
            f"| {feat['tolerance']} {feat.get('measurement_unit','mm')} "
            f"| {feat.get('datum_reference','—')} | {feat.get('criticality','—')} |"
        )

    lines += [
        _divider(),
        f"*Report generated {today} — Drone Manufacturing Quality Engineering*  ",
        f"*GD&T Inspection System v1.0 — Part {engine.part_number} Rev {engine.revision}*",
    ]

    content = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(content)
    return content


def generate_csv_report(engine, results: list, output_path: str) -> pd.DataFrame:
    df = engine.results_to_dataframe(results)
    df.to_csv(output_path, index=False)
    return df