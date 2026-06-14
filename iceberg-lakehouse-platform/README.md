# Apache Iceberg Open Lakehouse

A recruiter-focused data engineering project demonstrating an open lakehouse with Apache Iceberg, Spark, Nessie, MinIO, and Trino.

## Highlights

- Bronze, silver, and gold architecture
- ACID Iceberg tables on S3-compatible object storage
- Schema evolution and hidden partitioning
- Snapshot history and time travel
- Compaction and snapshot maintenance
- Multi-engine access from Spark and Trino
- Data quality quarantine tables
- CDC-style inserts, updates, and deletes through Iceberg `MERGE`
- Pipeline audit history and operational row-count metrics

See [PROJECT_SHOWCASE.md](PROJECT_SHOWCASE.md) and [docs/architecture.md](docs/architecture.md).

## Project Structure

```text
docker/        Local MinIO, Nessie, Spark, and Trino stack
src/           Data generation and Spark jobs
sql/           Trino analytics queries
trino/         Trino Iceberg catalog configuration
scripts/       Windows helper scripts
tests/         Unit tests
docs/          Architecture documentation
```

## Prerequisites

- Docker Desktop
- Python 3.11+
- PowerShell on Windows

## Setup

```powershell
cd iceberg-lakehouse-platform
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install dbt-trino==1.8.4
Copy-Item .env.example .env
```

## Start the Lakehouse

```powershell
.\scripts\start_full.ps1
```

Services:

- **MinIO console:** `http://localhost:9001`
- **Nessie API:** `http://localhost:19120/api/v2/config`
- **Trino UI:** `http://localhost:8080`
- **Airflow UI:** `http://localhost:8082` (admin / admin)
- **Streamlit Dashboard:** `http://localhost:8501`

Default MinIO credentials are in `.env.example` and should only be used locally.

## Run the Pipeline

You can trigger the pipeline manually via the Airflow UI (`lakehouse_pipeline` DAG) or via PowerShell:

```powershell
.\scripts\run_pipeline.ps1
```

This generates 5,000 orders and creates the `bronze` and `silver` Iceberg tables via PySpark.

## Transform Data with dbt

Once the raw data is ingested into the `silver` layer, run dbt to build the analytics models in the `gold` layer and run data quality tests:

```powershell
.\scripts\run_dbt.ps1
```

Models created:
- `lakehouse.silver.stg_orders`
- `lakehouse.gold.daily_sales`
- `lakehouse.gold.channel_performance`
- `lakehouse.gold.category_performance`

## View the Dashboard

Open the Streamlit application to view live data directly from the Trino query engine:

`http://localhost:8501`

## Run an Incremental CDC Batch

After the initial pipeline succeeds, apply a mix of inserts, updates, and deletes to demonstrate Iceberg `MERGE` and time-travel:

```powershell
.\scripts\run_incremental.ps1
```

## Run Iceberg Demos

```powershell
.\scripts\run_demos.ps1
```

The demos add a column through schema evolution and inspect historical Iceberg snapshots.

## Test

```powershell
pytest -q
```

## Stop

```powershell
.\scripts\stop.ps1
# or
docker compose -f docker/docker-compose.yml down
```

## Next Steps for Production

- Replace generated files with Kafka or Debezium CDC.
- Store data in AWS S3, Azure Data Lake Storage, or Google Cloud Storage.
- Add OpenLineage and Marquez for lineage visibility.
