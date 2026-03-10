import os
from pathlib import Path

import pandas as pd
import psycopg2


def _get_conn(host: str = None):
    """Shared connection """
    return psycopg2.connect(
        host=host or os.environ.get("PGHOST", "localhost"),
        database=os.environ.get("PGDATABASE", "airflow"),
        user=os.environ.get("PGUSER", "airflow"),
        password=os.environ.get("PGPASSWORD", "airflow"),
        port=os.environ.get("PGPORT", "5432"),
    )


def is_date_processed(run_date: str, host: str = None) -> bool:
    """if this run_date was already successfully loaded (skip incremental)."""
    conn = _get_conn(host)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pipeline_run_state WHERE run_date = %s::date",
                (run_date,),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()


def record_run_success(run_date: str, host: str = None) -> None:
    """Day 11: Record that this run_date was fully loaded (for incremental + backfills)."""
    conn = _get_conn(host)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pipeline_run_state (run_date, completed_at)
                VALUES (%s::date, CURRENT_TIMESTAMP)
                ON CONFLICT (run_date) DO UPDATE SET completed_at = CURRENT_TIMESTAMP
                """,
                (run_date,),
            )
        conn.commit()
        print(f"[Load] Recorded run success for {run_date}.")
    finally:
        conn.close()


def _run_schema(conn) -> None:
    """Run sql/schema.sql to create tables if they don't exist."""
    schema_path = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    if not schema_path.exists():
        return
    with open(schema_path, encoding="utf-8") as f:
        ddl = f.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def load_data(dim_df: pd.DataFrame, fact_df: pd.DataFrame, host: str = None) -> None:
    """Load dim and fact DataFrames into Postgres. Idempotent (upserts).
    Credentials from env: PGHOST, PGDATABASE, PGUSER, PGPASSWORD, PGPORT (defaults for local dev).
    """
    db_host = host or os.environ.get("PGHOST", "localhost")
    print(f"[Load] Connecting to Postgres at {db_host}...")
    conn = _get_conn(host)
    try:
        _run_schema(conn)
        print("[Load] Schema applied (tables exist).")
        cur = conn.cursor()

        # dim_city: insert or update on conflict
        if not dim_df.empty:
            for _, row in dim_df.iterrows():
                cur.execute(
                    """
                    INSERT INTO dim_city (city_key, city_name, latitude, longitude, timezone, elevation_m, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (city_key) DO UPDATE SET
                        city_name = EXCLUDED.city_name,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        timezone = EXCLUDED.timezone,
                        elevation_m = EXCLUDED.elevation_m,
                        created_at = EXCLUDED.created_at
                    """,
                    (
                        row["city_key"],
                        row["city_name"],
                        float(row["latitude"]),
                        float(row["longitude"]),
                        row["timezone"] if pd.notna(row["timezone"]) else None,
                        float(row["elevation_m"]) if pd.notna(row["elevation_m"]) else None,
                        row["created_at"],
                    ),
                )
            print(f"[Load] dim_city: {len(dim_df)} row(s) upserted.")

        # fact_weather_daily: insert or update on conflict
        if not fact_df.empty:
            for _, row in fact_df.iterrows():
                cur.execute(
                    """
                    INSERT INTO fact_weather_daily (city_key, date, avg_temperature_c, min_temperature_c, max_temperature_c, total_precipitation_mm, ingested_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (city_key, date) DO UPDATE SET
                        avg_temperature_c = EXCLUDED.avg_temperature_c,
                        min_temperature_c = EXCLUDED.min_temperature_c,
                        max_temperature_c = EXCLUDED.max_temperature_c,
                        total_precipitation_mm = EXCLUDED.total_precipitation_mm,
                        ingested_at = EXCLUDED.ingested_at
                    """,
                    (
                        row["city_key"],
                        row["date"],
                        float(row["avg_temperature_c"]) if pd.notna(row["avg_temperature_c"]) else None,
                        float(row["min_temperature_c"]) if pd.notna(row["min_temperature_c"]) else None,
                        float(row["max_temperature_c"]) if pd.notna(row["max_temperature_c"]) else None,
                        float(row["total_precipitation_mm"]) if pd.notna(row["total_precipitation_mm"]) else None,
                        row["ingested_at"],
                    ),
                )
            print(f"[Load] fact_weather_daily: {len(fact_df)} row(s) upserted.")

        conn.commit()
        print("[Load] Commit done. Load finished successfully.")
    finally:
        conn.close()
