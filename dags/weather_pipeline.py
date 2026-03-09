
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

import sys
from pathlib import Path

# Add project src to path so "extract" module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from extract import extract_weather

 
# def hello_weather():
#     print("Weather pipeline is alive!")



default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="weather_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["weather", "data-engineering"],
) as dag:

    weather_task = PythonOperator(
        task_id="extract_weather",
        # python_callable=hello_weather,
        python_callable=extract_weather,
        op_kwargs={"run_date": "{{ ds }}"}  # passes execution date
    )

    weather_task
