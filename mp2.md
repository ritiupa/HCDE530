# Mini Project 2 — Competency Claims

**Project:** LENS (Layered Evidence and Narrative Synthesizer)  
**Author:** Riti Upadhyay · HCDE 530 SP26  
**Live tool:** `[LOVABLE_URL]` *(replace before Canvas submission)*  
**Repository:** https://github.com/ritiupa/HCDE530  
**Reference implementation:** `MP2/mp2a/` (Python + Streamlit)

---

## What I built

LENS is a usability synthesis tool for UX researchers. It accepts moderated session recordings (upload or live browser capture), transcribes them, detects friction in think-aloud speech, and generates structured findings organized by severity and Nielsen heuristic—with timestamped evidence quotes, HMW statements, and recommendations. The deployed interface is built in **Lovable**; the analysis pipeline reference implementation is in **Python** (`ingestion.py`, `transcription.py`, `language_analysis.py`, `report_generator.py`, `cross_session.py`). Report structure is **generative**: the dominant friction pattern leads the readout rather than a fixed template.

---

## C3 — Data Cleaning and File Handling

`ingestion.py` normalizes heterogeneous inputs (MP4, MOV, WEBM, WAV, MP3, M4A) into a standard WAV for Whisper. Each session is keyed by participant ID with isolated output paths under `lens_output/`. `transcription.py` normalizes Whisper segment timestamps. `report_generator.py` persists findings as structured dicts for the UI and as downloadable Markdown. The Streamlit prototype validates duplicate participant IDs, stores live recordings to disk (not session memory), and handles missing files, unsupported formats, and API failures without crashing the run.

**Evidence:** `MP2/mp2a/ingestion.py`, `MP2/mp2a/app.py` (`_save_live_recording`, upload validation)

---

## C4 — APIs and Data Acquisition

Two acquisition paths: **local Whisper** (openai-whisper, no per-call cost) and **HuggingFace Inference API** for Mistral enrichment (`language_analysis.py`, `report_generator.py`). Keys load from `.env` via python-dotenv; only friction-flagged segments are sent to the API—not full transcripts—to limit usage. When the API is unavailable, local regex friction detection and rule-based finding templates still produce a report. Live browser recording uses the MediaRecorder API with quality presets bounded by a 200 MB cap (`recorder_config.py`, `components/video_recorder/`).

**Evidence:** `MP2/mp2a/language_analysis.py`, `MP2/mp2a/.env.example`, `MP2/mp2a/components/video_recorder/frontend/index.html`

---

## C5 — Data Analysis

`language_analysis.py` runs two passes: (1) regex pattern matching against a curated think-aloud friction phrase list, (2) optional Mistral enrichment for severity and heuristic tags. `report_generator.py` clusters friction segments by type, ranks by frequency and severity, and emits one finding per cluster. `cross_session.py` aggregates patterns across participants and flags recurring issues. The Lovable UI presents the same analytical structure—findings sorted Critical → Major → Minor with occurrence counts and cross-session highlights.

**Evidence:** `MP2/mp2a/language_analysis.py`, `MP2/mp2a/cross_session.py`, `MP2/mp2a/fixtures/P1_multimodal.json`

---

## C6 — Data Visualization and Communication

Findings render as expandable cards with severity badges, heuristic pills, evidence quote blocks, and HMW/recommendation panels. The transcript view highlights friction lines. Study overview shows metrics (sessions, friction moments, recurring patterns). Markdown export matches professional usability readout structure. The Lovable deployment prioritizes communication clarity for researchers who were not in the room—executive summary first, drill-down second.

**Evidence:** Lovable report UI; `MP2/mp2a/app.py` (`_render_finding_cards`, `_render_study_overview`); `MP2/mp2a/ui_theme.py`

---

## C7 — Critical Evaluation and Professional Judgment

Scope is deliberately transcript-first for the course MVP. Vocal emotion (`emotion_audio.py`), facial expression (`emotion_video.py`), and screen-state vision (`screen_analysis.py`) are stubbed and documented as roadmap—not shipped claims. The README and `decisions.md` state confidence limits and the text-only gap explicitly. Platform choice evolved: MP2a declared Cursor + Python + Streamlit for computation; the **final deployed UX** moved to Lovable for presentation quality while keeping the Python repo as the analysis reference. Pattern matching is fast but incomplete; Mistral adds depth at the cost of API dependency—the tool degrades gracefully rather than failing silently.

**Evidence:** `MP2/mp2a/README.md` (research roadmap), `MP2/mp2a/decisions.md`, `MP2/mp2/mp2.md` (this file)

---

## MP2a declaration (original)

**Problem:** UX researchers manually review hours of session video and miss behavioral signals not captured in notes.  
**Audience:** UX researchers conducting moderated usability tests under time pressure.  
**Data:** Session video/audio → Whisper transcription → friction analysis → structured findings.  
**Track:** Research.  
**Platform (declared):** Cursor + Python + Streamlit.  
**Platform (deployed):** Lovable (UI) + Python reference pipeline in GitHub.
