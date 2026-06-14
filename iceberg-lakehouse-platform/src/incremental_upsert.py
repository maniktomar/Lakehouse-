from __future__ import annotations

import argparse

from pyspark.sql import functions as F

from src.quality import enrich_quality_columns
from src.spark_session import create_spark_session


def run(input_path: str) -> None:
    spark = create_spark_session("IcebergIncrementalUpsert")
    changes = enrich_quality_columns(spark.read.json(input_path)).filter(
        F.col("quality_status") == "valid"
    )
    changes.createOrReplaceTempView("incoming_order_changes")

    spark.sql(
        """
        MERGE INTO lakehouse.silver.orders target
        USING incoming_order_changes source
          ON target.order_id = source.order_id
        WHEN MATCHED AND source.operation = 'delete' THEN DELETE
        WHEN MATCHED AND source.operation = 'update' THEN UPDATE SET
          target.event_id = source.event_id,
          target.event_time = source.event_time,
          target.customer_id = source.customer_id,
          target.customer_email = source.customer_email,
          target.product_id = source.product_id,
          target.category = source.category,
          target.quantity = source.quantity,
          target.unit_price = source.unit_price,
          target.order_amount = source.order_amount,
          target.currency = source.currency,
          target.sales_channel = source.sales_channel,
          target.country = source.country,
          target.status = source.status,
          target.event_timestamp = source.event_timestamp,
          target.ingested_at = source.ingested_at,
          target.computed_amount = source.computed_amount,
          target.quality_status = source.quality_status
        WHEN NOT MATCHED AND source.operation = 'insert' THEN INSERT (
          event_id, event_time, order_id, customer_id, customer_email,
          product_id, category, quantity, unit_price, order_amount,
          currency, sales_channel, country, status, event_timestamp,
          ingested_at, computed_amount, quality_status
        ) VALUES (
          source.event_id, source.event_time, source.order_id, source.customer_id,
          source.customer_email, source.product_id, source.category, source.quantity,
          source.unit_price, source.order_amount, source.currency, source.sales_channel,
          source.country, source.status, source.event_timestamp, source.ingested_at,
          source.computed_amount, source.quality_status
        )
        """
    )

    spark.sql(
        """
        CREATE OR REPLACE TABLE lakehouse.gold.daily_sales
        USING iceberg
        PARTITIONED BY (order_date)
        AS SELECT
          TO_DATE(event_timestamp) AS order_date,
          category,
          sales_channel,
          currency,
          COUNT(DISTINCT order_id) AS order_count,
          ROUND(SUM(order_amount), 2) AS gross_sales,
          ROUND(AVG(order_amount), 2) AS avg_order_value,
          COUNT(DISTINCT customer_id) AS unique_customers
        FROM lakehouse.silver.orders
        WHERE status = 'completed'
        GROUP BY TO_DATE(event_timestamp), category, sales_channel, currency
        """
    )

    print(f"Applied {changes.count()} valid CDC records")
    spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/generated/order_changes.jsonl")
    args = parser.parse_args()
    run(args.input)
