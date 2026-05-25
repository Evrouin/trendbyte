# TrendByte

A tech trend intelligence system that tracks emerging technologies across developer communities, analyzes momentum with ML/NLP, and presents insights via a real-time dashboard.

- Dashboard: https://trendbytedashboard.evrouin.com
- API: https://trendbyte.evrouin.com
- Frontend repo: https://github.com/Evrouin/trendbyte-dashboard

## Features

- 7 collectors (GitHub, Hacker News, Reddit, Dev.to, Lobsters, Stack Overflow, Mastodon)
- spaCy NER + whitelist-based tech name extraction
- VADER sentiment analysis on post titles
- Trend scoring with time decay, star normalization, and source diversity bonus
- Rising star predictor with confidence scoring
- ML trend predictor (gradient descent, weekly auto-training)
- Category classifier (TF-IDF + Logistic Regression)
- Lifecycle detection (rising, peaking, stable, declining)
- Correlation detection (Pearson correlation on weekly patterns)
- Content generation (daily signal, weekly recap, monthly report) with Twitter publishing
- Auto data cleanup pipeline (weekly)
- HMAC request signing security
- 10 categories (ai, web, devops, languages, databases, security, mobile, gaming, crypto, tools)
- Database-backed dynamic categories with auto-keyword suggestion
- Display name normalization (150+ canonical tech names)
- FastAPI with rate-limited REST endpoints and in-memory caching
- HTTP cache headers for CDN/browser caching
- Scheduled daily/weekly/training pipelines via GitHub Actions
- Dependency scanning workflow
- SonarCloud quality gate integration

## Architecture

```
src/
├── collectors/          Data ingestion (7 sources)
├── analysis/            Scoring, sentiment (VADER), rising stars, predictor, training
├── bot/                 Twitter/X posting
├── rendering/           HTML to PNG via Playwright + Jinja2
├── models/              Domain entities (dataclasses)
├── gateway.py           Database gateway (PostgreSQL)
├── ner.py               spaCy NER + entity ruler
├── stopwords.py         KNOWN_TECH whitelist
├── normalizer.py        Name normalization + aliases
├── display_names.py     Canonical display names (150+ entries)
├── categorizer.py       DB-backed categorization
├── config.py            Environment-based configuration
├── migrate.py           Sequential SQL migration runner
└── main.py              Pipeline orchestrator

api/
├── __init__.py          FastAPI app (CORS, rate limiting, cache middleware)
├── cache.py             In-memory TTL cache decorator
├── db.py                Connection helper
└── routes/              trends, predictions, categories, stats, news
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/trends` | Top trends (filterable by days, limit, category) |
| `GET /api/trends/{name}` | Trend detail with score history and related trends |
| `GET /api/trends/{name}/lifecycle` | Trend lifecycle phase (rising, peaking, stable, declining) |
| `GET /api/trends/by-category` | Trends grouped by category |
| `GET /api/predictions` | Rising star predictions |
| `GET /api/correlations` | Top correlated tech pairs |
| `GET /api/categories` | All categories with keywords |
| `GET /api/categories/predict?text=` | ML-predicted category for text |
| `GET /api/stats` | System stats (totals, sources, last run) |
| `GET /api/news` | Recent posts with source and date range filters |
| `GET /api/content/daily` | Daily signal content |
| `GET /api/content/weekly` | Weekly recap content |
| `GET /api/content/monthly` | Monthly report content |

## ML Features

- **Trend Scoring** — time-decayed, star-normalized, source-diversity-boosted scoring
- **VADER Sentiment** — social media optimized sentiment analysis on post titles
- **Rising Star Predictor** — gradient descent model, auto-trains weekly from labeled outcomes
- **Lifecycle Detection** — classifies trends as rising, peaking, stable, or declining via linear regression
- **Category Classifier** — TF-IDF + Logistic Regression predicts category from post text
- **Correlation Detection** — finds techs that trend together using Pearson correlation on weekly patterns

## Scoring Algorithm

Each mention is scored using:

1. Star normalization — source-specific multipliers (Reddit 0.02, HN 0.33, GitHub 0.1)
2. Time decay — 7-day half-life, recent mentions weighted exponentially higher
3. Source diversity bonus — 2^n where n is the number of distinct sources
4. Frequency bonus — log2(mentions + 1) rewards consistent discussion
5. Sentiment multiplier — VADER compound score provides up to 20% boost

Growth is calculated as velocity change: mention rate in the recent half vs the older half.

## Setup

```bash
git clone https://github.com/Evrouin/trendbyte.git
cd trendbyte

pip install -e ".[dev]"
pip install -r requirements.txt
python -m spacy download en_core_web_sm

cp .env.example .env
python -m src.migrate
```

## Usage

```bash
python -m src.main --no-post     # Full pipeline without Twitter
python -m src.main --dry-run     # No DB writes, no posting
python -m src.backfill           # Backfill historical data
python -m src.migrate            # Run migrations
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string |
| GITHUB_TOKEN | Yes | GitHub personal access token |
| REDDIT_CLIENT_ID | Yes | Reddit API client ID |
| REDDIT_CLIENT_SECRET | Yes | Reddit API client secret |
| REDDIT_USER_AGENT | Yes | Reddit API user agent |
| TWITTER_API_KEY | No | X API consumer key |
| TWITTER_API_SECRET | No | X API consumer secret |
| TWITTER_ACCESS_TOKEN | No | X API access token |
| TWITTER_ACCESS_SECRET | No | X API access token secret |

## Scheduling

| Workflow | Schedule | Description |
|----------|----------|-------------|
| Daily | 2 PM UTC | Collect, analyze, score, predict |
| Weekly | Sun 6 PM UTC | Aggregate weekly trends |
| Cleanup | Sun 8 PM UTC | Auto data cleanup pipeline |
| Training | Mon 12 PM UTC | Retrain ML predictor |
| Dependency Scanning | On schedule | Check for vulnerable dependencies |
| SonarCloud | On push | Code quality scan |

## Development

```bash
ruff check src/ api/ tests/
ruff format src/ api/ tests/
mypy src/ api/
pytest tests/ -v
```

## Tech Stack

- Python 3.12, FastAPI, psycopg 3, spaCy, VADER, Playwright
- PostgreSQL (Neon)
- GitHub Actions, Render (deployment)
- SonarCloud (quality)

## License

MIT
