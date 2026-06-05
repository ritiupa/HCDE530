"""
LENS data models — session timeline, capabilities, and report structures.
JSON-serializable for fixtures and API boundaries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(str, Enum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"


@dataclass
class InputCapabilities:
    """What inputs were available for this session."""

    has_video: bool = False
    has_audio: bool = False
    has_transcript: bool = False
    has_study_context: bool = False

    def modalities_count(self) -> int:
        return sum([self.has_video, self.has_audio, self.has_transcript])

    def summary(self) -> str:
        parts = []
        if self.has_video:
            parts.append("video")
        if self.has_audio:
            parts.append("audio")
        if self.has_transcript:
            parts.append("transcript")
        return ", ".join(parts) if parts else "none"


@dataclass
class SignalConfidence:
    """Confidence for one analytic signal at a point in time."""

    level: ConfidenceLevel
    score: float  # 0.0–1.0
    source: str  # e.g. whisper, wav2vec2, gpt4o_vision, mistral
    note: str = ""


@dataclass
class VocalEmotion:
    stress: float = 0.0
    engagement: float = 0.0
    confusion: float = 0.0
    frustration: float = 0.0
    confidence: Optional[SignalConfidence] = None


@dataclass
class FacialState:
    expression: str = "neutral"
    confusion: float = 0.0
    frustration: float = 0.0
    engagement: float = 0.0
    confidence: Optional[SignalConfidence] = None


@dataclass
class TimelineEvent:
    timestamp: str  # "MM:SS" or seconds as string for display
    timestamp_seconds: float = 0.0
    vocal_emotion: Optional[VocalEmotion] = None
    facial_expression: Optional[FacialState] = None
    ui_location: Optional[str] = None
    transcript_segment: Optional[str] = None
    friction_flag: bool = False
    friction_type: Optional[str] = None  # navigation, comprehension, etc.
    multi_modal_convergence: bool = False
    modalities_present: list[str] = field(default_factory=list)
    confidence_notes: str = ""


@dataclass
class Session:
    participant_id: str
    study_context: str = ""
    capabilities: InputCapabilities = field(default_factory=InputCapabilities)
    duration_seconds: float = 0.0
    timeline: list[TimelineEvent] = field(default_factory=list)
    friction_moments: list[TimelineEvent] = field(default_factory=list)
    engagement_curve: list[dict[str, Any]] = field(default_factory=list)
    key_quotes: list[dict[str, Any]] = field(default_factory=list)
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FrictionCluster:
    cluster_id: str
    title: str
    description: str
    heuristic: str
    severity: Severity
    participant_ids: list[str]
    frequency: int
    severity_score: float
    convergence_score: float
    evidence_confidence: ConfidenceLevel
    evidence_summary: str
    representative_quotes: list[dict[str, Any]] = field(default_factory=list)
    hmw_statement: str = ""
    design_recommendation: str = ""
    text_only_gap: str = ""  # what transcript-only tools would miss


@dataclass
class Report:
    executive_summary: str
    study_context: str
    clusters: list[FrictionCluster]
    text_only_comparison: str
    sessions_summary: list[dict[str, Any]]  # capabilities per participant
    report_structure_note: str = ""  # why sections ordered this way (generative UI)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
