# Lovable build prompt — LENS (full spec)

Copy everything below the line into Lovable as your project prompt. Deployed app: https://evidencesynthesizer.lovable.app

---

## Project: LENS — Layered Evidence and Narrative Synthesizer

### Reference (existing prototype — match functionality, massively improve UI/UX)

**Do not clone the Streamlit UI.** Use it only as a functional reference for what the tool must do.

| Reference | URL |
|-----------|-----|
| **GitHub prototype (Python + Streamlit)** | https://github.com/ritiupa/HCDE530/tree/main/MP2/mp2a |
| **Deployed Lovable app** | https://evidencesynthesizer.lovable.app |
| **Local prototype** | Clone repo → `cd MP2/mp2a` → `pip install -r requirements.txt` → `streamlit run app.py` |

The Streamlit prototype works but has poor UX: confusing flow, settings in the wrong places, cramped layout, and a recorder that feels like a developer tool—not a research product. **Your job is a massive improvement in both UI and UX**: clearer information architecture, professional visual design, obvious next steps at every stage, and a recording experience that feels intentional and trustworthy.

---

## What LENS is

LENS helps **UX researchers and designers** turn moderated usability session recordings into structured findings reports—without spending hours manually reviewing video and coding notes.

**Core insight:** A transcript tells you what was said. Facial confusion and vocal stress only exist in the recording. Text-only AI synthesis misses them. LENS preserves evidence (quotes, timestamps, severity) and organizes findings by Nielsen heuristics.

**Audience:** UX researchers running moderated think-aloud tests under deadline pressure—especially when they would otherwise skip behavioral signals and rely on notes alone.

**Study context used in development:** p5.js reference documentation usability (participants tasked with finding functions like `ellipse()`).

---

## Non-negotiable UX requirements

1. **Massive UI upgrade** — Modern, calm, research-grade aesthetic (not generic AI slop). Think: Linear, Notion, or a polished research SaaS—not default Bootstrap or purple gradients.
2. **Massive UX upgrade** — One clear path per mode. User always knows: where they are, what to do next, and when they can analyze.
3. **First impression** — Landing/setup screen explains value in one sentence for someone who was not in class.
4. **Progressive disclosure** — Advanced settings (Whisper model, recording quality) hidden until relevant.
5. **Empty states** — Every screen has helpful empty states with guidance, not blank space.
6. **Mobile-aware layout** — Desktop-first (researchers use laptops), but responsive for tablet.
7. **Accessibility** — Sufficient contrast, focus states, labels on all inputs, keyboard-friendly controls.

---

## User flow (3 steps — show in header/stepper)

### Step 1 — Setup
- **Study context** (textarea): What was tested? Task given to participants?
- **Transcription model** (select, default “base”): tiny / base / small — with short helper text on speed vs accuracy
- **How to add sessions** (segmented control or tabs):
  - **Upload files** — MP4, MOV, WEBM, WAV, MP3, M4A; multiple files
  - **Record live** — webcam + mic in browser

### Step 2 — Add & record sessions

**Upload mode:**
- Drag-and-drop uploader
- For each file: Participant ID (P1, P2…), optional note, filename visible
- Clear “Remove” per file or “Clear all”
- Duplicate ID validation before analyze

**Record live mode (critical UX):**
- **Camera preview visible immediately** when user selects Record live—no scrolling, no extra clicks
- Controls in this order: **Start → Pause/Resume → Stop → Redo**
- Flow: Start recording → Pause optional → Stop → review playback in preview → Redo (discard) OR proceed to analyze
- **Recording quality** select appears ONLY in Record live mode (Standard / Balanced / Extended) with duration hints and 200 MB cap explained briefly
- Participant ID + note fields adjacent to recorder, not buried in sidebar
- After Stop: show success state (“P1 ready — 2:34 — 12 MB”) with playback review

### Step 3 — Analyze & report
- **Analyze** button prominent; disabled until ≥1 valid session
- Processing screen: honest step labels (Extract audio → Transcribe → Detect friction → Enrich → Generate report → Cross-session synthesis if multiple)
- Do not fake progress—show current session and step
- Report view:
  - **Study overview** tab: executive summary, metrics (sessions, friction moments, recurring patterns, critical count), participant list, cross-session highlights, recurring patterns
  - **Per-session tabs**: summary, severity-sorted findings (expandable cards), evidence quotes with timestamps, HMW + recommendation, full transcript with friction highlights
  - **Export**: Download study report as Markdown

