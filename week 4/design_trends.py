import csv
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import requests
from requests.exceptions import RequestException, Timeout

# ---------------------------------------------------------------------------
# WHY THIS API
# The Wikimedia Pageviews REST API returns how many times any Wikipedia article
# was viewed on a given day. It is free, official, and requires no API key.
# When people are curious about a design trend, they look it up on Wikipedia --
# so daily page traffic is a clean proxy for public interest over time.
# We chose this over pytrends (Google Trends) because pytrends is an unofficial
# scraper that breaks frequently and would be unreliable for a deadline.
# ---------------------------------------------------------------------------
WIKIPEDIA_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"

# The MediaWiki API lets us query Wikipedia's category system programmatically.
# We use it to discover HCI and UX article titles automatically instead of
# hardcoding a fixed list that would need manual updates.
MEDIAWIKI_API = "https://en.wikipedia.org/w/api.php"

# These four Wikipedia categories cover the HCI and UX topic space.
# Articles from all four are combined into one candidate pool.
CATEGORIES = [
    "Category:Human\u2013computer_interaction",
    "Category:User_interfaces",
    "Category:Interaction_design",
    "Category:User_experience",
]

# How many candidate articles to discover before ranking by traffic.
# We pull more than we need so the ranking step can find the genuinely popular ones.
DISCOVERY_POOL_SIZE = 50

# After fetching traffic data, keep only the top N articles by total views.
TOP_RANKED = 50

# How many articles to include in the detailed summary CSV output.
TOP_DETAIL_ROWS = 5

# How many days of pageview history to pull.
# 90 days gives enough data to compare a recent 30-day window against a prior 30-day window,
# which is how we calculate momentum (Rising / Peaked-Stable / Fading).
DAYS_TO_ANALYZE = 90

# Used to estimate monthly views from a daily average.
# This is the exact average days per month across a full calendar year.
AVG_DAYS_PER_MONTH = 30.436875

# Network settings for API calls.
REQUEST_TIMEOUT_SECONDS = 15   # how long to wait before giving up on one request
MAX_TRANSPORT_RETRIES = 4      # how many consecutive timeouts before skipping an article
MAX_HTTP_ROUNDS = 12           # maximum total retry attempts per article
HTTP_429_BASE_WAIT = 2.0       # starting wait time (seconds) when the API rate-limits us
REQUEST_DELAY_SECONDS = 0.65   # pause between consecutive API calls to stay within rate limits

# Identifies our script to Wikipedia's servers -- required by their usage guidelines.
USER_AGENT = "HCDE530-student-project/1.0"


def title_for_pageviews_api(title: str) -> str:
    # The Pageviews API requires spaces in article titles to be underscores in the URL.
    # Example: "Dark mode" becomes "Dark_mode" in the request path.
    return title.replace(" ", "_")


