
CREATE TABLE IF NOT EXISTS dim_city (
    city_key    VARCHAR(100) PRIMARY KEY,   
    city_name   VARCHAR(100) NOT NULL,
    latitude    DECIMAL(9, 6) NOT NULL,
    longitude   DECIMAL(9, 6) NOT NULL,
    timezone    VARCHAR(50),               
    elevation_m NUMERIC(8, 2),             
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_weather_daily (
    id                    SERIAL PRIMARY KEY,
    city_key              VARCHAR(100) NOT NULL REFERENCES dim_city(city_key),
    date                  DATE NOT NULL,
    avg_temperature_c     DECIMAL(5, 2),  
    min_temperature_c     DECIMAL(5, 2),
    max_temperature_c     DECIMAL(5, 2),
    total_precipitation_mm DECIMAL(8, 2),  
    ingested_at           TIMESTAMPTZ,
    UNIQUE (city_key, date)
);

CREATE INDEX IF NOT EXISTS idx_fact_weather_daily_city ON fact_weather_daily(city_key);
CREATE INDEX IF NOT EXISTS idx_fact_weather_daily_date ON fact_weather_daily(date);

-- Day 11: incremental processing — which dates have been fully loaded
CREATE TABLE IF NOT EXISTS pipeline_run_state (
    run_date     DATE PRIMARY KEY,
    completed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
