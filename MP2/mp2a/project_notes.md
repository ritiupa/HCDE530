# LENS — project notes (agent memory across sessions)

Read this file first when continuing MP2 work. Update after each meaningful session.

**Course:** HCDE 530 SP26 · **Project:** MP2 — LENS  
**Location:** `HCDE 530/MP2/lens/`  
**Study:** p5.js reference documentation usability (3–5 real sessions, mixed input types)

---

## What we are building

**LENS** (Layered Evidence and Narrative Synthesizer) — multi-modal UX synthesis so researchers keep face + voice + language evidence, not transcript-only AI summaries.

**Related project — BLOOM (HCDE 539):** same multi-modal *concept* (face, voice, words); different output (kinetic sculpture). BLOOM code lives in **`Documents/Xeno/bloom/`** — not a shared repo or submodule with LENS.

---

## Decisions (stable)

| Date | Decision |
|------|----------|
| 2026-05 | Pivot from Wikipedia design-trends (A4) to Cornell-style cultural data → **film dialogue was MP1**; MP2 is **LENS + real usability recordings**. |
| 2026-05 | **Flexible inputs:** any combo of video / audio / transcript per session; skip missing channels; report confidence honestly. |
| 2026-05 | **Build core pipeline on fixtures first;** wire `ingestion.py` + extractors when testing real media. |
| 2026-05 | Repo lives under **`HCDE 530/MP2/lens/`** only (not `Documents/MP2`). |
| 2026-05 | **LLM (Mistral):** default **HuggingFace Inference API** (`HUGGINGFACE_API_KEY`); keep one code path + rule-based fallback. Ollama/other endpoints only if added later behind a single env flag. |
| 2026-05 | **BLOOM:** separate **Xeno** workspace; conceptual parity, no copied engine. |
| 2026-05 | June 3 demo: same session → transcript-only vs LENS → “what text-only missed.” |

---

## What works (verified)

- `python scripts/run_pipeline_fixture.py` — P1 multimodal + P2 transcript-only → report MD
- `streamlit run app.py` — **Run demo (fixtures)** loads pipeline
- ChromaDB optional — rule-based clustering fallback if not installed

---

## What to try next

- [ ] `pip install chromadb sentence-transformers` and re-run clustering
- [ ] Paste real transcripts into Upload → `session_builder` path (before video ingestion)
- [ ] Wire `ingestion.py` when recording formats are cataloged
- [ ] HuggingFace + OpenAI keys in `.env` for Mistral report + vision
- [ ] Streamlit Cloud deploy (Week 3)

---

## What did not work / watch-outs

- Browser `fig.show()` without `save_chart()` — PNGs saved to wrong cwd (fixed in MP1 week 8; LENS uses explicit `save_chart` pattern in rules)
- Notebook/code version drift — commit before big agent refactors
- Do not stack distinct-film counts in Q1-style charts without normalizing (lesson from MP1)

---

## Session log

### 2026-05 — Scaffold

- Created `models`, `session_builder`, `synthesis`, `report_generator`, `query_engine`, `export`, `app.py`, fixtures, stubs for ingestion/modality extractors
- `.cursorrules` + this file for agent continuity

---

## Prompts that worked

- “Read `project_notes.md` and `MP2/lens/.cursorrules` first, then …”
- One module per request aligned with build order in `.cursorrules`
- “Explain what `session_builder.py` does before changing it”
