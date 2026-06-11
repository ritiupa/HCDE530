# LENS — Deployed app (Lovable)

**Live URL:** https://evidencesynthesizer.lovable.app

**Course:** HCDE 530 · University of Washington  
**Project:** LENS — Layered Evidence and Narrative Synthesizer  
**Presented:** June 3, 2026

---

## What it does

LENS helps UX researchers turn moderated usability sessions into structured findings reports. Describe the study, add recordings by upload or live camera, run analysis, and review findings with severity tags, heuristic labels, evidence quotes, and exportable Markdown.

**Built for:** UX researchers who need faster, evidence-backed synthesis after think-aloud sessions.

---

## Use the live app

Open **https://evidencesynthesizer.lovable.app** in Chrome or Edge.

1. Enter study context
2. Upload files or record live (Start, Pause, Stop, Redo)
3. Click Analyze
4. Review the report and export

No install required for the deployed version.

---

## Run locally

```powershell
cd "MP2\mp2b"
bun install
bun run dev
```

Optional: copy `.env.example` to `.env` if you need Lovable AI gateway keys for enriched analysis.

---

## Project structure

```
mp2b/
├── src/
│   ├── routes/           # Setup, processing, report pages
│   ├── components/       # Recorder, uploader, finding cards
│   └── lib/              # Friction patterns, analysis, export
├── package.json
└── README.md
```

---

## Relationship to mp2a

`MP2/mp2a/` holds the Python reference pipeline (Whisper, ingestion, cross-session logic). This Lovable app is the polished interface submitted for MP2. Friction regex patterns in `src/lib/friction.ts` mirror the think-aloud patterns in `mp2a/language_analysis.py`.

---

## Repository

https://github.com/ritiupa/HCDE530
