import io
import re
import zipfile
from pathlib import Path

import pandas as pd
import requests

# The Cornell Movie Dialogs Corpus is hosted at Cornell University.
# This script downloads it, parses it, and saves three CSV files:
# 1. cornell_clean.csv -- one row per dialogue line (raw cleaned data)
# 2. cornell_tidy.csv -- tidy format, one row per term mention per line
# 3. cornell_term_by_decade.csv -- summary, one row per term per decade
#
# Emotion and agency analysis live in mp1_notebook.ipynb.
# This script only detects tech terms in each line and exports the CSVs.
CORNELL_ZIP_URL = "https://www.cs.cornell.edu/~cristian/data/cornell_movie_dialogs_corpus.zip"

OUTPUT_DIR = Path(__file__).parent

# Technology terms split into two categories for Q3 analysis.
# "call" excluded: matches everyday phrasing ("good call", "call them"), not technology.
COMM_TERMS = ["phone", "telephone", "radio", "television", "tv", "signal"]
COMP_TERMS = ["computer", "internet", "online", "email", "app", "algorithm",
              "ai", "robot", "digital", "machine", "screen", "device", "network", "data"]
ALL_TERMS = COMM_TERMS + COMP_TERMS

# Used for has_tech, tidy rows, and Q3 position columns. Emotion-keyword Q2 uses the
# same token list in the notebook (FOCUS_TERMS) so line tagging matches analysis.

print("Downloading Cornell Movie Dialogs Corpus...")
response = requests.get(CORNELL_ZIP_URL, timeout=60)

if response.status_code != 200:
    print(f"Download failed with status {response.status_code}")
    exit()

print(f"Downloaded {len(response.content) / 1_000_000:.1f} MB. Parsing...")

with zipfile.ZipFile(io.BytesIO(response.content)) as z:
    all_files = z.namelist()
    lines_path = next(f for f in all_files if "movie_lines.txt" in f)
    meta_path = next(f for f in all_files if "movie_titles_metadata.txt" in f)
    raw_lines = z.read(lines_path).decode("latin-1").strip().split("\n")
    raw_meta = z.read(meta_path).decode("latin-1").strip().split("\n")

print(f"Loaded {len(raw_lines):,} dialogue lines and {len(raw_meta):,} movie entries.")

# Parse movie metadata into a lookup dictionary.
movie_info = {}
for row in raw_meta:
    parts = [p.strip() for p in row.split("+++$+++")]
    if len(parts) < 6:
        continue
    movie_id = parts[0].strip()
    title = parts[1].strip()
    year_raw = parts[2].strip()
    year_match = re.search(r"\d{4}", year_raw)
    year = int(year_match.group()) if year_match else None
    genres = parts[5].strip()
    movie_info[movie_id] = {"title": title, "year": year, "genres": genres}

# Parse each dialogue line and join with movie metadata.
records = []
for row in raw_lines:
    parts = [p.strip() for p in row.split("+++$+++")]
    if len(parts) < 5:
        continue
    movie_id = parts[2].strip()
    text = parts[4].strip()
    if not text or movie_id not in movie_info:
        continue
    info = movie_info[movie_id]
    if info["year"] is None or info["year"] < 1930:
        continue

    year = info["year"]
    decade = (year // 10) * 10
    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text_lower)
    found_terms = [t for t in ALL_TERMS if re.search(r"\b" + t + r"\b", text_lower)]
    has_tech = len(found_terms) > 0

    first_position = None
    first_category = None
    for term in found_terms:
        m = re.search(r"\b" + term + r"\b", text_lower)
        if m:
            first_position = m.start() / max(len(text_lower), 1)
            first_category = "communication" if term in COMM_TERMS else "computational"
            break

    records.append({
        "movie_id": movie_id,
        "title": info["title"],
        "year": year,
        "decade": decade,
        "genres": info["genres"],
        "text": text,
        "has_tech": has_tech,
        "tech_terms_found": ", ".join(found_terms),
        "first_tech_position": first_position,
        "first_tech_category": first_category,
        "line_length": len(words),
    })

df = pd.DataFrame(records)
print(f"Parsed {len(df):,} lines across {df['decade'].nunique()} decades.")
print(f"Lines with tech terms: {df['has_tech'].sum():,}")

# CSV 1 -- full cleaned dataset, one row per dialogue line.
clean_path = OUTPUT_DIR / "cornell_clean.csv"
df.to_csv(clean_path, index=False, encoding="utf-8")
print(f"Saved: {clean_path}")

# CSV 2 -- tidy format, one row per term mention per dialogue line.
# This follows the tidy data principle from class:
# every variable is a column, every observation is a row.
# term and category become their own columns
# instead of being spread across a single comma-joined string.
tidy_rows = []
for _, row in df[df["has_tech"]].iterrows():
    for term in row["tech_terms_found"].split(", "):
        term = term.strip()
        if not term:
            continue
        tidy_rows.append({
            "decade": row["decade"],
            "year": row["year"],
            "title": row["title"],
            "term": term,
            "category": "communication" if term in COMM_TERMS else "computational",
            "line_text": row["text"],
            "first_tech_position": row["first_tech_position"],
            "first_tech_category": row["first_tech_category"],
        })

tidy_df = pd.DataFrame(tidy_rows)
tidy_path = OUTPUT_DIR / "cornell_tidy.csv"
tidy_df.to_csv(tidy_path, index=False, encoding="utf-8")
print(f"Saved: {tidy_path}")

# CSV 3 -- summary for charts, normalized per 1000 lines per decade.
lines_per_decade = df.groupby("decade").size().reset_index(name="total_lines")
term_counts = tidy_df.groupby(["decade", "term", "category"]).size().reset_index(name="count")
term_counts = term_counts.merge(lines_per_decade, on="decade")
term_counts["mentions_per_1000"] = (term_counts["count"] / term_counts["total_lines"]) * 1000

summary_path = OUTPUT_DIR / "cornell_term_by_decade.csv"
term_counts.to_csv(summary_path, index=False, encoding="utf-8")
print(f"Saved: {summary_path}")

print("\nAll files ready. Run the notebook next.")
