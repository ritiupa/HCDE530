# MP2 — LENS (HCDE 530)

**Live app:** https://evidencesynthesizer.lovable.app  
**Repository:** https://github.com/ritiupa/HCDE530

| Folder | Role |
|--------|------|
| **`mp2b/`** | Deployed Lovable app (primary submission UI) |
| **`mp2a/`** | Python pipeline + Streamlit prototype (analysis reference) |

**Canvas deliverables (repo root):** [`mp2.md`](../mp2.md) · [`reflection.md`](../reflection.md) · [`README.md`](../README.md)

```powershell
# Live app (local)
cd "MP2\mp2b"
bun install
bun run dev

# Python reference
cd "MP2\mp2a"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
