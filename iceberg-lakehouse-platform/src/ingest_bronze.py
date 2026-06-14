from __future__ import annotations

import argparse

from pyspark.sql import functions as F

from src.spark_session import create_spark_session


def run(input_path: str) -> None:
    spark = create_spark_session("IcebergBronzeIngestion")
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze")

    raw = spark.read.json(input_path).withColumn("ingested_at", F.current_timestamp())
    table_name = "lakehouse.bronze.orders_raw"
    if spark.catalog.tableExists(table_name):
        raw.writeTo(table_name).append()
    else:
        raw.writeTo(table_name).using("iceberg").partitionedBy(F.days("ingested_at")).create()

    print(f"Bronze rows: {raw.count()}")
    spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/generated/orders.jsonl")
    args = parser.parse_args()
    run(args.input)
