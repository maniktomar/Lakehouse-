from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def enrich_quality_columns(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("event_timestamp", F.to_timestamp("event_time"))
        .withColumn("ingested_at", F.current_timestamp())
        .withColumn("computed_amount", F.round(F.col("quantity") * F.col("unit_price"), 2))
        .withColumn(
            "quality_status",
            F.when(
                F.col("event_id").isNotNull()
                & F.col("order_id").isNotNull()
                & (F.col("quantity") > 0)
                & (F.col("unit_price") > 0)
                & (F.abs(F.col("order_amount") - F.col("computed_amount")) <= 0.05),
                "valid",
            ).otherwise("invalid"),
        )
    )

