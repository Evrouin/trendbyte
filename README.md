# TrendByte

A tech trend intelligence system that tracks emerging technologies across developer communities, analyzes momentum with ML/NLP, and presents insights via a real-time dashboard.

🔗 **Dashboard:** https://trendbytedashboard.evrouin.com  
🔗 **API:** https://trendbyte.evrouin.com  
🔗 **Frontend repo:** https://github.com/Evrouin/trendbyte-dashboard

## Features

- Multi-source data collection (GitHub, Hacker News, Dev.to, Lobsters)
- spaCy NER + whitelist-based tech name extraction
- Trend scoring with sentiment boost and cross-source deduplication
- Rising star detection with confidence scoring
- ML trend predictor (gradient descent, weekly auto-training)
- Influence scoring (cross-platform spread velocity)
- Database-backed dynamic categories with auto-keyword suggestion
- Branded image generation (dark glassmorphism cards via Playwright)
- FastAPI with rate-limited REST endpoints
- Scheduled daily/weekly pipelines via GitHub Actions
- SonarCloud quality gate integration

## Architecture

```
src/
├── collectors/          Data ingestion (GitHub, HN, Dev.to, Lobsters)
├── analysis/            Scoring, sentiment, rising stars, predictor, training
├── bot/                 Twitter/X posting (pending API credits)
├── rendering/           HTML→PNG via Playwright + Jinja2
├── models/              Domain entities (dataclasses)
├── gateway.py           Database gateway (PostgreSQL)
├── ner.py               spaCy NER + entity ruler
├── stopwords.py         KNOWN_TECH whitelist
├── normalizer.py        Name normalization + aliases
├── display_names.py     Canonical display names
├── categorizer.py       DB-backed categorization
├── report.py            Markdown report generation
├── config.py            Environment-based configuration
├── migrate.py           Sequential SQL migration runner
└── main.py              Pipeline orchestrator

api/
├── __init__.py          FastAPI app (CORS, rate limiting)
├── db.py                Connection helper
└── routes/              trends, predictions, categories, reports, stats, news
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/trends` | Top trends (filterable by days, limit) |
| `GET /api/trends/{name}` | Trend detail with score history |
| `GET /api/trends/by-category` | Trends grouped by category |
| `GET /api/predictions` | Rising star predictions |
| `GET /api/categories` | All categories with keywords |
| `GET /api/stats` | System stats (totals, sources, last run) |
| `GET /api/reports/latest` | Latest markdown report |
| `GET /api/news` | Recent posts from all sources |

## Setup

```bash
git clone https://github.com/Evrouin/trendbyte.git
cd trendbyte

pip install -e ".[dev]"
python -m spacy download en_core_web_sm
playwright install chromium

docker run -d --name trendbyte-db \
  -p 5432:5432 \
  -e POSTGRES_DB=trendbyte \
  -e POSTGRES_PASSWORD=postgres \
  postgres:16

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
| GITHUB_TOKEN | Yes | GitHub personal access token |
| DATABASE_URL | Yes | PostgreSQL connection string |
| TWITTER_API_KEY | No | X API consumer key |
| TWITTER_API_SECRET | No | X API consumer secret |
| TWITTER_ACCESS_TOKEN | No | X API access token |
| TWITTER_ACCESS_SECRET | No | X API access token secret |

## Scheduling

| Workflow | Schedule | Description |
|----------|----------|-------------|
| Daily | 2 PM UTC | Collect, analyze, score, predict |
| Weekly | Sun 6 PM UTC | Aggregate weekly trends |
| Training | Mon 12 PM UTC | Retrain ML predictor |
| SonarCloud | On push | Code quality scan |

## Development

```bash
ruff check src/ api/ tests/
ruff format src/ api/ tests/
pytest tests/ -v
```

## Tech Stack

- Python 3.12, FastAPI, psycopg 3, spaCy, Playwright
- PostgreSQL (Neon production)
- GitHub Actions, Render (deployment)
- SonarCloud (quality)

## License

MIT
