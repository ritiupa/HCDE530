"""Live recording limits and quality presets (optimized for ~200 MB cap)."""

from __future__ import annotations

MAX_UPLOAD_MB = 200
# Browser → Python transfer is heavy; live recordings use a slightly lower cap for reliability.
MAX_LIVE_RECORD_MB = 200

QUALITY_PRESETS = {
    "standard": {
        "label": "Standard — sharper face & screen",
        "width": 854,
        "height": 480,
        "frame_rate": 20,
        "video_bps": 900_000,
        "audio_bps": 64_000,
        "description": "Best for short sessions (~15–20 min within 200 MB).",
    },
    "balanced": {
        "label": "Balanced — recommended",
        "width": 640,
        "height": 480,
        "frame_rate": 15,
        "video_bps": 550_000,
        "audio_bps": 48_000,
        "description": "Clear expressions and actions (~25–35 min within 200 MB).",
    },
    "extended": {
        "label": "Extended — longest recording time",
        "width": 480,
        "height": 360,
        "frame_rate": 12,
        "video_bps": 320_000,
        "audio_bps": 32_000,
        "description": "Lower resolution, longer sessions (~45–55 min within 200 MB).",
    },
}


def total_bitrate(preset_key: str) -> int:
    p = QUALITY_PRESETS[preset_key]
    return p["video_bps"] + p["audio_bps"]


def max_duration_seconds(preset_key: str, max_mb: int = MAX_LIVE_RECORD_MB) -> int:
    """Estimate max seconds before hitting the size cap at the preset bitrate."""
    bps = total_bitrate(preset_key)
    max_bits = max_mb * 1024 * 1024 * 8
    return max(60, int(max_bits / bps))


def format_duration(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}h {m}m"
    return f"{m}m {s}s"
