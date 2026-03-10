
import sys
from pathlib import Path
from datetime import datetime

# Project root on sys.path so we can import src
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.extract import extract_weather
from src.transform import transform_data
from src.load import load_data


def main():
    run_date_str = sys.argv[1] if len(sys.argv) > 1 else None
    if run_date_str:
        run_date = datetime.strptime(run_date_str, "%Y-%m-%d")
    else:
        run_date = datetime.utcnow()

    print(f"Run date: {run_date.date()}")
    print("1. Extract (fetch API, save raw JSON)...")
    extract_weather(run_date=run_date)

    base_path = ROOT / "data" / "raw" / "weather" / run_date.strftime("%Y/%m/%d")
    print("2. Transform (raw → dim + fact DataFrames)...")
    dim_df, fact_df = transform_data(base_path)

    print(f"   dim_city rows: {len(dim_df)}, fact_weather_daily rows: {len(fact_df)}")
    if dim_df.empty and fact_df.empty:
        print("   No data to load (no JSON files?). Exiting.")
        return

    print("3. Load (insert/upsert into Postgres)...")
    load_data(dim_df, fact_df)
    print("Done. Full pipeline run successful.")


if __name__ == "__main__":
    main()
