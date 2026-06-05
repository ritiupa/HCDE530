# MP2 — LENS (HCDE 530)

Mini Project 2 lives in **`mp2a/`**.

- **App & pipeline:** `mp2a/app.py`, `ingestion.py`, `transcription.py`, `language_analysis.py`, `report_generator.py`
- **Submission docs:** `mp2a/mp2.md`, `mp2a/README.md`
- **Agent memory:** `mp2a/project_notes.md`, `mp2a/decisions.md`

```powershell
cd "MP2\mp2a"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The transcript pipeline is implemented. Multi-modal behavioral layers (vocal emotion, facial expression, ChromaDB clustering) are documented in the README research roadmap and exist as stubs for future work.
