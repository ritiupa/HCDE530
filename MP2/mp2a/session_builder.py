"""
Build a Session object from partial modality outputs.
Convergence and confidence are computed here — not in downstream report code.
"""

from __future__ import annotations

from models import (
    ConfidenceLevel,
    FacialState,
    InputCapabilities,
    Session,
    SignalConfidence,
    TimelineEvent,
    VocalEmotion,
)

# Minimum channels required to claim multi-modal convergence
MIN_CHANNELS_FOR_CONVERGENCE = 2

# If vocal confusion/frustration or facial confusion/frustration exceed threshold → friction signal
FRICTION_THRESHOLD = 0.55


def _channel_friction_flags(
    vocal: VocalEmotion | None,
    facial: FacialState | None,
    language_friction: bool,
) -> tuple[bool, list[str]]:
    """Return (any_friction, list of channel names that contributed)."""
    channels: list[str] = []
    if vocal and (
        vocal.confusion >= FRICTION_THRESHOLD
        or vocal.frustration >= FRICTION_THRESHOLD
        or vocal.stress >= FRICTION_THRESHOLD
    ):
        channels.append("vocal")
    if facial and (
        facial.confusion >= FRICTION_THRESHOLD
        or facial.frustration >= FRICTION_THRESHOLD
    ):
        channels.append("facial")
    if language_friction:
        channels.append("language")
    return len(channels) > 0, channels


def _overall_confidence(capabilities: InputCapabilities, timeline: list[TimelineEvent]) -> ConfidenceLevel:
    n = capabilities.modalities_count()
    if n >= 3 and any(e.multi_modal_convergence for e in timeline):
        return ConfidenceLevel.HIGH
    if n >= 2:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def build_session(
    participant_id: str,
    study_context: str,
    capabilities: InputCapabilities,
    timeline_rows: list[dict],
    duration_seconds: float = 0.0,
) -> Session:
    """
    Merge aligned rows into a Session.

    Each row in timeline_rows may include keys:
      timestamp, timestamp_seconds, vocal_emotion (dict), facial_expression (dict),
      ui_location, transcript_segment, language_friction (bool), friction_type
    """
    timeline: list[TimelineEvent] = []

    for row in timeline_rows:
        vocal = None
        if row.get("vocal_emotion") and capabilities.has_audio:
            v = row["vocal_emotion"]
            vocal = VocalEmotion(
                stress=float(v.get("stress", 0)),
                engagement=float(v.get("engagement", 0)),
                confusion=float(v.get("confusion", 0)),
                frustration=float(v.get("frustration", 0)),
                confidence=SignalConfidence(
                    level=ConfidenceLevel(v.get("confidence_level", "medium")),
                    score=float(v.get("confidence_score", 0.5)),
                    source=v.get("source", "wav2vec2"),
                )
                if v.get("confidence_level")
                else None,
            )

        facial = None
        if row.get("facial_expression") and capabilities.has_video:
            f = row["facial_expression"]
            facial = FacialState(
                expression=str(f.get("expression", "neutral")),
                confusion=float(f.get("confusion", 0)),
                frustration=float(f.get("frustration", 0)),
                engagement=float(f.get("engagement", 0)),
                confidence=SignalConfidence(
                    level=ConfidenceLevel(f.get("confidence_level", "medium")),
                    score=float(f.get("confidence_score", 0.5)),
                    source=f.get("source", "gpt4o_vision"),
                )
                if f.get("confidence_level")
                else None,
            )

        language_friction = bool(row.get("language_friction")) and capabilities.has_transcript
        friction, chans = _channel_friction_flags(vocal, facial, language_friction)
        convergence = friction and len(chans) >= MIN_CHANNELS_FOR_CONVERGENCE

        modalities_present = []
        if vocal:
            modalities_present.append("vocal")
        if facial:
            modalities_present.append("facial")
        if row.get("transcript_segment") and capabilities.has_transcript:
            modalities_present.append("language")
        if row.get("ui_location") and capabilities.has_video:
            modalities_present.append("screen")

        note_parts = []
        if not capabilities.has_video:
            note_parts.append("no video")
        if not capabilities.has_audio:
            note_parts.append("no audio")
        if not capabilities.has_transcript:
            note_parts.append("no transcript")

        event = TimelineEvent(
            timestamp=str(row.get("timestamp", "00:00")),
            timestamp_seconds=float(row.get("timestamp_seconds", 0)),
            vocal_emotion=vocal,
            facial_expression=facial,
            ui_location=row.get("ui_location"),
            transcript_segment=row.get("transcript_segment"),
            friction_flag=friction,
            friction_type=row.get("friction_type"),
            multi_modal_convergence=convergence,
            modalities_present=modalities_present,
            confidence_notes="; ".join(note_parts),
        )
        timeline.append(event)

    friction_moments = [e for e in timeline if e.friction_flag]
    session = Session(
        participant_id=participant_id,
        study_context=study_context,
        capabilities=capabilities,
        duration_seconds=duration_seconds,
        timeline=timeline,
        friction_moments=friction_moments,
        key_quotes=[
            {
                "timestamp": e.timestamp,
                "quote": e.transcript_segment,
                "convergence": e.multi_modal_convergence,
            }
            for e in friction_moments
            if e.transcript_segment
        ],
        overall_confidence=_overall_confidence(capabilities, timeline),
    )
    return session


def session_from_fixture(data: dict) -> Session:
    """Load a fixture JSON dict into a Session via build_session."""
    cap = InputCapabilities(**data.get("capabilities", {}))
    return build_session(
        participant_id=data["participant_id"],
        study_context=data.get("study_context", ""),
        capabilities=cap,
        timeline_rows=data.get("timeline_rows", []),
        duration_seconds=float(data.get("duration_seconds", 0)),
    )
