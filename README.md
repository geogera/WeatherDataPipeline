# Weather Data Pipeline

A production-style **ETL pipeline** that ingests weather data from an API, transforms it into a star schema, and loads it into Postgres—orchestrated by **Apache Airflow** with incremental processing and no full refreshes.

---

## Architecture

```
                    ┌─────────────────┐
                    │ Open-Meteo API  │
                    │ (hourly weather)│
                    └────────┬────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Apache Airflow (DAG)                              │
│  check_incremental → extract → transform → load → record_run_success      │
└──────────────────────────────────────────────────────────────────────────┘
     │                    │              │              │
     │                    ▼              ▼              ▼
     │             data/raw/weather/   Pandas        PostgreSQL
     │             YYYY/MM/DD/*.json   (dim + fact   (dim_city,
     │             (immutable raw)      DataFrames)   fact_weather_daily,
     │                                              pipeline_run_state)
     │
     └──────────────► Skip if run_date already in pipeline_run_state
```

- **Extract:** Fetch hourly temperature and precipitation for multiple cities; save raw JSON per city per date.
- **Transform:** Flatten hourly arrays, aggregate to daily metrics (avg/min/max temp, total precipitation), build dimension and fact DataFrames.
- **Load:** Upsert into Postgres (`dim_city`, `fact_weather_daily`); record successful run date for incremental logic.
- **Orchestration:** Airflow runs the pipeline daily; a short-circuit step skips dates already in `pipeline_run_state`, so we only process new dates and support backfills.

---

## Tech stack

| Layer        | Technology                          |
|-------------|--------------------------------------|
| Orchestration | Apache Airflow 2.8 (LocalExecutor) |
| Database    | PostgreSQL 15                        |
| Runtime     | Python 3.8+, Docker & Docker Compose |
| API         | [Open-Meteo](https://open-meteo.com/) (no API key) |
| Processing  | pandas, requests, psycopg2           |

---

## Pipeline flow

1. **check_incremental** — Query `pipeline_run_state`; if today’s (or the run’s) date is already there, skip the rest of the DAG.
2. **extract_weather** — For the run date, call the API per city and write raw JSON under `data/raw/weather/YYYY/MM/DD/<city>.json` with an `_ingested_at` timestamp.
3. **transform_weather** — Read all JSONs for that date, flatten hourly data, aggregate to daily (avg/min/max temp, sum precipitation), produce `dim_city` and `fact_weather_daily` DataFrames; push to XCom as JSON.
4. **load_weather** — Pull DataFrames from XCom, upsert into `dim_city` and `fact_weather_daily` (idempotent).
5. **record_run_success** — Insert the run date into `pipeline_run_state` so the next run skips it (incremental).

**Schedule:** `@daily`. **Backfills:** Trigger runs for past dates; they execute only for dates not yet in `pipeline_run_state`.

---

## Data model

- **dim_city** — One row per city: `city_key`, `city_name`, `latitude`, `longitude`, `timezone`, `elevation_m`, `created_at`. Primary key: `city_key`.
- **fact_weather_daily** — One row per city per day: `city_key` (FK), `date`, `avg_temperature_c`, `min_temperature_c`, `max_temperature_c`, `total_precipitation_mm`, `ingested_at`. Unique on `(city_key, date)` for idempotent upserts.
- **pipeline_run_state** — Tracks which dates have been fully loaded: `run_date` (PK), `completed_at`. Used to skip already-processed dates (incremental).

Analytics queries live in `sql/analytics.sql` (e.g. avg temp per city, hottest city in last 7 days, trends).

---

## Tradeoffs

- **LocalExecutor** — Simple to run in Docker; no Celery/Redis. Good for learning and small teams; for high concurrency you’d move to CeleryExecutor or a managed Airflow.
- **Raw JSON on disk** — Keeps an immutable raw layer and makes reprocessing easy; in production you might store raw data in object storage (e.g. S3) and only keep recent partitions locally.
- **Incremental by run date** — We only record “this date completed” and skip if already present. No full table refresh; backfills are supported by running the DAG for past dates.
- **XCom for transform → load** — DataFrames are serialized to JSON between tasks. Fine for moderate volume; for very large data you’d write to a staging table or file and pass a path.

---

## Improvements with AWS (or cloud)

- **Raw storage:** Ingest raw JSON to **S3** (e.g. `s3://bucket/raw/weather/YYYY/MM/DD/`) instead of (or in addition to) local disk; use lifecycle rules and optional Glacier for cost.
- **Warehouse:** Load into **Amazon RDS (Postgres)** or **Redshift** for analytics; keep the same schema and upsert logic, possibly with a dedicated load user and IAM.
- **Orchestration:** Run **MWAA** (Managed Workflows for Apache Airflow) or **Step Functions** + Lambda for a serverless option; DAG logic and incremental checks can stay the same.
- **Scaling:** Use **CeleryExecutor** with Redis and multiple workers; or run extract/transform/load in **ECS/Fargate** or **Lambda** triggered by Airflow.
- **Secrets:** Store DB credentials in **Secrets Manager** or **Parameter Store**; reference them from the DAG or task environment instead of env vars in the image.

---

## Quick start

**Prerequisites:** Docker Desktop (e.g. with WSL2 on Windows).

1. **Start Postgres and Airflow**
   ```bash
   docker compose up -d
   ```
2. **One-time DB and user setup** (if not done)
   ```bash
   docker compose run --rm airflow-webserver airflow db init
   docker compose run --rm airflow-webserver airflow users create --username airflow --password airflow --firstname Air --lastname Flow --role Admin --email airflow@example.com
   ```
3. **Open Airflow UI:** [http://localhost:8080](http://localhost:8080) (login: `airflow` / `airflow`). Enable the `weather_pipeline` DAG and trigger a run or wait for the daily schedule.

**Run the pipeline locally (no Airflow):**
```bash
python -m scripts.run_pipeline              # today
python -m scripts.run_pipeline 2026-03-10   # specific date
```
Requires Postgres (e.g. `docker compose up -d postgres`) and env vars or defaults for `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, `PGPORT`.

**Run analytics SQL:**
```bash
Get-Content sql/analytics.sql -Raw | docker exec -i airflow_postgres psql -U airflow -d airflow
```

---

## Project layout

```
├── dags/
│   └── weather_pipeline.py    # Airflow DAG (extract → transform → load)
├── src/
│   ├── extract.py             # API fetch + save raw JSON
│   ├── transform.py           # Raw → dim + fact DataFrames
│   └── load.py                # Upsert to Postgres + pipeline_run_state
├── sql/
│   ├── schema.sql             # dim_city, fact_weather_daily, pipeline_run_state
│   └── analytics.sql          # Example analytics queries
├── scripts/
│   └── run_pipeline.py       # Local ETL run (Day 8 style)
├── data/raw/weather/          # Raw JSON (YYYY/MM/DD/city.json)
├── docker-compose.yml        # Airflow + Postgres
└── README.md
```
