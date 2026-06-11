# Mini Project 2 — Competency Claims

**Project:** LENS (Layered Evidence and Narrative Synthesizer)  
**Author:** Riti Upadhyay · HCDE 530 SP26  
**Live tool:** https://evidencesynthesizer.lovable.app  
**Repository:** https://github.com/ritiupa/HCDE530  
**Lovable codebase:** `MP2/mp2b/`  
**Python reference:** `MP2/mp2a/`

---

## What I built

LENS helps UX researchers turn moderated usability sessions into structured findings reports. A researcher describes the study, uploads or records sessions, and receives findings ranked by severity with Nielsen heuristic tags, evidence quotes, HMW prompts, and recommendations. Multi-session studies get cross-participant pattern summaries.

The **deployed tool** is a Lovable web app (`MP2/mp2b/`). The **analysis reference** is Python (`MP2/mp2a/`): ingestion, Whisper transcription, friction detection, report generation, and cross-session synthesis. Report structure is generative. The lead finding follows what the data shows, not a fixed template.

---

## C3 — Data Cleaning and File Handling

`MP2/mp2a/ingestion.py` normalizes MP4, MOV, WEBM, WAV, MP3, and M4A into audio for Whisper. Each session uses a participant ID and its own output folder. The Lovable app (`SessionUploader.tsx`, `SessionRecorder.tsx`) validates duplicate IDs and handles upload and live capture in the browser.

**Evidence:** `MP2/mp2a/ingestion.py`, `MP2/mp2a/app.py`, `MP2/mp2b/src/components/SessionUploader.tsx`

---

## C4 — APIs and Data Acquisition

Week 4 and Week 6 assignments used public APIs (Wikimedia Pageviews, Cornell corpus download). For LENS: Whisper runs locally in `mp2a`; Mistral enrichment runs through HuggingFace when a key is set; the Lovable app uses the Lovable AI gateway and local friction regex (`mp2b/src/lib/friction.ts`) as fallback. Live recording uses the browser MediaRecorder API with quality presets and a 200 MB cap.

**Evidence:** `week 4/design_trends.py`, `week 6/fetch_cornell.py`, `MP2/mp2a/language_analysis.py`, `MP2/mp2b/src/lib/friction.ts`, `MP2/mp2b/src/routes/api/analyze.ts`

---

## C5 — Data Analysis

MP1b used deliberate pandas aggregations on the Cornell corpus (distinct film counts, emotion ratios, agency proxy). LENS runs two passes on transcripts: regex friction patterns, then optional LLM enrichment. `report_generator.py` and `cross_session.py` cluster findings and flag recurring patterns across participants.

**Evidence:** `week 8/mp1_notebook.ipynb`, `MP2/mp2a/language_analysis.py`, `MP2/mp2a/cross_session.py`, `MP2/mp2b/src/lib/analyze.functions.ts`

---

## C6 — Data Visualization and Communication

MP1b charts used deliberate Plotly types with interpretation cells. LENS communicates through severity-sorted finding cards, study overview metrics, highlighted transcript lines, and Markdown export. The Lovable report view (`mp2b/src/routes/report.tsx`) puts the executive summary first.

**Evidence:** MP1 chart PNGs in repo, `MP2/mp2a/app.py`, `MP2/mp2b/src/components/FindingCard.tsx`, `MP2/mp2b/src/routes/report.tsx`

---

## C7 — Critical Evaluation and Professional Judgment

My MP2a declaration was too large for a solo timeline. Professor feedback pushed me to cut scope honestly. I shipped a transcript-first MVP and documented vocal emotion, facial expression, and screen-state analysis as roadmap items, not finished features. I built the pipeline in Python first, then moved the public interface to Lovable when Streamlit UX could not support a credible demo. The live app and the Python repo serve different roles: presentation and reproducible analysis.

**Evidence:** `MP2/mp2a/decisions.md`, `MP2/mp2a/README.md`, `MP2/mp2b/README.md`

---

## MP2a declaration (original)

**Problem:** UX researchers spend hours reviewing session video and miss signals that never appear in notes.  
**Audience:** UX researchers under deadline pressure.  
**Data:** Session recordings, Whisper transcription, friction analysis, structured findings.  
**Track:** Research.  
**Platform (declared):** Cursor + Python + Streamlit.  
**Platform (submitted):** Lovable (live) + Python reference in GitHub.