---

## Analysis logic (implement or mock with clear structure)

If full backend is not feasible in Lovable, use Supabase Edge Functions or mock with realistic fixture data—but **structure the UI for real pipeline output**.

Pipeline per session:
1. Extract audio from video (or use audio directly)
2. Transcribe with Whisper (local in Python prototype; in Lovable: call external API or pre-processed transcript)
3. **Friction detection** — regex patterns on think-aloud phrases (“I’m not sure”, “where is”, “that’s confusing”, etc.)
4. **Enrichment** — Mistral via HuggingFace Inference API: severity (Critical/Major/Minor), Nielsen heuristic tag, finding title, description, HMW, recommendation
5. **Report generation** — cluster friction by type, sort by severity, generative structure (most frequent friction = lead finding)

Multi-session:
- Cross-session pattern aggregation
- Recurring patterns flagged when same friction type appears in 2+ sessions
- Executive summary across participants

**Graceful degradation:** If no API key, local pattern matching still runs; show badge “Template findings — add API key for enriched analysis.”

---

## Data model (suggested)

```typescript
Study {
  id, context, createdAt, whisperModel
  sessions: Session[]
  crossSession: { summary, patterns[], highlights[] }
}

Session {
  sessionId, participantNote, source: 'upload' | 'live'
  fileUrl?, durationSec, sizeBytes
  transcript: { start, text, frictionFlag }[]
  findings: Finding[]
  report: { summary, generatedAt, frictionCount }
}

Finding {
  title, description, severity, heuristic, occurrenceCount
  hmw, recommendation, evidence: string[]
}
```

---

## Visual design direction

- **Palette:** Dark or light mode (pick one, execute well)—neutral grays, single accent (blue or teal), semantic colors for severity (critical=red, major=amber, minor=green)
- **Typography:** Inter or similar; clear hierarchy (page title → section → body)
- **Components:** Cards for findings, pills for tags, avatar circles for participant IDs, quote blocks for evidence
- **Severity badges:** Always visible on findings; sort Critical → Major → Minor
- **No fake window chrome** (no macOS traffic lights, no faux OS metaphors)
- **Recorder:** Large 16:9 preview, control bar below, REC indicator + timer overlay, size meter

---

## Pages / routes

1. `/` — Setup + add sessions (combined or wizard)
2. `/processing` — Analysis in progress (auto-navigate)
3. `/report` — Results with tabs
4. Optional: `/about` — One paragraph on who this is for

---

## Copy tone

Professional, concise, for UX researchers—not developers. Example microcopy:
- “Describe what participants were trying to do.”
- “Camera ready — press Start when the participant begins the task.”
- “Review your recording, then analyze or redo.”
- “Findings are sorted by severity. Expand any card for evidence and recommendations.”

---

## What to keep from the prototype

From `MP2/mp2a` on GitHub:
- Multi-file upload + per-participant labeling
- Live browser recording with quality presets and size cap
- Cross-session synthesis for 2+ sessions
- Finding card structure (severity, heuristic, HMW, recommendation, evidence quotes)
- Markdown export structure
- Honest limitations section (transcript-first MVP; vocal/facial layers on roadmap)

---

## What to throw away from the prototype

- Split sidebar/main layout that hides the analyze action
- Record quality shown during upload mode
- Auto-saving recordings without explicit Stop → review step
- Generic Streamlit widget styling
- Developer-facing error dumps—replace with human-readable errors + retry

---

## Success criteria

A researcher who was **not in HCDE 530** can:
1. Open the Lovable URL
2. Understand what LENS does in 10 seconds
3. Record or upload a session without instructions
4. Get a readable findings report with evidence
5. Export or share results

**The UI/UX must feel like a product someone would demo to a design team—not a homework Streamlit app.**

---

## Submission placeholders (update after deploy)

- **Lovable live URL:** https://evidencesynthesizer.lovable.app
- **GitHub repo:** https://github.com/ritiupa/HCDE530
- **Lovable source:** `MP2/mp2b/`
- **Python reference:** `MP2/mp2a/`

---

## Optional stretch goals (if time)

- Side-by-side “transcript-only vs LENS” comparison view for demo
- Query box: “What confused participants about navigation?” over stored findings
- Participant video thumbnail on session cards

Build iteratively: nail Setup → Record → Analyze → Report flow with polished UI first, then enrich analysis integration.