def iter_category_members(cmtitle: str):
    # Generator that yields one article title at a time from a Wikipedia category.
    # It handles pagination automatically using the cmcontinue token --
    # Wikipedia returns a maximum of 500 articles per request, so large categories
    # need multiple calls to retrieve all members.
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmnamespace": "0",   # namespace 0 = main article space only (excludes talk pages etc.)
            "cmtype": "page",
            "cmlimit": "500",     # maximum allowed by the API per request
            "format": "json",
        }
        if cmcontinue:
            # If a previous response returned a continuation token,
            # include it to fetch the next page of results.
            params["cmcontinue"] = cmcontinue
        try:
            response = requests.get(
                MEDIAWIKI_API,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except RequestException as err:
            print(f"Category API error for {cmtitle!r}: {err}")
            return

        data = response.json()
        members = data.get("query", {}).get("categorymembers", [])
        for m in members:
            yield m["title"]

        # Check if there are more pages of results.
        # Wikipedia includes a "continue" block with a cmcontinue key when more results exist.
        cont = data.get("continue", {})
        if "cmcontinue" in cont:
            cmcontinue = cont["cmcontinue"]
        else:
            break   # no more pages -- we have all articles in this category


def discover_ux_candidate_titles(limit: int) -> list[str]:
    # Walks through each HCI/UX category and collects article titles until we reach the limit.
    # A "seen" set prevents duplicates across categories -- the same article can appear
    # in multiple categories (for example, "Usability" might be in both User_interfaces
    # and Human-computer_interaction).
    # Titles containing "/" are sub-pages (like "Usability/Overview") and are skipped
    # because they are rarely standalone articles worth tracking.
    titles: list[str] = []
    seen: set[str] = set()
    for cmtitle in CATEGORIES:
        for title in iter_category_members(cmtitle):
            if title in seen:
                continue
            if "/" in title:
                continue
            seen.add(title)
            titles.append(title)
            if len(titles) >= limit:
                return titles
    return titles


def get_pageviews(article, start_date, end_date):
    """
    Fetch daily Wikipedia pageview counts for one article title.
    Returns a list of (date, view_count) tuples, or an empty list on failure.
    Retries automatically on rate limiting (429) and server errors (5xx).
    """
    # Format dates as YYYYMMDD strings -- the format the Pageviews API URL requires.
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # Build the full API URL.
    # "all-access" combines desktop and mobile views.
    # "user" excludes automated bot traffic so we only count human readers.
    url = f"{WIKIPEDIA_API}/en.wikipedia/all-access/user/{article}/daily/{start_str}/{end_str}"

    transport_failures = 0  # tracks consecutive timeout failures
    last_status = None      # stores the last HTTP status code for the error message

    for round_i in range(MAX_HTTP_ROUNDS):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except Timeout:
            transport_failures += 1
            if transport_failures >= MAX_TRANSPORT_RETRIES:
                # Too many timeouts in a row -- skip this article entirely.
                print(f"  Timeout limit for '{article}' -- skipping.")
                return []
            # Exponential backoff: each retry waits longer than the last.
            # min() caps the wait at 45 seconds to avoid indefinite delays.
            wait = min(45.0, HTTP_429_BASE_WAIT * (2 ** min(round_i, 5)))
            print(f"  Timeout for '{article}', sleeping {wait:.1f}s (retry)...")
            time.sleep(wait)
            continue
        except RequestException as err:
            print(f"  Network error for '{article}': {err}")
            return []

        last_status = response.status_code

        if response.status_code == 200:
            # Success -- parse the JSON response and extract date + view count pairs.
            data = response.json()
            results = []
            for item in data.get("items", []):
                # Timestamps come back in "20260115T000000" format.
                # We only need the first 8 characters (the YYYYMMDD date).
                date_str = item["timestamp"][:8]
                date = datetime.strptime(date_str, "%Y%m%d")
                views = item["views"]
                results.append((date, views))
            return results

        if response.status_code == 429:
            # Rate limited -- the API is telling us to slow down.
            # We wait with exponential backoff before retrying.
            wait = min(60.0, HTTP_429_BASE_WAIT * (2 ** min(round_i, 5)))
            print(f"  Rate limited (429) for '{article}', sleeping {wait:.1f}s...")
            time.sleep(wait)
            continue

        if response.status_code in (404, 410):
            # Article does not exist or has been deleted -- no point retrying.
            return []

        if response.status_code in (500, 502, 503, 504):
            # Server-side errors are usually temporary -- retry with backoff.
            wait = min(45.0, 2.0 * (2 ** min(round_i, 4)))
            print(f"  HTTP {response.status_code} for '{article}', sleeping {wait:.1f}s...")
            time.sleep(wait)
            continue

        # Any other unexpected status code -- log and give up on this article.
        print(f"  Could not fetch data for '{article}' (status {response.status_code})")
        return []

    print(f"  Gave up on '{article}' after {MAX_HTTP_ROUNDS} rounds (last HTTP {last_status})")
    return []


def momentum_detail(views_list):
    """
    Classify an article's traffic trend based on recent vs prior 30-day averages.
    Returns: (label, pct_change, recent_avg, prior_avg)
    """
    # We need at least 60 days of data to compare two 30-day windows.
    if len(views_list) < 60:
        return "Insufficient data", None, None, None

    # Sort by date to make sure we are comparing the correct time windows.
    sorted_views = sorted(views_list, key=lambda x: x[0])

    # Split into the most recent 30 days and the 30 days before that.
    recent = sorted_views[-30:]
    prior = sorted_views[-60:-30]

    # Calculate average daily views for each 30-day window.
    recent_avg = sum(v for _, v in recent) / len(recent)
    prior_avg = sum(v for _, v in prior) / len(prior)

    # Guard against division by zero if the prior period had no traffic.
    if prior_avg == 0:
        return "Insufficient data", None, round(recent_avg, 2), round(prior_avg, 2)

    # Percentage change: positive = growing, negative = declining.
    change = (recent_avg - prior_avg) / prior_avg
    pct = round(change * 100, 1)

    # Classify: more than 10% growth = Rising, more than 10% decline = Fading,
    # anything in between = Peaked / Stable.
    if change > 0.10:
        label = "Rising"
    elif change < -0.10:
        label = "Fading"
    else:
        label = "Peaked / Stable"

    return label, pct, round(recent_avg, 2), round(prior_avg, 2)


def trend_status_slug(momentum_label: str) -> str:
    # Convert the human-readable momentum label into a URL-safe slug
    # for use as a filterable column value in the summary CSV.
    return {
        "Rising": "rising",
        "Fading": "fading",
        "Peaked / Stable": "peaked_or_stable",
        "Insufficient data": "insufficient_data",
    }.get(momentum_label, "unknown")


def build_summary_row(
    display_title: str,
    views: list,
    rank: int,
    window_start: datetime,
    window_end: datetime,
) -> dict:
    # Compute all summary statistics for one article and return them as a dictionary.
    # This dictionary maps directly to one row in the summary CSV.
    momentum, pct_chg, recent_avg, prior_avg = momentum_detail(views)

    total_views = sum(v for _, v in views)
    days_n = len(views)   # actual days of data received (may be less than 90 if data is missing)
    avg_day = total_views / days_n if days_n else 0.0

    # Estimated monthly views: multiply the daily average by the average days per month.
    est_month = avg_day * AVG_DAYS_PER_MONTH

    # Find the single day with the highest view count.
    peak_day = max(views, key=lambda x: x[1])

    # Peak-to-mean ratio: how much the peak day stands out from the daily average.
    # A very high ratio (e.g. 10x) suggests a viral event rather than organic growth.
    peak_ratio = round(peak_day[1] / avg_day, 2) if avg_day else ""

    return {
        "rank": rank,
        "trend": display_title,
        "window_start": window_start.strftime("%Y-%m-%d"),
        "window_end": window_end.strftime("%Y-%m-%d"),
        "days_with_data": days_n,
        "total_views_in_window": total_views,
        "avg_views_per_day": round(avg_day, 2),
        "est_views_per_month": round(est_month, 1),
        "peak_date": peak_day[0].strftime("%Y-%m-%d"),
        "peak_views": peak_day[1],
        "peak_to_mean_daily_ratio": peak_ratio,
        "recent_30d_avg_views": recent_avg if recent_avg is not None else "",
        "prior_30d_avg_views": prior_avg if prior_avg is not None else "",
        "pct_change_recent_vs_prior_30d": pct_chg if pct_chg is not None else "",
        "momentum": momentum,
        "trend_status": trend_status_slug(momentum),
        # Pre-formatted strings for the Arduino LCD display (16 character max per line).
        # These feed directly into the physical computing project LCD sketch.
        "lcd_line1": display_title[:16],
        "lcd_line2": f"Status: {momentum}"[:16],
    }


def build_raw_and_monthly_rows(scored, window_start: datetime, window_end: datetime):
    """
    Build the full raw dataset with one row per article per day,
    plus one monthly rollup row per article per calendar month.
    Both granularities go into the same raw CSV file.
    """
    ws = window_start.strftime("%Y-%m-%d")
    we = window_end.strftime("%Y-%m-%d")
    daily_rows = []

    # defaultdict(int) lets us accumulate monthly totals without checking
    # whether a key already exists -- missing keys automatically start at 0.
    month_totals: dict[tuple[str, str], int] = defaultdict(int)

    for display_title, views, _total in scored:
        for dt, v in views:
            day_s = dt.strftime("%Y-%m-%d")
            ym = dt.strftime("%Y-%m")   # calendar month key e.g. "2026-03"
            month_totals[(display_title, ym)] += v
            daily_rows.append({
                "granularity": "daily",
                "calendar_period": day_s,
                "article_title": display_title,
                "views": v,
                "window_start": ws,
                "window_end": we,
            })

    # Build monthly rollup rows from the totals we accumulated above.
    monthly_rows = []
    for (title, ym), total in sorted(month_totals.items()):
        monthly_rows.append({
            "granularity": "monthly",
            "calendar_period": ym,
            "article_title": title,
            "views": total,
            "window_start": ws,
            "window_end": we,
        })

    # Sort both sets by article title then date so the CSV is easy to read and filter.
    daily_rows.sort(key=lambda r: (r["article_title"], r["calendar_period"]))
    monthly_rows.sort(key=lambda r: (r["article_title"], r["calendar_period"]))

    # Return daily rows first, then monthly -- both go into the same output file.
    return daily_rows + monthly_rows


# ---------------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------------

# Set the analysis window: today going back DAYS_TO_ANALYZE days.
# We zero out the time component so the boundary is clean midnight-to-midnight.
end_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
start_date = end_date - timedelta(days=DAYS_TO_ANALYZE)

# Resolve output file paths relative to this script's location.
# This ensures the CSVs are always saved next to the script regardless of
# where it is run from.
script_dir = Path(__file__).resolve().parent
raw_csv_path = script_dir / "design_trends_raw.csv"
top_csv_path = script_dir / "design_trends.csv"

print(
    f"Discovering up to {DISCOVERY_POOL_SIZE} UX-related article titles from "
    f"{len(CATEGORIES)} Wikipedia categories...\n"
)

# Step 1: Discover candidate article titles from Wikipedia's HCI/UX categories.
candidates = discover_ux_candidate_titles(DISCOVERY_POOL_SIZE)
print(f"Found {len(candidates)} candidates. Fetching {DAYS_TO_ANALYZE}-day pageviews...\n")

# Step 2: Fetch daily pageview data for each candidate article.
# We store (title, views_list, total_views) so we can sort by popularity later.
scored: list[tuple[str, list, int]] = []
for i, display_title in enumerate(candidates, start=1):
    # Convert the display title to underscore format required by the Pageviews API URL.
    article = title_for_pageviews_api(display_title)
    print(f"[{i}/{len(candidates)}] {display_title}")
    views = get_pageviews(article, start_date, end_date)
    if views:
        total_views = sum(v for _, v in views)
        scored.append((display_title, views, total_views))
    # Pause between requests to stay within Wikipedia's rate limits.
    time.sleep(REQUEST_DELAY_SECONDS)

# Step 3: Sort all articles by total views (highest first) and keep only the top N.
scored.sort(key=lambda x: -x[2])
top_ranked = scored[:TOP_RANKED]

# Step 4: Save the raw CSV -- daily and monthly rows for all discovered articles.
# This is the full dataset for further analysis or visualization in the notebook.
raw_rows = build_raw_and_monthly_rows(scored, start_date, end_date)
raw_fieldnames = ["granularity", "calendar_period", "article_title", "views", "window_start", "window_end"]

with open(raw_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=raw_fieldnames)
    writer.writeheader()
    writer.writerows(raw_rows)

print(f"Saved {len(raw_rows)} raw rows (daily + monthly) to {raw_csv_path}")

# Step 5: Save the summary CSV -- one row per top article with all computed statistics.
# This is what the Week 5 analysis notebook loads for pandas operations and charts.
top_detail = top_ranked[:TOP_DETAIL_ROWS]
summary_rows = [
    build_summary_row(title, views, rank, start_date, end_date)
    for rank, (title, views, _) in enumerate(top_detail, start=1)
]

summary_fieldnames = [
    "rank", "trend", "window_start", "window_end", "days_with_data",
    "total_views_in_window", "avg_views_per_day", "est_views_per_month",
    "peak_date", "peak_views", "peak_to_mean_daily_ratio",
    "recent_30d_avg_views", "prior_30d_avg_views", "pct_change_recent_vs_prior_30d",
    "momentum", "trend_status", "lcd_line1", "lcd_line2",
]

with open(top_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=summary_fieldnames)
    writer.writeheader()
    writer.writerows(summary_rows)

print(f"Saved top {len(summary_rows)} trends to {top_csv_path}")

# Step 6: Print the LCD strings so they can be copied into the Arduino sketch.
# Each article produces two lines of 16 characters max -- the physical display constraint.
print("\nLCD display strings for Arduino sketch (top 5):")
for r in summary_rows:
    print(f"  Line 1: '{r['lcd_line1']}'")
    print(f"  Line 2: '{r['lcd_line2']}'")