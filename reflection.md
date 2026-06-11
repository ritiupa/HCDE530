# MP2 Reflection — LENS

**Riti Upadhyay · HCDE 530 · June 2026**

---

## What did you build?

LENS (Layered Evidence and Narrative Synthesizer) is a research tool for UX practitioners who run moderated think-aloud usability sessions. A researcher uploads or live-records a session, describes the study context, and receives a structured findings report: friction moments clustered by type, ranked by severity, tagged to Nielsen heuristics, and backed by timestamped transcript quotes. For multi-participant studies, LENS adds cross-session pattern detection and an executive summary. I built the analysis pipeline in Python—audio ingestion, local Whisper transcription, regex friction detection, optional Mistral enrichment via HuggingFace, and Markdown export—and deployed a polished web interface on Lovable for the class presentation and final submission. The tool targets a concrete HCD workflow: the hours between finishing recordings and delivering a readout, when teams either skip video evidence or burn time manually coding notes.

---

## What decisions did you make?

I chose a **research track** problem because the value proposition depends on analysis quality, not just interface polish. The MP2a declaration specified Cursor + Python + Streamlit because the pipeline requires real computation—Whisper, file ingestion, API calls—that no-code platforms cannot host natively. As the UI matured, I moved the **deployed experience to Lovable** while keeping the Python repo as the functional reference and submission code. That split let me demo a product-quality interface without abandoning the analysis logic I could test and version in Git. For data, I used my own p5.js documentation usability sessions rather than synthetic text, which forced honest handling of messy think-aloud speech. I scoped the MVP to **transcript-first friction detection** and documented vocal emotion, facial expression, and screen-state layers as roadmap stubs rather than shipping half-working multimodal claims. I also capped live recording at 200 MB with quality presets so browser capture would not silently fail on long sessions—a scope decision driven by real constraints, not feature ambition.

---

## What would you do differently?

First, I would **design the UI flow before wiring the pipeline**, not after. The Streamlit prototype accumulated UX debt—settings appearing in the wrong mode, recorder controls split across the page and an iframe—that took multiple redesign passes to fix. Starting with a single user journey storyboard (record → review → analyze → readout) would have saved rework. Second, I would **integrate one behavioral signal beyond transcript earlier**, even in lightweight form—for example, flagging long silences from audio waveform metadata alongside speech patterns. The transcript-only MVP proves the reporting structure, but the project’s core argument is that text-only synthesis misses what is visible and audible in the recording; demonstrating even one non-text signal would strengthen that claim in demo and submission.

---

## What does this work demonstrate?

**C3 (file handling):** `ingestion.py` converts mixed media formats to a analysis-ready audio path; the app validates participant IDs and persists live recordings safely. **C4 (APIs):** Whisper runs locally; Mistral runs through HuggingFace with `.env` configuration and graceful fallback when the key is absent. **C5 (analysis):** Two-pass friction detection, clustering, severity sorting, and cross-session aggregation in `language_analysis.py` and `cross_session.py` show analysis as design—not a single API prompt. **C6 (communication):** Finding cards, severity badges, evidence quotes, and Markdown export structure the output for stakeholder readouts; the Lovable UI makes that legible to non-builders. **C7 (judgment):** Roadmap modules remain stubs; README and `decisions.md` document limitations; the tool fails visibly rather than inventing findings when enrichment is unavailable. Together, the project shows I can scope a real HCD tool, implement a working analysis path, and communicate results in a form researchers would actually use.
