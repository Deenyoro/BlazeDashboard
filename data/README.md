# Data Directory

Drop Blaze POS CSV exports here. The API reads from this directory during ingestion.

## Ingestion

```bash
curl -X POST http://localhost:8001/api/v1/ingest/all
```

Files are matched by name. Ingestion is safe to re-run — duplicates are skipped automatically.
