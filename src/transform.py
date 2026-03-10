import json
from pathlib import Path
from datetime import datetime
from typing import Tuple

import pandas as pd


def transform_data(base_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform all raw JSON files in a given directory (for one date).

    Returns:
      dim_df  - one row per city (for dim_city)
      fact_df - one row per city per day (for fact_weather_daily)
    """
    dim_parts = []
    fact_parts = []

    for file_path in base_path.glob("*.json"):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        hourly = data["hourly"]
        hourly_df = pd.DataFrame(
            {
                "time": hourly["time"],
                "temperature_2m": hourly["temperature_2m"],
                "precipitation": hourly["precipitation"],
            }
        )

        # Clean and add date column
        hourly_df = hourly_df.dropna(subset=["temperature_2m"])
        hourly_df["time"] = pd.to_datetime(hourly_df["time"], utc=True)
        hourly_df["date"] = hourly_df["time"].dt.date

        # Aggregate to daily metrics
        daily_df = hourly_df.groupby("date", as_index=False).agg(
            avg_temperature_c=("temperature_2m", "mean"),
            min_temperature_c=("temperature_2m", "min"),
            max_temperature_c=("temperature_2m", "max"),
            total_precipitation_mm=("precipitation", "sum"),
        )

        city_key = file_path.stem
        city_name = city_key.replace("_", " ").title()
        ingested_at = pd.to_datetime(data.get("_ingested_at"), utc=True)

        daily_df["city_key"] = city_key
        daily_df["ingested_at"] = ingested_at

        fact_parts.append(
            daily_df[
                [
                    "city_key",
                    "date",
                    "avg_temperature_c",
                    "min_temperature_c",
                    "max_temperature_c",
                    "total_precipitation_mm",
                    "ingested_at",
                ]
            ]
        )

        dim_parts.append(
            pd.DataFrame(
                [
                    {
                        "city_name": city_name,
                        "latitude": data["latitude"],
                        "longitude": data["longitude"],
                        "timezone": data.get("timezone"),
                        "elevation_m": data.get("elevation"),
                        "created_at": ingested_at,
                    }
                ]
            )
        )

    dim_df = pd.concat(dim_parts, ignore_index=True) if dim_parts else pd.DataFrame()
    fact_df = pd.concat(fact_parts, ignore_index=True) if fact_parts else pd.DataFrame()

    return dim_df, fact_df








