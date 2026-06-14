from __future__ import annotations

from pyspark.sql import SparkSession

from src.config import iceberg_catalog_config


def create_spark_session(app_name: str) -> SparkSession:
    config = iceberg_catalog_config()
    spark = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,org.projectnessie.spark.extensions.NessieSparkSessionExtensions")
        .config("spark.sql.catalog.lakehouse", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.lakehouse.catalog-impl", "org.apache.iceberg.nessie.NessieCatalog")
        .config("spark.sql.catalog.lakehouse.uri", config["nessie_uri"])
        .config("spark.sql.catalog.lakehouse.ref", "main")
        .config("spark.sql.catalog.lakehouse.authentication.type", "NONE")
        .config("spark.sql.catalog.lakehouse.warehouse", config["warehouse"])
        .config("spark.sql.catalog.lakehouse.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config("spark.sql.catalog.lakehouse.s3.endpoint", config["minio_endpoint"])
        .config("spark.sql.catalog.lakehouse.s3.path-style-access", "true")
        .config("spark.sql.catalog.lakehouse.s3.access-key-id", config["access_key"])
        .config("spark.sql.catalog.lakehouse.s3.secret-access-key", config["secret_key"])
        .config("spark.sql.catalog.lakehouse.s3.region", config["region"])
        .config("spark.sql.defaultCatalog", "lakehouse")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark

