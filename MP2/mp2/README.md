# Mini Project 2 — LENS (formal submission)

**Course:** HCDE 530 — Computational Concepts in HCDE, University of Washington  
**Project:** LENS — Layered Evidence and Narrative Synthesizer  
**Presented:** June 3, 2026

---

## Live tool

**Lovable deployment:** `[LOVABLE_URL]` ← *replace with your public Lovable URL before Canvas submission*

**GitHub repository:** https://github.com/ritiupa/HCDE530

---

## What it does

LENS helps UX researchers turn moderated usability session recordings into structured findings reports. It transcribes think-aloud sessions, detects friction moments in the transcript, enriches findings with severity and Nielsen heuristic tags, and produces a research readout—with evidence quotes and timestamps—so researchers act on insights instead of spending hours manually reviewing video.

**Built for:** UX researchers and designers who conduct moderated usability testing and need faster, evidence-backed synthesis under deadline pressure.

**Not built for:** Automated UI scoring without human context, or teams that only need raw transcription.

---

## How to use it

### Web app (primary deliverable)

Open the Lovable deployment URL above in Chrome or Edge. No install required.

1. Enter study context and choose upload or live record
2. Add one or more participant sessions
3. Click **Analyze**
4. Review findings and export Markdown

### Reference implementation (Python)

The original pipeline and analysis logic live in [`../mp2a/`](../mp2a/). To run locally:

```powershell
cd "MP2\mp2a"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # optional: HuggingFace key for Mistral enrichment
streamlit run app.py
```

Open http://localhost:8501. This version uses local Whisper transcription and optional HuggingFace API for finding enrichment.

---

## Repository contents (Canvas checklist)

| Item | Location |
|------|----------|
| Complete code | `MP2/mp2a/` (Python pipeline + Streamlit prototype) + Lovable project (linked above) |
| Competency claims | [`../../mp2.md`](../../mp2.md) (repo root) |
| Reflection (~500 words) | [`../../reflection.md`](../../reflection.md) (repo root) |
| Lovable rebuild prompt | [`LOVABLE_PROMPT.md`](LOVABLE_PROMPT.md) |

---

## Architecture

- **Frontend (Lovable):** Polished UX for setup, recording, upload, processing, and report views
- **Backend reference (`mp2a/`):** `ingestion.py`, `transcription.py`, `language_analysis.py`, `report_generator.py`, `cross_session.py`
- **APIs:** Whisper (local), HuggingFace Inference API / Mistral (optional enrichment)

---

## Known limitations

- Current MVP is **transcript-first**; vocal emotion and facial expression layers are documented on the research roadmap (`mp2a/README.md`)
- Live recording requires browser camera permission; 200 MB size cap applies
- Without a HuggingFace API key, friction detection uses local patterns and template finding text

---

*Replace `[LOVABLE_URL]` in this file, root `README.md`, and `mp2.md` before submitting to Canvas.*
