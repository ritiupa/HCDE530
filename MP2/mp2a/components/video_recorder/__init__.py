"""Browser-based webcam recorder with size and duration limits."""

from __future__ import annotations

import os

import streamlit.components.v1 as components

_DIR = os.path.dirname(os.path.abspath(__file__))
_component = components.declare_component("lens_video_recorder", path=os.path.join(_DIR, "frontend"))


def video_recorder(
    *,
    quality: str = "balanced",
    max_size_mb: int = 200,
    max_duration_sec: int = 1800,
    key: str | None = None,
) -> dict | None:
    """
    Record from the user's webcam in the browser.

    Returns dict with keys: data (base64 webm), filename, duration_sec, size_bytes
    or None if nothing recorded yet.
    """
    result = _component(
        quality=quality,
        max_size_mb=max_size_mb,
        max_duration_sec=max_duration_sec,
        key=key,
        default=None,
        height=480,
    )
    if result is None or not isinstance(result, dict):
        return None
    if result.get("action") == "redo":
        return result
    if not result.get("data"):
        return None
    return result
