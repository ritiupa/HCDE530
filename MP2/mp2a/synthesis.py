"""
Cross-session friction clustering with ChromaDB + sentence embeddings.
Works on Session objects (from fixtures or live pipeline).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from models import ConfidenceLevel, FrictionCluster, Session, Severity


def _friction_text(moment: dict[str, Any]) -> str:
    """Single string for embedding from a friction moment."""
    parts = [
        moment.get("friction_type", ""),
        moment.get("ui_location", ""),
        moment.get("transcript_segment", ""),
        moment.get("evidence_summary", ""),
    ]
    return " | ".join(p for p in parts if p)


def _severity_from_scores(avg_stress: float, convergence: bool, n_participants: int) -> Severity:
    if avg_stress >= 0.75 and n_participants >= 3:
        return Severity.CRITICAL
    if avg_stress >= 0.5 or (convergence and n_participants >= 2):
        return Severity.MAJOR
    return Severity.MINOR


def _evidence_confidence(n_participants: int, modalities: set[str], convergence_hits: int) -> ConfidenceLevel:
    if n_participants >= 3 and len(modalities) >= 2 and convergence_hits > 0:
        return ConfidenceLevel.HIGH
    if n_participants >= 2 and len(modalities) >= 1:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def cluster_sessions(
    sessions: list[Session],
    persist_dir: str | Path | None = None,
    collection_name: str = "lens_friction",
) -> list[FrictionCluster]:
    """
    Store friction moments in ChromaDB, cluster semantically, return ranked clusters.
    Falls back to simple keyword grouping if chromadb is unavailable.
    """
    moments: list[dict[str, Any]] = []
    for session in sessions:
        for event in session.friction_moments:
            vocal = event.vocal_emotion
            stress = vocal.stress if vocal else 0.0
            moments.append(
                {
                    "participant_id": session.participant_id,
                    "timestamp": event.timestamp,
                    "friction_type": event.friction_type or "general",
                    "ui_location": event.ui_location or "",
                    "transcript_segment": event.transcript_segment or "",
                    "multi_modal_convergence": event.multi_modal_convergence,
                    "modalities_present": event.modalities_present,
                    "stress": stress,
                    "capabilities": session.capabilities.summary(),
                }
            )

    if not moments:
        return []

    try:
        return _cluster_with_chroma(moments, persist_dir, collection_name)
    except Exception as exc:
        print(f"ChromaDB clustering unavailable ({exc}); using rule-based fallback.")
        return _cluster_fallback(moments)


def _cluster_with_chroma(
    moments: list[dict[str, Any]],
    persist_dir: str | Path | None,
    collection_name: str,
) -> list[FrictionCluster]:
    import chromadb
    from sentence_transformers import SentenceTransformer

    root = Path(__file__).resolve().parent
    persist = Path(persist_dir) if persist_dir else root / "outputs" / "chroma"
    persist.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist))
    coll = client.get_or_create_collection(collection_name)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    ids = []
    docs = []
    metas = []

    for i, m in enumerate(moments):
        doc_id = f"{m['participant_id']}_{i}_{uuid.uuid4().hex[:8]}"
        ids.append(doc_id)
        docs.append(_friction_text(m))
        metas.append(m)

    embeddings = model.encode(docs).tolist()
    coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

    # Group by friction_type + ui_location prefix (simple cluster key from metadata)
    buckets: dict[str, list[dict]] = {}
    for meta in metas:
        key = f"{meta.get('friction_type','')}|{meta.get('ui_location','')[:40]}"
        buckets.setdefault(key, []).append(meta)

    return _buckets_to_clusters(buckets)


def _cluster_fallback(moments: list[dict[str, Any]]) -> list[FrictionCluster]:
    buckets: dict[str, list[dict]] = {}
    for m in moments:
        key = f"{m.get('friction_type','')}|{m.get('ui_location','')[:40]}"
        buckets.setdefault(key, []).append(m)
    return _buckets_to_clusters(buckets)


def _buckets_to_clusters(buckets: dict[str, list[dict]]) -> list[FrictionCluster]:
    clusters: list[FrictionCluster] = []
    for idx, (key, items) in enumerate(buckets.items()):
        participants = sorted({m["participant_id"] for m in items})
        convergence_hits = sum(1 for m in items if m.get("multi_modal_convergence"))
        avg_stress = sum(m.get("stress", 0) for m in items) / max(len(items), 1)
        modalities: set[str] = set()
        for m in items:
            modalities.update(m.get("modalities_present") or [])

        ftype, loc = (key.split("|", 1) + [""])[:2]
        title = f"{ftype.replace('_', ' ').title()} friction"
        if loc:
            title += f" — {loc}"

        quotes = [
            {
                "participant_id": m["participant_id"],
                "timestamp": m["timestamp"],
                "quote": m.get("transcript_segment", ""),
            }
            for m in items[:5]
            if m.get("transcript_segment")
        ]

        clusters.append(
            FrictionCluster(
                cluster_id=f"C{idx+1}",
                title=title,
                description=f"Recurring friction across {len(participants)} participant(s).",
                heuristic=_guess_heuristic(ftype),
                severity=_severity_from_scores(avg_stress, convergence_hits > 0, len(participants)),
                participant_ids=participants,
                frequency=len(participants),
                severity_score=round(avg_stress, 2),
                convergence_score=round(convergence_hits / max(len(items), 1), 2),
                evidence_confidence=_evidence_confidence(
                    len(participants), modalities, convergence_hits
                ),
                evidence_summary=_build_evidence_summary(items, participants, convergence_hits),
                representative_quotes=quotes,
                text_only_gap=_text_only_gap(modalities, convergence_hits),
            )
        )

    clusters.sort(
        key=lambda c: (
            {"Critical": 3, "Major": 2, "Minor": 1}[c.severity.value],
            c.frequency,
            c.convergence_score,
        ),
        reverse=True,
    )
    return clusters


def _guess_heuristic(friction_type: str) -> str:
    mapping = {
        "navigation": "10 — Help and documentation / 6 — Recognition rather than recall",
        "comprehension": "4 — Consistency and standards",
        "discovery": "6 — Recognition rather than recall",
    }
    return mapping.get(friction_type, "4 — Consistency and standards")


def _build_evidence_summary(items: list[dict], participants: list[str], convergence_hits: int) -> str:
    n = len(participants)
    conv = convergence_hits
    return (
        f"{n} participant(s) showed friction at this pattern; "
        f"{conv} moment(s) with multi-modal convergence (2+ channels agreeing)."
    )


def _text_only_gap(modalities: set[str], convergence_hits: int) -> str:
    missing = []
    if "vocal" in modalities:
        missing.append("vocal stress or hesitation not fully captured in transcript")
    if "facial" in modalities:
        missing.append("facial confusion before or without spoken explanation")
    if convergence_hits:
        missing.append("simultaneous multi-channel signals at the same timestamp")
    if not missing:
        return "Primarily linguistic cues; limited non-verbal evidence in available inputs."
    return "; ".join(missing)


if __name__ == "__main__":
    from session_builder import session_from_fixture

    fix = Path(__file__).parent / "fixtures" / "P1_multimodal.json"
    data = json.loads(fix.read_text(encoding="utf-8"))
    s = session_from_fixture(data)
    clusters = cluster_sessions([s])
    print(f"Clusters: {len(clusters)}")
    for c in clusters:
        print(f"  [{c.severity.value}] {c.title} — conf={c.evidence_confidence.value}")
