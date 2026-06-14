from __future__ import annotations

from datetime import datetime, timezone

from pyspark.sql import Row

from src.spark_session import create_spark_session


def run() -> None:
    spark = create_spark_session("IcebergPipelineAudit")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.monitoring")

    metrics = spark.sql(
        """
        SELECT
          (SELECT COUNT(*) FROM lakehouse.bronze.orders_raw) AS bronze_rows,
          (SELECT COUNT(*) FROM lakehouse.silver.orders) AS silver_rows,
          (SELECT COUNT(*) FROM lakehouse.silver.orders_quarantine)
            AS quarantined_rows,
          (SELECT COUNT(*) FROM lakehouse.gold.daily_sales) AS gold_rows
        """
    ).first()

    audit = spark.createDataFrame(
        [
            Row(
                run_at=datetime.now(timezone.utc).replace(tzinfo=None),
                bronze_rows=metrics["bronze_rows"],
                silver_rows=metrics["silver_rows"],
                quarantined_rows=metrics["quarantined_rows"],
                gold_rows=metrics["gold_rows"],
                run_status="success",
            )
        ]
    )
    table_name = "lakehouse.monitoring.pipeline_runs"
    if spark.catalog.tableExists(table_name):
        audit.writeTo(table_name).append()
    else:
        audit.writeTo(table_name).using("iceberg").create()

    audit.show(truncate=False)
    spark.stop()


if __name__ == "__main__":
    run()
