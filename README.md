# HCDE 530 — Riti Upadhyay

University of Washington · Computational Concepts in HCDE

---

## Mini Project 2 — LENS (submission)

**LENS** (Layered Evidence and Narrative Synthesizer) turns moderated usability session recordings into structured findings reports for UX researchers.

### Live tool

**https://evidencesynthesizer.lovable.app**

### Repository

https://github.com/ritiupa/HCDE530

### Who it is for

UX researchers and designers who run moderated think-aloud tests and need evidence-backed synthesis faster than manual video review.

### Code in this repo

| Folder | What it is |
|--------|------------|
| [`MP2/mp2b/`](MP2/mp2b/) | Deployed Lovable app (React + TanStack Start). Primary submission interface. |
| [`MP2/mp2a/`](MP2/mp2a/) | Python analysis pipeline + Streamlit prototype. Reference implementation. |

### Run locally

**Lovable app (mp2b):**

```powershell
cd "MP2\mp2b"
bun install
bun run dev
```

**Python pipeline (mp2a):**

```powershell
cd "MP2\mp2a"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Submission files

| File | Purpose |
|------|---------|
| [`mp2.md`](mp2.md) | Competency claims |
| [`reflection.md`](reflection.md) | Project reflection |
| [`MP2/mp2b/`](MP2/mp2b/) | Live app code + deployment readme |

---

## Course work

Weekly assignments and notebooks are in `week 4/`, `week 6/`, `week 8/`, and other week folders.
