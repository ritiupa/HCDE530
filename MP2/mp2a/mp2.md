# Mini Project 2 -- Competency Claims

## What I built

LENS (Layered Evidence and Narrative Synthesizer) is a Python tool that takes a usability session recording, transcribes it with Whisper, detects friction moments using pattern matching and Mistral via the HuggingFace Inference API, and generates a structured findings report organized by severity and Nielsen heuristic. The interface is built in Streamlit. The report structure is generative — it is determined by what the analysis found, not a fixed template.

---

## C3 -- Data Cleaning and File Handling

The ingestion module handles multiple file formats (MP4, MOV, WAV, MP3, M4A) and extracts a standardized WAV file from any input using moviepy. Each session gets its own output folder organized by session ID. The transcription module handles the Whisper output format and normalizes timestamps. The report generator saves findings both as a structured Python dict for the Streamlit interface and as a Markdown file for download. Every module includes error handling for missing files, unsupported formats, and failed API calls.

## C4 -- APIs and Data Acquisition

The tool uses two external APIs. Whisper runs locally via the openai-whisper package — no API key, no cost per call. Mistral runs via the HuggingFace Inference API for friction enrichment and finding generation. The HuggingFace key is stored in a .env file and loaded with python-dotenv. The tool degrades gracefully when the API is unavailable — local pattern matching still runs and the report is generated from a template instead. Only friction-flagged segments are sent to Mistral, not the full transcript, to keep API usage low.

## C5 -- Data Analysis

The language analysis module runs two passes over the transcript. The first pass uses regular expression pattern matching against a curated list of friction phrases drawn from usability research on think-aloud protocols. The second pass sends flagged segments to Mistral for severity classification and heuristic tagging. The report generator clusters friction segments by type, sorts clusters by frequency, and generates one finding per cluster. The most frequent friction type becomes the lead finding — the report structure reflects the data rather than a fixed template.

## C6 -- Data Visualization and Communication

The Streamlit interface displays findings as expandable cards sorted by severity, with color-coded severity badges, occurrence counts, heuristic tags, and timestamped evidence quotes. The full transcript is shown with friction moments highlighted. The report is also exported as a downloadable Markdown file. The output format is designed to match the structure of a real usability readout: findings first, evidence second, recommendations third.

## C7 -- Critical Evaluation and Professional Judgment

The tool makes deliberate scope decisions. Local pattern matching is fast and free but misses subtler signals. Mistral enrichment adds severity and heuristic tags but requires an API key and can fail. The tool handles both gracefully. The friction pattern list is based on established usability research but is not exhaustive — the README documents this limitation. The research roadmap section in the README frames the behavioral signal layers (vocal emotion, facial expression, screen state, cross-session clustering) as the next phase, making the gap the tool fills explicit rather than overpromising on what the current version does.

---

## MP2a Declaration (revised per professor feedback)

**Problem:** UX researchers who record moderated usability sessions currently have to manually review video footage, transcribe notes, and code findings before a readout, which takes three or more hours per session and misses behavioral signals like facial confusion and vocal stress that only exist in the recording, not the transcript.

**Audience:** UX researchers and designers who conduct moderated usability testing and record sessions. Researchers working under tight deadlines benefit most because they are the ones most likely to skip behavioral evidence when time pressure forces them to rely on text-only synthesis.

**Data:** The tool takes video or audio files from usability sessions, transcribes them with Whisper, and uses the HuggingFace Inference API (Mistral) for friction analysis and report generation. It produces structured findings organized by friction type, severity, and Nielsen heuristic.

**Track:** Research track.

**Platform:** Cursor + Python + Streamlit.

**Rationale:** This project requires real computation — audio extraction, local speech-to-text with Whisper, and API-driven language analysis — that cannot be built in Lovable or Bolt. The report structure is generative rather than templated: it is determined by what the analysis found, so the output format reflects the content.
