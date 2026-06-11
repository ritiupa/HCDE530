# HCDE 530 — Riti Upadhyay

University of Washington · Computational Concepts in HCDE

---

## Mini Project 2 — LENS (submission)

**LENS** (Layered Evidence and Narrative Synthesizer) turns moderated usability session recordings into structured findings reports for UX researchers.

### Live tool

**[LOVABLE_URL]** ← *replace with your public Lovable deployment URL*

### Repository

https://github.com/ritiupa/HCDE530

### Run locally (Python reference)

```powershell
cd "MP2\mp2a"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. Optional: add `HUGGINGFACE_API_KEY` to `.env` for Mistral finding enrichment.

### Who it is for

UX researchers and designers who conduct moderated think-aloud tests and need evidence-backed synthesis faster than manual video review—without losing quotes, severity, or heuristic context.

### Submission files

| File | Purpose |
|------|---------|
| [`mp2.md`](mp2.md) | Competency claims (C3–C7) |
| [`reflection.md`](reflection.md) | ~500-word project reflection |
| [`MP2/mp2/`](MP2/mp2/) | Submission folder + Lovable prompt |
| [`MP2/mp2a/`](MP2/mp2a/) | Complete Python code |

---

## Course work

Weekly assignments and notebooks are organized by week (`week 4/`, `week 6/`, `week 8/`, etc.).
