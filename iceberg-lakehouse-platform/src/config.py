from __future__ import annotations

import os


def iceberg_catalog_config() -> dict[str, str]:
    return {
        "nessie_uri": os.getenv("NESSIE_URI", "http://nessie:19120/api/v2"),
        "warehouse": os.getenv("ICEBERG_WAREHOUSE", "s3://warehouse"),
        "minio_endpoint": os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
        "access_key": os.getenv("AWS_ACCESS_KEY_ID", "admin"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", "admin12345"),
        "region": os.getenv("AWS_REGION", "us-east-1"),
    }

