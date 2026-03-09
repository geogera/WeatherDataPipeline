Love it. Windows + intermediate Python is totally fine.
Here’s a **clear, realistic 14-day plan** (≈1–1.5 hrs/day) that gets you to a **GitHub-ready, interview-ready data engineering project**.

No rushing. No filler days.

---

# 🗓️ 14-Day Data Engineering Project Plan

**Project:** Weather Data Pipeline (API → Airflow → Warehouse)

---

## 🔹 Day 1 — Project setup & mindset

**Goal:** Look like a professional from day one.

**Tasks**

* Create GitHub repo: `weather-data-pipeline`
* Add folders:

  ```
  dags/
  src/
  sql/
  data/raw/
  ```
* Write a **basic README** (title + short description)
* Get a free **OpenWeather API key**

**Deliverable**

* Clean repo structure
* README exists (even minimal)

---

## 🔹 Day 2 — Docker & local environment

**Goal:** One-command startup (huge DE signal).

**Tasks**

* Install:

  * Docker Desktop (Windows)
  * WSL2 (if not already)
* Create `docker-compose.yml` with:

  * Airflow
  * Postgres
* Make sure Airflow UI loads

**Deliverable**

* Airflow running at `localhost:8080`
* Postgres container running

---

## 🔹 Day 3 — API extraction (Python)

**Goal:** Reliable ingestion code.

**Tasks**

* Write `src/extract.py`
* Fetch weather data for 3–5 cities
* Handle:

  * Bad responses
  * Timeouts
* Save **raw JSON** to disk

**Deliverable**

* Raw weather JSON files saved locally

📌 *This proves you can talk to real APIs.*

---

## 🔹 Day 4 — Raw data partitioning

**Goal:** Production-style storage.

**Tasks**

* Organize files as:

  ```
  data/raw/weather/YYYY/MM/DD/city.json
  ```
* Add ingestion timestamp
* Ensure reruns don’t overwrite data

**Deliverable**

* Partitioned raw data

📌 Interview phrase: *“immutable raw layer”*

---

## 🔹 Day 5 — Data modeling

**Goal:** Show analytics thinking.

**Tasks**

* Design schema:

  * `dim_city`
  * `fact_weather_daily`
* Write `sql/schema.sql`
* Decide:

  * Primary keys
  * Data types

**Deliverable**

* SQL schema file

---

## 🔹 Day 6 — Transformation logic (Python)

**Goal:** Clean & normalize messy JSON.

**Tasks**

* Write `src/transform.py`
* Flatten JSON
* Handle missing values
* Convert timestamps
* Output clean Pandas DataFrames

**Deliverable**

* Transformed DataFrames ready for loading

---

## 🔹 Day 7 — Load into Postgres

**Goal:** Warehouse population.

**Tasks**

* Write `src/load.py`
* Insert into Postgres
* Avoid duplicates (incremental logic)
* Add basic indexes

**Deliverable**

* Tables populated in Postgres

📌 Interview phrase: *“idempotent loads”*

---

## 🔹 Day 8 — End-to-end local run (no Airflow)

**Goal:** Make sure logic works before orchestration.

**Tasks**

* Run extract → transform → load manually
* Validate row counts
* Fix edge cases

**Deliverable**

* Successful full pipeline run

---

## 🔹 Day 9 — First Airflow DAG

**Goal:** Orchestration begins.

**Tasks**

* Create `dags/weather_pipeline.py`
* Define tasks using PythonOperator
* Schedule daily runs
* Disable catchup

**Deliverable**

* DAG visible and runnable in Airflow

---

## 🔹 Day 10 — Airflow robustness

**Goal:** Show production awareness.

**Tasks**

* Add:

  * Retries
  * Logging
  * Failure alerts (logs only)
* Parameterize cities & dates

**Deliverable**

* Stable DAG that survives failures

---

## 🔹 Day 11 — Incremental processing

**Goal:** Separate juniors from real DEs.

**Tasks**

* Process only **new dates**
* Store last successful run date
* Support backfills

**Deliverable**

* Incremental pipeline

📌 Interview phrase: *“no full refreshes”*

---

## 🔹 Day 12 — Analytics queries

**Goal:** Prove business value.

**Tasks**

* Write SQL queries:

  * Avg temp per city
  * Hottest city (7 days)
  * Weather trends
* Save queries in `sql/analytics.sql`

**Deliverable**

* Insightful SQL queries

---

## 🔹 Day 13 — README polish (VERY IMPORTANT)

**Goal:** Turn project into a job magnet.

**README sections**

* Architecture diagram (ASCII is fine)
* Tech stack
* Pipeline flow
* Data model
* Tradeoffs
* Improvements with AWS

**Deliverable**

* Professional README

---

## 🔹 Day 14 — Interview prep & cleanup

**Goal:** Be able to defend every decision.

**Tasks**

* Clean repo
* Add comments
* Practice explaining:

  * Why Airflow?
  * Why raw data?
  * How you handle failures?
  * How it scales?

**Deliverable**

* Interview-ready project

---

## 🎯 After Day 14, you can truthfully say:

> “I built and orchestrated a production-style ETL pipeline using Airflow, Python, SQL, and Postgres with incremental processing.”

That sentence alone changes how recruiters see you.

---

## Want extra help?

I can:

* Give you a **starter `docker-compose.yml`**
* Write a **skeleton Airflow DAG**
* Do a **mock interview** using *this* project
* Review your README like a hiring manager

Just say the word and tell me what you want next 👌
