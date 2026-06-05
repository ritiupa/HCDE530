"""
Export LENS report to Markdown and PDF.
"""

from __future__ import annotations

from pathlib import Path

from models import Report


def report_to_markdown(report: Report) -> str:
    lines = [
        "# LENS Usability Synthesis Report",
        "",
        f"**Study:** {report.study_context}",
        "",
        "## Executive summary",
        "",
        report.executive_summary,
        "",
        f"*{report.report_structure_note}*",
        "",
        "## Sessions analyzed",
        "",
    ]
    for s in report.sessions_summary:
        lines.append(
            f"- **{s['participant_id']}**: {s['capabilities']} "
            f"(confidence: {s['overall_confidence']}, friction events: {s['friction_count']})"
        )
    lines.extend(["", "## Findings", ""])

    for c in report.clusters:
        lines.extend(
            [
                f"### {c.title} — **{c.severity.value}**",
                "",
                f"**Heuristic:** {c.heuristic}",
                "",
                f"**Evidence confidence:** {c.evidence_confidence.value}",
                "",
                c.description,
                "",
                f"**Evidence:** {c.evidence_summary}",
                "",
                "**Representative quotes:**",
                "",
            ]
        )
        for q in c.representative_quotes:
            lines.append(f"- {q.get('participant_id')} ({q.get('timestamp')}): \"{q.get('quote')}\"")
        lines.extend(
            [
                "",
                f"**HMW:** {c.hmw_statement}",
                "",
                f"**Recommendation:** {c.design_recommendation}",
                "",
                f"**Text-only gap:** {c.text_only_gap}",
                "",
                "---",
                "",
            ]
        )

    lines.extend(
        [
            "## What text-only AI would have missed",
            "",
            report.text_only_comparison,
            "",
        ]
    )
    return "\n".join(lines)


def save_markdown(report: Report, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_to_markdown(report), encoding="utf-8")
    return path


def save_pdf(report: Report, path: str | Path) -> Path:
    """Simple PDF via fpdf2 — ASCII-safe fallback for special chars."""
    from fpdf import FPDF

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    md = report_to_markdown(report)
    # fpdf core fonts are latin-1; replace common unicode dashes
    safe = md.replace("\u2014", "-").replace("\u2013", "-").encode("latin-1", errors="replace").decode(
        "latin-1"
    )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in safe.split("\n"):
        pdf.multi_cell(0, 5, line[:2000])
    pdf.output(str(path))
    return path
