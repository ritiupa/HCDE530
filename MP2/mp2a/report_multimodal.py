"""
Generative report assembly for multi-modal fixture pipeline.
Used by scripts/run_pipeline_fixture.py — not the live upload path in app.py.
"""

from __future__ import annotations

import json
import os
from typing import Any

from models import FrictionCluster, Report, Session, Severity

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _dominant_cluster(clusters: list[FrictionCluster]) -> bool:
    if len(clusters) < 2:
        return len(clusters) == 1
    return clusters[0].frequency >= 2 and clusters[0].frequency > clusters[1].frequency + 1


def _mistral_generate(prompt: str, max_tokens: int = 800) -> str | None:
    token = os.getenv("HUGGINGFACE_API_KEY")
    if not token:
        return None
    try:
        import requests

        url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": max_tokens, "return_full_text": False},
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        out = r.json()
        if isinstance(out, list) and out and "generated_text" in out[0]:
            return out[0]["generated_text"].strip()
        if isinstance(out, dict) and "generated_text" in out:
            return out["generated_text"].strip()
    except Exception as exc:
        print(f"Mistral API skipped: {exc}")
    return None


def _rule_based_hmw(cluster: FrictionCluster) -> str:
    return (
        f"How might we reduce {cluster.title.lower()} "
        f"on the p5.js reference site so researchers see fewer {cluster.heuristic.split('—')[0].strip()} violations?"
    )


def _rule_based_recommendation(cluster: FrictionCluster) -> str:
    return (
        f"Add clearer wayfinding and inline examples for '{cluster.title}' "
        f"so participants spend less time searching parameters."
    )


def enrich_cluster_with_mistral(cluster: FrictionCluster, study_context: str) -> FrictionCluster:
    prompt = f"""<s>[INST] You are a UX research assistant. Study: {study_context}

Friction cluster evidence:
{cluster.evidence_summary}
Quotes: {json.dumps(cluster.representative_quotes[:3])}
Heuristic hint: {cluster.heuristic}

Write JSON only:
{{"description": "...", "hmw_statement": "...", "design_recommendation": "..."}} [/INST]"""

    text = _mistral_generate(prompt, max_tokens=400)
    if text:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                cluster.description = data.get("description", cluster.description)
                cluster.hmw_statement = data.get("hmw_statement", "")
                cluster.design_recommendation = data.get("design_recommendation", "")
                return cluster
        except json.JSONDecodeError:
            pass

    cluster.hmw_statement = _rule_based_hmw(cluster)
    cluster.design_recommendation = _rule_based_recommendation(cluster)
    return cluster


def generate_multimodal_report(
    sessions: list[Session],
    clusters: list[FrictionCluster],
    study_context: str = "p5.js reference documentation (p5js.org/reference)",
    use_mistral: bool = True,
) -> Report:
    """Build Report from multi-modal Session objects; optionally enrich via Mistral."""
    if use_mistral:
        for i, c in enumerate(clusters):
            clusters[i] = enrich_cluster_with_mistral(c, study_context)

    for c in clusters:
        if not c.hmw_statement:
            c.hmw_statement = _rule_based_hmw(c)
        if not c.design_recommendation:
            c.design_recommendation = _rule_based_recommendation(c)

    dominant = _dominant_cluster(clusters)
    if dominant and clusters:
        lead = clusters[0]
        executive = (
            f"This study of {study_context} surfaced a dominant pattern: "
            f"{lead.title} ({lead.severity.value}), affecting {lead.frequency} participant(s). "
            f"Evidence confidence: {lead.evidence_confidence.value}. "
            f"{lead.evidence_summary}"
        )
        structure_note = "Report leads with the dominant cluster because it recurred across participants."
    elif clusters:
        executive = (
            f"Findings for {study_context} are distributed across {len(clusters)} themes "
            f"with no single dominant issue; sections are balanced by severity."
        )
        structure_note = "Balanced multi-section structure because friction patterns spread evenly."
    else:
        executive = "No friction clusters met threshold in the provided sessions."
        structure_note = "Minimal report — insufficient friction evidence in inputs."

    text_only_parts = [c.text_only_gap for c in clusters if c.text_only_gap]
    text_only_comparison = (
        "Compared to transcript-only AI synthesis, LENS retained: "
        + "; ".join(dict.fromkeys(text_only_parts))
        if text_only_parts
        else "Add video/audio sessions to populate multi-modal gap analysis."
    )

    sessions_summary = [
        {
            "participant_id": s.participant_id,
            "capabilities": s.capabilities.summary(),
            "overall_confidence": s.overall_confidence.value,
            "friction_count": len(s.friction_moments),
        }
        for s in sessions
    ]

    return Report(
        executive_summary=executive,
        study_context=study_context,
        clusters=clusters,
        text_only_comparison=text_only_comparison,
        sessions_summary=sessions_summary,
        report_structure_note=structure_note,
    )
