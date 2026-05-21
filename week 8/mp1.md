# Mini Project 1 -- Competency Claims

**Deliverables:** `mp1_notebook.ipynb`, `fetch_cornell.py`, three CSVs, seven chart PNGs in `week 8/`

---

## C2 -- Code Literacy and Documentation

The fetch script and notebook are documented in plain English: what each block does and why. Shared helpers (`get_context_words`, `count_emotion`, `count_agency`, `save_chart`) live in one place so Q2 and Q3 do not duplicate logic. The setup cell pins the working directory to `week 8/` and prints the full path of every saved PNG. I documented why the tidy file uses one row per term mention, why ambiguous tokens like *call* were dropped from the tech lexicon, and why acting and tool verb lists were kept mutually exclusive.

## C3 -- Data Cleaning and File Handling

`fetch_cornell.py` downloads the Cornell corpus zip, parses the `+++$+++` format, joins dialogue lines to movie metadata on `movie_id`, filters unparseable years and pre-1930 films, tags technology terms, and writes `cornell_clean.csv`, `cornell_tidy.csv`, and `cornell_term_by_decade.csv`. The tidy file follows class tidy-data rules (one row per term per line). The summary file normalizes mentions per 1,000 lines per decade. I ran the fetch on my local machine when the class network returned 403 on the Cornell URL, then analyzed from the saved CSVs in the notebook.

## C5 -- Data Analysis with Pandas

**Q1:** `drop_duplicates` on `(decade, term, title)`, then `groupby` to count distinct films per term per decade; within-decade **share %** for stacked bars so films mentioning multiple terms are not double-counted.

**Q2:** For each tech term in each line, count positive and negative lexicon hits in a 6-word context window (unique words only); `groupby` sums per decade and term; ratio = positive / negative when negative > 0, else missing.

**Q3:** Count non-overlapping acting vs tool verbs in the same windows; `groupby` by decade; merge tech-line counts per decade; compute acting/tool ratio and rates per 1,000 tech-containing lines. Assistive analysis uses `Counter` for top acting verbs by era.

## C6 -- Data Visualization

Seven PNGs, chosen from the class chart framework:

| Chart | Type | Question |
|-------|------|----------|
| `chart1a_film_spread_stacked.png` | Stacked bar (share %) | Q1 spread |
| `chart1b_first_appearance.png` | Bar (assistive) | Q1 first decade |
| `chart2a_emotion_ratio_by_term.png` | Multi-line + reference at 1.0 | Q2 emotion ratio |
| `chart2b_emotion_volume_by_decade.png` | Grouped bar (assistive) | Q2 volume |
| `chart3a_agency_ratio.png` | Two lines (acting vs tool rates) | Q3 agency |
| `chart3a_agency_ratio_line.png` | Line + reference at 1.0 | Q3 ratio threshold |
| `chart3b_acting_verbs_by_decade.png` | Faceted horizontal bars | Q3 verb breakdown |

Titles state the argument; axes include units; interpretation cells note what a reader could misread (e.g. thin data behind ratios).

## C7 -- Critical Evaluation and Professional Judgment

I reframed Q2 and Q3 when full sentiment scoring and dependency parsing were out of course scope. I reported limitations: lexicon cannot handle negation or irony; verb lists are a proxy for grammatical agency; Q3’s aggregate ratio **never crosses 1** in this corpus—technology is still framed as a tool more often than an agent. I revised charts when the **logic** was wrong (Q1 stacked raw film counts), not only when styling was off. Section 5 below is the full process narrative.

---

## Section 5 -- Process: How I Arrived at This Mini Project

This section is the story behind the notebook, charts, and CSVs—not a repeat of the findings themselves. It explains what I tried, what broke, what I changed, and what I learned along the way.

### Where I started (and what I searched for)

Mini Project 1 did not begin with film dialogue. It began with the same thread I had already been working on for Assignment 4: **public curiosity about design trends**, measured through the Wikimedia Pageviews API. I had a working pipeline (`design_trends.py`) that pulled 90 days of traffic for terms like neumorphism, dark mode, and liquid glass, classified momentum, and even formatted output for an Arduino LCD in my physical computing class. That project was technically solid, but MP1a feedback pushed me toward something more original and more clearly tied to human-centered design—not just “what is trending on Wikipedia.”

I spent time searching for a dataset that could support a cultural story about technology, not only a marketing one. I looked at app review corpora (too product-specific), survey data I had already cleaned in Week 3 (too small for decade-level change), and briefly considered staying with Wikipedia but changing the question. None of those felt big enough for eight decades of cultural shift. The Cornell Movie Dialogs Corpus kept coming up because it is public, well documented, and covers ordinary conversational language from the 1930s through the 2010s—language people did not produce for researchers.

### The pivot to film dialogue

The pivot was intentional, not accidental. I asked myself: *before HCI existed as a field, what did people already assume about technology?* Film dialogue felt like the right source because it is **unself-conscious**. A character in a 1960s script talking about a telephone is not answering a usability survey; they are living in a story. That authenticity mattered more to me than another trends dashboard.

Once I committed to Cornell, I rewrote my three questions:

1. **Spread** — which technology terms show up across distinct films per decade (cultural penetration, not raw mention counts in one obsessed screenplay).
2. **Emotion** — whether positive vs negative emotional language near those terms shifts over time.
3. **Agency** — when dialogue starts treating technology as something that *acts* rather than something people *use*.

