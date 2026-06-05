"""
report_generator.py
-------------------
Takes the enriched segment list from language_analysis.py and generates
a structured research findings report.

The report structure is determined by what was actually found -- sessions
dominated by navigation friction produce a different structure than sessions
with evenly distributed issues. This is the generative aspect of LENS.

Outputs a report as a Python dict that app.py renders in Streamlit,
and also saves it as a markdown file.
"""

import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def cluster_by_type(segments: list[dict]) -> dict:
    """Group friction segments by friction type."""
    clusters = defaultdict(list)
    for seg in segments:
        if seg.get("friction_flag"):
            ftype = seg.get("friction_type", "general")
            clusters[ftype].append(seg)
    return dict(clusters)


def generate_finding(cluster_type: str, segments: list[dict], session_id: str) -> dict:
    """
    Generate one structured finding from a cluster of friction segments.
    Calls Mistral to write the finding title, description, and recommendation.
    Falls back to a template if the API call fails.
    """
    api_key = os.getenv("HUGGINGFACE_API_KEY")

    quotes = [f'"{s["text"]}"' for s in segments[:5]]
    quotes_text = "\n".join(quotes)

    severities = [s.get("severity", "Minor") for s in segments]
    if "Critical" in severities:
        overall_severity = "Critical"
    elif "Major" in severities:
        overall_severity = "Major"
    else:
        overall_severity = "Minor"

    heuristic = segments[0].get("heuristic_mistral") or segments[0].get("heuristic", "")

    if api_key:
        prompt = f"""You are writing a usability research finding.
Friction type: {cluster_type}
Severity: {overall_severity}
Participant quotes showing friction:
{quotes_text}

Write a structured finding with exactly these fields:
Title: [short title, max 8 words]
Description: [one sentence describing the usability problem]
HMW: [How Might We reframe, one sentence starting with "How might we"]
Recommendation: [one specific design recommendation]"""

        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": 300, "temperature": 0.4},
                },
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            raw = (
                result[0]["generated_text"]
                if isinstance(result, list)
                else result.get("generated_text", "")
            )

            def extract_field(label, text):
                match = re.search(rf"{label}:\s*(.+?)(?=\n[A-Z]|\Z)", text, re.DOTALL)
                return match.group(1).strip() if match else ""

            return {
                "title": extract_field("Title", raw) or f"{cluster_type.title()} Friction",
                "description": extract_field("Description", raw),
                "hmw": extract_field("HMW", raw),
                "recommendation": extract_field("Recommendation", raw),
                "severity": overall_severity,
                "heuristic": heuristic,
                "evidence": quotes,
                "friction_type": cluster_type,
                "occurrence_count": len(segments),
                "timestamps": [s["start"] for s in segments],
            }

        except Exception as e:
            print(f"Mistral finding generation failed: {e}. Using template.")

    return {
        "title": f"{cluster_type.title()} Friction Detected",
        "description": (
            f"Participants showed {cluster_type} friction at {len(segments)} "
            f"points in session {session_id}."
        ),
        "hmw": f"How might we reduce {cluster_type} friction for users?",
        "recommendation": f"Review the {cluster_type} design pattern and test an alternative.",
        "severity": overall_severity,
        "heuristic": heuristic,
        "evidence": quotes,
        "friction_type": cluster_type,
        "occurrence_count": len(segments),
        "timestamps": [s["start"] for s in segments],
    }


def generate_report(
    segments: list[dict],
    session_id: str,
    context: str = "",
    participant_note: str = "",
    output_dir: str = "output",
) -> dict:
    """
    Generate the full structured report from analyzed segments.

    Parameters:
        segments   -- enriched segments from language_analysis.analyze()
        session_id -- label for this session e.g. "P1"
        context    -- brief description of what was being tested (optional)
        output_dir -- where to save the markdown report file

    Returns the full report as a dict.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    clusters = cluster_by_type(segments)
    sorted_clusters = sorted(clusters.items(), key=lambda x: -len(x[1]))

    print(f"Generating findings for {len(sorted_clusters)} friction cluster(s)...")

    findings = []
    for cluster_type, cluster_segments in sorted_clusters:
        findings.append(generate_finding(cluster_type, cluster_segments, session_id))

    total_friction = sum(1 for s in segments if s.get("friction_flag"))
    critical_count = sum(1 for f in findings if f["severity"] == "Critical")

    report = {
        "session_id": session_id,
        "context": context,
        "participant_note": participant_note,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_segments": len(segments),
        "friction_segments": total_friction,
        "findings": findings,
        "summary": (
            f"Session {session_id} produced {len(findings)} finding(s) "
            f"from {total_friction} friction moments. "
            f"{critical_count} finding(s) rated Critical."
        ),
    }

    md_path = output_dir / f"{session_id}_report.md"
    _save_markdown(report, md_path)
    print(f"Report saved to {md_path}")

    return report


def _save_markdown(report: dict, path: Path):
    """Write the report dict to a readable markdown file."""
    lines = [
        f"# LENS Report -- Session {report['session_id']}",
        f"**Generated:** {report['generated_at']}",
        f"**Context:** {report['context'] or 'Not specified'}",
    ]
    if report.get("participant_note"):
        lines.append(f"**Participant:** {report['participant_note']}")
    lines += [
        "",
        "## Summary",
        report["summary"],
        "",
        "## Findings",
        "",
    ]

    for i, finding in enumerate(report["findings"], 1):
        lines += [
            f"### Finding {i}: {finding['title']}",
            f"**Severity:** {finding['severity']}  ",
            f"**Heuristic:** {finding['heuristic']}  ",
            f"**Occurrences:** {finding['occurrence_count']}",
            "",
            f"**Description:** {finding['description']}",
            "",
            f"**HMW:** {finding['hmw']}",
            "",
            f"**Recommendation:** {finding['recommendation']}",
            "",
            "**Evidence:**",
        ]
        for quote in finding["evidence"]:
            lines.append(f"- {quote}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
