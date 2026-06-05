"""
Conversational queries over LENS findings — answers from session/report data, not model memory.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from models import Report, Session

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _build_context(report: Report, sessions: list[Session]) -> str:
    """Compact context for Mistral or rule-based answers."""
    lines = [
        f"Study: {report.study_context}",
        f"Executive summary: {report.executive_summary}",
        "",
        "Clusters:",
    ]
    for c in report.clusters:
        lines.append(
            f"- {c.cluster_id} [{c.severity.value}] {c.title}: {c.evidence_summary} "
            f"(confidence={c.evidence_confidence.value}, participants={c.participant_ids})"
        )
    lines.append("")
    lines.append("Sessions:")
    for s in sessions:
        lines.append(
            f"- {s.participant_id}: inputs=[{s.capabilities.summary()}], "
            f"confidence={s.overall_confidence.value}, friction_events={len(s.friction_moments)}"
        )
    return "\n".join(lines)


def _rule_based_answer(query: str, report: Report, sessions: list[Session]) -> str:
    q = query.lower()

    if "text-only" in q or "missed" in q or "transcript" in q:
        return report.text_only_comparison

    if "heuristic" in q or "violation" in q:
        counts: dict[str, int] = {}
        for c in report.clusters:
            counts[c.heuristic] = counts.get(c.heuristic, 0) + 1
        if not counts:
            return "No heuristic violations recorded."
        top = max(counts, key=counts.get)
        return f"Most frequent heuristic theme: {top} ({counts[top]} cluster(s))."

    if "ellipse" in q or "reference" in q or "page" in q:
        hits = []
        for s in sessions:
            for e in s.timeline:
                loc = (e.ui_location or "").lower()
                if "ellipse" in q and "ellipse" in loc:
                    hits.append(f"{s.participant_id} @ {e.timestamp}: {e.transcript_segment}")
                elif "reference" in q and "reference" in loc:
                    hits.append(f"{s.participant_id} @ {e.timestamp}: {loc}")
        return "\n".join(hits[:8]) if hits else "No matching UI location in analyzed sessions."

    if "frustration" in q and "confusion" in q and "simultaneous" in q:
        hits = []
        for s in sessions:
            for e in s.friction_moments:
                if e.multi_modal_convergence:
                    v = e.vocal_emotion
                    f = e.facial_expression
                    if v and f and v.frustration >= 0.5 and f.confusion >= 0.5:
                        hits.append(
                            f"{s.participant_id} {e.timestamp}: vocal frustration + facial confusion"
                        )
        return "\n".join(hits) if hits else "No moments with both frustration and confusion flagged as convergent."

    if "hmw" in q or "how might we" in q:
        return "\n".join(f"- {c.hmw_statement}" for c in report.clusters[:5])

    if "confidence" in q:
        return "\n".join(
            f"{x['participant_id']}: {x['overall_confidence']} ({x['capabilities']})"
            for x in report.sessions_summary
        )

    return (
        "Try asking about: text-only gaps, heuristics, ellipse/reference page moments, "
        "simultaneous frustration+confusion, HMW statements, or per-session confidence."
    )


def _mistral_answer(query: str, context: str) -> str | None:
    from report_generator import _mistral_generate

    prompt = f"""<s>[INST] Answer using ONLY this LENS analysis data. If data is missing, say so.

{context}

Question: {query} [/INST]"""
    return _mistral_generate(prompt, max_tokens=500)


def answer_query(
    query: str,
    report: Report,
    sessions: list[Session],
    use_mistral: bool = True,
) -> dict[str, Any]:
    """
    Return answer text plus metadata about how it was produced.
    """
    context = _build_context(report, sessions)
    source = "rules"
    text = _rule_based_answer(query, report, sessions)

    if use_mistral and os.getenv("HUGGINGFACE_API_KEY"):
        mistral = _mistral_answer(query, context)
        if mistral:
            text = mistral
            source = "mistral"

    return {
        "query": query,
        "answer": text,
        "source": source,
        "confidence": "medium" if source == "mistral" else "high",
    }
