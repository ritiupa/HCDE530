"""
cross_session.py
----------------
Aggregate per-session reports into study-level highlights,
summary, and recurring friction patterns across participants.
"""

from __future__ import annotations

import os
from collections import defaultdict

import requests
from dotenv import load_dotenv

load_dotenv()

SEVERITY_RANK = {"Critical": 3, "Major": 2, "Minor": 1}


def aggregate_patterns(session_reports: list[dict]) -> list[dict]:
    """Find friction types that recur across multiple participant sessions."""
    by_type: dict[str, dict] = defaultdict(
        lambda: {
            "session_ids": set(),
            "total_occurrences": 0,
            "max_severity": "Minor",
            "heuristics": set(),
            "sample_quotes": [],
            "titles": [],
        }
    )

    for report in session_reports:
        sid = report["session_id"]
        for finding in report.get("findings", []):
            ftype = finding.get("friction_type", "general")
            bucket = by_type[ftype]
            bucket["session_ids"].add(sid)
            bucket["total_occurrences"] += finding.get("occurrence_count", 0)
            sev = finding.get("severity", "Minor")
            if SEVERITY_RANK.get(sev, 0) > SEVERITY_RANK.get(bucket["max_severity"], 0):
                bucket["max_severity"] = sev
            if finding.get("heuristic"):
                bucket["heuristics"].add(finding["heuristic"])
            bucket["sample_quotes"].extend(finding.get("evidence", [])[:2])
            if finding.get("title"):
                bucket["titles"].append(finding["title"])

    patterns = []
    for ftype, data in by_type.items():
        patterns.append({
            "friction_type": ftype,
            "title": data["titles"][0] if data["titles"] else f"{ftype.title()} friction",
            "sessions_affected": len(data["session_ids"]),
            "session_ids": sorted(data["session_ids"]),
            "total_occurrences": data["total_occurrences"],
            "severity": data["max_severity"],
            "heuristic": next(iter(data["heuristics"]), "") if data["heuristics"] else "",
            "sample_quotes": data["sample_quotes"][:4],
            "recurring": len(data["session_ids"]) > 1,
        })

    patterns.sort(key=lambda p: (-p["sessions_affected"], -p["total_occurrences"]))
    return patterns


def build_highlights(session_reports: list[dict], limit: int = 6) -> list[dict]:
    """Surface the strongest findings across all sessions for the study overview."""
    highlights = []
    for report in session_reports:
        sid = report["session_id"]
        participant = report.get("participant_note") or ""
        for finding in report.get("findings", []):
            highlights.append({
                "session_id": sid,
                "participant_note": participant,
                "title": finding.get("title", ""),
                "severity": finding.get("severity", "Minor"),
                "friction_type": finding.get("friction_type", "general"),
                "description": finding.get("description", ""),
                "heuristic": finding.get("heuristic", ""),
                "occurrence_count": finding.get("occurrence_count", 0),
                "evidence": finding.get("evidence", [])[:2],
                "score": (
                    SEVERITY_RANK.get(finding.get("severity", "Minor"), 0) * 10
                    + finding.get("occurrence_count", 0)
                ),
            })

    highlights.sort(key=lambda h: -h["score"])
    return highlights[:limit]


def _rule_based_summary(
    study_context: str,
    session_reports: list[dict],
    patterns: list[dict],
) -> str:
    n = len(session_reports)
    total_friction = sum(r.get("friction_segments", 0) for r in session_reports)
    recurring = [p for p in patterns if p["recurring"]]

    if not patterns:
        return (
            f"Across {n} participant session(s)"
            + (f" testing {study_context}" if study_context else "")
            + ", no significant friction patterns were detected."
        )

    lead = patterns[0]
    parts = [
        f"Across {n} participant session(s)",
        f"testing {study_context}" if study_context else "",
        f", LENS detected {total_friction} friction moment(s) total.",
    ]
    summary = " ".join(p for p in parts if p).replace("  ", " ")

    if lead["sessions_affected"] == n:
        summary += (
            f" All participants showed {lead['friction_type']} friction "
            f"({lead['total_occurrences']} occurrence(s)) — a consistent study-wide pattern."
        )
    elif recurring:
        summary += (
            f" {len(recurring)} friction type(s) recurred across multiple participants; "
            f"the most common was {lead['friction_type']} "
            f"({lead['sessions_affected']}/{n} sessions)."
        )
    else:
        summary += (
            f" Friction varied by participant; the most frequent type was "
            f"{lead['friction_type']} in session {lead['session_ids'][0]}."
        )

    return summary


def _mistral_study_summary(
    study_context: str,
    session_reports: list[dict],
    patterns: list[dict],
) -> str | None:
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key or not patterns:
        return None

    session_lines = []
    for r in session_reports:
        note = f" ({r['participant_note']})" if r.get("participant_note") else ""
        session_lines.append(
            f"- {r['session_id']}{note}: {r.get('friction_segments', 0)} friction moments, "
            f"{len(r.get('findings', []))} finding(s)"
        )

    pattern_lines = []
    for p in patterns[:5]:
        pattern_lines.append(
            f"- {p['friction_type']}: {p['sessions_affected']} session(s), "
            f"{p['total_occurrences']} occurrence(s), severity {p['severity']}"
        )

    prompt = f"""You are summarizing a multi-participant usability study for a research readout.

Study context: {study_context or 'Not specified'}

Sessions:
{chr(10).join(session_lines)}

Cross-session patterns:
{chr(10).join(pattern_lines)}

Write a 2-3 sentence executive summary highlighting what recurred across participants and the top design implication. Be specific and concise."""

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"inputs": prompt, "parameters": {"max_new_tokens": 250, "temperature": 0.3}},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        raw = (
            result[0]["generated_text"]
            if isinstance(result, list)
            else result.get("generated_text", "")
        )
        return raw.strip() if raw else None
    except Exception as exc:
        print(f"Cross-session Mistral summary failed: {exc}")
        return None


def synthesize_study(
    study_context: str,
    session_reports: list[dict],
) -> dict:
    """
    Build study-level overview from individual session reports.

    Returns dict with summary, highlights, patterns, and session roll-up stats.
    """
    patterns = aggregate_patterns(session_reports)
    highlights = build_highlights(session_reports)
    summary = _mistral_study_summary(study_context, session_reports, patterns)
    if not summary:
        summary = _rule_based_summary(study_context, session_reports, patterns)

    recurring_patterns = [p for p in patterns if p["recurring"]]
    total_friction = sum(r.get("friction_segments", 0) for r in session_reports)
    critical_sessions = [
        r["session_id"]
        for r in session_reports
        if any(f.get("severity") == "Critical" for f in r.get("findings", []))
    ]

    return {
        "study_context": study_context,
        "summary": summary,
        "highlights": highlights,
        "patterns": patterns,
        "recurring_patterns": recurring_patterns,
        "session_count": len(session_reports),
        "total_friction_moments": total_friction,
        "sessions_with_critical": critical_sessions,
        "dominant_pattern": patterns[0] if patterns else None,
    }
