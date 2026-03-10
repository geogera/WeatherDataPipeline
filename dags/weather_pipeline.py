from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from datetime import datetime, timedelta
from pathlib import Path
import sys

import pandas as pd

# Add project src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from extract import extract_weather
from transform import transform_data
from load import load_data, is_date_processed, record_run_success


default_args = {
    "owner": "airflow",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


def should_run_for_date(run_date: str, host: str = "postgres") -> bool:
    """ Return False if this date was already processed (skip). True = run pipeline."""
    if is_date_processed(run_date, host=host):
        print(f"[Incremental] Skipping {run_date}: already processed.")
        return False
    print(f"[Incremental] Will process {run_date} (new date).")
    return True


def run_transform(run_date: str, **context):
    """Build path from run_date, run transform, push DataFrames to XCom as JSON."""
    base_path = Path("data/raw/weather") / run_date.replace("-", "/")
    dim_df, fact_df = transform_data(base_path)
    return {
        "dim_df": dim_df.to_json(orient="split"),
        "fact_df": fact_df.to_json(orient="split"),
    }


def run_load(**context):
    """Pull dim_df and fact_df from XCom, deserialize, load into Postgres."""
    ti = context["ti"]
    data = ti.xcom_pull(task_ids="transform_weather")
    if not data:
        return
    dim_df = pd.read_json(data["dim_df"], orient="split")
    fact_df = pd.read_json(data["fact_df"], orient="split")
    # Restore date/datetime types
    if "created_at" in dim_df.columns:
        dim_df["created_at"] = pd.to_datetime(dim_df["created_at"])
    if "date" in fact_df.columns:
        fact_df["date"] = pd.to_datetime(fact_df["date"]).dt.date
    if "ingested_at" in fact_df.columns:
        fact_df["ingested_at"] = pd.to_datetime(fact_df["ingested_at"])
    load_data(dim_df, fact_df, host="postgres")


def run_record_success(run_date: str, host: str = "postgres") -> None:
    """ Record successful load so we skip this date on next run (incremental)."""
    record_run_success(run_date, host=host)


with DAG(
    dag_id="weather_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["weather", "data-engineering"],
) as dag:

    # Day 11: only run extract/transform/load if this date not already processed
    check_task = ShortCircuitOperator(
        task_id="check_incremental",
        python_callable=should_run_for_date,
        op_kwargs={"run_date": "{{ ds }}", "host": "postgres"},
    )
    extract_task = PythonOperator(
        task_id="extract_weather",
        python_callable=extract_weather,
        op_kwargs={"run_date": "{{ ds }}"},
    )
    transform_task = PythonOperator(
        task_id="transform_weather",
        python_callable=run_transform,
        op_kwargs={"run_date": "{{ ds }}"},
    )
    load_task = PythonOperator(
        task_id="load_weather",
        python_callable=run_load,
    )
    record_success_task = PythonOperator(
        task_id="record_run_success",
        python_callable=run_record_success,
        op_kwargs={"run_date": "{{ ds }}", "host": "postgres"},
    )

    check_task >> extract_task >> transform_task >> load_task >> record_success_task
