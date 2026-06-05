# HCDE 530 — Task tracker

Track work **per week folder** (`week 2` … `week N`). Update this file when you start, finish, or defer a task. Cursor agents should read and update it per [`.cursorrules`](.cursorrules).

**Last updated:** 2026-05-20

---

## How to use

| Symbol | Meaning |
|--------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[-]` | Skipped / N/A (note why in *Notes*) |

1. Add a **Week N** section when a new `week N/` folder appears (copy the template at the bottom).
2. List concrete deliverables (scripts, notebooks, CSVs, charts, `weekN.md`, competency claims).
3. Set status as you go; keep *Notes* for blockers, due dates, or links to assignment prompts.
4. Do not delete completed rows—strike through or mark `[x]` for a record of what shipped.

---

## Summary

| Week | Folder | Focus (short) | Overall |
|------|--------|-----------------|---------|
| 2 | `week 2/` | Dashboard + demo scripts | `[x]` Complete |
| 3 | `week 3/` | Survey cleaning + buggy/fixed analysis | `[x]` Complete |
| 4 | `week 4/` | Wikipedia design trends API | `[x]` Complete |
| 5 | `week 5/` | Pandas demos + 5b trends notebook | `[x]` Complete |
| 6 | `week 6/` | Cornell corpus fetch + MP1 charts | `[x]` Complete |
| 7 | `week 7/` | Figma forum feedback analysis | `[~]` In progress |
| 8 | `week 8/` | Mini Project 1 (Cornell) | `[x]` Complete |
| MP2 | `MP2/lens/` | LENS multi-modal synthesis | `[~]` In progress |

---

## Week 2 — `week 2/`

| Status | Task | Deliverable(s) |
|--------|------|----------------|
| `[x]` | HTML dashboard from survey data | `dashboard.html` |
| `[x]` | Word-count demo script | `demo_word_count.py`, `demo_responses.csv` |
| `[x]` | Competency claims | `Week 2 Competency Claims.md` |

**Notes:** Standalone dashboard week; no ongoing tasks unless instructor reopens.

---

## Week 3 — `week 3/`

| Status | Task | Deliverable(s) |
|--------|------|----------------|
| `[x]` | Clean messy survey CSV | `clean_responses.py`, `responses_cleaned.csv` |
| `[x]` | Role counts | `count_roles.py`, `role_counts.csv` |
| `[x]` | Fixed vs buggy analysis | `week3_analysis_fixed.py`, `week3_analysis_buggy.py` |
| `[x]` | Competency claims | `Week 3 Competency Claims.md` |

**Notes:** —

---

## Week 4 — `week 4/`

| Status | Task | Deliverable(s) |
|--------|------|----------------|
| `[x]` | Fetch Wikipedia pageviews for design trends | `design_trends.py` |
| `[x]` | Raw + summary CSVs | `design_trends_raw.csv`, `design_trends.csv` |
| `[x]` | Competency / reflection writeup | `week4.md` |

**Notes:** Arduino LCD fields (`lcd_line1`, `lcd_line2`) live in script output if still using physical computing integration.

---

## Week 5 — `week 5/` (+ `week 5/week 5b/`)

| Status | Task | Deliverable(s) |
|--------|------|----------------|
| `[x]` | Pandas intro notebook | `week5_pandas_demo.ipynb` |
| `[x]` | Merge demo | `week5_merge_demo.ipynb` |
| `[x]` | Design trends pipeline (5b) | `week 5b/design_trends.py`, CSVs |
| `[x]` | Trends analysis notebook | `week 5b/week5b_design_trends_analysis.ipynb` |
| `[x]` | Competency claims | `week 5b/week5.md` |

**Notes:** Optional Arduino serial: `ENABLE_ARDUINO_SERIAL=1`, port `COM4` (see `.cursorrules`).

---

## Week 6 — `week 6/`

| Status | Task | Deliverable(s) |
|--------|------|----------------|
| `[x]` | Fetch + clean Cornell corpus | `fetch_cornell.py`, `cornell_*.csv` |
| `[x]` | Analysis notebook (Q1–Q3, emotion lexicon in notebook) | `week6_cornell_analysis.ipynb` |
| `[x]` | Charts + justifications | `chart*.png`, `week6.md` |

**Notes:** Regenerating `cornell_clean.csv` can take several minutes.

---

## Week 7 — `week 7/`

| Status | Task | Deliverable(s) |
|--------|------|----------------|
| `[x]` | Source data | `week7_figma_feedback.csv` |
| `[x]` | Card 2 — severity analysis (3 problems + ratings) | `severity_feedback.md` |
| `[ ]` | Card 1 | *(add filename when assigned)* |
| `[ ]` | Card 3 | *(add filename when assigned)* |
| `[ ]` | Card 4 | *(add filename when assigned)* |
| `[ ]` | Card 5 | *(add filename when assigned)* |
| `[ ]` | Week 7 competency / summary doc | `week7.md` *(if required)* |

**Notes:** `severity_feedback.md` references **Card 2 of 5**; fill in cards 1, 3–5 from the assignment sheet.

---

## Week 8 — `week 8/`

| Status | Task | Deliverable(s) |
|--------|------|----------------|
| `[x]` | Cornell fetch script + CSVs | `fetch_cornell.py`, `cornell_*.csv` |
| `[x]` | MP1 analysis notebook (Q1–Q3 + charts) | `mp1_notebook.ipynb` |
| `[x]` | Chart PNGs (7 files) | `chart1a`–`chart3b`, `chart3a_agency_ratio_line` |
| `[x]` | Competency claims + Section 5 process | `mp1.md` |
| `[x]` | Re-run analysis | `python run_notebook.py` |

**Notes:** Q3 ratio stays below 1 in this corpus (tech still framed as tool more than agent).

---

## Template — new week

Copy when you create `week N/`:

```markdown
## Week N — `week N/`

| Status | Task | Deliverable(s) |
|--------|------|----------------|
| `[ ]` | | |
| `[ ]` | | |

**Notes:** Assignment due: ___ | Data source: ___
```

Also add a row to the **Summary** table at the top.

---

## Repo-wide (optional)

| Status | Task | Where |
|--------|------|-------|
| `[x]` | Workspace-wide Cursor rules | `.cursorrules` |
| `[x]` | Task tracker (this file) | `TASK_TRACKER.md` |
