# TrendByte

Tech trend intelligence bot — tracks emerging technologies across GitHub, Reddit, and Hacker News, then tweets daily insights.

## Setup

```bash
# clone
git clone <repo-url> && cd trendbyte

# install
pip install -e ".[dev]"
playwright install chromium

# database (docker)
docker run -d --name trendbyte-db -p 5432:5432 -e POSTGRES_DB=trendbyte -e POSTGRES_PASSWORD=postgres postgres:16

# configure
cp .env.example .env
# fill in your API keys

# run
python -m src.main
```

## Development

```bash
# lint & format
black src/ tests/
ruff check src/ tests/
mypy src/

# test
pytest --cov=src
```

## Architecture

```
src/
├── collectors/   → data ingestion (GitHub, Reddit, HN)
├── analysis/     → trend scoring & anomaly detection
├── bot/          → twitter posting
├── rendering/    → HTML templates → PNG images
├── models/       → domain entities
├── database.py   → PostgreSQL connection & schema
├── config.py     → env-based configuration
└── main.py       → pipeline orchestrator
```

## License

MIT
