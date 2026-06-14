from __future__ import annotations

from src.spark_session import create_spark_session

# Tables that benefit from regular compaction and snapshot expiry.
_MANAGED_TABLES = [
    "silver.orders",
    "gold.daily_sales",
    "monitoring.pipeline_runs",
]


def run() -> None:
    spark = create_spark_session("IcebergMaintenance")

    for table in _MANAGED_TABLES:
        qualified = f"lakehouse.{table}"
        if not spark.catalog.tableExists(qualified):
            print(f"Skipping {qualified} — table does not exist yet")
            continue

        print(f"\n── Compacting {qualified} ──")
        spark.sql(
            f"CALL lakehouse.system.rewrite_data_files(table => '{table}')"
        ).show(truncate=False)

        print(f"── Expiring old snapshots on {qualified} (retain last 3) ──")
        spark.sql(
            f"CALL lakehouse.system.expire_snapshots(table => '{table}', retain_last => 3)"
        ).show(truncate=False)

    spark.stop()


if __name__ == "__main__":
    run()
