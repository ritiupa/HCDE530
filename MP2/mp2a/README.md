# LENS -- Layered Evidence and Narrative Synthesizer

A Python tool that transforms raw usability session recordings into structured research findings. It transcribes audio with Whisper, identifies friction moments and hesitation patterns in the transcript, and generates a heuristic-tagged report organized by severity — so researchers spend time acting on findings instead of producing them.

**Built for:** HCDE 530 — Computational Concepts in HCDE, University of Washington  
**Track:** Research  
**Platform:** Cursor + Python + Streamlit

---

## What it does

1. Takes one or more usability session recordings (upload or **live browser recording**)
2. Extracts audio and transcribes each session locally using Whisper
3. Detects friction moments per participant: hesitation, confusion, navigation problems
4. Generates per-session findings plus a study-wide summary of recurring patterns
5. Outputs reports in Streamlit and as a downloadable Markdown file

### Live recording

Use the **Record live** tab to capture think-aloud sessions from your webcam. Three quality presets trade resolution for duration within a **200 MB cap**:

| Preset | Resolution | Approx. max duration |
|--------|------------|----------------------|
| Standard | 854×480 | ~15–20 min |
| Balanced | 640×480 | ~25–35 min |
| Extended | 480×360 | ~45–55 min |

Recording stops automatically at the size or time limit. Requires Chrome/Edge and camera permission. Live recordings are saved to `lens_output/incoming/` before analysis.

## How to run

**Install dependencies:**

```powershell
cd "MP2\mp2a"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Set your HuggingFace API key** (optional — local friction detection works without it):

```powershell
copy .env.example .env
# Edit .env and add your key from huggingface.co/settings/tokens
```

**Run the Streamlit app:**

```powershell
streamlit run app.py
```

Upload one or more session recordings, describe the study context, optionally label each participant, and click **Analyze sessions**.

## File structure

```
mp2a/
├── app.py                  # Streamlit interface
├── ingestion.py            # Extract audio from video
├── transcription.py        # Whisper transcription
├── language_analysis.py    # Friction detection and Mistral enrichment
├── report_generator.py     # Per-session structured findings
├── cross_session.py        # Cross-participant patterns and study summary
├── requirements.txt        # Dependencies
├── .env.example            # API key template
├── mp2.md                  # Competency claims for submission
└── README.md
```

### Work in progress (documented, not built yet)

These modules exist as stubs for the multi-modal research roadmap:

| Module | Planned capability |
|--------|-------------------|
| `emotion_audio.py` | wav2vec2 vocal emotion (stress, frustration) |
| `emotion_video.py` | GPT-4o facial expression analysis |
| `screen_analysis.py` | GPT-4o screen/UI state at friction moments |
| `synthesis.py` | ChromaDB cross-session clustering |

The fixture-based pipeline (`models.py`, `session_builder.py`, `fixtures/`) supports offline demo of the full LENS vision.

## Research roadmap

The current tool works on audio and transcripts. The full LENS vision includes behavioral signal layers that go beyond what a transcript can capture:

**Vocal emotion analysis (wav2vec2):** Detect stress, frustration, and engagement directly from the audio waveform — signals that exist in the voice but disappear in the transcript.

**Facial expression analysis (GPT-4o vision):** Analyze camera feed frames for confusion, frustration, and engagement signals that participants may not verbalize.

**Screen state analysis (GPT-4o vision):** Identify which page or UI state the participant is on at each friction moment, enabling findings to be tied to specific interface locations.

**Cross-session clustering (ChromaDB):** Store friction moments as semantic vectors and cluster them across multiple participant sessions to surface recurring patterns.

These layers are documented here as the research roadmap. The transcript pipeline is the foundation they build on.

---

*The core insight LENS is built on: a transcript tells you what was said. Facial confusion and vocal stress only exist in the recording. Current AI synthesis tools miss them entirely.*
