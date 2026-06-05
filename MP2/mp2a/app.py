"""
app.py
------
LENS -- Layered Evidence and Narrative Synthesizer
Streamlit interface. Run with: streamlit run app.py

User flow:
  Page 1 -- Upload: study context, multiple recordings, per-participant notes
  Page 2 -- Processing: per-recording pipeline + cross-session synthesis
  Page 3 -- Report: study overview + per-session tabs
"""

import base64
import html
import streamlit as st
import time
from datetime import datetime
from pathlib import Path

from components.video_recorder import video_recorder
from recorder_config import (
    MAX_LIVE_RECORD_MB,
    QUALITY_PRESETS,
    format_duration,
    max_duration_seconds,
)
from ui_theme import APP_CSS, app_header, metrics_row, progress_html

INCOMING_DIR = Path("lens_output") / "incoming"

# Page config must be the first Streamlit call.
st.set_page_config(
    page_title="LENS",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(APP_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT

def reset_session():
    """Clear all analysis state and return to upload."""
    st.session_state.page = "upload"
    st.session_state.study_report = None
    st.session_state.upload = None
    st.session_state.processing_status = None
    st.session_state.processing_error = None
    st.session_state.processing_progress = None
    st.session_state.staged_live = []
    st.session_state.live_recording = None
    st.session_state.last_rec_sig = None
    st.session_state.upload_key = st.session_state.get("upload_key", 0) + 1
    st.session_state.recorder_key = st.session_state.get("recorder_key", 0) + 1


if "page" not in st.session_state:
    st.session_state.page = "upload"
if "study_report" not in st.session_state:
    st.session_state.study_report = None
if "upload" not in st.session_state:
    st.session_state.upload = None
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
if "processing_status" not in st.session_state:
    st.session_state.processing_status = None
if "processing_error" not in st.session_state:
    st.session_state.processing_error = None
if "processing_progress" not in st.session_state:
    st.session_state.processing_progress = None
if "staged_live" not in st.session_state:
    st.session_state.staged_live = []
if "live_recording" not in st.session_state:
    st.session_state.live_recording = None
if "last_rec_sig" not in st.session_state:
    st.session_state.last_rec_sig = None
if "recorder_key" not in st.session_state:
    st.session_state.recorder_key = 0


# ─────────────────────────────────────────────
# SHARED HEADER
# ─────────────────────────────────────────────
def render_header(show_back=False, step: int = 0, subtitle: str = ""):
    col_title, col_action = st.columns([5, 1])
    with col_title:
        st.markdown(app_header(step, subtitle), unsafe_allow_html=True)
    with col_action:
        if show_back:
            if st.button("New study", type="secondary", use_container_width=True):
                reset_session()
                st.rerun()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
SEVERITY_ORDER = {"Critical": 0, "Major": 1, "Minor": 2}


def _default_session_id(index: int) -> str:
    return f"P{index + 1}"


def _recording_bytes(rec: dict) -> bytes:
    if rec.get("file_bytes") is not None:
        return rec["file_bytes"]
    path = rec.get("file_path")
    if path:
        return Path(path).read_bytes()
    raise ValueError(f"No recording data for session {rec.get('session_id')}")


def _save_live_recording(
    result: dict,
    session_id: str,
    participant_note: str,
) -> dict:
    """Decode browser recording, write to disk, return staging metadata (no base64 in session)."""
    raw = base64.b64decode(result["data"])
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > MAX_LIVE_RECORD_MB:
        raise ValueError(
            f"Recording is {size_mb:.1f} MB — limit is {MAX_LIVE_RECORD_MB} MB. "
            "Use Extended quality or record a shorter session."
        )

    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{session_id}_{result.get('filename', 'live.webm')}"
    path = INCOMING_DIR / filename
    path.write_bytes(raw)

    return {
        "file_path": str(path),
        "file_name": filename,
        "session_id": session_id,
        "participant_note": participant_note,
        "source": "live",
        "duration_sec": result.get("duration_sec"),
        "size_bytes": len(raw),
    }


def _next_session_id(existing: list[dict]) -> str:
    used = {r["session_id"] for r in existing}
    n = 1
    while f"P{n}" in used:
        n += 1
    return f"P{n}"


def _render_finding_cards(findings: list[dict], expanded_first: bool = True):
    sorted_findings = sorted(
        findings,
        key=lambda f: SEVERITY_ORDER.get(f.get("severity", "Minor"), 3),
    )
    for i, finding in enumerate(sorted_findings):
        severity = finding.get("severity", "Minor")
        badge_class = f"badge-{severity.lower()}"
        severity_emoji = {"Critical": "●", "Major": "●", "Minor": "●"}.get(severity, "○")

        with st.expander(
            f"{severity_emoji} {finding['title']}",
            expanded=(expanded_first and i == 0),
        ):
            st.markdown(f"""
            <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:1rem;">
              <span class="badge {badge_class}">{severity}</span>
              <span class="pill">{html.escape(finding.get('heuristic', ''))}</span>
              <span class="pill">{finding['occurrence_count']} occurrences</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(
                f'<p class="finding-body">{html.escape(finding["description"])}</p>',
                unsafe_allow_html=True,
            )
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div class="insight-box insight-box-accent">
                  <p class="eyebrow">How Might We</p>
                  <p style="font-size:0.85rem; color:var(--text-primary); margin:0; line-height:1.6;">
                    {html.escape(finding['hmw'])}
                  </p>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                <div class="insight-box">
                  <p class="eyebrow">Recommendation</p>
                  <p style="font-size:0.85rem; color:var(--text-primary); margin:0; line-height:1.6;">
                    {html.escape(finding['recommendation'])}
                  </p>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('<p class="eyebrow" style="margin-top:1rem;">Evidence</p>', unsafe_allow_html=True)
            for quote in finding["evidence"]:
                st.markdown(
                    f'<div class="quote-block">{html.escape(quote)}</div>',
                    unsafe_allow_html=True,
                )


def _render_transcript(segments: list[dict]):
    rows_html = ""
    for seg in segments:
        is_friction = seg.get("friction_flag", False)
        mark = '<div class="friction-mark"></div>' if is_friction else '<div style="width:5px;"></div>'
        text_class = "transcript-text-friction" if is_friction else "transcript-text"
        rows_html += f"""
        <div class="transcript-row">
          {mark}
          <span class="transcript-ts">{seg['start']}s</span>
          <span class="{text_class}">{html.escape(seg['text'])}</span>
        </div>"""
    st.markdown(f'<div class="transcript-wrap">{rows_html}</div>', unsafe_allow_html=True)


def _session_report_markdown(report: dict) -> str:
    lines = [
        f"## Session {report['session_id']}",
        f"**Generated:** {report['generated_at']}",
    ]
    if report.get("participant_note"):
        lines.append(f"**Participant:** {report['participant_note']}")
    lines += ["", report["summary"], ""]
    for i, f in enumerate(report["findings"], 1):
        lines += [
            f"### Finding {i}: {f['title']}",
            f"**Severity:** {f['severity']} · **Heuristic:** {f.get('heuristic', '')}",
            f"**Description:** {f['description']}",
            f"**HMW:** {f['hmw']}",
            f"**Recommendation:** {f['recommendation']}",
            "",
        ]
        for q in f["evidence"]:
            lines.append(f"- {q}")
        lines.append("")
    return "\n".join(lines)


def _study_report_markdown(study: dict) -> str:
    cross = study["cross_session"]
    lines = [
        f"# LENS Study Report",
        f"**Generated:** {study['generated_at']}",
        f"**Study context:** {study.get('study_context') or 'Not specified'}",
        f"**Sessions analyzed:** {cross['session_count']}",
        "",
        "## Executive summary",
        cross["summary"],
        "",
        "## Cross-session patterns",
        "",
    ]
    if cross["patterns"]:
        for p in cross["patterns"]:
            recurring = " (recurring)" if p["recurring"] else ""
            lines += [
                f"### {p['title']}{recurring}",
                f"- Sessions: {', '.join(p['session_ids'])} ({p['sessions_affected']} total)",
                f"- Occurrences: {p['total_occurrences']} · Severity: {p['severity']}",
                f"- Heuristic: {p.get('heuristic', '')}",
                "",
            ]
            for q in p.get("sample_quotes", [])[:3]:
                lines.append(f"- {q}")
            lines.append("")
    else:
        lines.append("No friction patterns detected across sessions.\n")

    lines += ["## Highlights", ""]
    for h in cross.get("highlights", []):
        note = f" — {h['participant_note']}" if h.get("participant_note") else ""
        lines.append(
            f"- **{h['session_id']}{note}** [{h['severity']}]: {h['title']} — {h['description']}"
        )
    lines.append("")

    for session in study["sessions"]:
        lines.append(_session_report_markdown(session["report"]))
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# PAGE 1 -- UPLOAD
# ─────────────────────────────────────────────
def _render_session_queue(live_recordings: list[dict], upload_entries: list[dict]):
    """Show unified list of sessions queued for analysis."""
    total = len(upload_entries) + len(live_recordings)
    if total == 0:
        st.caption("No sessions added yet.")
        return total

    st.markdown(f"**{total} session(s) ready**")
    for rec in live_recordings:
        dur = format_duration(rec["duration_sec"]) if rec.get("duration_sec") else "—"
        size = f"{rec['size_bytes'] / (1024*1024):.1f} MB" if rec.get("size_bytes") else ""
        note = rec.get("participant_note") or "No note"
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(
                f'<div class="session-item">'
                f'<span class="session-item-id">{html.escape(rec["session_id"])}</span>'
                f'<span class="session-item-meta">{html.escape(note)} · {dur} · {size}</span>'
                f'<span class="session-item-source">Live</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            idx = live_recordings.index(rec)
            if st.button("Remove", key=f"rm_live_{idx}_{rec['session_id']}", type="secondary"):
                st.session_state.staged_live.pop(idx)
                st.session_state.last_rec_sig = None
                st.session_state.recorder_key += 1
                st.rerun()

    for i, rec in enumerate(upload_entries):
        note = rec.get("participant_note") or "No note"
        st.markdown(
            f'<div class="session-item">'
            f'<span class="session-item-id">{html.escape(rec["session_id"])}</span>'
            f'<span class="session-item-meta">{html.escape(note)} · {html.escape(rec["file_name"][:48])}</span>'
            f'<span class="session-item-source">Upload</span></div>',
            unsafe_allow_html=True,
        )
    return total


def page_upload():
    render_header(step=0, subtitle="New study")

    # ── Study settings ──
    st.markdown('<p class="section-label">Study settings</p>', unsafe_allow_html=True)
    study_context = st.text_area(
        "Study context",
        placeholder="What was tested? e.g. p5.js reference docs — task: find ellipse()",
        height=72,
        help="Brief description of the usability test and task given to participants.",
    )
    whisper_model = st.selectbox(
        "Transcription model",
        options=["tiny (fastest)", "base (recommended)", "small (most accurate)"],
        index=1,
        help="Whisper model used for speech-to-text. Base is a good balance of speed and accuracy.",
    )
    model_key = whisper_model.split(" ")[0]

    st.markdown("---")

    # ── Add sessions ──
    st.markdown('<p class="section-label">Add sessions</p>', unsafe_allow_html=True)
    input_mode = st.segmented_control(
        "How are you adding recordings?",
        options=["Upload files", "Record live"],
        default="Upload files",
    )

    upload_meta: list[dict] = []

    if input_mode == "Upload files":
        st.caption("Upload one or more audio/video files from your usability sessions.")
        uploaded_files = st.file_uploader(
            "Session recordings",
            type=["mp4", "mov", "webm", "wav", "mp3", "m4a"],
            accept_multiple_files=True,
            key=f"session_uploader_{st.session_state.upload_key}",
        )
        if uploaded_files:
            if st.button("Clear uploads", type="secondary"):
                st.session_state.upload_key += 1
                st.rerun()

            st.markdown("**Label each session** — set a participant ID and optional note.")
            for i, f in enumerate(uploaded_files):
                default_id = _default_session_id(
                    len(st.session_state.staged_live) + i
                )
                c1, c2, c3 = st.columns([1, 2, 2])
                with c1:
                    sid = st.text_input(
                        "Participant ID",
                        value=default_id,
                        key=f"sid_{st.session_state.upload_key}_{i}",
                        label_visibility="collapsed",
                        placeholder="P1",
                    ).strip() or default_id
                with c2:
                    participant_note = st.text_input(
                        "Note",
                        placeholder="Optional participant note",
                        key=f"note_{st.session_state.upload_key}_{i}",
                        label_visibility="collapsed",
                    ).strip()
                with c3:
                    st.text(f.name)
                upload_meta.append({
                    "file_bytes": f.getvalue(),
                    "file_name": f.name,
                    "session_id": sid,
                    "participant_note": participant_note,
                    "source": "upload",
                })

    else:
        st.caption("Your camera starts automatically. Record the session, then analyze when ready.")

        rec_result = video_recorder(
            quality=st.session_state.get("record_quality", "balanced"),
            max_size_mb=MAX_LIVE_RECORD_MB,
            max_duration_sec=max_duration_seconds(
                st.session_state.get("record_quality", "balanced"), MAX_LIVE_RECORD_MB
            ),
            key=f"video_rec_{st.session_state.recorder_key}",
        )

        live_default_id = _next_session_id(
            ([st.session_state.live_recording] if st.session_state.live_recording else [])
        )
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.text_input(
                "Participant ID",
                value=live_default_id,
                key="rec_session_id",
                placeholder="P1",
            )
        with c2:
            st.text_input(
                "Participant note",
                placeholder="Optional note",
                key="rec_participant_note",
            )
        with c3:
            st.selectbox(
                "Recording quality",
                options=list(QUALITY_PRESETS.keys()),
                index=1,
                format_func=lambda k: QUALITY_PRESETS[k]["label"].split("—")[0].strip(),
                key="record_quality",
                help="Lower quality = longer recordings within the size limit.",
            )

        if rec_result:
            if rec_result.get("action") == "redo":
                st.session_state.live_recording = None
                st.session_state.last_rec_sig = None
                st.session_state.recorder_key += 1
                st.rerun()
            elif rec_result.get("action") == "ready":
                sig = f"{rec_result.get('filename')}:{rec_result.get('size_bytes')}"
                if sig != st.session_state.last_rec_sig:
                    rec_session_id = st.session_state.get("rec_session_id", live_default_id).strip() or live_default_id
                    rec_participant_note = st.session_state.get("rec_participant_note", "").strip()
                    try:
                        saved = _save_live_recording(rec_result, rec_session_id, rec_participant_note)
                        st.session_state.live_recording = saved
                        st.session_state.last_rec_sig = sig
                        st.toast("Recording ready — click Analyze session below")
                    except ValueError as exc:
                        st.error(str(exc))

        if st.session_state.live_recording:
            rec = st.session_state.live_recording
            dur = format_duration(rec["duration_sec"]) if rec.get("duration_sec") else "—"
            size = f"{rec['size_bytes'] / (1024*1024):.1f} MB"
            st.success(
                f"**{rec['session_id']}** ready · {dur} · {size} — review playback above, "
                "then click **Analyze session** below."
            )

    st.markdown("---")

    # ── Analyze ──
    if input_mode == "Record live":
        live_list = [st.session_state.live_recording] if st.session_state.live_recording else []
        all_recordings = live_list
        if all_recordings:
            if st.button("Analyze session", type="primary"):
                st.session_state.upload = {
                    "study_context": study_context.strip(),
                    "model": model_key,
                    "recordings": all_recordings,
                }
                st.session_state.processing_status = None
                st.session_state.processing_error = None
                st.session_state.processing_progress = None
                st.session_state.page = "processing"
                st.rerun()
        else:
            st.button("Analyze session", type="primary", disabled=True)
            st.caption("Record and stop a session first, then analyze.")
    else:
        st.markdown('<p class="section-label">Review & analyze</p>', unsafe_allow_html=True)
        all_recordings = upload_meta + st.session_state.staged_live
        total = _render_session_queue(st.session_state.staged_live, upload_meta)

        if all_recordings:
            session_ids = [m["session_id"] for m in all_recordings]
            duplicates = {s for s in session_ids if session_ids.count(s) > 1}
            if duplicates:
                st.error(f"Duplicate participant IDs: {', '.join(sorted(duplicates))}. Each session needs a unique ID.")
            else:
                label = f"Analyze {len(all_recordings)} sessions" if len(all_recordings) > 1 else "Analyze session"
                if st.button(label, type="primary"):
                    st.session_state.upload = {
                        "study_context": study_context.strip(),
                        "model": model_key,
                        "recordings": all_recordings,
                    }
                    st.session_state.processing_status = None
                    st.session_state.processing_error = None
                    st.session_state.processing_progress = None
                    st.session_state.page = "processing"
                    st.rerun()
        else:
            st.button("Analyze session", type="primary", disabled=True)


# ─────────────────────────────────────────────
# PAGE 2 -- PROCESSING
# Live progress with honest step labels
# ─────────────────────────────────────────────
def page_processing():
    render_header(step=1, subtitle="Processing")

    upload = st.session_state.get("upload")
    recordings = (upload or {}).get("recordings", [])
    if not upload or not recordings:
        st.warning("No recordings to analyze.")
        if st.button("Back to setup", type="secondary"):
            reset_session()
            st.rerun()
        return

    if st.session_state.processing_status == "done":
        st.session_state.page = "report"
        st.rerun()

    study_context = upload.get("study_context", "")
    n_sessions = len(recordings)
    progress = st.session_state.processing_progress or {"current": 0, "phase": "session"}

    step_placeholder = st.empty()
    error_placeholder = st.empty()

    def render_progress(session_idx: int, phase: str, step_idx: int):
        session_label = recordings[session_idx]["session_id"] if session_idx < n_sessions else "—"
        if phase == "session":
            title = f"Session {session_idx + 1} of {n_sessions} — {session_label}"
            subtitle = "This may take a few minutes per recording. Keep this tab open."
            steps = ["Extract audio", "Transcribe", "Detect friction", "Enrich", "Write report"]
        else:
            title = "Cross-session synthesis"
            subtitle = "Finding patterns across participants"
            steps = ["Aggregate", "Highlights", "Summary"]

        step_placeholder.markdown(
            progress_html(title, subtitle, steps, step_idx),
            unsafe_allow_html=True,
        )

    if st.session_state.processing_status == "error":
        render_progress(progress.get("current", 0), progress.get("phase", "session"), 0)
        err = html.escape(st.session_state.processing_error or "Unknown error")
        error_placeholder.markdown(
            f'<div class="error-panel"><p style="color:#fca5a5;font-weight:600;margin:0 0 0.35rem 0;">Something went wrong</p>'
            f'<p style="color:var(--text-secondary);font-size:0.82rem;margin:0;">{err}</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Back to setup", type="secondary"):
            st.session_state.processing_status = None
            st.session_state.processing_error = None
            st.session_state.processing_progress = None
            st.session_state.page = "upload"
            st.rerun()
        return

    from cross_session import synthesize_study
    from ingestion import ingest_session
    from language_analysis import analyze
    from report_generator import generate_report
    from transcription import transcribe

    output_dir = Path("lens_output")
    output_dir.mkdir(exist_ok=True)

    try:
        st.session_state.processing_status = "running"
        session_results = []
        session_reports = []

        for idx, rec in enumerate(recordings):
            st.session_state.processing_progress = {"current": idx, "phase": "session"}
            session_id = rec["session_id"]
            participant_note = rec.get("participant_note", "")

            if rec.get("file_path"):
                input_path = Path(rec["file_path"])
            else:
                input_path = output_dir / f"{session_id}_{rec['file_name']}"
                input_path.write_bytes(rec["file_bytes"])

            render_progress(idx, "session", 0)
            result = ingest_session(str(input_path), session_id, str(output_dir))

            render_progress(idx, "session", 1)
            segments = transcribe(result["audio_path"], model_size=upload.get("model", "base"))

            render_progress(idx, "session", 2)
            enriched = analyze(segments)

            render_progress(idx, "session", 3)
            time.sleep(0.3)

            render_progress(idx, "session", 4)
            report = generate_report(
                segments=enriched,
                session_id=session_id,
                context=study_context,
                participant_note=participant_note,
                output_dir=str(output_dir),
            )

            session_results.append({"report": report, "segments": enriched})
            session_reports.append(report)

        # Cross-session synthesis (also runs for single session — unified overview)
        st.session_state.processing_progress = {"current": 0, "phase": "cross"}
        render_progress(0, "cross", 0)
        cross_session = synthesize_study(study_context, session_reports)

        render_progress(0, "cross", 1)
        time.sleep(0.2)

        render_progress(0, "cross", 2)
        st.session_state.study_report = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "study_context": study_context,
            "sessions": session_results,
            "cross_session": cross_session,
        }

        st.session_state.processing_status = "done"
        st.session_state.staged_live = []
        st.session_state.live_recording = None
        st.session_state.page = "report"
        st.rerun()

    except Exception as e:
        st.session_state.processing_status = "error"
        st.session_state.processing_error = str(e)
        st.rerun()


# ─────────────────────────────────────────────
# PAGE 3 -- REPORT
# Severity-sorted findings, transcript, export
# ─────────────────────────────────────────────
def _render_study_overview(study: dict):
    cross = study["cross_session"]
    n = cross["session_count"]
    recurring = len(cross.get("recurring_patterns", []))
    critical = len(cross.get("sessions_with_critical", []))

    st.markdown(f"""
    <div class="surface-accent">
      <p class="eyebrow">Study overview · {study['generated_at']}</p>
      <p class="headline" style="font-size:1.2rem; margin-bottom:0.75rem;">{html.escape(cross['summary'])}</p>
      {metrics_row([
          (str(n), "Sessions"),
          (str(cross['total_friction_moments']), "Friction"),
          (str(recurring), "Recurring"),
          (str(critical), "Critical"),
      ])}
    </div>
    """, unsafe_allow_html=True)

    if study.get("study_context"):
        st.markdown(f"""
        <p style="font-size:0.82rem; color:var(--text-tertiary); margin:0 0 1.5rem 0;">
          {html.escape(study['study_context'])}
        </p>
        """, unsafe_allow_html=True)

    st.markdown('<p class="section-title">Sessions</p>', unsafe_allow_html=True)
    for s in study["sessions"]:
        r = s["report"]
        note = r.get("participant_note") or "No participant note"
        friction = r.get("friction_segments", 0)
        findings = len(r.get("findings", []))
        st.markdown(f"""
        <div class="participant-row">
          <div class="participant-avatar">{html.escape(r['session_id'][-2:])}</div>
          <div>
            <p class="participant-name">{html.escape(r['session_id'])}</p>
            <p class="participant-meta">{html.escape(note)} · {friction} friction · {findings} findings</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    if cross.get("highlights"):
        st.markdown('<p class="section-title" style="margin-top:1.5rem;">Highlights</p>', unsafe_allow_html=True)
        for h in cross["highlights"]:
            sev = h.get("severity", "Minor")
            badge_class = f"badge-{sev.lower()}"
            note = f" · {html.escape(h['participant_note'])}" if h.get("participant_note") else ""
            st.markdown(f"""
            <div class="highlight-card">
              <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.5rem;">
                <span class="badge {badge_class}">{sev}</span>
                <span class="pill">{html.escape(h['session_id'])}{note}</span>
              </div>
              <p class="finding-title">{html.escape(h['title'])}</p>
              <p class="finding-body">{html.escape(h['description'])}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<p class="section-title" style="margin-top:1.5rem;">Cross-session patterns</p>', unsafe_allow_html=True)
    if not cross.get("patterns"):
        st.markdown('<div class="surface-inset"><p class="finding-body">No friction patterns detected.</p></div>', unsafe_allow_html=True)
    else:
        for p in cross["patterns"]:
            sev = p.get("severity", "Minor")
            badge_class = f"badge-{sev.lower()}"
            recurring_tag = " · recurring" if p.get("recurring") else ""
            with st.expander(
                f"{p['title']} — {p['sessions_affected']}/{n} sessions{recurring_tag}",
                expanded=p.get("recurring", False) and p == cross["patterns"][0],
            ):
                st.markdown(f"""
                <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.75rem;">
                  <span class="badge {badge_class}">{sev}</span>
                  <span class="pill">{', '.join(p['session_ids'])}</span>
                  <span class="pill">{p['total_occurrences']} total</span>
                </div>
                """, unsafe_allow_html=True)
                if p.get("heuristic"):
                    st.caption(p["heuristic"])
                for q in p.get("sample_quotes", []):
                    st.markdown(f'<div class="quote-block">{html.escape(q)}</div>', unsafe_allow_html=True)


def _render_session_detail(session_data: dict):
    report = session_data["report"]
    segments = session_data["segments"]

    friction_count = sum(1 for s in segments if s.get("friction_flag"))
    critical = sum(1 for f in report["findings"] if f["severity"] == "Critical")
    major = sum(1 for f in report["findings"] if f["severity"] == "Major")

    participant_html = ""
    if report.get("participant_note"):
        participant_html = f'<span class="pill">{html.escape(report["participant_note"])}</span>'

    st.markdown(f"""
    <div class="surface-accent">
      <p class="eyebrow">Session {html.escape(report['session_id'])} · {report['generated_at']}</p>
      <p class="headline" style="font-size:1.05rem; margin-bottom:0.75rem;">{html.escape(report['summary'])}</p>
      <div>{participant_html}</div>
      {metrics_row([
          (str(report['total_segments']), "Segments"),
          (str(friction_count), "Friction"),
          (str(critical), "Critical"),
          (str(major), "Major"),
      ])}
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="section-title">Findings</p>', unsafe_allow_html=True)
    if not report["findings"]:
        st.markdown("""
        <div class="surface-inset" style="text-align:center; padding:2.5rem;">
          <p class="finding-body">No significant friction detected in this session.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        _render_finding_cards(report["findings"])

    st.markdown("<hr>", unsafe_allow_html=True)
    with st.expander("Full transcript", expanded=False):
        st.caption("Highlighted lines indicate detected friction")
        _render_transcript(segments)


def page_report():
    st.markdown('<div class="report-page">', unsafe_allow_html=True)
    render_header(show_back=True, step=2, subtitle="Report")

    study = st.session_state.study_report
    if not study:
        st.session_state.page = "upload"
        st.rerun()

    tab_labels = ["Study overview"] + [
        s["report"]["session_id"] for s in study["sessions"]
    ]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        _render_study_overview(study)

    for tab, session_data in zip(tabs[1:], study["sessions"]):
        with tab:
            _render_session_detail(session_data)

    st.markdown('<p class="section-title">Export</p>', unsafe_allow_html=True)
    md_content = _study_report_markdown(study)
    st.download_button(
        label="Download study report",
        data=md_content,
        file_name="lens_study_report.md",
        mime="text/markdown",
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
if st.session_state.page == "upload":
    page_upload()
elif st.session_state.page == "processing":
    page_processing()
elif st.session_state.page == "report":
    page_report()
