# BlazeDashboard

Dashboard for viewing and analyzing exported Blaze POS data. Drop your CSV exports into `data/`, run ingestion, and browse everything through a web UI.

## Setup

```bash
cp .env.example .env
# Edit .env with your credentials

docker compose up -d
```

| Service    | URL                        |
|------------|----------------------------|
| Frontend   | http://localhost:3000       |
| API        | http://localhost:8001       |
| API Docs   | http://localhost:8001/docs  |
| PostgreSQL | localhost:5433              |

## Ingestion

Place CSV exports from Blaze in the `data/` directory, then trigger ingestion:

```bash
# Ingest all CSVs
curl -X POST http://localhost:8001/api/v1/ingest/all

# Check table counts
curl http://localhost:8001/api/v1/ingest/all/status

# Validate no duplicates
curl http://localhost:8001/api/v1/ingest/validate
```

Ingestion is idempotent. Records are deduplicated by transaction ID or line hash, so re-running is safe.

## Scraper (optional)

The scraper uses Playwright to pull CSVs directly from the Blaze retail portal. It's gated behind Docker Compose profiles so it doesn't start by default.

```bash
# Full historical export
docker compose --profile scraper run scraper node scraper.js full

# Incremental (new data only)
docker compose --profile scraper run scraper node scraper.js incremental

# Date range
docker compose --profile scraper run scraper node scraper.js 2025-04-01 2025-12-31

# Enable daily schedule (11:59 PM EST)
docker compose --profile scheduler up -d scraper-scheduled
```

## Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Recharts
- **API**: FastAPI, async SQLAlchemy, asyncpg
- **Database**: PostgreSQL 16
- **Scraper**: Node.js, Playwright

## Data Flow

```
Blaze POS Portal --> Scraper --> CSV exports --> API ingestion --> PostgreSQL --> React dashboard
```

## Pages

- **Dashboard** -- overview stats, recent transactions, top employees
- **Transactions** -- full transaction list with detail modals, filtering, search
- **Customers** -- consumer directory, member performance, inactive tracking, marketing contacts
- **Products** -- product catalog, batches, vendor breakdown, aging, sell-through
- **Employees** -- sales performance, activity log, time clock
- **Inventory** -- current stock, aging, distribution, valuation, transfers, reconciliation
- **Reports** -- 15 report types across sales breakdowns, financials, and operations
- **Analytics** -- trends, top customers, payment breakdowns
- **Settings** -- database status, manual ingestion trigger

## Environment Variables

```env
BLAZE_EMAIL=your@email.com
BLAZE_PASSWORD=yourpassword

# Optional
BLAZE_API_KEY=...
BLAZE_API_SECRET=...
```

## License

Private
