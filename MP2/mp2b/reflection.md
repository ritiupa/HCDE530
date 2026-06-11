# MP2 Reflection - LENS

**Riti Upadhyay · HCDE 530 · June 2026**

**Live tool:** https://evidencesynthesizer.lovable.app  
**Repository:** https://github.com/ritiupa/HCDE530

---

## What did you build?

LENS is a usability synthesis tool for UX researchers. You describe the study, upload or record a think-aloud session, and get a findings report with severity tags, heuristic labels, evidence quotes, and recommendations. For multiple participants, it also surfaces cross-session patterns.

I built two versions in Git. `MP2/mp2a/` is the Python pipeline: audio ingestion, Whisper transcription, friction detection, and report generation. `MP2/mp2b/` is the Lovable app I presented and submitted. That is the public tool at evidencesynthesizer.lovable.app. The core idea is simple. A transcript is not the whole session. Confusion and stress often show up in the recording, not in the text alone.

---

## What decisions did you make?

I started MP2 on the research track because the value is in analysis quality, not just a nice screen. My first declaration listed four ML pipelines, a vector database, and a query layer. Professor feedback was direct. That scope fit a team over months, not one person in a few weeks. I listened and cut the build to a transcript pipeline that still tests the main argument.

I built the analysis logic in Python and Streamlit first because Whisper and file handling need real code. Streamlit got the pipeline working, but the UX was hard to demo. Settings showed up in the wrong places. The recorder felt like a developer widget. I moved the public interface to Lovable and kept Python in the repo as the reference implementation.

I used my own p5.js documentation usability sessions as data. That forced me to handle messy real speech, not clean sample text. I capped live recording at 200 MB with quality presets so long sessions fail predictably instead of silently corrupting. I documented vocal emotion and facial analysis as future work in the README instead of shipping half-built modules.

---

## What would you do differently?

I would storyboard the full user flow before writing pipeline code. Record, review, analyze, readout. I spent extra weeks fixing layout and flow problems that a paper sketch would have caught. I would also add one non-text signal earlier, even something small like pause length from audio, so the demo supports the multimodal argument beyond transcript quotes.

---

## What does this work demonstrate?

**C3:** Mixed media ingestion in Python and session handling in the Lovable upload and recorder components. **C4:** Public APIs in early assignments; Whisper, HuggingFace, MediaRecorder, and the Lovable AI gateway in MP2. **C5:** Deliberate aggregations in MP1b and two-pass friction analysis in LENS. **C6:** Chart choices in MP1b and finding cards, study overview, and Markdown export in the report UI. **C7:** Scope cuts after instructor feedback, honest README limitations, and splitting Python logic from Lovable presentation. Together this shows I can scope a real HCD tool, implement it, and communicate results in a form researchers can use.
