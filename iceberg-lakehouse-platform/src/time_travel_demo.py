from __future__ import annotations

from src.spark_session import create_spark_session


def run() -> None:
    spark = create_spark_session("IcebergTimeTravel")
    snapshots = spark.sql("SELECT snapshot_id, committed_at, operation FROM lakehouse.silver.orders.snapshots ORDER BY committed_at DESC")
    snapshots.show(truncate=False)

    rows = snapshots.collect()
    if len(rows) < 2:
        print("Create another table version before comparing snapshots.")
    else:
        current_id = rows[0]["snapshot_id"]
        previous_id = rows[1]["snapshot_id"]
        print(f"Current snapshot: {current_id}; previous snapshot: {previous_id}")
        spark.sql(f"SELECT COUNT(*) AS previous_row_count FROM lakehouse.silver.orders VERSION AS OF {previous_id}").show()
        spark.sql("SELECT COUNT(*) AS current_row_count FROM lakehouse.silver.orders").show()
    spark.stop()


if __name__ == "__main__":
    run()