Feedback on the first draft of those questions was essential. Q2 originally aimed at full sentiment scoring; Q3 aimed at grammatical subject/object parsing via dependency analysis. Both are reasonable research questions and both are **out of scope** for a pandas-only course project. I reframed Q2 as a **positive-to-negative emotion word ratio** near each term using a curated lexicon, and Q3 as an **acting-verb vs tool-verb ratio** in a short context window—a proxy for agency, not a claim about syntax. That reframing kept the intellectual intent while making every step inspectable in code I could explain line by line.

### Building the data (multiple passes, not one download)

The data work was not a single clean import. `fetch_cornell.py` downloads the corpus zip from Cornell, parses the non-standard `+++$+++` format, joins dialogue lines to movie metadata on `movie_id`, filters broken years and pre-1930 films, tags technology terms, and writes three files:

- `cornell_clean.csv` — one row per dialogue line  
- `cornell_tidy.csv` — one row per term mention (tidy data from class)  
- `cornell_term_by_decade.csv` — normalized summary counts  

The first technical wall was environmental: in the class network, the Cornell URL sometimes returned **403 Forbidden**, so I could not treat “run in the notebook cloud” as reliable. I ran the fetch script **on my own machine**, saved the CSVs into `week 8/`, and treated the notebook as analysis-only on top of those files. That is a real process detail: my final assets depend on a local preprocessing step the grader cannot see unless I document it here.

I also aligned the technology lexicon between the fetch script and the notebook (for example, dropping **“call”** as a tech term because it matched everyday phrasing like “good call,” not devices). Small mismatches between files caused confusing counts until I forced the two lists to match.

### Analysis iterations the final charts do not show

The submitted charts look stable, but they are the result of several revisions:

**Q1 — Stacked bars and double counting.** My first stacked bar chart summed *distinct films per term* within each decade. That sounds right until you realize one film can mention both “phone” and “radio” in the same decade—so the stack implied a total “film count” that could not exist. A Cursor-assisted review flagged that logical flaw. I changed the main chart to **within-decade share (%)** among the top terms so each decade’s stack sums to 100%, and kept a separate assistive chart for **first decade of appearance** with raw film counts.

**Q2 — Lexicon noise and ratio edge cases.** Early emotion lists still contained high-frequency words like “like” and “good,” which appeared near everything and made every term look artificially positive. I expanded the lists, then **pruned** ambiguous tokens. I also stopped faking ratios when negative hits were zero (no more dividing by 0.01). The assistive volume chart exists because I learned the hard way that a ratio can look dramatic when it is built from three words.

**Q3 — Agency never crosses the threshold.** I honestly expected recent decades to show technology “taking action” more often. The data did not support that story in aggregate: **acting/tool ratio stays below 1** across the corpus—dialogue still frames tech as something people operate more than something that decides on its own. The AI did not invent that finding; it helped me **notice** that my chart code and my narrative were drifting apart (including a phase where communication vs computational categories split the lines, which I removed because it distracted from the main question). The final Q3 view uses two rate lines (acting vs tool verbs per 1,000 tech-containing lines) plus a ratio chart with a reference line at 1.0, and a faceted bar chart of top **acting** verbs by era so readers can see *what kind* of actions appear even when tool verbs dominate.

### Tools I used (and what required my judgment)

- **Cursor / Claude** — coding partner, debugging, and “second reader” on logic (stacked-bar flaw, lexicon overlap between acting and tool verbs, saving PNGs to the correct folder).  
- **Instructor feedback** — scope control on Q2/Q3.  
- **My own judgment** — choosing Cornell over Wikipedia for MP1, deciding which terms belong in the lexicon, interpreting Q3’s below-1 ratios honestly instead of forcing a dramatic “AI awakening” headline.

The most useful AI moments were not “write my entire project.” They were specific: “your stacked bars double-count films,” “your notebook term list does not match your fetch script,” “show volume behind emotion ratios.” The least useful moments were when generated code looked fine in the browser but **did not save charts** to `week 8/` because the working directory was wrong—I fixed that by adding a setup cell that changes directory to the notebook folder and a `save_chart()` helper that prints the full path of every PNG.

I did not lose the whole project, but I did lose **confidence in a single notebook version** at least once: I would run cells, see plots in the browser, and later discover the `.ipynb` on disk had reverted to an older analysis while PNGs on disk were from a different run. That is why I now run **Setup first**, then all analysis cells, then a final verification cell that lists every expected `chart*.png` in the folder.

### What I would do next

If I continued this project, I would tag science-fiction films separately to see whether agency language leads mainstream dialogue, add negation handling for emotion words (“not afraid” still counts *afraid* today), and experiment with dependency parsing on a small hand-checked sample—not because pandas proxies failed, but because they set a baseline I can defend in my competency claims.

### How this connects to my claims

- **C2 (Code literacy):** fetch script + notebook helpers documented in plain language.  
- **C3 (Cleaning):** custom parser, joins, tidy reshape, decade filters.  
- **C5 (Analysis):** groupby, dedupe, ratios, merges—each tied to a question.  
- **C6 (Visualization):** chart types chosen from the class framework, assistive charts for spread, volume, and verbs.  
- **C7 (Judgment):** reframed questions when methods were too ambitious; reported limitations; revised charts when the logic was wrong, not when the picture was merely ugly.

That is the honest arc: **trends API → cultural corpus → simpler proxies → iterative fixing → charts and claims I can explain without hiding the messy middle.**
