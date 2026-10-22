# State AI Policy Tracker (India)

A pipeline and dashboard tracking state-level artificial intelligence policy, MoUs, governance deployments, and institutional initiatives across key Indian states.

Built for the SAFL Data Analysis and Engineering work test.

## Overview

Instead of trying to scrape all 28 states with noisy or partial results, I focused on 6 states that drive the majority of tech policy and governance adoption in India:
- Karnataka (Bengaluru tech hub, state AI policy)
- Telangana (Hyderabad AI City, Global AI Summit)
- Tamil Nadu (digitization, manufacturing & electronics AI MoUs)
- Maharashtra (Mumbai/Pune commercial tech & governance initiatives)
- Gujarat (GIFT City AI cluster, tech partnerships)
- Uttar Pradesh (large-scale public administration, skilling like 'AI for All', agricultural/policing pilot deployments)

## Pipeline Architecture

The pipeline runs sequentially in five stages:

1. `fetch.py`
   Queries Google News RSS across combinations of the target states and specific governance action keywords (`"AI policy"`, `"AI mission"`, `"AI MoU"`, `"AI task force"`, `"AI centre of excellence"`, `"artificial intelligence government"`). Drops raw records into `data/raw.csv`.

2. `normalize.py`
   Normalizes state variations (e.g. `UP`, `Uttar-Pradesh` -> `Uttar Pradesh`). Parses dates into standard ISO `YYYY-MM-DD` and records `date_precision` (`day` vs approximate). Strips trailing publisher attribution strings from titles.

3. `classify.py`
   Filters out noise (editorials, opinion pieces, surveys, and non-news social platforms like Twitter, Reddit, LinkedIn). Disambiguates state assignment by checking if the headline explicitly mentions a different state before trusting the search query state. Categorizes each action into a 6-tier taxonomy:
   - MoU/Partnership
   - Task force/CoE
   - Policy/Mission
   - Budget
   - Regulation/Ethics
   - Governance deployment
   Assigns a lifecycle status: `announced`, `planned`, `approved`, `signed`, or `cancelled`.

4. `dedupe.py`
   Deduplicates identical events reported across multiple media outlets using:
   - Entity anchors (company names, universities, scheme names).
   - Fuzzy title matching (`token_set_ratio >= 80`) within a 7-day window.
   Records that look like near-misses (same state, category, status within 2 days) are flagged in `possible_dup_of` so they can be spot-checked. Outputs to `data/final.csv`.

5. `server.py`
   A lightweight Python HTTP server that serves the static dashboard (`docs/index.html`), exposes API endpoints (`/api/status`, `/api/data`), and handles real-time pipeline execution via Server-Sent Events (SSE).

## How to Run

1. Install dependencies:
   ```bash
   pip install feedparser pandas rapidfuzz python-dateutil
   ```

2. Run the server and dashboard:
   ```bash
   python server.py
   ```
   Open `http://localhost:8000` in your browser.

3. To run the data pipeline manually from terminal:
   ```bash
   python fetch.py
   python normalize.py
   python classify.py
   python dedupe.py
   ```

## Dataset Schema

The output in `data/final.csv` contains:
- `state`: Canonical state name.
- `title`: Clean headline.
- `date`: ISO date (`YYYY-MM-DD`).
- `date_precision`: `day` or estimated.
- `source_name`: Publishing news outlet.
- `source_url`: Link to article / Google News record.
- `summary`: One-line summary (clean headline).
- `category`: Taxonomy classification.
- `status`: Action status (announced / planned / approved / signed / cancelled).
- `duplicate_count`: Number of media outlets reporting this event.
- `also_reported_by`: Semicolon-separated list of secondary outlets.
- `possible_dup_of`: Flagged near-duplicate title for human spot-check.
- `state_basis`: Whether state was inferred from headline text (`title`) or search query (`query`).

## Assumptions and Known Limitations

- Headlines as Summaries: I chose to use the cleaned headline as the one-line summary rather than scraping full article bodies, avoiding paywalls and unverified scraper fragments.
- Date Boundaries: Only events from `2024-01-01` onwards are retained to keep the tracker focused on current, active initiatives.
- Google News Redirects: Article links are Google News RSS permalinks; while they preserve provenance, they occasionally introduce redirect delays.
- Near-Miss Duplicates: Fuzzy matching threshold is set at 80. Edge cases with radically different headlines about the same event require the `possible_dup_of` flag and manual review.
