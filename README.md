# TrendByte

A tech trend intelligence system that tracks emerging technologies across developer communities, analyzes momentum, and generates daily reports with visual summaries.

## Overview

TrendByte collects data from multiple developer platforms, scores technologies by mention frequency and cross-source confirmation, detects rising stars before they peak, and produces branded visual cards for social media distribution.

Twitter/X posting is currently pending API credit activation. The system operates fully in collect, analyze, and report mode.

## Features

- Multi-source data collection (GitHub, Hacker News, Dev.to, Lobsters)
- Trend scoring with sentiment-boosted ranking
- Cross-source deduplication and name normalization
- Rising star detection with confidence scoring
- Database-backed dynamic category management with auto-suggestion
- Branded image generation (dark theme, glassmorphism cards)
- Sequential SQL migrations with version tracking
- Scheduled daily and weekly pipelines via GitHub Actions
- Local markdown report generation per run

## Architecture

```
src/
├── collectors/          Data ingestion (GitHub, HN, Dev.to, Lobsters, Reddit)
├── analysis/            Trend scoring, sentiment, rising star detection
├── bot/                 Twitter/X posting (pending activation)
├── rendering/           HTML/CSS templates rendered to PNG via Playwright
├── models/              Domain entities (dataclasses)
├── gateway.py           Database gateway (all PostgreSQL operations)
├── categorizer.py       DB-backed technology categorization
├── normalizer.py        Name normalization and alias resolution
├── analytics.py         Tweet engagement tracking
├── report.py            Local markdown report generation
├── config.py            Environment-based configuration
├── logger.py            Centralized logging
├── migrate.py           Sequential SQL migration runner
└── main.py              Pipeline orchestrator
```

## Requirements

- Python 3.12+
- PostgreSQL 16 (local Docker or Neon for production)
- Playwright (Chromium) for image rendering
- GitHub personal access token

## Setup

```bash
git clone https://github.com/Evrouin/trendbyte.git
cd trendbyte

pip install -e ".[dev]"
playwright install chromium

docker run -d --name trendbyte-db \
  -p 5432:5432 \
  -e POSTGRES_DB=trendbyte \
  -e POSTGRES_PASSWORD=postgres \
  postgres:16

cp .env.example .env
# Fill in GITHUB_TOKEN and DATABASE_URL

python -m src.migrate
```

## Usage

```bash
# Full pipeline (collect, analyze, save, generate image and report)
python -m src.main --no-post

# Dry run (no database writes, no posting)
python -m src.main --dry-run

# Full pipeline with Twitter posting (requires API credits)
python -m src.main

# Run migrations only
python -m src.migrate
```

## Configuration

All configuration is loaded from environment variables. See `.env.example` for the full list.

| Variable | Required | Description |
|----------|----------|-------------|
| GITHUB_TOKEN | Yes | GitHub personal access token |
| DATABASE_URL | Yes | PostgreSQL connection string |
| TWITTER_API_KEY | No | X API consumer key |
| TWITTER_API_SECRET | No | X API consumer secret |
| TWITTER_ACCESS_TOKEN | No | X API access token |
| TWITTER_ACCESS_SECRET | No | X API access token secret |
| TWITTER_BEARER_TOKEN | No | X API bearer token |
| REDDIT_CLIENT_ID | No | Reddit app client ID |
| REDDIT_CLIENT_SECRET | No | Reddit app client secret |

## Database

PostgreSQL with sequential numbered migrations in `migrations/`. Tables:

- `mentions` — raw data from collectors
- `trends` — scored and ranked technologies
- `predictions` — rising star detections with confidence
- `posts` — published tweet history
- `analytics` — tweet engagement metrics
- `categories` / `category_keywords` — dynamic categorization
- `schema_migrations` — migration version tracking

## Scheduling

GitHub Actions workflows run on cron:

- **Daily** (2 PM UTC): Collect, analyze, score, predict, generate report
- **Weekly** (Sunday 6 PM UTC): Aggregate weekly trends, generate comparison chart

Both workflows can be triggered manually via `workflow_dispatch`.

## Development

```bash
black src/ tests/
ruff check src/ tests/
mypy src/
pytest --cov=src
```

## Testing

30 unit tests covering:

- Trend scoring and ranking
- Name normalization and deduplication
- Sentiment analysis
- Rising star detection
- Twitter bot (mocked API)
- Retry logic and error handling
- Category classification

## Project Status

| Component | Status |
|-----------|--------|
| Data collection (4 sources) | Complete |
| Trend analysis and scoring | Complete |
| Rising star predictions | Complete |
| Image generation | Complete |
| Report generation | Complete |
| Database and migrations | Complete |
| GitHub Actions scheduling | Complete |
| Twitter/X posting | Pending (API credits required) |
| Reddit collector | Pending (API approval required) |

## License

MIT
