# 📊 BSE Announcements Data Pipeline

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Airflow](https://img.shields.io/badge/Airflow-2.8.1-red)
![dbt](https://img.shields.io/badge/dbt-1.5.0-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A production-ready ELT pipeline that automates the extraction, storage, and analysis of corporate announcements from the Bombay Stock Exchange (BSE) using a modern data stack.

---

## 🎯 Project Overview

This project implements an **ELT (Extract, Load, Transform)** workflow that:

- **Extracts** announcements from the BSE website/API
- **Loads** raw data into a local SQLite database
- **Transforms** the data with **dbt** into analytics-ready models
- **Orchestrates** the workflow using **Apache Airflow**

The main Airflow DAG is:

- **DAG ID**: `bse_announcements_pipeline`
- **Default schedule (Docker setup)**: `*/5 * * * *` (every 5 minutes)

---

## 🏗️ Architecture

High-level architecture:

1. **BSE Source**
   - HTTP client scrapes / fetches corporate announcements.

2. **Orchestration (Airflow)**
   - Schedules and runs the `bse_announcements_pipeline` DAG.
   - Handles retries and branching based on whether new data was fetched.

3. **Storage (SQLite)**
   - Raw announcements stored in `data/announcements.db`.
   - Accessed via SQLAlchemy models in `src/storage.py` and `src/models.py`.

4. **Transformations (dbt)**
   - dbt models in `dbt_project/bse_analytics` build:
     - Staging model: `stg_announcements`
     - Analytics models: `daily_announcement_summary`, `company_activity`, `hourly_patterns`

5. **Analytics**
   - Query the analytics tables using SQL or connect external BI tools to the SQLite database.

---

## 🛠️ Technology Stack

| Component           | Technology            | Purpose                           |
|---------------------|----------------------|-----------------------------------|
| **Orchestration**   | Apache Airflow 2.8.1 | Workflow scheduling & monitoring  |
| **Transformations** | dbt Core 1.5.0       | SQL-based data modeling           |
| **Database**        | SQLite               | Lightweight local data storage    |
| **Language**        | Python 3.11          | Scraping & pipeline logic         |
| **Containerization**| Docker & Compose     | Local, reproducible environment   |
| **ORM**             | SQLAlchemy           | Database abstraction              |
| **Config**          | Pydantic, PyYAML     | Typed configuration management    |

---

## 📂 Project Structure

```text
nseanalytics/
├── airflow/                    # Local Airflow metadata & runtime (airflow.db, logs, plugins)
│   ├── dags/
│   ├── logs/
│   └── airflow.db
│
├── dags/                       # DAGs mounted into the Dockerised Airflow
│   └── bse_announcements_dag.py
│
├── src/                        # Python source code
│   ├── scraper.py              # BSE scraper
│   ├── storage.py              # DB access helpers
│   ├── models.py               # SQLAlchemy models
│   ├── orchestrator.py         # Orchestration of scrape/store steps
│   ├── config.py               # Configuration loader
│   └── fetcher_bse.py          # HTTP client for BSE
│
├── dbt_project/
│   └── bse_analytics/
│       ├── models/
│       │   ├── staging/
│       │   │   └── stg_announcements.sql
│       │   └── analytics/
│       │       ├── daily_announcement_summary.sql
│       │       ├── company_activity.sql
│       │       └── hourly_patterns.sql
│       ├── profiles/           # dbt profile for SQLite
│       │   └── profiles.yml
│       ├── dbt_project.yml
│       └── schema.yml
│
├── config/
│   └── config.yaml             # Data source & storage configuration
│
├── data/
│   ├── announcements.db        # SQLite database
│   └── attachments/            # Downloaded attachments (if enabled)
│
├── logs/                       # Airflow/logging output
├── docker-compose-simple.yml   # Single-container Airflow setup
├── Dockerfile                  # Airflow image with project code
├── requirements.txt            # Python dependencies
├── pyproject.toml / setup.py   # Packaging / dev configuration
└── README.md
```

---

## 🚀 Quick Start (Docker)

### Prerequisites

- Docker & Docker Compose installed
- At least **4 GB** of free RAM
- Port **8080** available

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/nseanalytics.git
cd nseanalytics
```

### 2. Start Airflow

```bash
docker-compose -f docker-compose-simple.yml up -d
```

Wait for Airflow to come up:

```bash
docker logs -f nse-airflow
```

Once you see Airflow webserver and scheduler running, press `Ctrl+C` to stop tailing logs (the container stays up).

### 3. Access Airflow UI

- URL: `http://localhost:8080`
- Username: `admin`
- Password: `admin`

In the **DAGs** page:

1. Find the DAG **`bse_announcements_pipeline`**
2. Toggle it **on** to unpause
3. Optionally click the **play** button to trigger a manual run

By default (Docker setup), this DAG is scheduled to run **every 5 minutes**.

---

## 📊 Data Models

### Raw Layer (Bronze)

- **Table**: `announcements`
- **Source**: Directly from BSE HTTP responses

Example schema:

```sql
id INTEGER PRIMARY KEY,
symbol TEXT,
company_name TEXT,
subject TEXT,
description TEXT,
broadcast_datetime TEXT,
category TEXT,
attachment_url TEXT,
feed_source TEXT,
created_at TEXT
```

### Staging Layer (Silver) – dbt

- **Model**: `stg_announcements`
- **Purpose**:
  - Normalize and clean raw fields
  - Parse and standardize datetimes
  - Add helper flags (e.g. `has_attachment`)

### Analytics Layer (Gold) – dbt

- **Model**: `daily_announcement_summary`

  ```sql
  announcement_date,
  category_group,
  announcement_count,
  unique_companies,
  with_attachments,
  pct_with_attachments
  ```

- **Model**: `company_activity`

  ```sql
  symbol,
  company_name,
  total_announcements,
  category_types,
  first_announcement,
  last_announcement,
  days_since_last_announcement
  ```

- **Model**: `hourly_patterns`

  ```sql
  hour_of_day,
  announcement_count,
  unique_companies,
  financial_count,
  governance_count,
  avg_per_day
  ```

---

## 🧪 Data Quality (dbt Tests)

dbt tests are defined in `dbt_project/bse_analytics/schema.yml` and cover:

- **Uniqueness** – primary keys are unique
- **Non-null constraints** – critical columns are always populated
- **Accepted values** – controlled vocabularies for categories
- **Relationships** – referential integrity between models

Run tests inside the Airflow container:

```bash
docker exec nse-airflow bash -c \
  "cd /opt/airflow/dbt && dbt test --profiles-dir /opt/airflow/dbt/profiles"
```

---

## 💻 Local Development (Without Docker)

### 1. Create and activate a virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run a one-off scrape

```python
from src.scraper import BSEScraper
from src.storage import Storage

scraper = BSEScraper()
storage = Storage()

announcements = scraper.fetch_announcements()
total, new = storage.bulk_add_announcements(announcements)

print(f"Fetched {total} announcements ({new} new)")
```

### 4. Run dbt models locally

```bash
cd dbt_project/bse_analytics
dbt run  --profiles-dir ./profiles
dbt test --profiles-dir ./profiles
```

---

## 📈 Sample Analytics Queries

### Top 10 most active companies

```sql
SELECT
  symbol,
  company_name,
  total_announcements,
  days_since_last_announcement
FROM company_activity
ORDER BY total_announcements DESC
LIMIT 10;
```

### Daily announcement trends (last 30 days)

```sql
SELECT
  announcement_date,
  category_group,
  announcement_count,
  unique_companies
FROM daily_announcement_summary
WHERE announcement_date >= date('now', '-30 days')
ORDER BY announcement_date DESC;
```

### Peak announcement hours

```sql
SELECT
  hour_of_day,
  announcement_count,
  avg_per_day
FROM hourly_patterns
ORDER BY announcement_count DESC
LIMIT 5;
```

---

## 🐛 Troubleshooting

- **Airflow container not starting**

  ```bash
  docker logs nse-airflow
  # Check for port conflicts or permission issues
  ```

- **DAG not showing up in UI**

  ```bash
  docker exec nse-airflow airflow dags list
  # Confirm that bse_announcements_pipeline is listed
  ```

- **dbt models failing**

  ```bash
  docker exec nse-airflow bash -c \
    "cd /opt/airflow/dbt && dbt debug --profiles-dir /opt/airflow/dbt/profiles"
  ```

- **SQLite 'database is locked' errors**

  - SQLite has limited concurrency.
  - Reduce Airflow parallelism in `docker-compose-simple.yml` if needed:

    ```yaml
    AIRFLOW__CORE__PARALLELISM: 1
    AIRFLOW__CORE__DAG_CONCURRENCY: 1
    ```

---

## 🤝 Contributing

Contributions are welcome:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## 👤 Author

- **Name**: Sugaan Kandhasamy  
- **Portfolio**: [`https://sugaan.github.io/`](https://sugaan.github.io/)  
- **LinkedIn**: [`https://www.linkedin.com/in/sugaan-kandhasamy-5b549aa3/`](https://www.linkedin.com/in/sugaan-kandhasamy-5b549aa3/)  
- **GitHub**: [`https://github.com/sugaan`](https://github.com/sugaan)

---

## 🙏 Acknowledgments & References

- BSE India (publicly available data)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [dbt Documentation](https://docs.getdbt.com/)

If you find this project useful, consider starring the repository.

