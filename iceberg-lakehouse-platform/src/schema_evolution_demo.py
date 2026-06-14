from __future__ import annotations

from src.spark_session import create_spark_session


def run() -> None:
    spark = create_spark_session("IcebergSchemaEvolution")
    spark.sql("ALTER TABLE lakehouse.silver.orders ADD COLUMN IF NOT EXISTS loyalty_tier STRING")
    spark.sql("UPDATE lakehouse.silver.orders SET loyalty_tier = 'standard' WHERE loyalty_tier IS NULL")
    spark.sql("DESCRIBE lakehouse.silver.orders").show(truncate=False)
    spark.stop()


if __name__ == "__main__":
    run()

