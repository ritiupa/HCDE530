# LENS — design decisions log

Short entries only. Details live in `project_notes.md` and code.

## Input model

- **Any combination** of video, audio, transcript per participant.
- `InputCapabilities` drives which analyzers run; never fabricate missing modalities.
- **Confidence** at signal, event, cluster, and session level.

## Analysis proxies (course scope)

- Q2 emotion: positive/negative lexicon in context window (not full sentiment model).
- Q3 agency: acting verbs vs tool verbs near tech terms (not dependency parsing).
- **Multi-modal convergence:** ≥2 channels with friction signal at same alignment window.

## Report / UI

- **Generative structure:** dominant cluster vs balanced sections depends on evidence.
- **Query layer:** answers from stored session/report data, not model memory.
- **Text-only gap** section required in every report.

## LLM access (keep simple)

- **Default:** HuggingFace Inference API for Mistral (`report_generator.py`, `query_engine.py`).
- **Fallback:** rule-based text when no key or API error (fixtures/demo always work offline).
- **Optional later:** `LLM_PROVIDER=ollama` or similar — one thin wrapper, not multiple parallel implementations.

## BLOOM / Xeno (HCDE 539)

- BLOOM is **not** a git submodule or copied `lens/` code.
- Lives in `Documents/Xeno/bloom/`; analyzes multi-modal experience **for sculpture mapping**, not UX reports.

## Deferred

- `ingestion.py` and GPT-4o vision batching until fixture pipeline signed off.
- Video layout adapters (PiP vs dual track vs separate files) — decide during media testing.

## Submission (MP2)

Include in GitHub: `.cursorrules`, `project_notes.md`, `decisions.md`, `README.md`, full `lens/` code, no `.env` or raw recordings.
