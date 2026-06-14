# Open Lakehouse with Apache Iceberg

## Business Problem

Traditional data lakes store cheap files but often lack reliable transactions, schema evolution, and consistent multi-engine access. Warehouses solve reliability but can create cost and platform lock-in.

## Solution

This project builds an open lakehouse using Apache Iceberg over S3-compatible MinIO storage. Spark writes curated tables, Nessie manages catalog metadata, and Trino queries the same tables without copying data.

## Recruiter-Relevant Capabilities

- Apache Iceberg ACID tables
- Bronze, silver, and gold data architecture
- Schema evolution without table rewrites
- Hidden partitioning
- Time travel and snapshot inspection
- Data compaction and snapshot expiration
- Multi-engine Spark and Trino access
- Data quality quarantine flow
- CDC-style inserts, updates, and deletes using Iceberg `MERGE`
- Pipeline audit history for operational monitoring
- Dockerized reproducible environment
- Automated tests and GitHub Actions-ready structure

## Resume Bullet

Built an open data lakehouse using Apache Iceberg, Spark, Nessie, MinIO,
and Trino, implementing medallion architecture, CDC-style `MERGE` upserts,
schema evolution, time travel, data quality controls, pipeline auditing,
and multi-engine analytics.

## Recruiter Demo Flow

1. Run the initial bronze, silver, and gold pipeline.
2. Apply an incremental batch containing inserts, updates, and deletes.
3. Display Iceberg snapshot history and query an older snapshot.
4. Add a new column without rewriting existing files.
5. Query the same gold table from Trino to show engine interoperability.
6. Show pipeline audit history and quarantine counts.
