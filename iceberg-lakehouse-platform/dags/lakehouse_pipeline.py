"""Airflow DAG — Iceberg Lakehouse Daily Pipeline.

Orchestrates the full Bronze → Silver → Gold pipeline using BashOperator
tasks that trigger spark-submit inside the running Spark container via
docker exec. This replaces the manual PowerShell run_pipeline.ps1 script.

DAG Graph:
    generate_orders ──► ingest_bronze ──► build_silver_gold ──► pipeline_audit
                                                    │
                                                    └──► run_maintenance (weekly)

Usage:
    1. Start the full stack: .\\scripts\\start_full.ps1
    2. Open Airflow UI: http://localhost:8082  (admin / admin)
    3. Enable the DAG and trigger it manually, or let the daily schedule run.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# ── Constants ──────────────────────────────────────────────────────────────────
SPARK_CONTAINER = "docker-spark-1"

# Iceberg + Nessie Maven packages required by spark-submit
PACKAGES = ",".join([
    "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.8.1",
    "org.apache.iceberg:iceberg-aws-bundle:1.8.1",
    "org.projectnessie.nessie-integrations:nessie-spark-extensions-3.5_2.12:0.102.5",
])

# Reusable spark-submit prefix (runs inside the Spark container)
SPARK_SUBMIT = (
    f"docker exec {SPARK_CONTAINER} "
    f"/opt/spark/bin/spark-submit "
    f"--conf spark.jars.ivy=/tmp/iceberg-ivy "
    f"--conf spark.executorEnv.PYTHONPATH=/opt/lakehouse "
    f"--conf spark.driver.extraJavaOptions=-Dpython.path=/opt/lakehouse "
    f"--packages {PACKAGES}"
)

# ── Default args ───────────────────────────────────────────────────────────────
default_args = {
    "owner": "lakehouse",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

# ── DAG ────────────────────────────────────────────────────────────────────────
with DAG(
    dag_id="lakehouse_pipeline",
    description="Bronze → Silver → Gold pipeline via Spark on Iceberg/Nessie",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["lakehouse", "iceberg", "spark"],
    doc_md=__doc__,
) as dag:

    # ── Task 1: Generate synthetic orders ─────────────────────────────────────
    generate_orders = BashOperator(
        task_id="generate_orders",
        bash_command=(
            f"docker exec {SPARK_CONTAINER} "
            f"python -m src.generate_orders --count 5000"
        ),
        doc_md="Generates 5,000 synthetic e-commerce orders as a JSONL file.",
    )

    # ── Task 2: Ingest raw orders into Bronze Iceberg table ───────────────────
    ingest_bronze = BashOperator(
        task_id="ingest_bronze",
        bash_command=f"{SPARK_SUBMIT} src/ingest_bronze.py",
        doc_md="Reads raw JSONL orders and writes them to the Bronze Iceberg table.",
    )

    # ── Task 3: Clean + transform Bronze → Silver → Gold ─────────────────────
    build_silver_gold = BashOperator(
        task_id="build_silver_gold",
        bash_command=f"{SPARK_SUBMIT} src/build_silver_gold.py",
        doc_md=(
            "Validates and cleans Bronze data into the Silver orders table. "
            "Aggregates Silver into the Gold daily_sales table."
        ),
    )

    # ── Task 4: Write pipeline audit record ───────────────────────────────────
    pipeline_audit = BashOperator(
        task_id="pipeline_audit",
        bash_command=f"{SPARK_SUBMIT} src/pipeline_audit.py",
        doc_md="Writes a pipeline run record to the monitoring.pipeline_runs table.",
    )

    # ── Task 5: Run CDC incremental batch (generates + merges changes) ────────
    run_incremental = BashOperator(
        task_id="run_incremental",
        bash_command=(
            f"docker exec {SPARK_CONTAINER} python -m src.generate_changes && "
            f"{SPARK_SUBMIT} src/merge_changes.py"
        ),
        doc_md="Generates CDC changes (insert/update/delete) and merges them into Silver.",
    )

    # ── Weekly maintenance (compact small files, expire old snapshots) ────────
    run_maintenance = BashOperator(
        task_id="run_maintenance",
        bash_command=f"{SPARK_SUBMIT} src/maintenance.py",
        trigger_rule="all_done",     # run even if upstream partially failed
        doc_md=(
            "Compacts small Parquet files and expires old Iceberg snapshots "
            "to keep storage efficient. Runs after every pipeline cycle."
        ),
    )

    # ── Dependencies ──────────────────────────────────────────────────────────
    (
        generate_orders
        >> ingest_bronze
        >> build_silver_gold
        >> pipeline_audit
        >> run_incremental
        >> run_maintenance
    )
