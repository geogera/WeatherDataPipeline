-- Day 12: Analytics queries (PostgreSQL)
-- Run against the airflow DB after pipeline has loaded data.

-- 1. Avg temp per city (one row per city, overall average daily temp)
SELECT
    dc.city_name,
    ROUND(AVG(fwd.avg_temperature_c)::numeric, 2) AS avg_temperature_c
FROM dim_city dc
JOIN fact_weather_daily fwd ON fwd.city_key = dc.city_key
GROUP BY dc.city_key, dc.city_name
ORDER BY avg_temperature_c DESC;


-- 2. Hottest city in the last 7 days (city with highest max daily avg in that window)
SELECT
    dc.city_name,
    MAX(fwd.avg_temperature_c) AS max_daily_avg_c
FROM dim_city dc
JOIN fact_weather_daily fwd ON fwd.city_key = dc.city_key
WHERE fwd.date BETWEEN (CURRENT_DATE - interval '7 days')::date AND CURRENT_DATE
GROUP BY dc.city_key, dc.city_name
ORDER BY max_daily_avg_c DESC
LIMIT 1;


-- 3. Weather trends (e.g. daily avg temp over time per city — last 14 days)
SELECT
    dc.city_name,
    fwd.date,
    fwd.avg_temperature_c,
    fwd.total_precipitation_mm
FROM dim_city dc
JOIN fact_weather_daily fwd ON fwd.city_key = dc.city_key
WHERE fwd.date >= (CURRENT_DATE - interval '14 days')::date
ORDER BY dc.city_name, fwd.date;
