from datetime import datetime
import json

from pathlib import Path

import requests


CITIES = {
    "london": {"lat":"51.507","long":"-0.1278"},
    "paris": {"lat":"48.8566","long":"2.3522"},
    "new_york": {"lat":"40.7128","long":"-74.0060"},
}

BASE_URL = "https://api.open-meteo.com/v1/forecast"



def fetch_weather_data(city_coords)-> dict:
    # fetch weather data from open-meteo API
    params={
        "latitude": city_coords["lat"],
        "longitude": city_coords["long"],
        "hourly": "temperature_2m,precipitation"
    }
	
    response=requests.get(params=params,url=BASE_URL,timeout=10)
    response.raise_for_status()
    return response.json()

def save_raw_data(city_key: str, data: dict,date: datetime) -> None:
    # save weather data to raw json file
    base_path = Path("data/raw/weather") / date.strftime("%Y/%m/%d")
    base_path.mkdir(parents=True, exist_ok=True)

    data["_ingested_at"]= date.isoformat()
    file_path= base_path / f"{city_key}.json"

    with open(file=file_path, mode="w",encoding="utf-8") as f:
        json.dump(data,f,indent=2)


def extract_weather(run_date=None):
    # extract weather data for all cities for a given date
    if isinstance(run_date, str):
        run_date = datetime.strptime(run_date, "%Y-%m-%d")  # convert string to datetime
    if run_date is None:
        run_date = datetime.utcnow()

    for city_key,city_coords in CITIES.items():
        try:  # handle any errors that may occur
            print(f"Processing for date: {run_date} and city: {city_key}")
            weather_data = fetch_weather_data(city_coords=city_coords)  # fetch weather data from open-meteo API
            save_raw_data(city_key=city_key, data=weather_data, date=run_date)  # save weather data to raw json file
            print("Data were saved successfully for city: " + city_key)
        except Exception as e:  # handle any errors that may occur
            print(f"Failed for {city_key}: {e}")
            # Re-raise so Airflow marks the task as failed and can retry
            raise

if __name__ == "__main__": # main function to extract weather data for all cities for a given date
    extract_weather()