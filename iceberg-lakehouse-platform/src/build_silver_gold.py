from __future__ import annotations

from pyspark.sql import functions as F

from src.quality import enrich_quality_columns
from src.spark_session import create_spark_session


def run() -> None:
    spark = create_spark_session("IcebergSilverGold")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.gold")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.monitoring")

    bronze = spark.table("lakehouse.bronze.orders_raw")
    enriched = enrich_quality_columns(bronze).dropDuplicates(["event_id"])

    valid = enriched.filter(F.col("quality_status") == "valid")
    invalid = enriched.filter(F.col("quality_status") == "invalid")

    # ── Silver: valid orders ─────────────────────────────────────────────────
    # Use overwrite-by-partition so we replace only the affected month
    # partitions on re-runs while preserving historical Iceberg snapshots
    # (each run produces a new snapshot → time-travel stays meaningful).
    if spark.catalog.tableExists("lakehouse.silver.orders"):
        valid.writeTo("lakehouse.silver.orders").overwritePartitions()
    else:
        (
            valid.writeTo("lakehouse.silver.orders")
            .using("iceberg")
            .partitionedBy(F.months("event_timestamp"))
            .create()
        )

    # ── Silver: quarantine ───────────────────────────────────────────────────
    if spark.catalog.tableExists("lakehouse.silver.orders_quarantine"):
        invalid.writeTo("lakehouse.silver.orders_quarantine").overwritePartitions()
    else:
        (
            invalid.writeTo("lakehouse.silver.orders_quarantine")
            .using("iceberg")
            .create()
        )

    # ── Gold: daily sales aggregate ──────────────────────────────────────────
    daily = (
        valid.filter(F.col("status") == "completed")
        .groupBy(
            F.to_date("event_timestamp").alias("order_date"),
            "category",
            "sales_channel",
            "currency",
        )
        .agg(
            F.countDistinct("order_id").alias("order_count"),
            F.round(F.sum("order_amount"), 2).alias("gross_sales"),
            F.round(F.avg("order_amount"), 2).alias("avg_order_value"),
            F.countDistinct("customer_id").alias("unique_customers"),
        )
    )

    if spark.catalog.tableExists("lakehouse.gold.daily_sales"):
        daily.writeTo("lakehouse.gold.daily_sales").overwritePartitions()
    else:
        (
            daily.writeTo("lakehouse.gold.daily_sales")
            .using("iceberg")
            .partitionedBy("order_date")
            .create()
        )

    print(f"Silver valid rows:      {valid.count()}")
    print(f"Silver quarantine rows: {invalid.count()}")
    print(f"Gold aggregate rows:    {daily.count()}")
    spark.stop()


if __name__ == "__main__":
    run()
