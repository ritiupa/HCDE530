# HCDE 530 Final Reflection

**Riti Upadhyay · June 2026**

**Repository:**

https://github.com/ritiupa/HCDE530

This reflection is a case for what my submitted work shows, not a list of deliverables. Each claim below points to a file, commit, or deployment you can verify in the repo.

---

## C5 - Data Analysis

**Evidence:** In Week 8 (`week 8/mp1_notebook.ipynb`, Q1 block), I counted how many *distinct films* mention each technology term per decade. I used `drop_duplicates` on `(decade, term, title)`, then `groupby(["decade", "term"])` to sum `distinct_films`. My first stacked bar chart summed those counts within a decade, which double-counted films that mention more than one term. I fixed the logic in the same notebook: the main chart (`chart1a_film_spread_stacked.png`) plots each term's **share %** within the decade so the stack sums to 100%. The interpretation cell under that chart explains why raw counts were misleading.

For Q3 in the same notebook, I compared acting verbs (technology as subject) to tool verbs (people using technology) in a 6-word window around tech terms, then `groupby("decade")` to sum hits and compute `ratio = acting / tool`. The printed table and `chart3a_agency_ratio_line.png` show the ratio **never crosses 1.0** across decades. I reported that honestly instead of forcing a "technology takes over" story. That analysis ships in commit `cc8aa0d` with the notebook and seven PNGs in `week 8/`.

For MP2, I carried the same habit of inspectable analysis into LENS. `MP2/mp2a/language_analysis.py` runs a local regex pass on transcript segments (`FRICTION_PATTERNS`, lines 22-43), then optional Mistral enrichment through HuggingFace. The deployed Lovable app mirrors that logic in `MP2/mp2b/src/lib/friction.ts` (uncertainty, search-confusion, and expectation-mismatch patterns mapped to Nielsen heuristics). `MP2/mp2a/cross_session.py` clusters findings across participants when more than one session is uploaded. The live tool at https://evidencesynthesizer.lovable.app ships in commit `9cf1412`.

**What this demonstrates:** I can define a question, choose an aggregation that matches it, catch when the math answers a different question than I intended, and extend that discipline from a pandas notebook to a production analysis path. Being able to do this means I can defend findings under review, not just produce output that looks plausible in a demo.

---

## C6 - Data Visualization and Communication

**Evidence:** MP1b required charts chosen from the course framework, not default plots. I saved seven PNGs to `week 8/` with titles that state the argument: `chart2a_emotion_ratio_by_term.png` is a multi-line chart with a reference line at 1.0 for positive-to-negative emotion ratios by term over decades; `chart3a_agency_ratio.png` plots acting and tool verb *rates* per 1,000 tech-containing lines so readers see volume behind the ratio. I added assistive charts when the main metric was easy to misread: `chart2b_emotion_volume_by_decade.png` shows raw positive and negative hit counts because thin denominators made ratios look dramatic; `chart3b_acting_verbs_by_decade.png` faceted bars show *which* acting verbs appear even when tool verbs dominate. Each chart has a markdown interpretation cell in `mp1_notebook.ipynb` calling out what a reader could misread.

For MP2, the audience is a UX researcher under deadline, not a grader running a notebook. Communication moved to the report UI: `MP2/mp2b/src/routes/report.tsx` leads with an executive summary; `MP2/mp2b/src/components/FindingCard.tsx` sorts findings by severity with heuristic tags, evidence quotes, and recommendations; `MP2/mp2b/src/lib/export.ts` exports Markdown for handoff to a team doc. The Python Streamlit prototype in `MP2/mp2a/app.py` kept the same information hierarchy while I iterated on layout.

**What this demonstrates:** I match visual and interface choices to the decision a reader needs to make. In MP1 that decision is "is this trend real or an artifact of how I counted?" In LENS it is "what should we fix first?" Knowing how to do this shows I can translate analysis into action, which is the point of HCD data work.

---

## C7 - Critical Evaluation and Professional Judgment

**Evidence:** Scope control appears across the quarter. My MP2a declaration described four ML pipelines, a vector database, and a query layer. Instructor feedback said that scope fit a team over months. I cut to a transcript-first MVP, documented vocal emotion and facial analysis as roadmap items in `MP2/mp2a/README.md` and `MP2/mp2a/decisions.md`, and shipped what I could defend. I built analysis in Python first (`MP2/mp2a/`) because Whisper and file ingestion need real code; when Streamlit could not support a credible demo flow (recorder UX, settings in the wrong step), I moved the public interface to Lovable (`MP2/mp2b/`) without pretending the deferred modalities were finished.

The same judgment shows up earlier. Week 4 `week 4/design_trends.py` documents why I used the Wikimedia Pageviews API instead of an unofficial Google Trends scraper that would break before a deadline. Week 3 commit `ef1abc9` adds `parse_experience_years()` so rows like R009 with "fifteen" in `experience_years` return `None` instead of crashing the script. MP1 Section 5 in `week 8/mp1.md` narrates when I reframed Q2 and Q3 after feedback: full sentiment scoring and dependency parsing were out of course scope, so I used lexicon ratios and verb proxies I could explain line by line.

**What this demonstrates:** I can narrow a project to what evidence and time actually support, document what is not built, and change platforms when the research story and the demo story diverge. That is professional judgment: knowing what to ship, what to defer, and what to say out loud about both.

---

## One thing I learned outside the stated objectives

The syllabus does not list "trust but verify your own artifacts" as a learning goal, but that habit is what kept my work honest this quarter.

The clearest example is MP1. I would run notebook cells, see charts in the browser, and later find PNGs on disk from a different run or a working directory pointed at the wrong folder. The fix was procedural: a setup cell that `chdir`s to `week 8/`, a `save_chart()` helper that prints the full path of every PNG, and a final verification cell that lists expected `chart*.png` files. I learned to treat "it looked right in the session" as insufficient. The graded artifact is what is committed.

A second habit was asking whether code answers the question I posed, before polishing presentation. The stacked-bar double-count in Q1 and the below-1.0 agency ratio in Q3 were not styling problems. Cursor helped me spot the logic flaw; I still had to decide whether to revise the chart or revise the claim. That split, mechanical debugging vs. judgment about what to conclude, was not on the syllabus, but it is how I will work on real HCD projects where stakeholders see the chart before they read the notebook.

---

**Summary:** Across MP1b and LENS, my strongest evidence sits in C5 (aggregations I can defend), C6 (charts and report UI that foreground decisions), and C7 (scope cuts and honest limitations). The repo, commit history, and live deployment are the backing exhibits for this case.
